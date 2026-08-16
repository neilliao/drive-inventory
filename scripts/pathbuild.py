"""從 files.list 撈回的扁平檔案清單，用 parents 重建每個檔案的完整路徑。"""

from __future__ import annotations


def build_path(file_id: str, id_to_file: dict, drive_names: dict) -> tuple[str, bool]:
    """回傳 (完整路徑, 是否有多重 parent 的歧義)。

    從檔案本身往上沿 parents[0] 走，直到走到一個不在 id_to_file 裡的 id
    （代表那就是 Shared Drive 的根，用 driveId 對應的硬碟名稱收尾）。
    """
    record = id_to_file[file_id]
    segments = [record["name"]]
    ambiguous = len(record.get("parents") or []) > 1

    current = record
    seen = {file_id}
    while True:
        parents = current.get("parents") or []
        if not parents:
            break
        parent_id = parents[0]
        if parent_id in seen:
            break
        parent = id_to_file.get(parent_id)
        if parent is None:
            break
        segments.append(parent["name"])
        seen.add(parent_id)
        current = parent

    drive_label = drive_names.get(record.get("driveId"), record.get("driveId") or "?")
    segments.append(drive_label)
    return "/".join(reversed(segments)), ambiguous
