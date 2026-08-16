import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pathbuild import build_path


def make_id_map(*records):
    return {r["id"]: r for r in records}


def test_top_level_file_resolves_to_drive_name():
    id_map = make_id_map(
        {"id": "f1", "name": "表格.pdf", "parents": ["drive1"], "driveId": "drive1"},
    )
    path, ambiguous = build_path("f1", id_map, {"drive1": "A.公開"})
    assert path == "A.公開/表格.pdf"
    assert ambiguous is False


def test_nested_folders_build_full_chain():
    id_map = make_id_map(
        {"id": "root", "name": "A01.表格", "parents": ["drive1"], "driveId": "drive1"},
        {"id": "sub", "name": "2024", "parents": ["root"], "driveId": "drive1"},
        {"id": "f1", "name": "報名表.docx", "parents": ["sub"], "driveId": "drive1"},
    )
    path, ambiguous = build_path("f1", id_map, {"drive1": "A.公開"})
    assert path == "A.公開/A01.表格/2024/報名表.docx"
    assert ambiguous is False


def test_multiple_parents_flagged_ambiguous_but_still_resolves():
    id_map = make_id_map(
        {"id": "root", "name": "資料夾", "parents": ["drive1"], "driveId": "drive1"},
        {"id": "f1", "name": "共用檔.pdf", "parents": ["root", "other"], "driveId": "drive1"},
    )
    path, ambiguous = build_path("f1", id_map, {"drive1": "A.公開"})
    assert path == "A.公開/資料夾/共用檔.pdf"
    assert ambiguous is True


def test_unknown_drive_id_falls_back_to_raw_id():
    id_map = make_id_map(
        {"id": "f1", "name": "檔案.pdf", "parents": ["driveX"], "driveId": "driveX"},
    )
    path, _ = build_path("f1", id_map, {})
    assert path == "driveX/檔案.pdf"


def test_cycle_does_not_infinite_loop():
    id_map = make_id_map(
        {"id": "a", "name": "A", "parents": ["b"], "driveId": "drive1"},
        {"id": "b", "name": "B", "parents": ["a"], "driveId": "drive1"},
    )
    path, _ = build_path("a", id_map, {"drive1": "測試"})
    assert path == "測試/B/A"
