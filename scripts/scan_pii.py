"""掃描 EM 域現役碟的個資候選檔案，輸出可複核的清單。

規則來源：docs/specs/2026-08-20-drive-execution-spec.md 附錄 D，
外加 8/21 銀行帳戶截圖漏網事件後追加的財務詞（附錄 D 建議永久追加）。

與 8/21 那輪的差別：那輪用 Drive API 的 `name contains` 全域查詢，中文分詞不可靠；
本腳本改成完整爬取後在本機用 regex 比對，並重建完整路徑，才能做資料夾層級的複核。

用法：
    .venv/bin/python scripts/scan_pii.py crawl   # 爬碟（.done 標記可中斷續跑）
    .venv/bin/python scripts/scan_pii.py scan    # 只做本機比對與輸出
    .venv/bin/python scripts/scan_pii.py all
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from auth import get_credentials
from crawl import build_drive_service, list_drive_files
from pathbuild import build_path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "pii-scan" / "raw"
OUT_DIR = ROOT / "data" / "pii-scan"

FOLDER_MIME = "application/vnd.google-apps.folder"

# 治理範圍＝EM 域現役碟。非 EM 域（L 靈隱／HX／M／N 友單位）依附錄 F「完全不碰」。
DRIVES = {
    "0AMEB8osSvxu4Uk9PVA": "101公開",
    "0AELmEQKbrV5sUk9PVA": "102治理",
    "0AIOq4cEIifRzUk9PVA": "201課題",
    "0AJmjVqhFJZjMUk9PVA": "202文史",
    "0AKwwg4-IKBjcUk9PVA": "203美工",
    "0AHPs-tGwoxqjUk9PVA": "204錄音",
    "0AEn_l7W8JRb3Uk9PVA": "205音樂",
    "0ADVhDxVRiDtpUk9PVA": "206照片",
    "0AFNMKda95OWUUk9PVA": "207影音",
    "0AGnFkLCFAHSKUk9PVA": "208會議",
    "0ANxgSHDN2zOnUk9PVA": "301弘法組",
    "0AMzUYod8xdA4Uk9PVA": "302學務組",
    "0ACRNcvHbDM-RUk9PVA": "303成全組",
    "0AC47Fb29_4OPUk9PVA": "304文書組",
    "0AFlMw6Ll1bE6Uk9PVA": "305文教組",
    "0AEaE_MeXR4HNUk9PVA": "306庶務組",
    "0AK22bQlRygoDUk9PVA": "307天廚組",
    "0AAzOrSEO680tUk9PVA": "308財務組",
    "0AH6mQBLn8gl2Uk9PVA": "309國外組",
    "0ABMWJuoNcRz6Uk9PVA": "401士林區",
    "0ABuJijGCx15OUk9PVA": "402板橋區",
    "0AOTaD7sMEoBoUk9PVA": "403中壢區",
    "0ACPhX4gNgtDzUk9PVA": "404湖口區",
    "0ACkv4ekF6FQAUk9PVA": "405竹苗區",
    "0ACDGINtmjHA5Uk9PVA": "406北港區",
    "0AJ2KV5BiM2udUk9PVA": "407嘉義區",
    "0ACI0aEupRUbJUk9PVA": "501各國",
    "0AGTyOGkmJvNmUk9PVA": "601綜合班",
    "0AGuS_pyyw4FWUk9PVA": "602線上課程",
    "0ACQbLEnXYbyfUk9PVA": "701道峨眉",
    "0ALoHPaXbmKcEUk9PVA": "801道務平台",
    "0AGBiO_MSMCwoUk9PVA": "902舊人事",
    "0AGpGeYinMki7Uk9PVA": "各區班程(未編碼)",
    "0AH_GumbkmLrlUk9PVA": "資料庫(未編碼)",
    "0APtY8R50aYgCUk9PVA": "4D各組(未編碼)",
    "0AK-5ksRiKswqUk9PVA": "文書組攝影(未編碼)",
}

# 曝險分層＝實際掛在碟上的檢視者群組（2026-08-25 由 permissions().list 實查，非沿用 spec 假設）。
# A：掛 emei-cloud（全組織有職務的前賢，巢狀 21 群）＝命中就是真曝險
# B：只掛 emei-jingli 或單組群＝限閱
# C：只有個人 organizer，無任何群組＝封閉
EXPOSURE_A = {
    "101公開", "201課題", "203美工", "205音樂", "206照片",
    "208會議", "501各國", "601綜合班", "602線上課程", "801道務平台",
}
EXPOSURE_C = {
    "902舊人事", "4D各組(未編碼)", "各區班程(未編碼)",
    "資料庫(未編碼)", "文書組攝影(未編碼)", "701道峨眉",
}

# 已是管制碟：命中不代表要處置，本來就該關在裡面。
CONTROLLED_DRIVES = {"902舊人事"}


def exposure(drive_label: str) -> str:
    if drive_label in EXPOSURE_A:
        return "A 全組織可見"
    if drive_label in EXPOSURE_C:
        return "C 封閉"
    return "B 限閱"

CORE_KEYWORDS = ["名冊", "名單", "人事表", "報名表", "通訊錄", "電話", "住址", "身分證", "個資"]
FINANCE_KEYWORDS = ["帳戶", "存款", "存摺", "銀行", "匯款", "信用卡", "戶名", "帳號"]
# 觀察詞：不列入正式候選，只統計「規則放寬會多出多少」，供是否擴充規則的判斷。
WATCH_KEYWORDS = ["出勤", "簽到", "戶籍", "手機", "地址", "履歷", "聯絡人", "同意書", "身份證"]

HIGH_RISK_EXTS = {".xlsx", ".xls", ".csv", ".docx", ".doc", ".ods", ".odt", ".numbers"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
GSUITE_SHEET_DOC = {
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.document",
}


def _ext(name: str) -> str:
    idx = name.rfind(".")
    return name[idx:].lower() if idx > 0 else ""


def match_keywords(name: str) -> tuple[list[str], list[str]]:
    """回傳 (正式規則命中詞, 觀察詞命中)。"""
    hits = [k for k in CORE_KEYWORDS + FINANCE_KEYWORDS if k in name]
    watch = [k for k in WATCH_KEYWORDS if k in name]
    return hits, watch


def risk_level(name: str, mime: str, hits: list[str]) -> str:
    if not hits:
        return ""
    if mime == FOLDER_MIME:
        return "資料夾"
    ext = _ext(name)
    if ext in HIGH_RISK_EXTS or mime in GSUITE_SHEET_DOC:
        return "高風險"
    if ext in IMAGE_EXTS:
        return "人工複核"
    return "低風險"


def run_crawl(only: list[str] | None = None) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    service = build_drive_service(get_credentials())
    targets = only or list(DRIVES)
    for drive_id in targets:
        label = DRIVES.get(drive_id, drive_id)
        done = RAW_DIR / f"{drive_id}.done"
        if done.exists():
            print(f"[skip] {label} 已完成（{done.read_text().strip()} 筆）")
            continue
        print(f"[crawl] {label} ...", flush=True)
        count = 0
        out = RAW_DIR / f"{drive_id}.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for record in list_drive_files(service, drive_id):
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
        done.write_text(str(count))
        print(f"[done] {label} {count} 筆", flush=True)


def _load_drive(drive_id: str) -> list[dict]:
    path = RAW_DIR / f"{drive_id}.jsonl"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def suggest(drive_label: str, level: str, in_hit_folder: bool) -> str:
    if drive_label in CONTROLLED_DRIVES:
        return "留置管制（已在封存碟）"
    if level == "資料夾":
        return "整夾判定"
    if in_hit_folder:
        return "跟隨所屬資料夾"
    if level == "高風險":
        return "移管制（優先）" if exposure(drive_label) == "A 全組織可見" else "移管制"
    if level == "人工複核":
        return "人工複核（翻拍名冊疑慮）"
    return "抽驗後多為誤判"


def run_scan() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    drive_names = {did: label for did, label in DRIVES.items()}

    rows: list[dict] = []
    watch_only = 0
    totals = Counter()

    for drive_id, label in DRIVES.items():
        records = _load_drive(drive_id)
        if not records:
            print(f"[warn] {label} 沒有資料，尚未爬取？")
            continue
        totals[label] = len(records)
        by_id = {r["id"]: r for r in records}

        # 先找出命中的資料夾，其底下所有檔案都視為「在命中夾內」。
        hit_folder_ids = set()
        for r in records:
            if r.get("mimeType") != FOLDER_MIME:
                continue
            hits, _ = match_keywords(r["name"])
            if hits:
                hit_folder_ids.add(r["id"])

        def inside_hit_folder(rec: dict) -> bool:
            seen = set()
            cur = rec
            while True:
                parents = cur.get("parents") or []
                if not parents:
                    return False
                pid = parents[0]
                if pid in hit_folder_ids:
                    return True
                if pid in seen or pid not in by_id:
                    return False
                seen.add(pid)
                cur = by_id[pid]

        for r in records:
            name = r["name"]
            mime = r.get("mimeType", "")
            hits, watch = match_keywords(name)
            in_folder = False if hits and mime == FOLDER_MIME else inside_hit_folder(r)
            if not hits and not in_folder:
                if watch:
                    watch_only += 1
                continue
            level = risk_level(name, mime, hits) if hits else ("資料夾內檔案" if mime != FOLDER_MIME else "")
            if not level:
                continue
            full_path, _ = build_path(r["id"], by_id, drive_names)
            parent_path = full_path.rsplit("/", 1)[0] if "/" in full_path else full_path
            rows.append(
                {
                    "碟": label,
                    "曝險層": exposure(label),
                    "資料夾路徑": parent_path,
                    "檔名": name,
                    "命中詞": "、".join(hits),
                    "風險級": level,
                    "建議處置": suggest(label, level, in_folder and not hits),
                    "在命中夾內": "是" if in_folder else "",
                    "修改時間": (r.get("modifiedTime") or "")[:10],
                    "檔案id": r["id"],
                }
            )

    files_csv = OUT_DIR / "candidates.csv"
    with open(files_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["碟"])
        w.writeheader()
        w.writerows(rows)

    folder_agg: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in rows:
        folder_agg[(row["碟"], row["資料夾路徑"])][row["風險級"]] += 1

    folder_rows = []
    for (drive, folder), counter in sorted(folder_agg.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counter.values())
        folder_rows.append(
            {
                "碟": drive,
                "資料夾路徑": folder,
                "命中總數": total,
                "高風險": counter["高風險"],
                "人工複核(圖片)": counter["人工複核"],
                "低風險": counter["低風險"],
                "資料夾名命中": counter["資料夾"],
                "夾內連坐": counter["資料夾內檔案"],
                "處置": "",
            }
        )

    folders_csv = OUT_DIR / "by_folder.csv"
    with open(folders_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(folder_rows[0].keys()) if folder_rows else ["碟"])
        w.writeheader()
        w.writerows(folder_rows)

    group_agg: dict[tuple[str, str, str], Counter] = defaultdict(Counter)
    group_samples: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in rows:
        segs = row["資料夾路徑"].split("/")
        key = (row["曝險層"], row["碟"], "/".join(segs[:2]))
        group_agg[key][row["風險級"]] += 1
        if row["風險級"] == "高風險" and len(group_samples[key]) < 5:
            group_samples[key].append(row["檔名"])

    group_rows = []
    for (level, drive, group), counter in sorted(
        group_agg.items(), key=lambda kv: (kv[0][0], -sum(kv[1].values()))
    ):
        group_rows.append(
            {
                "曝險層": level,
                "碟": drive,
                "業務分組": group,
                "命中總數": sum(counter.values()),
                "高風險": counter["高風險"],
                "圖片": counter["人工複核"],
                "低風險": counter["低風險"],
                "夾內連坐": counter["資料夾內檔案"],
                "高風險檔名樣本": " ｜ ".join(group_samples[(level, drive, group)]),
                "處置": "",
                "備註": "",
            }
        )

    groups_csv = OUT_DIR / "by_group.csv"
    with open(groups_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()) if group_rows else ["曝險層"])
        w.writeheader()
        w.writerows(group_rows)

    level_counter = Counter(r["風險級"] for r in rows)
    drive_counter = Counter(r["碟"] for r in rows)

    print()
    print(f"掃描檔案總數：{sum(totals.values()):,}（{len([d for d in totals if totals[d]])} 顆碟）")
    print(f"命中候選：{len(rows):,} 筆，分布在 {len(folder_rows):,} 個資料夾")
    print(f"觀察詞另中（未列入候選）：{watch_only:,} 筆")
    print()
    print("風險級分布：")
    for level, n in level_counter.most_common():
        print(f"  {level}: {n:,}")
    print()
    print("碟別分布（前 15）：")
    for drive, n in drive_counter.most_common(15):
        print(f"  {drive}: {n:,}")
    print()
    exposure_counter = Counter(r["曝險層"] for r in rows)
    print("曝險層分布：")
    for lv, n in sorted(exposure_counter.items()):
        print(f"  {lv}: {n:,}")
    print()
    print(f"輸出：{files_csv}（逐檔）")
    print(f"輸出：{folders_csv}（逐夾 {len(folder_rows)} 列）")
    print(f"輸出：{groups_csv}（業務分組 {len(group_rows)} 列，複核用）")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["crawl", "scan", "all"])
    parser.add_argument("--drive", action="append", help="只跑指定 driveId")
    args = parser.parse_args()

    if args.step in ("crawl", "all"):
        run_crawl(args.drive)
    if args.step in ("scan", "all"):
        run_scan()


if __name__ == "__main__":
    main()
