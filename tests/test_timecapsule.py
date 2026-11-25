import os, time
import pytest
from datetime import datetime
from timecapsule import Capsule
from timecapsule.cli import main


def touch(p, content="x", when=None):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(content)
    if when:
        os.utime(p, (when, when))


@pytest.fixture
def cap(tmp_path):
    return Capsule(str(tmp_path / "c.db")), tmp_path / "work"


def test_nothing_recorded_until_folder_added(cap, tmp_path):
    c, w = cap
    touch(str(w / "a.txt"))
    assert c.scan() == 0 and c.stats()["events"] == 0


def test_first_scan_is_snapshot_only(cap):
    c, w = cap
    touch(str(w / "a.txt"))
    c.add_folder(w)
    assert c.scan() == 0
    assert c.stats()["events"] == 0


def test_created_modified_deleted(cap):
    c, w = cap
    touch(str(w / "a.txt"))
    c.add_folder(w); c.scan()
    touch(str(w / "b.py"), when=1_700_000_000)
    assert c.scan() == 1
    touch(str(w / "b.py"), "changed!!", when=1_700_000_500)
    assert c.scan() == 1
    os.remove(w / "b.py")
    assert c.scan(now=1_700_001_000) == 1
    kinds = [e[1] for e in c.events()]
    assert kinds == ["created", "modified", "deleted"]


def test_excludes_default_and_custom(cap):
    c, w = cap
    c.add_folder(w) if w.exists() else (w.mkdir(), c.add_folder(w))
    c.scan()
    touch(str(w / ".git" / "x"))
    touch(str(w / "my_password.txt"))
    touch(str(w / "movie.mp4"))
    c.add_exclude("*.mp4")
    touch(str(w / "ok.md"))
    assert c.scan() == 1
    assert [os.path.basename(e[2]) for e in c.events()] == ["ok.md"]


def test_pause(cap):
    c, w = cap
    w.mkdir(); c.add_folder(w); c.scan()
    c.set_paused(True)
    touch(str(w / "a.txt"))
    assert c.scan() == 0
    c.set_paused(False)
    assert c.scan() == 1


def test_day_last_and_around(cap):
    c, w = cap
    w.mkdir(); c.add_folder(w); c.scan()
    t0 = datetime(2026, 10, 12, 10, 30).timestamp()
    touch(str(w / "Graduation_Project.pdf"), when=t0)
    touch(str(w / "architecture.py"), when=t0 + 45 * 60)
    touch(str(w / "unrelated_taxes.xlsx"), when=t0 + 20 * 86400)
    touch(str(w / "presentation_final.pptx"), when=t0 + 3600)
    c.scan()
    day = c.day("2026-10-12")
    assert [os.path.basename(e[2]) for e in day] == ["Graduation_Project.pdf", "architecture.py", "presentation_final.pptx"]
    assert c.last("architecture")[0][2].endswith("architecture.py")
    win = c.around("presentation")
    names = {os.path.basename(e[2]) for _, _, evs in win for e in evs}
    assert names == {"Graduation_Project.pdf", "architecture.py", "presentation_final.pptx"}


def test_forget(cap):
    c, w = cap
    w.mkdir(); c.add_folder(w); c.scan()
    touch(str(w / "a.txt"), when=1_000_000_000); touch(str(w / "b.txt"), when=1_700_000_000)
    c.scan()
    c.forget(before=1_500_000_000)
    assert [os.path.basename(e[2]) for e in c.events()] == ["b.txt"]
    c.forget(path_contains="b.txt")
    assert c.events() == []
    touch(str(w / "c.txt")); c.scan()
    c.forget(everything=True)
    assert c.stats()["events"] == 0


def test_contents_never_stored(cap):
    c, w = cap
    w.mkdir(); c.add_folder(w); c.scan()
    touch(str(w / "a.txt"), "SUPERSECRETCONTENT")
    c.scan()
    with open(c.path, "rb") as f:
        assert b"SUPERSECRETCONTENT" not in f.read()


def test_cli(tmp_path, capsys):
    db = str(tmp_path / "c.db"); w = tmp_path / "w"; w.mkdir()
    assert main(["--db", db, "add", str(w)]) == 0
    touch(str(w / "notes.docx"))
    assert main(["--db", db, "scan"]) == 0
    assert main(["--db", db, "last", "notes"]) == 0
    assert main(["--db", db, "forget", "--everything", "--yes"]) == 0
    assert main(["--db", db, "last", "notes"]) == 1
    assert main(["--db", db, "add", str(tmp_path / "nope")]) == 3
