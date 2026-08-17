"""重構計畫產生器（dry-run）：讀爬取快照＋分類映射表，產出搬遷計畫與同碟去重清單。

不碰任何線上資料，純離線推演。輸出兩份 CSV 供人工審核，
執行器（restructure_apply.py，另寫）吃同一份計畫執行。

用法：
    python scripts/restructure_plan.py H
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DRAFT_DIR = ROOT / "docs" / "drafts"

DRIVES = {
    "H": {"id": "0AHPs-tGwoxqjUk9PVA", "name": "未編碼-道義入門與法會錄音", "new_name": "8H.錄音"},
    "I": {"id": "0AEn_l7W8JRb3Uk9PVA", "name": "未編碼-聖歌音樂庫", "new_name": "9I.音樂"},
    "J": {"id": "0ADVhDxVRiDtpUk9PVA", "name": "未編碼-照片庫", "new_name": "10J.照片"},
    "K": {"id": "0AFNMKda95OWUUk9PVA", "name": "未編碼-聖歌專輯與影片", "new_name": "11K.影音"},
}

FOLDER_MIME = "application/vnd.google-apps.folder"
YEAR_RE = re.compile(r"^(19|20)\d{2}")
# 僅在日期格式能被完整辨識時才改名，抓不準就原名保留
DATE_PREFIX_RE = re.compile(r"^((?:19|20)\d{2})[-./年]\s?(\d{1,2})[-./月]\s?(\d{1,2})日?")


def normalize_date_prefix(name: str) -> str:
    m = DATE_PREFIX_RE.match(name)
    if not m:
        return name
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    return f"{y}-{mo:02d}-{d:02d}{name[m.end():]}"


def load_records(drive_id: str) -> list[dict]:
    path = RAW_DIR / f"{drive_id}.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_plan(letter: str) -> None:
    cfg = DRIVES[letter]
    records = load_records(cfg["id"])
    by_id = {r["id"]: r for r in records}
    mapping = pd.read_csv(DRAFT_DIR / f"2026-08-17-{letter}-mapping.csv", dtype=str)

    # 頂層項目：parent 是硬碟根
    top_items = [r for r in records if (r.get("parents") or [None])[0] == cfg["id"]]
    folder_target: dict[str, str] = {}
    file_target: dict[str, str] = {}
    for _, row in mapping.iterrows():
        loc, dest = str(row["現位置"]), str(row["建議歸位"])
        if str(row["層級"]) == "資料夾":
            folder_target[loc] = dest
        else:
            fname = re.sub(r"^\((根目錄|下載夾解散)\) ", "", loc)
            file_target[fname] = dest

    def resolve(dest: str, item_name: str) -> str:
        """把映射表的歸位字串解析成目標路徑（含年夾）。"""
        code = dest.split("（")[0]
        if "入年夾" in dest:
            fixed = re.search(r"入(\d{4})年夾", dest)
            year = fixed.group(1) if fixed else (YEAR_RE.match(item_name).group(0) if YEAR_RE.match(item_name) else "未知年")
            return f"{code}/{year}"
        return code

    plan_rows, skeleton = [], set()
    unmapped = []
    for item in top_items:
        name = item["name"]
        is_folder = item["mimeType"] == FOLDER_MIME
        dest = folder_target.get(name) if is_folder else file_target.get(name)
        if dest is None:
            # 下載夾本身：解散後資料夾留空刪除，子檔在 file_target
            if is_folder and name == "下載":
                plan_rows.append({"動作": "解散後刪空夾", "itemId": item["id"], "類型": "資料夾", "現名": name, "新名": "", "目標路徑": "(垃圾桶)"})
                continue
            unmapped.append(name)
            continue
        target = resolve(dest, name)
        skeleton.add(target)
        new_name = normalize_date_prefix(name) if target.startswith(f"{letter}90") else name
        plan_rows.append({
            "動作": "搬移＋改名" if new_name != name else "搬移",
            "itemId": item["id"], "類型": "資料夾" if is_folder else "檔案",
            "現名": name, "新名": new_name if new_name != name else "",
            "目標路徑": target,
        })

    # 下載夾子檔（K 專用）：一層深的檔案逐檔搬
    download = next((r for r in top_items if r["name"] == "下載" and r["mimeType"] == FOLDER_MIME), None)
    if download:
        for r in records:
            if (r.get("parents") or [None])[0] == download["id"] and r["mimeType"] != FOLDER_MIME:
                dest = file_target.get(r["name"])
                if dest:
                    target = resolve(dest, r["name"])
                    skeleton.add(target)
                    plan_rows.append({"動作": "搬移", "itemId": r["id"], "類型": "檔案", "現名": r["name"], "新名": "", "目標路徑": target})

    # 骨架資料夾（含年夾的父層）
    skeleton_full = set()
    for s in skeleton:
        parts = s.split("/")
        for i in range(1, len(parts) + 1):
            skeleton_full.add("/".join(parts[:i]))

    # 同碟去重：MD5 全在本碟的群組，正本＝目標碼最「正式」（碼號最小）那份
    def code_rank(fid: str) -> int:
        cur = by_id.get(fid)
        while cur is not None:
            pid = (cur.get("parents") or [None])[0]
            if pid == cfg["id"]:
                dest = folder_target.get(cur["name"]) if cur["mimeType"] == FOLDER_MIME else file_target.get(cur["name"])
                if dest:
                    m = re.match(rf"{letter}(\d+)", dest)
                    return int(m.group(1)) if m else 999
                return 999
            cur = by_id.get(pid)
        return 999

    groups = defaultdict(list)
    for r in records:
        if r.get("md5Checksum") and r["mimeType"] != FOLDER_MIME:
            groups[r["md5Checksum"]].append(r)
    dedup_rows, trash_bytes = [], 0
    for md5, grp in groups.items():
        if len(grp) <= 1:
            continue
        grp.sort(key=lambda f: (code_rank(f["id"]), len(f.get("name", ""))))
        keep, rest = grp[0], grp[1:]
        for f in rest:
            trash_bytes += int(f.get("size") or 0)
            dedup_rows.append({"md5": md5, "處置": "刪(進垃圾桶)", "itemId": f["id"], "檔名": f["name"], "MB": round(int(f.get("size") or 0) / 1024**2, 1), "保留正本": keep["name"]})

    plan = pd.DataFrame(plan_rows).sort_values(["目標路徑", "類型"])
    plan.to_csv(DRAFT_DIR / f"2026-08-17-{letter}-moveplan.csv", index=False)
    dedup = pd.DataFrame(dedup_rows)
    dedup.to_csv(DRAFT_DIR / f"2026-08-17-{letter}-dedup-dryrun.csv", index=False)

    n_folder_moves = sum(1 for r in plan_rows if r["類型"] == "資料夾" and r["動作"].startswith("搬移"))
    n_file_moves = sum(1 for r in plan_rows if r["類型"] == "檔案")
    n_renames = sum(1 for r in plan_rows if r["新名"])
    print(f"=== {letter}（{cfg['name']} → {cfg['new_name']}）dry-run ===")
    print(f"建骨架資料夾: {len(skeleton_full)} 個")
    print(f"資料夾搬移: {n_folder_moves} 筆（整棵子樹一次到位）")
    print(f"散檔搬移: {n_file_moves} 筆")
    print(f"改名（日期正規化）: {n_renames} 筆")
    print(f"同碟去重: {len(set(r['md5'] for r in dedup_rows))} 組 / 刪 {len(dedup_rows)} 檔 / 省 {trash_bytes/1024**3:.1f}GB")
    if unmapped:
        print(f"⚠ 映射表沒涵蓋的頂層項目: {unmapped}")
    print(f"計畫: docs/drafts/2026-08-17-{letter}-moveplan.csv")
    print(f"去重: docs/drafts/2026-08-17-{letter}-dedup-dryrun.csv")


if __name__ == "__main__":
    build_plan(sys.argv[1].upper())
