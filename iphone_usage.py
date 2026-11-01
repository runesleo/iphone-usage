#!/usr/bin/env python3
"""Read real per-app iPhone usage from the copy macOS already syncs to your Mac.

macOS keeps the App.InFocus stream of every device signed in to the same Apple ID
(with "Share across devices" on in Screen Time) under ~/Library/Biome. This reads it
locally: no cable, no jailbreak, no Screen Time export, nothing leaves the Mac.

Usage:
  iphone_usage.py devices
  iphone_usage.py report <device> [--days 30] [--top 25] [--json FILE]
  iphone_usage.py unused <device> --installed FILE [--days 30] [--json FILE]

<device> is a device id or a unique prefix of one (see `devices`).
--installed takes a JSON list or object of bundle ids, e.g. the output of
`pymobiledevice3 apps list --type User > apps.json` with the phone on USB.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import struct
import sys
from pathlib import Path

BIOME = Path(os.environ.get("BIOME_ROOT", Path.home() / "Library/Biome"))
STREAM = "streams/restricted/App.InFocus/remote"
APPLE_EPOCH = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc)
MAX_SESSION_S = 4 * 3600  # a foreground stretch longer than this is a missed "end" event, not usage
# One focus event in the SEGB records: field 2 = 1, field 3 = starting(1)/ending(0),
# field 4 = absolute time (double, seconds since 2001), field 6 = bundle id (length-prefixed).
EVENT = re.compile(rb"\x10\x01\x18([\x00\x01])\x21(.{8})\x32(.)", re.S)
# Lock screen, Face ID sheets, watch faces: they take focus but are not apps you chose to open
SYSTEM_UI = re.compile(r"^com\.apple\.(springboard|SleepLockScreen|.*UIService|.*ViewService|carousel\.|InCallService)", re.I)


def apple_time(t: float) -> dt.datetime:
    return APPLE_EPOCH + dt.timedelta(seconds=t)


def parse_events(blob: bytes) -> list[tuple[float, bool, str]]:
    out = []
    for m in EVENT.finditer(blob):
        n = m.group(3)[0]
        bid = blob[m.end():m.end() + n].decode("utf-8", "ignore")
        t = struct.unpack("<d", m.group(2))[0]
        # bundle ids have a dot; times outside 2020-2029 are a false match on other bytes
        if "." in bid and len(bid) == n and 6e8 < t < 9.5e8 and not SYSTEM_UI.match(bid):
            out.append((t, m.group(1) == b"\x01", bid))
    return out


def device_events(device_dir: Path) -> list[tuple[float, bool, str]]:
    ev = set()
    for f in device_dir.iterdir():
        try:
            if f.is_file():
                ev.update(parse_events(f.read_bytes()))
        except PermissionError:
            raise
        except OSError:
            continue  # a segment rotated away mid-read
    # same timestamp: an app's end (False) sorts before the next app's start (True)
    return sorted(ev)


def summarize(events, since: float | None = None) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    current = None
    for t, starting, bid in events:
        if since is not None and t < since:
            continue
        s = stats.setdefault(bid, {"launches": 0, "seconds": 0.0, "days": set(), "last": 0.0})
        if starting:
            s["launches"] += 1
            s["days"].add(apple_time(t).astimezone().date())
            current = (t, bid)
        else:
            if current and current[1] == bid and 0 < t - current[0] < MAX_SESSION_S:
                s["seconds"] += t - current[0]
            current = None
        s["last"] = max(s["last"], t)
    return {b: {"launches": s["launches"], "minutes": round(s["seconds"] / 60, 1), "active_days": len(s["days"]),
                "last_used": apple_time(s["last"]).astimezone().date().isoformat()}
            for b, s in stats.items() if s["launches"]}


def peers() -> dict[str, dict]:
    db = BIOME / "sync/sync.db"
    if not db.exists():
        return {}
    try:
        # immutable=1: no lock or -shm writes next to Apple's database
        con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
        try:
            rows = con.execute("select device_identifier, me, model, platform, last_sync_date from DevicePeer").fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return {}  # only used for the build column
    return {r[0]: {"me": bool(r[1]), "build": r[2], "platform": r[3], "last_sync": r[4]} for r in rows}


def device_dirs() -> dict[str, Path]:
    root = BIOME / STREAM
    try:
        dirs = sorted(root.iterdir())
    except FileNotFoundError:
        return {}
    # skip devices with no event files, so a prefix unique in `devices` is unique here too
    return {p.name: p for p in dirs if p.is_dir() and any(f.is_file() and f.stat().st_size for f in p.iterdir())}


def resolve(prefix: str) -> Path:
    hits = [p for name, p in device_dirs().items() if name.upper().startswith(prefix.upper())]
    if len(hits) != 1:
        sys.exit(f"device '{prefix}': {'no match' if not hits else 'ambiguous'} (run `devices`)")
    return hits[0]


def cmd_devices(_args) -> int:
    meta = peers()
    rows = []
    for name, path in device_dirs().items():
        ev = device_events(path)
        if not ev:
            continue
        top = summarize(ev, ev[-1][0] - 30 * 86400)
        top_apps = sorted(top, key=lambda b: -top[b]["launches"])[:3]
        rows.append((ev[-1][0], name, meta.get(name, {}).get("build") or "?", len(ev), top_apps))
    if not rows:
        print("No synced device usage found. On the iPhone: Settings > Screen Time > Share Across Devices.")
        return 1
    print(f"{'device':38} {'build':8} {'last event':11} {'events':>7}  most opened (last 30 days)")
    for last, name, build, n, top_apps in sorted(rows, reverse=True):
        print(f"{name:38} {build:8} {apple_time(last).astimezone():%Y-%m-%d} {n:>7}  {', '.join(top_apps)}")
    return 0


def window(args):
    ev = device_events(resolve(args.device))
    if not ev:
        sys.exit("no events for this device")
    return ev, ev[-1][0] - args.days * 86400


def emit(data, path: str | None):
    if path:
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def cmd_report(args) -> int:
    ev, since = window(args)
    stats = summarize(ev, since)
    emit(stats, args.json)
    print(f"{len(stats)} apps opened in the last {args.days} days (to {apple_time(ev[-1][0]).astimezone():%Y-%m-%d})")
    print(f"{'app':44} {'opens':>6} {'minutes':>8} {'days':>5}  last used")
    for bid in sorted(stats, key=lambda b: (-stats[b]["launches"], b))[:args.top]:
        s = stats[bid]
        print(f"{bid:44} {s['launches']:>6} {s['minutes']:>8} {s['active_days']:>5}  {s['last_used']}")
    return 0


def installed_ids(path: str) -> list[str]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"--installed {path}: not a readable JSON list/object of bundle ids ({e})")
    ids = list(data) if isinstance(data, (list, dict)) else []
    return sorted({i for i in ids if isinstance(i, str) and "." in i})


def cmd_unused(args) -> int:
    ev, since = window(args)
    used = summarize(ev, since)
    ever = summarize(ev)
    rows = [{"bundle_id": b, "last_used": ever.get(b, {}).get("last_used")}
            for b in installed_ids(args.installed) if b not in used]
    emit(rows, args.json)
    first = apple_time(ev[0][0]).astimezone().date()
    last = apple_time(ev[-1][0]).astimezone().date()
    print(f"{len(rows)} installed apps not opened in the {args.days} days to {last} (history starts {first})")
    for r in sorted(rows, key=lambda r: (r["last_used"] or "", r["bundle_id"])):
        print(f"{r['bundle_id']:44} last used {r['last_used'] or 'never in history'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("devices", help="list devices with synced usage")
    for name in ("report", "unused"):
        p = sub.add_parser(name)
        p.add_argument("device")
        p.add_argument("--days", type=int, default=30)
        p.add_argument("--json")
        if name == "report":
            p.add_argument("--top", type=int, default=25)
        else:
            p.add_argument("--installed", required=True)
    args = ap.parse_args(argv)
    try:
        return {"devices": cmd_devices, "report": cmd_report, "unused": cmd_unused}[args.cmd](args)
    except PermissionError:
        sys.exit("macOS blocked reading ~/Library/Biome: give your terminal Full Disk Access "
                 "(System Settings > Privacy & Security > Full Disk Access).")


if __name__ == "__main__":
    sys.exit(main())
