"""指揮爬取、落地、分析、輸出 Sheet 全流程。

用法：
    python scripts/main.py crawl      # 爬 11 顆硬碟到 data/raw/
    python scripts/main.py analyze    # 產出 data/inventory.csv 等分析結果
    python scripts/main.py sheet      # 把分析結果寫進 Google Sheet
    python scripts/main.py all        # 三步驟依序做完
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from analyze import BULK_FOLDER_THRESHOLD, dormant_files, find_duplicate_groups, fold_bulk_folders, summarize_by_drive, top_largest
from auth import get_credentials
from crawl import build_drive_service, list_drive_files
from pathbuild import build_path
from sheet_writer import write_inventory_sheet

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
COMBINED_RAW_PATH = ROOT / "data" / "raw.jsonl"
CSV_PATH = ROOT / "data" / "inventory.csv"

DRIVES = {
    "0AMEB8osSvxu4Uk9PVA": "A.共用資源",
    "0AIOq4cEIifRzUk9PVA": "B.班程教材",
    "0AJmjVqhFJZjMUk9PVA": "C.道務紀錄",
    "0APtY8R50aYgCUk9PVA": "D.各組業務",
    "0ACI0aEupRUbJUk9PVA": "E.國際道場",
    "0AKwwg4-IKBjcUk9PVA": "F.設計素材",
    "0AGBiO_MSMCwoUk9PVA": "G.道親/法會",
    "0AHPs-tGwoxqjUk9PVA": "未編碼-道義入門與法會錄音",
    "0AEn_l7W8JRb3Uk9PVA": "未編碼-聖歌音樂庫",
    "0ADVhDxVRiDtpUk9PVA": "未編碼-照片庫",
    "0AFNMKda95OWUUk9PVA": "未編碼-聖歌專輯與影片",
}

SHEET_HOST_DRIVE_ID = "0AMEB8osSvxu4Uk9PVA"  # A.共用資源，spec 指定放這裡


def run_crawl(drive_ids: list[str] | None = None) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    creds = get_credentials()
    service = build_drive_service(creds)

    targets = drive_ids or list(DRIVES.keys())
    for drive_id in targets:
        done_marker = RAW_DIR / f"{drive_id}.done"
        out_path = RAW_DIR / f"{drive_id}.jsonl"
        if done_marker.exists():
            print(f"[skip] {DRIVES.get(drive_id, drive_id)} 已完成，跳過")
            continue

        print(f"[crawl] {DRIVES.get(drive_id, drive_id)} ({drive_id}) 開始...")
        count = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for record in list_drive_files(service, drive_id):
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
        done_marker.write_text(str(count))
        print(f"[done] {DRIVES.get(drive_id, drive_id)} 共 {count} 筆")


def _load_all_records() -> list[dict]:
    records = []
    for drive_id in DRIVES:
        path = RAW_DIR / f"{drive_id}.jsonl"
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def run_combine() -> list[dict]:
    records = _load_all_records()
    with open(COMBINED_RAW_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[combine] 合併 {len(records)} 筆到 {COMBINED_RAW_PATH}")
    return records


def _file_row(r: dict, path: str) -> dict:
    return {
        "硬碟": DRIVES.get(r.get("driveId"), r.get("driveId")),
        "完整路徑": path,
        "檔名": r.get("name"),
        "類型": r.get("mimeType"),
        "大小(bytes)": int(r["size"]) if r.get("size") else None,
        "建立日": r.get("createdTime"),
        "修改日": r.get("modifiedTime"),
        "最後開啟日": r.get("viewedByMeTime"),
        "擁有者": ", ".join(o.get("displayName", "") for o in r.get("owners", []) or []),
        "連結": f"https://drive.google.com/file/d/{r['id']}/view",
        "md5": r.get("md5Checksum"),
    }


def _folded_summary_row(summary: dict) -> dict:
    return {
        "硬碟": None,
        "完整路徑": summary["folderPath"],
        "檔名": f"⟨已摺疊：{summary['fileCount']}筆檔案，不逐檔列出⟩",
        "類型": f"{summary['topMimeType']} 等",
        "大小(bytes)": summary["totalBytes"],
        "建立日": None,
        "修改日": None,
        "最後開啟日": None,
        "擁有者": None,
        "連結": None,
        "md5": None,
    }


def run_analyze() -> dict:
    records = run_combine()
    id_to_file = {r["id"]: r for r in records}

    ambiguous_count = 0
    full_rows = []
    for r in records:
        path, ambiguous = build_path(r["id"], id_to_file, DRIVES)
        if ambiguous:
            ambiguous_count += 1
        full_rows.append(_file_row(r, path))

    df = pd.DataFrame(full_rows)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"[analyze] 完整索引 {len(df)} 列寫進 {CSV_PATH}（{ambiguous_count} 筆多重 parent，路徑取第一個）")

    # 給人瀏覽的 Sheet「索引」分頁：單一資料夾直屬檔案數超過門檻的摺成一行摘要，
    # 完整明細仍留在 inventory.csv，不影響下面的去重/沉睡區/最大檔統計（那些吃 records 全量）。
    kept, folded = fold_bulk_folders(records, id_to_file, DRIVES)
    sheet_rows = [_file_row(r, build_path(r["id"], id_to_file, DRIVES)[0]) for r in kept]
    sheet_rows += [_folded_summary_row(s) for s in folded]
    sheet_rows.sort(key=lambda row: row["完整路徑"] or "")
    if folded:
        print(f"[analyze] {len(folded)} 個資料夾因檔案數過多摺成摘要（門檻 {BULK_FOLDER_THRESHOLD} 筆），Sheet索引改列 {len(sheet_rows)} 列")

    now = datetime.now(timezone.utc)
    dormant_all = dormant_files(records, now)
    # 「沉睡區」口徑（>5年沒動）在這種歷史錄音檔案庫裡幾乎沒有篩選力，
    # 大部分內容本來就是放著不會再動，全部列出等於又一次幾十萬列問題。
    # 比照「最大檔Top100」的做法，只列最久沒動的前 500 筆，完整統計數字仍保留。
    DORMANT_SHEET_LIMIT = 500
    dormant_for_sheet = sorted(dormant_all, key=lambda f: f.get("modifiedTime") or "")[:DORMANT_SHEET_LIMIT]

    return {
        "records": records,
        "index_rows": sheet_rows,
        "full_index_rows": full_rows,
        "folded_folders": folded,
        "drive_summary": summarize_by_drive(records, DRIVES),
        "duplicate_groups": find_duplicate_groups(records),
        "top_largest": top_largest(records, n=100),
        "dormant": dormant_for_sheet,
        "dormant_total_count": len(dormant_all),
        "generated_at": now.isoformat(),
        "ambiguous_path_count": ambiguous_count,
        "_bulk_threshold": BULK_FOLDER_THRESHOLD,
    }


def run_sheet(analysis: dict | None = None) -> str:
    analysis = analysis or run_analyze()
    creds = get_credentials()
    url = write_inventory_sheet(creds, DRIVES, SHEET_HOST_DRIVE_ID, analysis)
    print(f"[sheet] 完成：{url}")
    return url


def main():
    parser = argparse.ArgumentParser(description="峨眉書院雲端共用硬碟盤點")
    parser.add_argument("step", choices=["crawl", "analyze", "sheet", "all"])
    parser.add_argument("--drive-id", action="append", help="只跑指定的 driveId（可重複），預設全部")
    args = parser.parse_args()

    if args.step == "crawl":
        run_crawl(args.drive_id)
    elif args.step == "analyze":
        run_analyze()
    elif args.step == "sheet":
        run_sheet()
    elif args.step == "all":
        run_crawl(args.drive_id)
        analysis = run_analyze()
        run_sheet(analysis)


if __name__ == "__main__":
    main()
