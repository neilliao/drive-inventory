"""把 304文書組 的「舊4D資料」承接夾拆平到第一層，並套五位數頂層編碼。

Neil 2026-09-01 拍板「拆平」。規則沿用 docs/specs/2026-08-24-toplevel-5digit-coding.md：
五位數＝硬碟三位數（304）＋資料夾兩位數，沿用各碟原本命名風格（帶點的維持帶點）。

編碼取捨：**盡量沿用 D07xx 原本的後兩碼**，讓認得舊代碼的人不必重學。
唯一例外是 D0700.年度計畫——00 已被骨架「00說明檔」佔用，改配 01。

只搬移＋改名，不複製、不刪除。同一顆共用硬碟內搬移只改 parents，不搬檔案內容。
冪等：已在第一層且已是新名字的，跳過。

用法：
    .venv/bin/python scripts/adhoc/flatten_304_toplevel.py            # dry-run，只印計畫
    .venv/bin/python scripts/adhoc/flatten_304_toplevel.py --execute  # 真的動
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from auth import get_credentials
from crawl import build_drive_service

DRIVE_ID = "0AC47Fb29_4OPUk9PVA"
HOLDING_FOLDER = "舊4D資料"

# 舊名 → 新名（後兩碼沿用 D07xx，年度計畫因 00 被骨架佔用改配 01）
RENAME_MAP = {
    "D0700.年度計畫": "30401.年度計畫",
    "D0711.雲端同步": "30411.雲端同步",
    "D0712.總覽紀錄": "30412.總覽紀錄",
    "D0713.會議記錄": "30413.會議記錄",
    "D0714.中心文書": "30414.中心文書",
    "D0715.請款紀錄": "30415.請款紀錄",
    "D0721.法會文書": "30421.法會文書",
    "D0722.中區文書": "30422.中區文書",
    "D0723.道學詞語": "30423.道學詞語",
    "D0731.專案計畫": "30431.專案計畫",
    "D0732.圖書管理": "30432.圖書管理",
    "D0733.設備紀錄": "30433.設備紀錄",
}

# 骨架（已在第一層，只改名）
SKELETON_MAP = {
    "00說明檔": "30400說明檔",
    "90": "30490",
    "99": "30499",
}

# 這輪不碰：去向未定，等 Neil 拍板
LEAVE_ALONE = {"中心回傳", "峨眉圖書", "峨眉辦事(台灣)", "書籍資料庫"}


def list_children(service, parent_id: str) -> list[dict]:
    out, token = [], None
    while True:
        resp = service.files().list(
            q=f"'{parent_id}' in parents and trashed = false",
            corpora="drive", driveId=DRIVE_ID,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
            fields="nextPageToken, files(id, name, mimeType, parents)",
            pageSize=200, pageToken=token,
        ).execute()
        out.extend(resp.get("files", []))
        token = resp.get("nextPageToken")
        if not token:
            return out


def main() -> None:
    execute = "--execute" in sys.argv
    service = build_drive_service(get_credentials())

    top = list_children(service, DRIVE_ID)
    by_name = {f["name"]: f for f in top}
    print(f"304 第一層現有 {len(top)} 項：{', '.join(sorted(by_name))}\n")

    actions = []

    holding = by_name.get(HOLDING_FOLDER)
    if holding:
        for child in list_children(service, holding["id"]):
            new_name = RENAME_MAP.get(child["name"])
            if not new_name:
                actions.append(("⚠️ 未列在對照表，跳過", child["name"], "", child["id"]))
                continue
            actions.append(("搬到第一層＋改名", child["name"], new_name, child["id"]))
    else:
        print(f"（找不到「{HOLDING_FOLDER}」，可能已拆平）\n")

    for old, new in SKELETON_MAP.items():
        f = by_name.get(old)
        if f:
            actions.append(("改名（已在第一層）", old, new, f["id"]))

    for name in sorted(LEAVE_ALONE & set(by_name)):
        actions.append(("保持不動（去向待拍板）", name, "", by_name[name]["id"]))

    print(f"{'動作':<24}{'現名':<20}{'新名'}")
    for act, old, new, _ in actions:
        print(f"{act:<24}{old:<20}{new}")

    todo = [a for a in actions if a[0].startswith(("搬到", "改名"))]
    print(f"\n要動的共 {len(todo)} 項。")

    if not execute:
        print("\n[dry-run] 沒有動任何東西。確認後加 --execute 再跑一次。")
        return

    print("\n開始施工…")
    ok = fail = 0
    for act, old, new, fid in todo:
        body = {"name": new}
        kwargs = {"fileId": fid, "body": body, "supportsAllDrives": True, "fields": "id, name, parents"}
        if act.startswith("搬到"):
            kwargs["addParents"] = DRIVE_ID
            kwargs["removeParents"] = holding["id"]
        try:
            service.files().update(**kwargs).execute()
            print(f"  ✅ {old} → {new}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ❌ {old}：{exc}")
            fail += 1

    print(f"\n完成：成功 {ok}、失敗 {fail}")

    after = list_children(service, DRIVE_ID)
    print(f"\n施工後第一層 {len(after)} 項：")
    for f in sorted(after, key=lambda x: x["name"]):
        print(f"  {f['name']}")


if __name__ == "__main__":
    main()
