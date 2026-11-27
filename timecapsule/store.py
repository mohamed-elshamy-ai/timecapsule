"""Local SQLite store, folder watching by polling, queries and deletion.

Design rules:
  * Nothing is recorded until you add a folder and run `watch` or `scan`.
  * Only file names, paths, sizes and times are stored. File contents are never read.
  * `pause` stops recording. `forget` deletes. Excluded patterns are never recorded.
  * Everything stays in one SQLite file on your machine.
"""
import fnmatch
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_EXCLUDES = [".git", "node_modules", "__pycache__", ".venv", "venv", ".cache", ".ssh", ".gnupg",
                    "*.tmp", "*.swp", "*~", "~$*", ".DS_Store", "Thumbs.db", "*.pyc", "*.lock",
                    "*password*", "*secret*", "*.kdbx", "*.pem", "*.key", ".env"]


def default_db():
    return os.environ.get("TIMECAPSULE_DB", str(Path.home() / ".timecapsule" / "capsule.db"))


class Capsule:
    def __init__(self, path=None):
        self.path = path or default_db()
        try: Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        except OSError as e: raise ValueError(f"cannot create the database folder for {self.path}: {e.strerror or e}")
        try: self.db = sqlite3.connect(self.path)
        except sqlite3.Error as e: raise ValueError(f"cannot open the database {self.path}: {e}")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS folders(path TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS excludes(pattern TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS state(path TEXT PRIMARY KEY, mtime REAL, size INTEGER);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts REAL, kind TEXT, path TEXT, size INTEGER);
            CREATE INDEX IF NOT EXISTS ev_ts ON events(ts);
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        """)
        if not self.db.execute("SELECT 1 FROM excludes LIMIT 1").fetchone():
            self.db.executemany("INSERT OR IGNORE INTO excludes VALUES (?)", [(p,) for p in DEFAULT_EXCLUDES])
        self.db.commit()

    # ---- settings ----
    def add_folder(self, folder):
        folder = str(Path(folder).expanduser().resolve())
        if not os.path.exists(folder):
            raise ValueError(f"that folder does not exist: {folder}")
        if not os.path.isdir(folder):
            raise ValueError(f"that is a file, not a folder: {folder}. Give timecapsule the folder that contains your work.")
        self.db.execute("INSERT OR IGNORE INTO folders VALUES (?)", (folder,))
        self.db.commit()
        return folder

    def remove_folder(self, folder):
        cur = self.db.execute("DELETE FROM folders WHERE path=?", (str(Path(folder).expanduser().resolve()),))
        self.db.commit()
        return cur.rowcount

    def folders(self):
        return [r[0] for r in self.db.execute("SELECT path FROM folders ORDER BY path")]

    def add_exclude(self, pattern):
        self.db.execute("INSERT OR IGNORE INTO excludes VALUES (?)", (pattern,))
        self.db.commit()

    def excludes(self):
        return [r[0] for r in self.db.execute("SELECT pattern FROM excludes ORDER BY pattern")]

    def paused(self):
        r = self.db.execute("SELECT value FROM meta WHERE key='paused'").fetchone()
        return bool(r and r[0] == "1")

    def set_paused(self, value):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES ('paused', ?)", ("1" if value else "0",))
        self.db.commit()

    def _excluded(self, path):
        pats = self.excludes()
        parts = Path(path).parts
        for pat in pats:
            if any(fnmatch.fnmatch(p.lower(), pat.lower()) for p in parts):
                return True
        return False

    # ---- recording ----
    def scan(self, now=None):
        """Compare folders with the last snapshot and record created/modified/deleted files.

        The first scan of a folder only takes a snapshot (no events), so your history is not flooded.
        Event time is the file's modification time for created/modified, and `now` for deleted.
        Returns the number of events recorded.
        """
        if self.paused():
            return 0
        now = now if now is not None else time.time()
        known = {p: (m, s) for p, m, s in self.db.execute("SELECT path, mtime, size FROM state")}
        snapped = {r[0] for r in self.db.execute("SELECT key FROM meta WHERE key LIKE 'snap:%'")}
        seen, count = set(), 0
        cur = self.db.cursor()
        for folder in self.folders():
            first_run = ("snap:" + folder) not in snapped
            cur.execute("INSERT OR REPLACE INTO meta VALUES (?, '1')", ("snap:" + folder,))
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if not self._excluded(d)]
                for f in files:
                    if self._excluded(f):
                        continue
                    p = os.path.join(root, f)
                    try:
                        st = os.stat(p)
                    except OSError:
                        continue
                    seen.add(p)
                    old = known.get(p)
                    if old is None:
                        if not first_run:
                            cur.execute("INSERT INTO events(ts,kind,path,size) VALUES (?,?,?,?)", (st.st_mtime, "created", p, st.st_size))
                            count += 1
                        cur.execute("INSERT OR REPLACE INTO state VALUES (?,?,?)", (p, st.st_mtime, st.st_size))
                    elif (old[0], old[1]) != (st.st_mtime, st.st_size):
                        cur.execute("INSERT INTO events(ts,kind,path,size) VALUES (?,?,?,?)", (st.st_mtime, "modified", p, st.st_size))
                        cur.execute("INSERT OR REPLACE INTO state VALUES (?,?,?)", (p, st.st_mtime, st.st_size))
                        count += 1
        watched = tuple(self.folders())
        for p in list(known):
            if p not in seen and p.startswith(watched):
                cur.execute("INSERT INTO events(ts,kind,path,size) VALUES (?,?,?,?)", (now, "deleted", p, known[p][1]))
                cur.execute("DELETE FROM state WHERE path=?", (p,))
                count += 1
        self.db.commit()
        return count

    def watch(self, interval=10, stop=lambda: False):
        while not stop():
            self.scan()
            time.sleep(interval)

    # ---- queries ----
    @staticmethod
    def _day_bounds(day):
        d = datetime.strptime(day, "%Y-%m-%d")
        return d.timestamp(), (d + timedelta(days=1)).timestamp()

    def events(self, start=None, end=None, text=None, limit=1000):
        q, a = "SELECT ts, kind, path, size FROM events WHERE 1=1", []
        if start is not None:
            q += " AND ts>=?"; a.append(start)
        if end is not None:
            q += " AND ts<?"; a.append(end)
        if text:
            q += " AND lower(path) LIKE ?"; a.append(f"%{text.lower()}%")
        q += " ORDER BY ts LIMIT ?"; a.append(limit)
        return self.db.execute(q, a).fetchall()

    def day(self, day):
        s, e = self._day_bounds(day)
        return self.events(s, e)

    def last(self, name):
        """Most recent events for files whose path contains `name`."""
        return self.db.execute("SELECT ts, kind, path, size FROM events WHERE lower(path) LIKE ? ESCAPE '\\' ORDER BY ts DESC LIMIT 5",
                               ("%" + name.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%",)).fetchall()

    def around(self, text, window_hours=2.0, max_windows=5):
        """Find files whose names match `text`, then list what else you worked on in the same time window."""
        hits = self.events(text=text, limit=100000)
        if not hits:
            return []
        w = window_hours * 3600
        windows = []
        for ts, *_ in hits:
            if windows and ts - windows[-1][1] <= w:
                windows[-1][1] = ts
            else:
                windows.append([ts, ts])
        out = []
        for a, b in windows[-max_windows:]:
            evs = self.events(a - w, b + w)
            out.append((a, b, evs))
        return out

    def stats(self):
        n = self.db.execute("SELECT count(*) FROM events").fetchone()[0]
        first = self.db.execute("SELECT min(ts) FROM events").fetchone()[0]
        return {"events": n, "first": first, "folders": self.folders(), "paused": self.paused()}

    # ---- deletion ----
    def forget(self, before=None, path_contains=None, everything=False):
        cur = self.db.cursor()
        if everything:
            cur.execute("DELETE FROM events"); cur.execute("DELETE FROM state")
        if before is not None:
            cur.execute("DELETE FROM events WHERE ts<?", (before,))
        if path_contains:
            cur.execute("DELETE FROM events WHERE lower(path) LIKE ?", (f"%{path_contains.lower()}%",))
        n = cur.rowcount
        self.db.commit()
        return n
