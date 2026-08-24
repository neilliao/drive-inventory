"""把 202文史/C02.會議紀錄 依 Neil 8/24 拍板的分類搬進 208會議。

分類規則：
  - 檔名帶「(中心)」前綴 → 靈隱會議紀錄（行程/輪值/拜年 → 行程表；會議記錄/經理會 → 會議記錄；都不中 → 經理記錄附件）
  - 檔名帶其他部門前綴（學務部/法會部/寺務組...） → 一律經理記錄附件
  - 無前綴（峨眉書院自己的） → 依關鍵字分策畫會記錄/聯絡圈記錄/行程表，不中 → 經理記錄附件
  - 各分類底下按原有年份夾維持結構

用法：.venv/bin/python scripts/migrate_c02_to_208.py
輸出：data/audit-media/c02-migration-log.csv（每筆搬移紀錄，可對帳/回復）
"""

from __future__ import annotations

import csv
import re
import time
from pathlib import Path

from auth import get_credentials
from crawl import build_drive_service, list_drive_files
from googleapiclient.errors import HttpError

SRC_DRIVE = "0AJmjVqhFJZjMUk9PVA"  # 202文史
DST_DRIVE = "0AGnFkLCFAHSKUk9PVA"  # 208會議
C02_ID = "1htMtGP1BDJ0EI9CfwGrSp42doHQvdg3B"

TOP_FOLDERS = {
    "靈隱/會議記錄": "10.靈隱會議紀錄",
    "靈隱/行程表": "10.靈隱會議紀錄",
    "峨眉/策畫會記錄": "20.峨眉會議紀錄",
    "峨眉/聯絡圈記錄": "20.峨眉會議紀錄",
    "峨眉/行程表": "20.峨眉會議紀錄",
    "經理記錄附件": None,  # 直接用既有 11.經理記錄附件
}
LEAF_NAME = {
    "靈隱/會議記錄": "會議記錄",
    "靈隱/行程表": "行程表",
    "峨眉/策畫會記錄": "策畫會記錄",
    "峨眉/聯絡圈記錄": "聯絡圈記錄",
    "峨眉/行程表": "行程表",
    "經理記錄附件": None,
}

BRACKET = re.compile(r"^[\(（]([^\)）]+)[\)）]")
YEAR = re.compile(r"^(\d{4})年")

CENTER_RULES = [
    ("行程", "靈隱/行程表"),
    ("輪值", "靈隱/行程表"),
    ("拜年", "靈隱/行程表"),
    ("會議紀錄", "靈隱/會議記錄"),
    ("會議記錄", "靈隱/會議記錄"),
    ("經理會", "靈隱/會議記錄"),
]
EM_RULES = [
    ("聯絡圈", "峨眉/聯絡圈記錄"),
    ("策劃會", "峨眉/策畫會記錄"),
    ("策畫會", "峨眉/策畫會記錄"),
    ("操辦會議", "峨眉/策畫會記錄"),
    ("操持會議", "峨眉/策畫會記錄"),
    ("會議記錄", "峨眉/策畫會記錄"),
    ("會議紀錄", "峨眉/策畫會記錄"),
    ("行程表", "峨眉/行程表"),
    ("道務行程", "峨眉/行程表"),
    ("輪值表", "峨眉/行程表"),
]


def classify(name: str) -> str:
    m = BRACKET.match(name)
    prefix = m.group(1) if m else None
    if prefix == "中心":
        for kw, tag in CENTER_RULES:
            if kw in name:
                return tag
        return "經理記錄附件"
    if prefix is not None:
        return "經理記錄附件"
    for kw, tag in EM_RULES:
        if kw in name:
            return tag
    return "經理記錄附件"


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


def main() -> None:
    service = build_drive_service(get_credentials())

    print("爬 202文史 全碟（重建 parent 關係與既有頂層資料夾 id）…")
    src_records = {f["id"]: f for f in list_drive_files(service, SRC_DRIVE)}
    dst_records = {f["id"]: f for f in list_drive_files(service, DST_DRIVE)}

    dst_top = {r["name"]: fid for fid, r in dst_records.items() if (r.get("parents") or [None])[0] == DST_DRIVE}
    for needed in ("10.靈隱會議紀錄", "20.峨眉會議紀錄", "11.經理記錄附件"):
        if needed not in dst_top:
            raise RuntimeError(f"208會議 缺頂層資料夾 {needed}，請先確認 Drive 現況")

    def under(root_id: str) -> list[dict]:
        out, stack = [], [root_id]
        while stack:
            cur = stack.pop()
            for fid, r in src_records.items():
                if (r.get("parents") or [None])[0] == cur:
                    out.append(r)
                    if r["mimeType"].endswith("folder"):
                        stack.append(fid)
        return out

    def year_of(f: dict) -> str:
        cur = f
        for _ in range(6):
            parents = cur.get("parents") or []
            if not parents:
                break
            parent = src_records.get(parents[0])
            if parent is None:
                break
            m = YEAR.match(parent["name"])
            if m:
                return m.group(1)
            cur = parent
        return "未知年份"

    items = under(C02_ID)
    files = [i for i in items if not i["mimeType"].endswith("folder")]
    print(f"C02.會議紀錄 共 {len(files)} 個檔案，開始分類搬移")

    folder_cache: dict[tuple[str, str], str] = {}

    def leaf_folder_id(bucket: str, year: str) -> str:
        key = (bucket, year)
        if key in folder_cache:
            return folder_cache[key]

        top_name = TOP_FOLDERS[bucket] or "11.經理記錄附件"
        top_id = dst_top[top_name]

        leaf_name = LEAF_NAME[bucket]
        if leaf_name is None:
            mid_id = top_id
        else:
            mid_key = (top_name, leaf_name)
            mid_id = folder_cache.get(("mid", *mid_key))
            if mid_id is None:
                existing = next(
                    (fid for fid, r in dst_records.items() if r["name"] == leaf_name and (r.get("parents") or [None])[0] == top_id),
                    None,
                )
                if existing:
                    mid_id = existing
                else:
                    created = retry(
                        lambda: service.files()
                        .create(
                            body={"name": leaf_name, "mimeType": "application/vnd.google-apps.folder", "parents": [top_id]},
                            supportsAllDrives=True,
                            fields="id",
                        )
                        .execute()
                    )
                    mid_id = created["id"]
                    dst_records[mid_id] = {"id": mid_id, "name": leaf_name, "parents": [top_id], "mimeType": "application/vnd.google-apps.folder"}
                folder_cache[("mid", *mid_key)] = mid_id

        year_id = next(
            (fid for fid, r in dst_records.items() if r["name"] == year and (r.get("parents") or [None])[0] == mid_id),
            None,
        )
        if year_id is None:
            created = retry(
                lambda: service.files()
                .create(
                    body={"name": year, "mimeType": "application/vnd.google-apps.folder", "parents": [mid_id]},
                    supportsAllDrives=True,
                    fields="id",
                )
                .execute()
            )
            year_id = created["id"]
            dst_records[year_id] = {"id": year_id, "name": year, "parents": [mid_id], "mimeType": "application/vnd.google-apps.folder"}

        folder_cache[key] = year_id
        return year_id

    log_rows = []
    done = 0
    for f in files:
        bucket = classify(f["name"])
        year = year_of(f)
        dest_id = leaf_folder_id(bucket, year)
        old_parent = (f.get("parents") or [None])[0]

        try:
            retry(
                lambda: service.files()
                .update(
                    fileId=f["id"],
                    addParents=dest_id,
                    removeParents=old_parent,
                    supportsAllDrives=True,
                    fields="id, parents",
                )
                .execute()
            )
            status = "ok"
        except HttpError as e:
            status = f"error:{e}"

        log_rows.append(
            {
                "file_id": f["id"],
                "name": f["name"],
                "bucket": bucket,
                "year": year,
                "old_parent": old_parent,
                "new_parent": dest_id,
                "status": status,
            }
        )
        done += 1
        if done % 200 == 0:
            print(f"  {done}/{len(files)}")

    out_dir = Path(__file__).resolve().parent.parent / "data" / "audit-media"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "c02-migration-log.csv"
    with open(log_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(log_rows[0].keys()))
        writer.writeheader()
        writer.writerows(log_rows)

    ok = sum(1 for r in log_rows if r["status"] == "ok")
    err = len(log_rows) - ok
    print(f"完成：{ok} 成功 / {err} 失敗，log → {log_path}")


if __name__ == "__main__":
    main()
