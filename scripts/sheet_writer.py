"""把分析結果寫成一份 Google Sheet，含 spec 要求的六個分頁，首列凍結＋篩選器。"""

from __future__ import annotations

from datetime import datetime, timezone

from googleapiclient.discovery import build

SHEET_TITLES = ["索引", "各硬碟總覽", "重複清單", "最大檔Top100", "沉睡區", "說明"]


def _bytes_to_human(n) -> str:
    if not n:
        return "0"
    n = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def _index_rows(analysis: dict) -> list[list]:
    header = ["硬碟", "完整路徑", "檔名", "類型", "大小(bytes)", "建立日", "修改日", "最後開啟日", "擁有者", "連結"]
    rows = [header]
    for r in analysis["index_rows"]:
        rows.append([r.get(k) for k in header])
    return rows


def _drive_summary_rows(analysis: dict) -> list[list]:
    header = ["硬碟", "檔數", "總大小", "最舊修改", "最新修改"]
    rows = [header]
    for d in analysis["drive_summary"]:
        rows.append(
            [d["driveName"], d["fileCount"], _bytes_to_human(d["totalBytes"]), d["oldestModified"], d["newestModified"]]
        )
    return rows


def _duplicate_rows(analysis: dict) -> list[list]:
    header = ["MD5", "筆數", "單筆大小", "可省空間", "檔名與連結（同群）"]
    rows = [header]
    for g in analysis["duplicate_groups"]:
        names = "; ".join(
            f"{f.get('name')} (https://drive.google.com/file/d/{f['id']}/view)" for f in g["files"]
        )
        rows.append([g["md5Checksum"], g["count"], _bytes_to_human(g["sizeEach"]), _bytes_to_human(g["reclaimableBytes"]), names])
    return rows


def _top_largest_rows(analysis: dict) -> list[list]:
    header = ["檔名", "大小", "硬碟", "修改日", "連結"]
    rows = [header]
    drive_names = analysis.get("_drive_names", {})
    for f in analysis["top_largest"]:
        drive_name = drive_names.get(f.get("driveId"), f.get("driveId"))
        size = int(f["size"]) if f.get("size") else 0
        rows.append([f.get("name"), _bytes_to_human(size), drive_name, f.get("modifiedTime"), f"https://drive.google.com/file/d/{f['id']}/view"])
    return rows


def _dormant_rows(analysis: dict) -> list[list]:
    header = ["檔名", "硬碟", "修改日", "連結"]
    rows = [header]
    drive_names = analysis.get("_drive_names", {})
    for f in analysis["dormant"]:
        drive_name = drive_names.get(f.get("driveId"), f.get("driveId"))
        rows.append([f.get("name"), drive_name, f.get("modifiedTime"), f"https://drive.google.com/file/d/{f['id']}/view"])
    return rows


def _notes_rows(analysis: dict) -> list[list]:
    folded = analysis.get("folded_folders") or []
    rows = [
        ["說明"],
        ["產製時間", analysis["generated_at"]],
        ["索引總列數", str(len(analysis["index_rows"]))],
        ["多重 parent（路徑取第一個）筆數", str(analysis["ambiguous_path_count"])],
        ["沉睡區口徑", f"最後修改時間距今 > 5 年，全庫共 {analysis.get('dormant_total_count', '?')} 筆符合，Sheet 只列最久沒動的前 {len(analysis['dormant'])} 筆"],
        ["重複判定口徑", "md5Checksum 完全相同；Google 原生 Docs/Sheets/Slides 沒有 md5，不參與比對"],
        ["資料來源", "Google Drive API files.list，corpora=drive，唯讀爬取"],
    ]
    if folded:
        rows.append(
            [
                "索引摺疊規則",
                f"單一資料夾直屬檔案數超過 {analysis.get('_bulk_threshold', '?')} 筆的，索引分頁改列一行摘要不逐檔列（共 {len(folded)} 個資料夾），完整逐檔明細在專案本機的 data/inventory.csv，去重/沉睡區/最大檔統計仍算全部檔案",
            ]
        )
    return rows


def _get_sheet_ids(sheets_service, spreadsheet_id: str) -> dict:
    meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields="sheets.properties").execute()
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}


def write_inventory_sheet(creds, drive_names: dict, host_drive_id: str, analysis: dict) -> str:
    analysis = {**analysis, "_drive_names": drive_names}

    drive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
    sheets_service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    file_metadata = {
        "name": f"全組織檔案地圖 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [host_drive_id],
    }
    spreadsheet_file = (
        drive_service.files().create(body=file_metadata, fields="id", supportsAllDrives=True).execute()
    )
    spreadsheet_id = spreadsheet_file["id"]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {"updateSheetProperties": {"properties": {"sheetId": 0, "title": SHEET_TITLES[0]}, "fields": "title"}}
            ]
            + [{"addSheet": {"properties": {"title": title}}} for title in SHEET_TITLES[1:]]
        },
    ).execute()

    data = {
        "索引": _index_rows(analysis),
        "各硬碟總覽": _drive_summary_rows(analysis),
        "重複清單": _duplicate_rows(analysis),
        "最大檔Top100": _top_largest_rows(analysis),
        "沉睡區": _dormant_rows(analysis),
        "說明": _notes_rows(analysis),
    }

    _resize_grids(sheets_service, spreadsheet_id, data)
    _write_values(sheets_service, spreadsheet_id, data)
    _freeze_and_filter(sheets_service, spreadsheet_id, data)

    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def _resize_grids(sheets_service, spreadsheet_id: str, data: dict) -> None:
    """新分頁預設格線只有 1000 列，資料超過的話 values.update 會直接 400。
    寫值之前先把每個分頁的格線撐大到裝得下。"""
    sheet_id_by_title = _get_sheet_ids(sheets_service, spreadsheet_id)
    requests = []
    for title, rows in data.items():
        if not rows:
            continue
        sheet_id = sheet_id_by_title[title]
        requests.append(
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "rowCount": len(rows) + 10,
                            "columnCount": max(len(rows[0]) + 2, 26),
                        },
                    },
                    "fields": "gridProperties.rowCount,gridProperties.columnCount",
                }
            }
        )
    if requests:
        sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()


def _write_values(sheets_service, spreadsheet_id: str, data: dict) -> None:
    """索引分頁可能有上萬列，分批寫避免單次 payload 過大。"""
    CHUNK = 5000
    for title, rows in data.items():
        if not rows:
            continue
        for start in range(0, len(rows), CHUNK):
            chunk = rows[start : start + CHUNK]
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{title}!A{start + 1}",
                valueInputOption="RAW",
                body={"values": chunk},
            ).execute()


def _freeze_and_filter(sheets_service, spreadsheet_id: str, data: dict) -> None:
    sheet_id_by_title = _get_sheet_ids(sheets_service, spreadsheet_id)
    requests = []
    for title, rows in data.items():
        if not rows:
            continue
        sheet_id = sheet_id_by_title[title]
        requests.append(
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }
            }
        )
        requests.append(
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": len(rows),
                            "startColumnIndex": 0,
                            "endColumnIndex": len(rows[0]),
                        }
                    }
                }
            }
        )
    if requests:
        sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
