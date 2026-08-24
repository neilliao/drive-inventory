"""205音樂 收成 01聖歌/02輕音樂/03禮儀/04音效/05歌詞 五夾（Neil 8/24 拍板）。

規則：
  - 頂層資料夾名稱前綴「聖歌：」→ 01聖歌
  - 前綴「輕音樂：」或裸名「輕音樂」 → 02輕音樂
  - 前綴「禮儀：」→ 03禮儀
  - 前綴「音效：」→ 04音效
  - 8 個散落音檔（無資料夾）→ 進 99 暫存待分類（不硬猜）
  - 另外把 101公開/A03.聖歌（1,055 個慈訓歌詞文字檔，非音檔，媒材不同不合併進 01聖歌）
    整個搬進 05歌詞，維持台語/華語/英語/漢拼子結構

用法：.venv/bin/python scripts/reorg_205_music.py
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

from auth import get_credentials
from crawl import build_drive_service, list_drive_files
from googleapiclient.errors import HttpError

DRIVE_205 = "0AEn_l7W8JRb3Uk9PVA"
DRIVE_101 = "0AMEB8osSvxu4Uk9PVA"


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


def ensure_folder(service, name: str, parent_id: str, existing: dict) -> str:
    for fid, r in existing.items():
        if r["name"] == name and (r.get("parents") or [None])[0] == parent_id:
            return fid
    created = retry(
        lambda: service.files()
        .create(body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}, supportsAllDrives=True, fields="id")
        .execute()
    )
    existing[created["id"]] = {"id": created["id"], "name": name, "parents": [parent_id], "mimeType": "application/vnd.google-apps.folder"}
    return created["id"]


def main() -> None:
    service = build_drive_service(get_credentials())

    print("爬 205音樂…")
    recs205 = {f["id"]: f for f in list_drive_files(service, DRIVE_205)}
    tops = [r for r in recs205.values() if (r.get("parents") or [None])[0] == DRIVE_205]

    bucket_id = {}
    for name in ("01聖歌", "02輕音樂", "03禮儀", "04音效", "05歌詞", "99"):
        existing = next((fid for fid, r in recs205.items() if r["name"] == name and (r.get("parents") or [None])[0] == DRIVE_205), None)
        bucket_id[name] = existing or ensure_folder(service, name, DRIVE_205, recs205)

    def classify(name: str) -> str | None:
        if name.startswith("聖歌："):
            return "01聖歌"
        if name.startswith("輕音樂：") or name == "輕音樂":
            return "02輕音樂"
        if name.startswith("禮儀："):
            return "03禮儀"
        if name.startswith("音效："):
            return "04音效"
        return None

    log_rows = []
    for t in tops:
        if t["id"] in bucket_id.values():
            continue  # 自己就是分類夾，跳過
        dest_name = classify(t["name"])
        if dest_name is None:
            dest_id = bucket_id["99"] if not t["mimeType"].endswith("folder") else None
            if dest_id is None:
                log_rows.append({"name": t["name"], "action": "skip-manual-review", "dest": ""})
                continue
        else:
            dest_id = bucket_id[dest_name]

        old_parent = (t.get("parents") or [None])[0]
        try:
            retry(
                lambda: service.files()
                .update(fileId=t["id"], addParents=dest_id, removeParents=old_parent, supportsAllDrives=True, fields="id")
                .execute()
            )
            status = "ok"
        except HttpError as e:
            status = f"error:{e}"
        log_rows.append({"name": t["name"], "action": dest_name or "99暫存(散檔)", "dest": dest_id, "status": status})

    print(f"205音樂 本體重編：{len(log_rows)} 項")

    # A03.聖歌 → 205音樂/05歌詞
    print("搬 101公開/A03.聖歌 → 205音樂/05歌詞…")
    recs101 = {f["id"]: f for f in list_drive_files(service, DRIVE_101)}
    a03 = next((r for r in recs101.values() if r["name"] == "A03.聖歌"), None)
    if a03 is None:
        print("找不到 A03.聖歌，略過")
    else:
        old_parent = (a03.get("parents") or [None])[0]
        retry(
            lambda: service.files()
            .update(fileId=a03["id"], addParents=bucket_id["05歌詞"], removeParents=old_parent, supportsAllDrives=True, fields="id")
            .execute()
        )
        print("A03.聖歌 已搬進 05歌詞（保留台語/華語/英語/漢拼子結構）")

    out_dir = Path(__file__).resolve().parent.parent / "data" / "audit-media"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "205-reorg-log.csv"
    if log_rows:
        with open(log_path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=["name", "action", "dest", "status"])
            writer.writeheader()
            for r in log_rows:
                r.setdefault("status", "")
                writer.writerow(r)
        print(f"log → {log_path}")


if __name__ == "__main__":
    main()
