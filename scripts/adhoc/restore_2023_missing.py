import json, sys, time
sys.path.insert(0, '/Users/liaoneil/projects/drive-inventory/scripts')
from auth import get_credentials
from crawl import build_drive_service, list_drive_files
from googleapiclient.errors import HttpError

DRIVE_208 = "0AGnFkLCFAHSKUk9PVA"
TOP11 = "1BmfNmtGFrD63SDt0Fx_wZrzblzvPC70Y"

svc = build_drive_service(get_credentials())
recs = {f['id']: f for f in list_drive_files(svc, DRIVE_208)}

y2023 = next(r for r in recs.values() if r['name'] == '2023' and (r.get('parents') or [None])[0] == TOP11)
month_dest = {}
for r in recs.values():
    if (r.get('parents') or [None])[0] == y2023['id'] and r['name'].startswith('2023-') and '經理會議附件' in r['name']:
        mm = r['name'][5:7]
        month_dest[mm] = r['id']
print('目的月份夾對照:', month_dest)

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

restore_list = json.load(open('/tmp/2023_restore_list.json'))
results = []
for item in restore_list:
    fid = item['file_id']
    mm = item['month']
    dest = month_dest.get(mm)
    try:
        # 1) untrash
        retry(lambda: svc.files().update(fileId=fid, body={"trashed": False}, supportsAllDrives=True, fields="id,parents").execute())
        # 2) get current parent (should be old 202文史 C02 month folder id, or wherever it was before trash)
        cur = retry(lambda: svc.files().get(fileId=fid, supportsAllDrives=True, fields="id,parents").execute())
        old_parent = (cur.get('parents') or [None])[0]
        if dest:
            retry(lambda: svc.files().update(fileId=fid, addParents=dest, removeParents=old_parent, supportsAllDrives=True, fields="id").execute())
            status = 'restored_and_filed'
        else:
            status = f'restored_no_dest_month_{mm}'
        results.append({**item, 'status': status})
    except HttpError as e:
        results.append({**item, 'status': f'error:{e}'})

json.dump(results, open('/tmp/2023_restore_result.json', 'w'), ensure_ascii=False, indent=2)
from collections import Counter
print(Counter(r['status'] for r in results))
