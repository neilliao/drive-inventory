import json, sys, time
sys.path.insert(0, '/Users/liaoneil/projects/drive-inventory/scripts')
from auth import get_credentials
from crawl import build_drive_service
from googleapiclient.errors import HttpError

svc = build_drive_service(get_credentials())
plan = json.load(open('/tmp/toplevel_5digit_plan.json'))

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
for p in plan:
    try:
        retry(lambda: svc.files().update(fileId=p['file_id'], body={"name": p['new_name']}, supportsAllDrives=True, fields="id").execute())
        ok += 1
    except HttpError as e:
        errs.append((p['old_name'], str(e)[:150]))
    if ok % 20 == 0:
        print(f"{ok}/{len(plan)}")

print(f"完成：{ok} 成功 / {len(errs)} 失敗")
for e in errs:
    print(" 錯誤:", e)
