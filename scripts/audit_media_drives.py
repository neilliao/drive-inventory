"""盤點 205音樂／207影音 兩顆碟：出完整清單＋頂層資料夾摘要。

用途：這兩顆碟是從未整理過的原始庫存（數百個平鋪資料夾），
spec 2026-08-20 §1-4 判定「先寫 audit script 出完整清單再議分類」。
本腳本只讀不寫，輸出 data/audit-media/。

用法：.venv/bin/python scripts/audit_media_drives.py
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from auth import get_credentials
from crawl import build_drive_service, list_drive_files

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "audit-media"

TARGET_DRIVES = {
    "0AEn_l7W8JRb3Uk9PVA": "205音樂",
    "0AFNMKda95OWUUk9PVA": "207影音",
}

FOLDER_MIME = "application/vnd.google-apps.folder"

MEDIA_KINDS = {
    "audio": (".mp3", ".wav", ".m4a", ".wma", ".flac", ".aac", ".aif", ".aiff"),
    "video": (".mp4", ".wmv", ".mov", ".avi", ".mkv", ".mpg", ".mpeg", ".m4v", ".flv", ".rmvb", ".vob", ".ts"),
    "image": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".psd", ".ai"),
    "doc": (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".rtf", ".odt"),
    "archive": (".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".dmg"),
}


def classify(name: str, mime: str) -> str:
    if mime == FOLDER_MIME:
        return "folder"
    if mime.startswith("application/vnd.google-apps"):
        return "gsuite"
    lower = name.lower()
    for kind, exts in MEDIA_KINDS.items():
        if lower.endswith(exts):
            return kind
    return "other"


def crawl_targets(service) -> dict:
    records = {}
    for drive_id, label in TARGET_DRIVES.items():
        count = 0
        for f in list_drive_files(service, drive_id):
            records[f["id"]] = f
            count += 1
        print(f"  {label}: {count} 筆")
    return records


def path_of(file_id: str, records: dict) -> list[str]:
    """回傳從硬碟根往下的資料夾名稱串（不含檔案自己）。"""
    record = records[file_id]
    segments: list[str] = []
    seen = {file_id}
    current = record
    while True:
        parents = current.get("parents") or []
        if not parents:
            break
        parent_id = parents[0]
        if parent_id in seen:
            break
        parent = records.get(parent_id)
        if parent is None:
            break
        segments.append(parent["name"])
        seen.add(parent_id)
        current = parent
    return list(reversed(segments))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    service = build_drive_service(get_credentials())

    print("爬取中…")
    records = crawl_targets(service)
    print(f"合計 {len(records)} 筆")

    rows = []
    for file_id, record in records.items():
        ancestors = path_of(file_id, records)
        kind = classify(record["name"], record.get("mimeType", ""))
        size = int(record.get("size") or 0)
        rows.append(
            {
                "drive": TARGET_DRIVES[record["driveId"]],
                "top_folder": ancestors[0] if ancestors else "(根目錄)",
                "depth": len(ancestors),
                "path": "/".join(ancestors + [record["name"]]),
                "name": record["name"],
                "kind": kind,
                "mime": record.get("mimeType", ""),
                "size_bytes": size,
                "modified": record.get("modifiedTime", ""),
                "created": record.get("createdTime", ""),
                "md5": record.get("md5Checksum", ""),
                "id": file_id,
            }
        )
    rows.sort(key=lambda r: (r["drive"], r["top_folder"], r["path"]))

    detail_path = OUT_DIR / "media-inventory.csv"
    with open(detail_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"明細 → {detail_path}（{len(rows)} 列）")

    # 頂層資料夾摘要：Neil 要看的是「每一格裝什麼、多大、多久沒動」
    buckets: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"files": 0, "folders": 0, "bytes": 0, "kinds": defaultdict(int), "newest": "", "oldest": ""}
    )
    for row in rows:
        bucket = buckets[(row["drive"], row["top_folder"])]
        if row["kind"] == "folder":
            bucket["folders"] += 1
        else:
            bucket["files"] += 1
            bucket["bytes"] += row["size_bytes"]
            bucket["kinds"][row["kind"]] += 1
            modified = row["modified"]
            if modified:
                if not bucket["newest"] or modified > bucket["newest"]:
                    bucket["newest"] = modified
                if not bucket["oldest"] or modified < bucket["oldest"]:
                    bucket["oldest"] = modified

    summary_rows = []
    for (drive, top_folder), bucket in sorted(buckets.items(), key=lambda kv: (kv[0][0], -kv[1]["bytes"])):
        kinds = sorted(bucket["kinds"].items(), key=lambda kv: -kv[1])
        summary_rows.append(
            {
                "drive": drive,
                "top_folder": top_folder,
                "files": bucket["files"],
                "subfolders": bucket["folders"],
                "size_gb": round(bucket["bytes"] / 1024**3, 2),
                "kind_mix": " ".join(f"{k}:{v}" for k, v in kinds),
                "main_kind": kinds[0][0] if kinds else "",
                "oldest_modified": bucket["oldest"][:10],
                "newest_modified": bucket["newest"][:10],
            }
        )

    summary_path = OUT_DIR / "media-top-folders.csv"
    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"頂層摘要 → {summary_path}（{len(summary_rows)} 列）")

    stats = {
        "drives": {},
        "generated_from": "scripts/audit_media_drives.py",
    }
    for drive in TARGET_DRIVES.values():
        drive_rows = [r for r in rows if r["drive"] == drive]
        files = [r for r in drive_rows if r["kind"] != "folder"]
        kind_mix: dict[str, int] = defaultdict(int)
        for r in files:
            kind_mix[r["kind"]] += 1
        stats["drives"][drive] = {
            "total_entries": len(drive_rows),
            "files": len(files),
            "folders": len(drive_rows) - len(files),
            "top_level_folders": len([r for r in drive_rows if r["depth"] == 0 and r["kind"] == "folder"]),
            "max_depth": max((r["depth"] for r in drive_rows), default=0),
            "size_gb": round(sum(r["size_bytes"] for r in files) / 1024**3, 2),
            "kind_mix": dict(sorted(kind_mix.items(), key=lambda kv: -kv[1])),
        }
    (OUT_DIR / "media-stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
