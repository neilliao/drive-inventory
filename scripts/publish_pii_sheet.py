"""把 scan_pii.py 的結果寫成一份可複核的 Google Sheet。

放在 902舊人事（只有 neil / admin 兩個 organizer，無任何群組）——
這份清單本身就是通往個資的地圖，不能放在有群組檢視者的碟上。

用法：.venv/bin/python scripts/publish_pii_sheet.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from googleapiclient.discovery import build

from auth import get_credentials

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "pii-scan"
HOST_DRIVE_ID = "0AGBiO_MSMCwoUk9PVA"  # 902舊人事
TITLE = "峨眉個資候選複核 2026-08-25"

DISPOSITIONS = ["移管制", "改走道籍", "留置", "誤判排除"]

NOTES = [
    ["峨眉個資候選複核清單", ""],
    ["產出日期", "2026-08-25"],
    ["掃描範圍", "EM 域 36 顆現役碟，共 391,739 筆檔案／資料夾"],
    ["規則", "附錄 D 九個關鍵字 ＋ 8/21 追加的財務八詞；資料夾名命中者底下檔案整批連坐"],
    ["這份表放這裡的原因", "清單本身是通往個資的地圖，902舊人事 無任何群組檢視者，只有 neil / admin"],
    ["", ""],
    ["曝險層怎麼分的", "2026-08-25 用 permissions().list 實查每顆碟的檢視者群組，不是沿用規格假設"],
    ["A 全組織可見", "碟上掛 emei-cloud（巢狀 21 群）＝有職務的前賢都看得到"],
    ["B 限閱", "只掛 emei-jingli 或單一組群"],
    ["C 封閉", "只有個人 organizer，沒有任何群組"],
    ["", ""],
    ["目前實際曝險", "24 個群組現在只有 neil / admin 兩位 OWNER，沒有真人；也就是說現在處置零風險，等加人就來不及"],
    ["", ""],
    ["處置四選一", "／".join(DISPOSITIONS)],
    ["移管制", "搬進 902舊人事／個資隔離區（待處置）"],
    ["改走道籍", "這類名冊應該是道籍系統的結構化資料，檔案本身封存"],
    ["留置", "原地不動（多半是 B/C 層，或已在管制碟）"],
    ["誤判排除", "關鍵字命中但不是個資，例如空白表格範本、廟務財務記錄"],
    ["", ""],
    ["怎麼用", "在「業務分組」分頁的 處置 欄填一次，底下的檔案跟著走；有例外再去「逐檔明細」分頁單挑"],
]


def _read(name: str) -> list[list[str]]:
    path = OUT_DIR / name
    with open(path, encoding="utf-8-sig") as f:
        return [list(row) for row in csv.reader(f)]


def main() -> None:
    creds = get_credentials()
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)

    file_id = (
        drive.files()
        .create(
            body={
                "name": TITLE,
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "parents": [HOST_DRIVE_ID],
            },
            fields="id",
            supportsAllDrives=True,
        )
        .execute()["id"]
    )

    groups = _read("by_group.csv")
    folders = _read("by_folder.csv")
    files = _read("candidates.csv")

    tabs = {
        "說明": NOTES,
        "業務分組": groups,
        "逐夾": folders,
        "逐檔明細": files,
    }

    existing = sheets.spreadsheets().get(spreadsheetId=file_id, fields="sheets.properties").execute()
    first_id = existing["sheets"][0]["properties"]["sheetId"]

    requests = [
        {"updateSheetProperties": {"properties": {"sheetId": first_id, "title": "說明"}, "fields": "title"}}
    ]
    for title, rows in tabs.items():
        if title == "說明":
            continue
        requests.append(
            {
                "addSheet": {
                    "properties": {
                        "title": title,
                        "gridProperties": {"rowCount": len(rows) + 10, "columnCount": max(len(r) for r in rows) + 2},
                    }
                }
            }
        )
    sheets.spreadsheets().batchUpdate(spreadsheetId=file_id, body={"requests": requests}).execute()

    # 說明分頁也要夠大
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=file_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": first_id, "gridProperties": {"rowCount": len(NOTES) + 10, "columnCount": 4}},
                        "fields": "gridProperties",
                    }
                }
            ]
        },
    ).execute()

    for title, rows in tabs.items():
        sheets.spreadsheets().values().update(
            spreadsheetId=file_id,
            range=f"'{title}'!A1",
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()

    ids = {
        s["properties"]["title"]: s["properties"]["sheetId"]
        for s in sheets.spreadsheets().get(spreadsheetId=file_id, fields="sheets.properties").execute()["sheets"]
    }

    fmt_requests = []
    for title in ("業務分組", "逐夾", "逐檔明細"):
        sid = ids[title]
        fmt_requests += [
            {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            {"setBasicFilter": {"filter": {"range": {"sheetId": sid, "startRowIndex": 0}}}},
            {"repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }},
        ]

    # 業務分組的「處置」欄做成下拉
    gsid = ids["業務分組"]
    header = groups[0]
    col = header.index("處置")
    fmt_requests.append(
        {
            "setDataValidation": {
                "range": {"sheetId": gsid, "startRowIndex": 1, "endRowIndex": len(groups), "startColumnIndex": col, "endColumnIndex": col + 1},
                "rule": {
                    "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": d} for d in DISPOSITIONS]},
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        }
    )
    sheets.spreadsheets().batchUpdate(spreadsheetId=file_id, body={"requests": fmt_requests}).execute()

    url = f"https://docs.google.com/spreadsheets/d/{file_id}/edit"
    print(f"已建立：{url}")
    print(f"業務分組 {len(groups) - 1} 列｜逐夾 {len(folders) - 1} 列｜逐檔 {len(files) - 1} 列")


if __name__ == "__main__":
    main()
