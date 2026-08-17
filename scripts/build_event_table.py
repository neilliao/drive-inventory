"""從既有 inventory.csv 產出活動事件總表草稿：把 H/J/K/C/D07 五路裡日期開頭的資料夾（或散檔）
依「日期＋相似活動名」對齊成一列，欄位含錄音／相簿／影片／文件／辦事五種連結。

純離線計算，讀 inventory.csv、寫 CSV，不呼叫任何 Drive API，不會動到任何線上資料。
inventory.csv 裡的「連結」欄是以 file id 組出的 Drive 連結，H 硬碟正在進行中的搬移
不影響這裡算出來的連結有效性（Drive 連結認 id 不認路徑）。

用法：
    python scripts/build_event_table.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from difflib import SequenceMatcher

import pandas as pd

CSV_PATH = "data/inventory.csv"
OUT_PATH = "docs/drafts/2026-08-17-event-table-draft.csv"

DATE_RE = re.compile(r"^((?:19|20)\d{2})[-./年]?\s?(\d{1,2})?[-./月]?\s?(\d{1,2})?")


def date_key(name: str) -> str | None:
    m = DATE_RE.match(str(name))
    if not m or not m.group(2) or not m.group(3):
        return None
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{y}-{mo:02d}-{d:02d}"


EXT_RE = re.compile(r"\.(docx?|pdf|pptx?|xlsx?|mp[34]|m4a|wav|wma|mov|avi|mpg|MP[34]|txt|jpg|png)$", re.IGNORECASE)


def extract(df: pd.DataFrame, drive: str, depth_range: range, must_be_folder: bool = False) -> list[dict]:
    """從指定硬碟抓出「完整路徑」在 depth_range 這幾層裡、名稱帶完整日期的項目。"""
    sub = df[df["硬碟"] == drive]
    if must_be_folder:
        sub = sub[sub["類型"] == "application/vnd.google-apps.folder"]
    out = []
    seen_paths = set()
    for _, r in sub.iterrows():
        parts = str(r["完整路徑"]).split("/")
        is_folder = r["類型"] == "application/vnd.google-apps.folder"
        for depth in depth_range:
            if len(parts) <= depth:
                continue
            seg = parts[depth]
            key = date_key(seg)
            if not key:
                continue
            path_prefix = "/".join(parts[: depth + 1])
            if path_prefix in seen_paths:
                continue
            seen_paths.add(path_prefix)
            display = seg if is_folder else EXT_RE.sub("", seg)
            out.append({"date": key, "name": seg, "display": display, "is_folder": is_folder, "link": r["連結"], "path": path_prefix})
            break
    return out


def main():
    df = pd.read_csv(CSV_PATH, dtype=str)

    sources = {
        "錄音(H)": extract(df, "未編碼-道義入門與法會錄音", range(1, 2)),
        "相簿(J)": extract(df, "未編碼-照片庫", range(2, 3)),
        "影片(K)": extract(df, "未編碼-聖歌專輯與影片", range(1, 2)),
        "文件(C)": extract(df, "C.道務紀錄", range(1, 4)),
        "辦事(D07)": extract(df, "D.各組業務", range(1, 5)),
    }
    # D07 只留 D0721.法會文書 底下的
    sources["辦事(D07)"] = [
        x for x in sources["辦事(D07)"] if "D0721" in x["path"] or "法會文書" in x["path"]
    ]

    for k, v in sources.items():
        print(f"{k}: {len(v)} 個日期鍵資料夾")

    by_date: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for col, items in sources.items():
        for it in items:
            by_date[it["date"]][col].append(it)

    rows = []
    for date in sorted(by_date):
        cols = by_date[date]
        hit_cols = list(cols.keys())
        # 同一天可能有多場：用名稱相似度分群，相似度低於門檻就各自成列並標記待確認
        all_items = [(col, it) for col, items in cols.items() for it in items]
        groups: list[list[tuple]] = []
        for col, it in all_items:
            placed = False
            for g in groups:
                # 跟群組裡任一項比相似度
                if any(SequenceMatcher(None, it["name"], g_it["name"]).ratio() > 0.35 for _, g_it in g):
                    g.append((col, it))
                    placed = True
                    break
            if not placed:
                groups.append([(col, it)])

        multi_group = len(groups) > 1
        for g in groups:
            row = {"日期": date, "活動名": "", "命中來源數": len(set(c for c, _ in g)), "待確認": "是" if multi_group else ""}
            for col in sources:
                row[col] = ""
            # 選活動名：優先資料夾、其次名稱較長者（較長通常較完整）
            best = max(
                (it for _, it in g),
                key=lambda it: (it["is_folder"], len(it["display"])),
            )
            for col, it in g:
                if row[col]:
                    row[col] += " | " + it["link"]
                else:
                    row[col] = it["link"]
            row["活動名"] = best["display"]
            rows.append(row)

    out_df = pd.DataFrame(rows)[["日期", "活動名", "命中來源數", "待確認", "錄音(H)", "相簿(J)", "影片(K)", "文件(C)", "辦事(D07)"]]
    out_df = out_df.sort_values(["日期", "活動名"])
    out_df.to_csv(OUT_PATH, index=False)

    multi_hit = out_df[out_df["命中來源數"] >= 2]
    print(f"\n總列數: {len(out_df)}")
    print(f"命中 ≥2 種來源（真正跨硬碟串起來的活動）: {len(multi_hit)}")
    print(f"命中 ≥3 種來源: {len(out_df[out_df['命中來源數'] >= 3])}")
    print(f"待確認（同天疑似多場撞期）: {len(out_df[out_df['待確認'] == '是'])}")
    print(f"輸出: {OUT_PATH}")


if __name__ == "__main__":
    main()
