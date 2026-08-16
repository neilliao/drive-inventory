"""遞迴爬取單一 Shared Drive 底下所有檔案，含分頁與指數退避重試。"""

from __future__ import annotations

import time
from collections.abc import Iterator

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

FIELDS = (
    "nextPageToken, files(id, name, mimeType, size, md5Checksum, "
    "createdTime, modifiedTime, viewedByMeTime, owners(displayName,emailAddress), "
    "parents, driveId, trashed, shortcutDetails)"
)


def build_drive_service(creds):
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_drive_files(service, drive_id: str, max_retries: int = 6) -> Iterator[dict]:
    """列出某個 Shared Drive 底下所有未刪除檔案（扁平，靠 parents 之後重建路徑）。"""
    page_token = None
    while True:
        resp = _execute_with_retry(
            service.files().list(
                corpora="drive",
                driveId=drive_id,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                q="trashed = false",
                fields=FIELDS,
                pageSize=1000,
                pageToken=page_token,
            ),
            max_retries=max_retries,
        )
        yield from resp.get("files", [])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break


def _execute_with_retry(request, max_retries: int):
    for attempt in range(max_retries):
        try:
            return request.execute()
        except HttpError as e:
            status = getattr(e.resp, "status", None)
            if status in (429, 500, 503) and attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    raise RuntimeError("unreachable")
