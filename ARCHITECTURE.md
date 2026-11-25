# TimeCapsule: technical notes / الشرح التقني

## English

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

## بالعربي

**الأجزاء**: `store.py` فيه كلاس `Capsule` (قاعدة SQLite، ماسح بالمراقبة الدورية، الاستعلامات، الحذف). `cli.py` سطر الأوامر. من غير مكتبات خارجية.

**البيانات**: جداول الفولدرات المختارة والاستثناءات وآخر حالة لكل ملف والأحداث (وقت، نوع، مسار، حجم). محتوى الملفات ما بيتقراش ولا بيتخزن، وفيه اختبار بيتأكد من كده.

**الخوارزمية**: بيمشي على الفولدرات ويقارن كل ملف بآخر حالة: جديد = created، اتغير وقته أو حجمه = modified، اختفى = deleted. أول مسح للفولدر بياخد لقطة بس. أمر `around` بيدور على ملفات اسمها فيه الكلمة، بيجمعها في نوافذ زمنية، وبيعرض كل اللي اتلمس في نفس الوقت.

**قرارات التصميم**: اختياري وبيانات وصفية بس لأن سجل النشاط حساس، وأسماء زي password وsecret و`.env` و`.ssh` مستثناة تلقائياً. المراقبة الدورية بمكتبة بايثون القياسية عشان تشتغل على أي نظام.

**الاختبار**: ٩ اختبارات. **الحدود**: بيشوف تغييرات الملفات بس، مش "فتح الملف" ولا المواقع ولا التطبيقات، والبحث بالاسم والوقت بس.
