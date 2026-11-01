# Pre-release review: iphone-usage v0.1.0 (branch chore/release-v0.1.0)

Independent pass. Commits reviewed: `47289ee`, `6200f5a` (`git log -p --all`).
Checks run: `python3 -m pytest -q` (3.14.6: 3 passed), `/usr/bin/python3 -m pytest -q` (3.9.6: 3 passed),
`ast.parse(feature_version=(3,9))` on both .py files (ok), read-only `devices` / `report` against this Mac's
real Biome data, and edge cases against a synthetic Biome tree in a scratch dir.
Real device ids, paths and app names seen during the run are deliberately not reproduced here.

## 🔴 Blockers

1. **README sample output is the author's real usage data.** `README.md:19-26`, `README.zh.md:19-26`.
   Running `report <one real device> --days 7 --top 3` on this Mac produced the same header ("16 apps ... to 2026-11-01")
   and the same opens / days / last-used numbers on all three rows. Row 1 is a real third-party bundle id (only its
   minutes differ, so it was edited by hand), and row 3 has a real app renamed to `com.example.*` but keeps the real
   numbers. The rows do not line up either: row 3's columns are offset because it was edited by hand. Since this
   publishes a private app list (what the author plays and for how long), it blocks a public repo. Fix: use a fully
   synthetic sample (all `com.example.*`, made-up numbers), for example generated from the test fixture, and keep the
   column alignment the code really prints.

## 🟡 Warnings

1. **Commit metadata exposes a personal mailbox.** `git log --format='%an <%ae>'` on both commits: the author/committer
   email is a personal number-based address, not a GitHub `noreply` address, and the author name is a different account
   from the `runesleo` GitHub owner the README links to. Once pushed, this stays public and links the two identities.
   Rewrite author/committer to the intended public identity / noreply address before the first push (only 2 commits, so this is cheap).
2. **sync.db is opened `mode=ro`, but it is a WAL database.** `iphone_usage.py:89`. On this Mac `sync.db` is in WAL mode,
   with `-wal` and `-shm` files next to it. A read-only SQLite connection still takes read locks and can write the
   wal-index into the existing `-shm` file. The database file itself never changes, so this is not a blocker. But "opens
   ... the sync database read-only" (`README.md:49`) is not literally true at the file level. Options: copy
   `sync.db`, `-wal` and `-shm` to a temp dir and open the copy, or accept the behaviour and change the wording. The
   data used is only cosmetic (the build string).
3. **Any sqlite error crashes `devices` with a traceback.** `iphone_usage.py:85-94`, called unconditionally at
   `:110`. A schema change (for example a renamed column), a locked or corrupt db, or a missing `DevicePeer` table raises
   `sqlite3.DatabaseError`/`OperationalError`, which `main()` (`:191`) does not catch. Reproduced: a junk `sync.db` gives
   `sqlite3.DatabaseError: file is not a database`. Since the metadata is optional, `peers()` should catch
   `sqlite3.Error` and return `{}`.
4. **On Python 3.12+ the Full Disk Access hint is replaced by a misleading message.** `iphone_usage.py:98-99`, `:119-120`.
   `Path.exists()` on newer Pythons returns False on permission errors instead of raising. Reproduced with a
   permission-denied stream root: 3.9.6 prints the Full Disk Access message, while 3.14.6 (the default Homebrew
   `python3` here) prints "No synced device usage found ... Share Across Devices". This sends users and agents
   (`install.md:9-10`) down the wrong fix. Not reproduced under real TCC, only with POSIX permissions. Fix: check
   `os.access` / try `iterdir()` on `BIOME` and raise `PermissionError` explicitly.
5. **Other OS errors give a traceback.** `iphone_usage.py:58-60`, `:191`. Only `PermissionError` is caught. Biome
   rotates segment files while syncing, so a file deleted between `iterdir()` and `read_bytes()` raises
   `FileNotFoundError`. Skip unreadable/vanished files per file (`except OSError: continue`), or catch `OSError` in main.
6. **Prefix resolution counts empty device dirs that `devices` hides.** `iphone_usage.py:103` against `:113-115`. On this
   Mac most of the device dirs under `remote/` have no events. `devices` skips them, but `resolve()` still matches them,
   so a prefix that looks unique in the `devices` listing can still come back "ambiguous". Resolve only among dirs that
   have events, or list the matching ids in the error.
7. **System-UI filter drops more than the docs say.** `iphone_usage.py:37` against `README.md:72` / `README.zh.md:72`.
   The regex also excludes `InCallService` (phone/FaceTime calls) and every `com.apple.*UIService` / `*ViewService`
   (for example payment sheets and share sheets). The docs only mention lock screen, Face ID and watch faces. Document
   the call exclusion at least.
8. **The time window ends at the device's last synced event, not today.** `iphone_usage.py:116`, `:132`. "Last 30
   days" for a device that stopped syncing weeks ago is a window in the past. `report` prints `(to DATE)`, but
   `unused` (`:169`) does not, so "not opened in the last N days" can be wrong for a stale device. Print the window end
   in `unused` too, or anchor to now and warn when the data is stale.
9. **pymobiledevice3 command differs between docstring and docs, and neither is verified.** `iphone_usage.py:15` uses
   `apps list --no-color`, while `README.md:58`, `README.zh.md:58` and `install.md:13` use `apps list --type User`.
   pymobiledevice3 is not installed here, so I could not confirm that `--type User` exists or that stdout is pure JSON.
   Pick one form and test it once with a real phone.
10. **Undisclosed referral link.** `README.md:95`, `README.zh.md:95`. The Polymarket URL carries referral parameters in an
    unrelated tool's README. Disclose it as a referral link or drop the parameters. Polymarket is also geo-restricted in
    several jurisdictions.
11. **Claims that cannot be checked from the repo.** `README.md:30` (exact knowledgeC row count, a one-machine snapshot)
    and `README.md:77` ("4 of the 6" manual-review match). Both are anecdotal. Wording such as "on the author's Mac"
    avoids implying it is a general measurement. The ZH version (`README.zh.md:30`) already says "我...查过".
12. **Tests miss the load-bearing edge cases.** `test_iphone_usage.py`. On real data a large share of end/start events
    share an exact timestamp with the previous app's event, so correct pairing depends on the sort ordering `end`
    before `start` at the same `t` (`iphone_usage.py:61`, tuple order `False < True`). No test covers this. Also
    untested: the "ambiguous" prefix path (`:105`; `test_iphone_usage.py:72-73` only covers "no match"), the
    permission path (`:191`), and a session that crosses the `since` boundary.

### Nits

- `iphone_usage.py:50`: the comment says 2020-2029, but `9.5e8` is about Feb 2031.
- `iphone_usage.py:35,47`: the bundle-id length is read as one byte. A protobuf varint length of 128 or more is silently
  dropped, which is acceptable but could be documented.
- `iphone_usage.py:67-78`: a session that starts before `since` and ends inside the window gets 0 minutes. A session
  that crosses midnight counts only toward its start day.
- `iphone_usage.py:182,185`: `--days` and `--top` accept 0 or negative values with no validation.
- `README.md:40` says "Nothing to install", but `README.md:76` runs tests with pytest, which is not stdlib.
- Raw byte scanning ignores SEGB record state and checksum, and `tombstone/` subdirs are not read. On this Mac the
  tombstone files held no matching events, so this changes nothing today, but it is an assumption tied to the format.

## 🟢 OK

- **Read-only on Biome:** the only file reads are `iterdir()` / `read_bytes()` (`iphone_usage.py:58-60`, `:99`) and the
  sqlite `mode=ro` URI (`:89`). The only write is `emit()` to the user's `--json` path (`:135-137`). There is no
  network, subprocess, delete or rename anywhere. Not a blocker (but see Warning 2 about `-shm`).
- **Python 3.9 compatibility:** `from __future__ import annotations` (`:17`) makes the `X | None` and `list[...]`
  annotations safe. The AST parses with `feature_version=(3,9)`, and the tests pass on system 3.9.6 and on 3.14.6.
  `add_subparsers(required=True)` is fine on 3.7+.
- **Pairing works on real data:** across 5 real devices with events (about 46k events), more than 99.9% of end events
  matched the open start. There were a handful of start-while-open cases and 3 over-4h sessions, which the
  `MAX_SESSION_S` rule handles as documented (`README.md:71`).
- **Dedupe:** the set of `(t, starting, bid)` across segment files (`:57-61`) removes duplicated records. The test
  covers it (`test_iphone_usage.py:34`).
- **Empty or missing root:** prints a clear message and exits 1 (`:119-121`). A device with no events, a no-match
  prefix and an ambiguous prefix all exit with a clear message (`:105`, `:131`).
- **Output format matches the docs:** the header width (77 chars), the `N apps opened ... (to DATE)` line and the JSON
  keys (`launches`, `minutes`, `active_days`, `last_used`) match `README.md:20-22` and `:66-67`.
- **No personal paths or device ids in history:** `git log -p --all` has no `/Users/...` paths, hostnames or real
  UUIDs. The only UUID is the synthetic `AAAA1111-0000-...` in the tests. `BIOME_ROOT` uses `Path.home()`, not a
  hard-coded path.
- **No real device names:** `.gitignore` covers `*.json`, so usage exports are not committed by accident. The README
  claim "Device names are not stored" (`README.md:85`) matches this Mac: the `DevicePeer.name` column is empty for
  every row.
- **Docs agree with each other:** LICENSE (MIT), the CHANGELOG entries and `install.md` safety wording (never
  uninstall without confirmation, do not upload the JSON) are consistent with the code. The EN and ZH READMEs match
  section by section.

---

## Resolution (before v0.1.0)

- 🔴 Real usage in the README sample: replaced with a fully made-up sample in both READMEs.
- 🟡 Fixed: corrupt `sync.db` falls back to no build column; it is opened with `immutable=1` (no `-shm`/lock writes); rotated segment files are skipped; a permission-denied stream root now gives the Full Disk Access hint; device folders with no events are ignored so prefixes match `devices`; `unused` prints the window end date; docstring uses `--type User`; README lists every filtered system screen; the knowledgeC count is stated as one Mac's observation.
- 🟡 Tests added: same-timestamp app switch, empty device folder vs prefix, corrupt `sync.db`, permission denied (7 tests, Python 3.9 and 3.14).
- 🟡 Left as is: author block referral link (standard author footer); commit identity matches the author's other public repos.
