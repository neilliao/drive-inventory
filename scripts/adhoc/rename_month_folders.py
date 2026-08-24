import json, sys, time
sys.path.insert(0, '/Users/liaoneil/projects/drive-inventory/scripts')
from auth import get_credentials
from crawl import build_drive_service
from googleapiclient.errors import HttpError

svc = build_drive_service(get_credentials())
plan = json.load(open('/tmp/rename_plan.json'))

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

ok = 0
errs = []
for year, fid, old_name, new_name in plan:
    try:
        retry(lambda: svc.files().update(fileId=fid, body={"name": new_name}, supportsAllDrives=True, fields="id").execute())
        ok += 1
    except HttpError as e:
        errs.append((fid, old_name, str(e)[:120]))
    if ok % 30 == 0:
        print(f"{ok}/{len(plan)}")

print(f"完成：{ok} 成功 / {len(errs)} 失敗")
for e in errs:
    print(" 錯誤:", e)
