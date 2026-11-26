# TimeCapsule: technical notes

**Modules**: `store.py` has the `Capsule` class (SQLite store, polling scanner, queries, deletion). `cli.py` is the command line. There are no third-party dependencies.

**Data model** (SQLite): `folders` (what you chose to track), `excludes` (patterns), `state` (last seen mtime and size per file), `events` (time, kind, path, size), `meta` (pause flag, per-folder snapshot flag). File contents are never read or stored; a test checks that file text does not appear in the database.

**Algorithm**
1. `scan()` walks each tracked folder (skipping excluded directory and file names), stats each file and compares with `state`.
2. New file: `created`. Changed mtime or size: `modified`. In `state` but gone: `deleted`. Event time is the file's mtime (for deleted it is the scan time).
3. The first scan of a folder is only a snapshot (a per-folder flag), so existing files do not flood the history.
4. `day`: events between local midnight and the next. `last`: latest events whose path contains a name. `around`: find events whose path matches a word, merge them into time windows (gap of at most the window size), then list all events within the window plus a margin. This is how "what else was I working on when I prepared the presentation" is answered, with file names and time proximity.
5. `forget` deletes by date, by path text, or everything. `pause` makes `scan()` a no-op.

**Design decisions**
- Opt-in and metadata only, because activity logs are sensitive. Sensitive-looking names (password, secret, keys, `.env`, `.ssh`) are excluded by default.
- Polling with the standard library so it works on any OS with no install; the cost is a scan interval and CPU on huge folders.
- Event times from mtime make results independent of when the scanner happened to run.

**Testing** (9 tests): nothing recorded before a folder is added, first scan snapshot, created/modified/deleted, default and custom excludes, pause, day/last/around on a built timeline, forget, contents never stored, CLI behaviour.

**Limits**: sees file changes only (no "opened", no web history, no app usage), name and time search only, polling.
