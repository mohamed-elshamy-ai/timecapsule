import argparse
import os
import sys
from datetime import datetime, date

from . import __version__
from .store import Capsule

VERB = {"created": "Created", "modified": "Edited", "deleted": "Deleted"}


def fmt(ts):
    return datetime.fromtimestamp(ts).strftime("%I:%M %p")


def show_events(evs):
    last_day = None
    for ts, kind, path, size in evs:
        d = datetime.fromtimestamp(ts).strftime("%B %d").upper()
        if d != last_day:
            print(f"\n{d}")
            last_day = d
        print(f"  {fmt(ts)}  {VERB[kind]} {os.path.basename(path)}   ({os.path.dirname(path)})")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="timecapsule", description="A private timeline of the files you work on.")
    ap.add_argument("--db", help="database path (default ~/.timecapsule/capsule.db or $TIMECAPSULE_DB)")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add", help="start tracking a folder (nothing is tracked until you do this)"); s.add_argument("folder")
    s = sub.add_parser("unwatch", help="stop tracking a folder"); s.add_argument("folder")
    sub.add_parser("scan", help="record changes once")
    s = sub.add_parser("watch", help="keep recording until you press Ctrl+C"); s.add_argument("--interval", type=int, default=10)
    s = sub.add_parser("day", help="show a day, default today"); s.add_argument("date", nargs="?", default=date.today().isoformat())
    s = sub.add_parser("last", help="when did I last touch a file"); s.add_argument("name")
    s = sub.add_parser("around", help="what else was I working on when I touched files matching a word")
    s.add_argument("text"); s.add_argument("--hours", type=float, default=2.0)
    s = sub.add_parser("exclude", help="never record paths matching a pattern, e.g. '*.mp4'"); s.add_argument("pattern")
    sub.add_parser("pause"); sub.add_parser("resume"); sub.add_parser("status")
    s = sub.add_parser("forget", help="delete recorded history")
    s.add_argument("--before", help="YYYY-MM-DD"); s.add_argument("--path", help="delete events whose path contains this")
    s.add_argument("--everything", action="store_true"); s.add_argument("--yes", action="store_true", help="skip the confirmation")
    a = ap.parse_args(argv)
    c = Capsule(a.db)
    try:
        if a.cmd == "add":
            f = c.add_folder(a.folder); c.scan(); print(f"Tracking {f}. Only file names, sizes and times are recorded, never contents.")
        elif a.cmd == "unwatch":
            c.remove_folder(a.folder); print("No longer tracking it. Existing history is kept; use 'forget' to delete.")
        elif a.cmd == "scan":
            print(f"{c.scan()} event(s) recorded")
        elif a.cmd == "watch":
            print("Recording. Press Ctrl+C to stop.")
            try:
                c.watch(a.interval)
            except KeyboardInterrupt:
                print("Stopped.")
        elif a.cmd == "day":
            evs = c.day(a.date)
            show_events(evs) if evs else print("Nothing recorded for that day.")
        elif a.cmd == "last":
            evs = c.last(a.name)
            if not evs:
                print("No events found for that name."); return 1
            for ts, kind, path, size in evs:
                print(f"{datetime.fromtimestamp(ts):%Y-%m-%d %H:%M}  {VERB[kind]}  {path}")
        elif a.cmd == "around":
            res = c.around(a.text, a.hours)
            if not res:
                print("No files matching that word in your history."); return 1
            for start, end, evs in res:
                print(f"\n== Around {datetime.fromtimestamp(start):%Y-%m-%d %H:%M} ==")
                for ts, kind, path, size in evs:
                    print(f"  {fmt(ts)}  {VERB[kind]} {os.path.basename(path)}")
        elif a.cmd == "exclude":
            c.add_exclude(a.pattern); print("Excluded from now on. Use 'forget --path' to delete what was already recorded.")
        elif a.cmd == "pause":
            c.set_paused(True); print("Paused. Nothing is recorded.")
        elif a.cmd == "resume":
            c.set_paused(False); print("Recording resumed.")
        elif a.cmd == "status":
            st = c.stats()
            print(f"Recording: {'PAUSED' if st['paused'] else 'on'}\nEvents stored: {st['events']}")
            print("Folders:", ", ".join(st["folders"]) or "none (nothing is tracked yet)")
            print("Database:", c.path)
        elif a.cmd == "forget":
            if not (a.before or a.path or a.everything):
                print("Say what to forget: --before DATE, --path TEXT or --everything"); return 3
            if not a.yes and input("Delete this history permanently? [y/N] ").lower() != "y":
                print("Cancelled."); return 1
            before = datetime.strptime(a.before, "%Y-%m-%d").timestamp() if a.before else None
            print(f"Deleted {c.forget(before, a.path, a.everything)} event(s).")
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr); return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
