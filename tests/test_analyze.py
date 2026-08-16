import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from analyze import (
    dormant_files,
    find_duplicate_groups,
    fold_bulk_folders,
    is_dormant,
    summarize_by_drive,
    top_largest,
    years_since,
)

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


def test_years_since_computes_fractional_years():
    assert abs(years_since("2024-08-16T00:00:00.000Z", NOW) - 2.0) < 0.02


def test_years_since_none_when_missing():
    assert years_since(None, NOW) is None


def test_is_dormant_true_when_older_than_five_years():
    assert is_dormant("2018-01-01T00:00:00.000Z", NOW) is True


def test_is_dormant_false_when_recent():
    assert is_dormant("2026-01-01T00:00:00.000Z", NOW) is False


def test_find_duplicate_groups_only_keeps_groups_over_one():
    files = [
        {"id": "1", "name": "a.mp3", "md5Checksum": "hash1", "size": "1000"},
        {"id": "2", "name": "a copy.mp3", "md5Checksum": "hash1", "size": "1000"},
        {"id": "3", "name": "b.mp3", "md5Checksum": "hash2", "size": "500"},
    ]
    groups = find_duplicate_groups(files)
    assert len(groups) == 1
    assert groups[0]["count"] == 2
    assert groups[0]["reclaimableBytes"] == 1000


def test_find_duplicate_groups_skips_files_without_md5():
    files = [
        {"id": "1", "name": "doc", "mimeType": "application/vnd.google-apps.document"},
        {"id": "2", "name": "doc2", "mimeType": "application/vnd.google-apps.document"},
    ]
    assert find_duplicate_groups(files) == []


def test_top_largest_sorts_descending_and_caps_at_n():
    files = [{"id": str(i), "size": str(i)} for i in range(150)]
    top = top_largest(files, n=100)
    assert len(top) == 100
    assert top[0]["size"] == "149"


def test_dormant_files_filters_by_age():
    files = [
        {"id": "1", "modifiedTime": "2015-01-01T00:00:00.000Z"},
        {"id": "2", "modifiedTime": "2026-06-01T00:00:00.000Z"},
    ]
    result = dormant_files(files, NOW)
    assert [f["id"] for f in result] == ["1"]


def test_summarize_by_drive_aggregates_correctly():
    files = [
        {"driveId": "d1", "size": "100", "mimeType": "image/jpeg", "modifiedTime": "2024-01-01T00:00:00.000Z"},
        {"driveId": "d1", "size": "200", "mimeType": "image/jpeg", "modifiedTime": "2025-01-01T00:00:00.000Z"},
        {"driveId": "d2", "size": "50", "mimeType": "audio/mpeg", "modifiedTime": "2020-01-01T00:00:00.000Z"},
    ]
    rows = summarize_by_drive(files, {"d1": "照片", "d2": "音檔"})
    by_name = {r["driveName"]: r for r in rows}
    assert by_name["照片"]["fileCount"] == 2
    assert by_name["照片"]["totalBytes"] == 300
    assert by_name["照片"]["oldestModified"].startswith("2024-01-01")
    assert by_name["音檔"]["fileCount"] == 1


def test_fold_bulk_folders_leaves_small_folders_untouched():
    root = {"id": "root", "name": "小資料夾", "mimeType": "application/vnd.google-apps.folder", "parents": ["drive1"], "driveId": "drive1"}
    id_to_file = {"root": root}
    files = [{"id": f"f{i}", "name": f"file{i}", "parents": ["root"], "driveId": "drive1", "size": "10"} for i in range(5)]
    for f in files:
        id_to_file[f["id"]] = f

    kept, folded = fold_bulk_folders([root] + files, id_to_file, {"drive1": "測試"}, threshold=1000)
    assert len(kept) == 5
    assert folded == []


def test_fold_bulk_folders_collapses_folders_over_threshold():
    root = {"id": "root", "name": "黑版畫", "mimeType": "application/vnd.google-apps.folder", "parents": ["drive1"], "driveId": "drive1"}
    id_to_file = {"root": root}
    leaf_files = [
        {"id": f"f{i}", "name": f"{i}_1.AI", "parents": ["root"], "driveId": "drive1", "size": "100", "mimeType": "application/postscript"}
        for i in range(10)
    ]
    for f in leaf_files:
        id_to_file[f["id"]] = f

    kept, folded = fold_bulk_folders([root] + leaf_files, id_to_file, {"drive1": "F.設計素材"}, threshold=5)
    assert kept == []
    assert len(folded) == 1
    assert folded[0]["fileCount"] == 10
    assert folded[0]["totalBytes"] == 1000
    assert folded[0]["folderPath"] == "F.設計素材/黑版畫"
    assert folded[0]["topMimeType"] == "application/postscript"


def test_fold_bulk_folders_mixed_keeps_small_and_folds_large():
    small = {"id": "small", "name": "小資料夾", "mimeType": "application/vnd.google-apps.folder", "parents": ["drive1"], "driveId": "drive1"}
    big = {"id": "big", "name": "大資料夾", "mimeType": "application/vnd.google-apps.folder", "parents": ["drive1"], "driveId": "drive1"}
    id_to_file = {"small": small, "big": big}
    small_files = [{"id": f"s{i}", "name": f"s{i}", "parents": ["small"], "driveId": "drive1", "size": "1"} for i in range(2)]
    big_files = [{"id": f"b{i}", "name": f"b{i}", "parents": ["big"], "driveId": "drive1", "size": "1"} for i in range(20)]
    for f in small_files + big_files:
        id_to_file[f["id"]] = f

    kept, folded = fold_bulk_folders([small, big] + small_files + big_files, id_to_file, {"drive1": "測試"}, threshold=10)
    assert len(kept) == 2
    assert {f["id"] for f in kept} == {"s0", "s1"}
    assert len(folded) == 1
    assert folded[0]["fileCount"] == 20


def test_fold_bulk_folders_picks_nearest_root_ancestor_for_nested_bulk_subtree():
    """檔案分散在很多層小資料夾裡，但整棵子樹疊起來超過門檻，要在最靠近根的那層摺一次，
    不是每層小資料夾各自摺、也不是漏抓。"""
    id_to_file = {
        "A": {"id": "A", "name": "A頂層", "mimeType": "application/vnd.google-apps.folder", "parents": ["drive1"], "driveId": "drive1"},
        "B": {"id": "B", "name": "B次層", "mimeType": "application/vnd.google-apps.folder", "parents": ["A"], "driveId": "drive1"},
    }
    leaf_files = [
        {"id": f"leaf{i}", "name": f"leaf{i}", "parents": ["B"], "driveId": "drive1", "size": "1", "mimeType": "image/png"}
        for i in range(20)
    ]
    for f in leaf_files:
        id_to_file[f["id"]] = f

    all_records = [id_to_file["A"], id_to_file["B"]] + leaf_files
    kept, folded = fold_bulk_folders(all_records, id_to_file, {"drive1": "測試"}, threshold=10)

    assert kept == []
    assert len(folded) == 1
    assert folded[0]["fileCount"] == 20
    assert folded[0]["folderPath"] == "測試/A頂層"


def test_fold_bulk_folders_excludes_folder_records_from_kept():
    id_to_file = {
        "root": {"id": "root", "name": "小資料夾", "mimeType": "application/vnd.google-apps.folder", "parents": ["drive1"], "driveId": "drive1"},
    }
    leaf = {"id": "f1", "name": "file1", "parents": ["root"], "driveId": "drive1", "size": "1"}
    id_to_file["f1"] = leaf
    kept, folded = fold_bulk_folders([id_to_file["root"], leaf], id_to_file, {"drive1": "測試"}, threshold=1000)
    assert kept == [leaf]
    assert folded == []
