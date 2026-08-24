"""把 208會議/11.經理記錄附件 底下的年份平鋪檔案拆回月份子夾。

C02→208 搬移時只保留了年份、遺失了月份分層（Neil 8/24 發現：某些年份
單層塞 100-280 個檔，2013 年最多 280 個，不好找）。查證後只有
11.經理記錄附件 有這個問題（10/20 底下五個分類每年最多 74 檔，不拆）。

月份來源三層 fallback：
  1. migration log 記錄的 old_parent（202文史 C02 底下的原始「YYYY年MM月OO紀錄」
     資料夾，該資料夾殼還留著未刪，可回查名稱）→ 89% 檔案適用
  2. 檔名裡抓得到日期（西元 YYYY-MM 或 YYYYMMDD 或民國 YYY.MM 開頭）→ 次選
  3. 都抓不到 → 用檔案 modifiedTime 的月份，並在 log 標記 source=modified_time_fallback
     方便 Neil 抽查

用法：.venv/bin/python scripts/split_managers_by_month.py
"""

from __future__ import annotations

import csv
import re
import time
from pathlib import Path

from auth import get_credentials
from crawl import build_drive_service, list_drive_files
from googleapiclient.errors import HttpError

DRIVE_208 = "0AGnFkLCFAHSKUk9PVA"
DRIVE_202 = "0AJmjVqhFJZjMUk9PVA"
MIGRATION_LOG = Path(__file__).resolve().parent.parent / "data" / "audit-media" / "c02-migration-log.csv"

MONTH_FROM_FOLDER_NAME = re.compile(r"^\d{4}年(\d{1,2})月")
FILENAME_YMD = re.compile(r"(?:19|20)\d{2}[-.](\d{1,2})[-.]\d{1,2}")
FILENAME_YMD_COMPACT = re.compile(r"(?:19|20)\d{2}(\d{2})\d{2}")
FILENAME_ROC = re.compile(r"\b1\d{2}[.\-](\d{1,2})[.\-]\d{1,2}\b")  # 民國年.月.日 如 113.12.04


def retry(call, max_retries=6):
    for attempt in range(max_retries):
        try:
            return call()
        except HttpError as e:
            status = getattr(e.resp, "status", None)
            if status in (403, 429, 500, 503) and attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    raise RuntimeError("unreachable")


def month_from_filename(name: str) -> str | None:
    for pattern in (FILENAME_YMD, FILENAME_ROC, FILENAME_YMD_COMPACT):
        m = pattern.search(name)
        if m:
            mm = int(m.group(1))
            if 1 <= mm <= 12:
                return f"{mm:02d}"
    return None


def main() -> None:
    service = build_drive_service(get_credentials())

    print("讀 migration log…")
    log_by_file = {}
    with open(MIGRATION_LOG, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            log_by_file[row["file_id"]] = row

    print("爬 202文史（回查原始月份資料夾名稱，資料夾殼還在）…")
    recs202 = {f["id"]: f for f in list_drive_files(service, DRIVE_202)}

    print("爬 208會議…")
    recs208 = {f["id"]: f for f in list_drive_files(service, DRIVE_208)}

    top11 = next(r for r in recs208.values() if r["name"] == "11.經理記錄附件")
    year_folders = {r["name"]: r["id"] for r in recs208.values() if (r.get("parents") or [None])[0] == top11["id"]}

    files = [r for r in recs208.values() if not r["mimeType"].endswith("folder") and recs208.get((r.get("parents") or [None])[0], {}).get("id") in year_folders.values()]
    print(f"11.經理記錄附件 底下共 {len(files)} 個檔案（平鋪）")

    month_dir_cache: dict[tuple[str, str], str] = {}

    def month_folder_id(year: str, month: str) -> str:
        key = (year, month)
        if key in month_dir_cache:
            return month_dir_cache[key]
        year_id = year_folders[year]
        name = f"{month}月"
        existing = next((fid for fid, r in recs208.items() if r["name"] == name and (r.get("parents") or [None])[0] == year_id), None)
        if existing:
            month_dir_cache[key] = existing
            return existing
        created = retry(
            lambda: service.files()
            .create(body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [year_id]}, supportsAllDrives=True, fields="id")
            .execute()
        )
        recs208[created["id"]] = {"id": created["id"], "name": name, "parents": [year_id], "mimeType": "application/vnd.google-apps.folder"}
        month_dir_cache[key] = created["id"]
        return created["id"]

    log_rows = []
    source_counts = {"log": 0, "filename": 0, "modified_time_fallback": 0, "no_year_skip": 0}

    for f in files:
        year_id = (f.get("parents") or [None])[0]
        year_name = recs208.get(year_id, {}).get("name")
        if year_name not in year_folders:
            source_counts["no_year_skip"] += 1
            continue

        month = None
        source = None

        log_row = log_by_file.get(f["id"])
        if log_row:
            old_parent = recs202.get(log_row["old_parent"])
            if old_parent:
                m = MONTH_FROM_FOLDER_NAME.match(old_parent["name"])
                if m:
                    month = f"{int(m.group(1)):02d}"
                    source = "log"

        if month is None:
            month = month_from_filename(f["name"])
            if month:
                source = "filename"

        if month is None:
            modified = f.get("modifiedTime", "")
            if len(modified) >= 7:
                month = modified[5:7]
                source = "modified_time_fallback"

        if month is None:
            source_counts["no_year_skip"] += 1
            continue

        source_counts[source] += 1
        dest_id = month_folder_id(year_name, month)

        try:
            retry(
                lambda: service.files()
                .update(fileId=f["id"], addParents=dest_id, removeParents=year_id, supportsAllDrives=True, fields="id")
                .execute()
            )
            status = "ok"
        except HttpError as e:
            status = f"error:{e}"

        log_rows.append({"file_id": f["id"], "name": f["name"], "year": year_name, "month": month, "source": source, "status": status})

    print("來源分布：", source_counts)

    out_path = Path(__file__).resolve().parent.parent / "data" / "audit-media" / "managers-month-split-log.csv"
    if log_rows:
        with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=["file_id", "name", "year", "month", "source", "status"])
            writer.writeheader()
            writer.writerows(log_rows)
    ok = sum(1 for r in log_rows if r["status"] == "ok")
    print(f"完成：{ok} 成功 / {len(log_rows)-ok} 失敗，log → {out_path}")


if __name__ == "__main__":
    main()
