"""盤點 304文書組：出兩層資料夾摘要＋完整明細。

用途：304 第一層是「舊4D資料」承接夾（D07 搬入 10,712 檔）＋既有雜物夾，
2026-08-24 五位數編碼把它列為「暫不套用」的 17 顆之一，要先定分類。
本腳本只讀不寫，輸出 data/audit-304/。

用法：.venv/bin/python scripts/adhoc/audit_304_wenshu.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from auth import get_credentials
from crawl import build_drive_service, list_drive_files

OUT_DIR = ROOT / "data" / "audit-304"
DRIVE_ID = "0AC47Fb29_4OPUk9PVA"
DRIVE_NAME = "304文書組"
FOLDER_MIME = "application/vnd.google-apps.folder"

KINDS = {
    "doc": (".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf"),
    "sheet": (".xls", ".xlsx", ".csv"),
    "slide": (".ppt", ".pptx"),
    "image": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".psd", ".ai"),
    "audio": (".mp3", ".wav", ".m4a", ".wma", ".flac"),
    "video": (".mp4", ".wmv", ".mov", ".avi", ".mkv", ".mpg", ".m4v"),
    "archive": (".zip", ".rar", ".7z"),
}


def classify(name: str, mime: str) -> str:
    if mime == FOLDER_MIME:
        return "folder"
    if mime.startswith("application/vnd.google-apps"):
        return "gsuite"
    lower = name.lower()
    for kind, exts in KINDS.items():
        if lower.endswith(exts):
            return kind
    return "other"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    service = build_drive_service(get_credentials())

    items = {}
    for f in list_drive_files(service, DRIVE_ID):
        items[f["id"]] = f
    print(f"抓到 {len(items)} 個項目")

    def parent_of(f):
        p = f.get("parents") or []
        return p[0] if p else None

    # 從每個項目往上走到根，記錄第一層與第二層祖先
    def ancestry(fid):
        chain = []
        seen = set()
        cur = fid
        while cur and cur in items and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            cur = parent_of(items[cur])
        chain.reverse()  # 由上而下（不含 drive 根）
        return chain

    rows = []
    for fid, f in items.items():
        chain = ancestry(fid)
        lvl1 = items[chain[0]]["name"] if len(chain) >= 1 else "(根目錄)"
        lvl2 = items[chain[1]]["name"] if len(chain) >= 2 else ""
        depth = len(chain)
        size = int(f.get("size") or 0)
        rows.append({
            "第一層": lvl1,
            "第二層": lvl2,
            "深度": depth,
            "名稱": f["name"],
            "類型": classify(f["name"], f["mimeType"]),
            "bytes": size,
            "建立日": (f.get("createdTime") or "")[:10],
            "修改日": (f.get("modifiedTime") or "")[:10],
            "擁有者": (f.get("owners") or [{}])[0].get("emailAddress", ""),
            "連結": f"https://drive.google.com/file/d/{fid}/view",
        })

    detail = OUT_DIR / "304-inventory.csv"
    with detail.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def summarize(keyfn, path, headers):
        agg = defaultdict(lambda: {"檔": 0, "夾": 0, "bytes": 0, "kinds": defaultdict(int),
                                   "最舊": "9999", "最新": "0000"})
        for r in rows:
            k = keyfn(r)
            a = agg[k]
            if r["類型"] == "folder":
                a["夾"] += 1
            else:
                a["檔"] += 1
                a["kinds"][r["類型"]] += 1
            a["bytes"] += r["bytes"]
            if r["修改日"]:
                a["最舊"] = min(a["最舊"], r["修改日"])
                a["最新"] = max(a["最新"], r["修改日"])
        out = []
        for k, a in agg.items():
            kinds = sorted(a["kinds"].items(), key=lambda kv: -kv[1])
            row = dict(zip(headers, k if isinstance(k, tuple) else (k,)))
            row.update({
                "檔": a["檔"], "夾": a["夾"],
                "GB": round(a["bytes"] / 1024**3, 3),
                "型別": " ".join(f"{n}:{c}" for n, c in kinds[:4]),
                "最舊": a["最舊"] if a["最舊"] != "9999" else "",
                "最新": a["最新"] if a["最新"] != "0000" else "",
            })
            out.append(row)
        out.sort(key=lambda r: -r["檔"])
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
        return out

    lvl1 = summarize(lambda r: r["第一層"], OUT_DIR / "304-level1.csv", ["第一層"])
    lvl2 = summarize(lambda r: (r["第一層"], r["第二層"]), OUT_DIR / "304-level2.csv", ["第一層", "第二層"])

    print(f"\n=== {DRIVE_NAME} 第一層 ===")
    print(f"{'資料夾':<20}{'檔':>7}{'夾':>6}{'GB':>9}  {'型別':<28}{'最舊':<12}{'最新':<12}")
    for r in lvl1:
        print(f"{r['第一層']:<20}{r['檔']:>7}{r['夾']:>6}{r['GB']:>9.2f}  {r['型別']:<28}{r['最舊']:<12}{r['最新']:<12}")
    total_f = sum(r["檔"] for r in lvl1)
    total_d = sum(r["夾"] for r in lvl1)
    print(f"\n合計：{total_f} 檔、{total_d} 夾、{round(sum(r['GB'] for r in lvl1), 2)} GB")
    print(f"輸出：{detail}、304-level1.csv、304-level2.csv")


if __name__ == "__main__":
    main()
