"""從落地的檔案清單算出 spec 要的四個統計面向：多大、多舊、哪些重複、各硬碟總覽。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from pathbuild import build_path

DORMANT_YEARS = 5
BULK_FOLDER_THRESHOLD = 1000


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def years_since(modified_time: str | None, now: datetime) -> float | None:
    dt = _parse_time(modified_time)
    if dt is None:
        return None
    return (now - dt).days / 365.25


def is_dormant(modified_time: str | None, now: datetime, years: int = DORMANT_YEARS) -> bool:
    age = years_since(modified_time, now)
    return age is not None and age > years


def find_duplicate_groups(files: list[dict]) -> list[dict]:
    """依 md5Checksum 分組，只留下筆數 > 1 的群組，並估算可省空間。

    沒有 md5Checksum 的檔案（Google 原生 Docs/Sheets/Slides）一律跳過，
    這些交給呼叫端另外用「同名候選」處理，不在這裡誤判為重複。
    """
    by_md5: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        md5 = f.get("md5Checksum")
        if md5:
            by_md5[md5].append(f)

    groups = []
    for md5, group in by_md5.items():
        if len(group) <= 1:
            continue
        sizes = [int(f["size"]) for f in group if f.get("size")]
        size = sizes[0] if sizes else 0
        groups.append(
            {
                "md5Checksum": md5,
                "count": len(group),
                "sizeEach": size,
                "reclaimableBytes": size * (len(group) - 1),
                "files": group,
            }
        )
    groups.sort(key=lambda g: g["reclaimableBytes"], reverse=True)
    return groups


def top_largest(files: list[dict], n: int = 100) -> list[dict]:
    sized = [f for f in files if f.get("size")]
    return sorted(sized, key=lambda f: int(f["size"]), reverse=True)[:n]


def dormant_files(files: list[dict], now: datetime, years: int = DORMANT_YEARS) -> list[dict]:
    return [f for f in files if is_dormant(f.get("modifiedTime"), now, years)]


def _is_folder(f: dict) -> bool:
    return f.get("mimeType") == "application/vnd.google-apps.folder"


def _children_map(files: list[dict]) -> dict:
    children: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        parent = (f.get("parents") or [None])[0]
        children[parent].append(f)
    return children


def _descendant_leaf_counts(files: list[dict]) -> dict:
    """回傳 {資料夾id: 底下所有葉檔案（不含資料夾本身）的遞迴總數}，記憶化後序遍歷。"""
    children = _children_map(files)
    memo: dict[str, int] = {}

    def count(folder_id: str) -> int:
        if folder_id in memo:
            return memo[folder_id]
        total = 0
        for child in children.get(folder_id, []):
            total += count(child["id"]) if _is_folder(child) else 1
        memo[folder_id] = total
        return total

    for f in files:
        if _is_folder(f):
            count(f["id"])
    return memo


def _nearest_root_fold_ancestor(file_record: dict, id_to_file: dict, descendant_counts: dict, threshold: int):
    """從檔案往上找祖先資料夾鏈，回傳「最靠近硬碟根、且遞迴檔案數仍超過門檻」的資料夾 id。

    找不到符合的祖先就回傳 None（代表這個檔案不用摺疊，維持逐檔列出）。
    """
    fold_point = None
    current = file_record
    seen: set[str] = set()
    while True:
        parents = current.get("parents") or []
        if not parents:
            break
        parent_id = parents[0]
        if parent_id in seen:
            break
        seen.add(parent_id)
        parent = id_to_file.get(parent_id)
        if parent is None:
            break
        if descendant_counts.get(parent_id, 0) > threshold:
            fold_point = parent_id  # 持續往外層覆寫，留下最靠近根的那個
        current = parent
    return fold_point


def fold_bulk_folders(
    files: list[dict], id_to_file: dict, drive_names: dict, threshold: int = BULK_FOLDER_THRESHOLD
) -> tuple[list[dict], list[dict]]:
    """把遞迴檔案數超過門檻的資料夾子樹，從逐檔列表收斂成一行摘要。

    用「遞迴」總數判斷，不是只看資料夾直屬子項——爆量檔案常常是分散在很多層小資料夾裡
    （例如一堆按編號分類的小資料夾，每個都沒超過門檻，但整棵子樹疊起來是幾十萬筆）。
    找的是「最靠近硬碟根、遞迴總數仍超過門檻」的那一層，同一個爆量子樹只會產生一筆摘要，
    不會每層資料夾各自摺一次。

    只影響「索引」分頁要不要逐檔列出，不影響去重/沉睡區/最大檔這些統計
    （那些呼叫端要用完整的 files 清單去算，不要用這裡回傳的 kept）。
    資料夾本身（mimeType 是資料夾）不會出現在 kept 或摘要的檔案清單裡，只當路徑的一部分。

    回傳 (kept, folded_summaries)：
    - kept：不屬於爆量子樹的檔案，維持逐檔列出
    - folded_summaries：每個被摺疊的資料夾子樹一筆摘要
    """
    descendant_counts = _descendant_leaf_counts(files)

    kept: list[dict] = []
    fold_groups: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        if _is_folder(f):
            continue
        fold_point = _nearest_root_fold_ancestor(f, id_to_file, descendant_counts, threshold)
        if fold_point is None:
            kept.append(f)
        else:
            fold_groups[fold_point].append(f)

    folded_summaries = []
    for folder_id, group in fold_groups.items():
        sizes = [int(f["size"]) for f in group if f.get("size")]
        mime_counts: dict[str, int] = defaultdict(int)
        for f in group:
            mime_counts[f.get("mimeType", "?")] += 1
        top_mime = max(mime_counts.items(), key=lambda kv: kv[1])[0] if mime_counts else "?"

        if folder_id in id_to_file:
            folder_path, _ = build_path(folder_id, id_to_file, drive_names)
        else:
            drive_id = group[0].get("driveId") if group else None
            folder_path = f"{drive_names.get(drive_id, drive_id)}/(資料夾未在索引中)"

        folded_summaries.append(
            {
                "folderPath": folder_path,
                "fileCount": len(group),
                "totalBytes": sum(sizes),
                "topMimeType": top_mime,
                "mimeTypeCounts": dict(mime_counts),
            }
        )
    return kept, folded_summaries


def summarize_by_drive(files: list[dict], drive_names: dict) -> list[dict]:
    """各硬碟總覽：檔數 / 總大小 / 類型分佈 / 最舊 / 最新。"""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for f in files:
        grouped[f.get("driveId") or "?"].append(f)

    rows = []
    for drive_id, group in grouped.items():
        sizes = [int(f["size"]) for f in group if f.get("size")]
        mtimes = [_parse_time(f.get("modifiedTime")) for f in group]
        mtimes = [m for m in mtimes if m is not None]
        mime_counts: dict[str, int] = defaultdict(int)
        for f in group:
            mime_counts[f.get("mimeType", "?")] += 1
        rows.append(
            {
                "driveId": drive_id,
                "driveName": drive_names.get(drive_id, drive_id),
                "fileCount": len(group),
                "totalBytes": sum(sizes),
                "mimeTypeCounts": dict(mime_counts),
                "oldestModified": min(mtimes).isoformat() if mtimes else None,
                "newestModified": max(mtimes).isoformat() if mtimes else None,
            }
        )
    rows.sort(key=lambda r: r["driveName"])
    return rows
