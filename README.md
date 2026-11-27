# TimeCapsule

[![tests](https://github.com/Hamasa-ElShamy/timecapsule/actions/workflows/tests.yml/badge.svg)](https://github.com/Hamasa-ElShamy/timecapsule/actions/workflows/tests.yml) ![tests: 10 passing](https://img.shields.io/badge/tests-10%20passing-brightgreen) ![license: MIT](https://img.shields.io/badge/license-MIT-blue)

**What was I working on on October 12? When did I last edit that file?**

TimeCapsule keeps a private timeline of the files you create, edit and delete in folders you choose, and lets you ask it questions by day, by file name, or by topic ("what else was I working on when I touched the presentation?").

It is opt-in and local-first. Nothing is recorded until you add a folder. Only file names, paths, sizes and times are stored, **never file contents**. One SQLite file on your machine. No cloud, no AI model.

## Install and use

```bash
git clone https://github.com/Hamasa-ElShamy/timecapsule
cd timecapsule
pip install -e .

timecapsule add ~/Projects        # start tracking a folder (takes a snapshot, records nothing yet)
timecapsule watch                 # keep recording until Ctrl+C (or run `timecapsule scan` whenever you like)
timecapsule day 2026-10-12        # what happened that day
timecapsule last architecture     # when did I last touch a file with this in its name
timecapsule around presentation   # what else did I work on around the same time
timecapsule exclude "*.mp4"       # never record these
timecapsule pause / resume
timecapsule forget --before 2026-01-01   # delete history (asks first; --yes skips)
timecapsule forget --everything
timecapsule status
```

Real output from [`demo/`](demo/):

```
OCTOBER 12
  10:30 AM  Created Graduation_Project.pdf
  11:15 AM  Created architecture.py
  12:00 PM  Created meeting_notes.docx
  02:00 PM  Created project_presentation.pptx

$ timecapsule around presentation --hours 3
== Around 2026-10-12 14:00 ==
  11:15 AM  Created architecture.py
  12:00 PM  Created meeting_notes.docx
  02:00 PM  Created project_presentation.pptx
```

Already excluded by default: `.git`, `node_modules`, `__pycache__`, virtual envs, temp files, `.ssh`, `.env`, key files, and any name containing `password` or `secret`. Add more with `exclude`.

## Install on Windows, macOS and Linux

Needs Python 3.9 or newer. On Windows install it from python.org and tick "Add python.exe to PATH".

```bash
# Windows (PowerShell):  py -m pip install git+https://github.com/Hamasa-ElShamy/timecapsule
# macOS:                 python3 -m pip install git+https://github.com/Hamasa-ElShamy/timecapsule
# Linux:                 python3 -m pip install --user git+https://github.com/Hamasa-ElShamy/timecapsule
```

Tested on Linux only (verified `pip install` from GitHub in a clean environment). Android and browser: not available, a website cannot watch your folders. Technical notes (architecture, algorithms, testing): [ARCHITECTURE.md](ARCHITECTURE.md). Website: https://hamasa-elshamy.github.io/timecapsule/

## How it works

1. **You choose** which folders to track. A first scan only takes a snapshot.
2. **Scan** (every 10 seconds in `watch` mode): walk the folders, compare with the last snapshot, and record each file that is new, changed (modified time or size), or gone.
3. **Store** events in SQLite: time, kind, path, size.
4. **Ask**: by day, by file name, or `around`, which finds files matching a word and then lists everything else touched within a few hours of them.
5. **Control**: pause, exclude patterns, and delete history by date, by path, or all of it.

## Limitations

- It sees **file changes only**. It does **not** know when you merely open or read a file, which websites you visited, or which apps you used. "Opened X" entries like in the idea sketch are not recorded.
- Edit times come from the file's modified time, so the timeline is as accurate as the scan interval and your system clock. Files changed and changed back between scans leave one event or none.
- "Search by memory" is by file name and time proximity. There is no meaning-based (embedding) search and no search inside file contents.
- Folders you stop tracking keep their old history until you run `forget`.
- Scanning is by polling, so very large folders cost CPU every interval. There is no OS-level file events backend, no browser extension and no window app yet.

## Development

```bash
pip install -e ".[dev]" && pytest
```

## Roadmap (not yet built)

OS file-event backend, browser extension (opt-in), semantic search, a window app.

## License

MIT

## Related tools

[OpenRecall](https://github.com/openrecall/openrecall/) (screenshots and OCR) and Windows Recall do a broader version of this. TimeCapsule is much smaller on purpose: opt-in, only file activity (no screenshots), local, standard library only. It sees less, and is therefore less invasive.
