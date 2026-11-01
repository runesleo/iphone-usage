# iphone-usage

[中文](README.zh.md) · ![license](https://img.shields.io/badge/license-MIT-blue) ![python](https://img.shields.io/badge/python-3.9%2B-blue) ![platform](https://img.shields.io/badge/platform-macOS-lightgrey)

See which iPhone apps you actually open, and which ones you never do. The data comes from the copy your Mac already keeps.

## What you get

- Every device that syncs usage to your Mac, with its three most-opened apps so you can tell them apart.
- For each app: how often it was opened, minutes on screen, how many days it was used and when it was last used.
- A list of installed apps you have not opened in N days, to help you clean up.
- JSON output that you can feed into a home-screen organizer, a spreadsheet or your own scripts.
- Read-only and local: no cable, no jailbreak, no Screen Time export, no network, no third-party packages.

## How it works

If your iPhone shares Screen Time across devices, macOS writes a log of every app that comes to the front on each of your devices under `~/Library/Biome`. The tool finds each start/end event in that log, pairs them up and adds up the totals.

```text
$ python3 iphone_usage.py report A1B2 --days 7 --top 3
16 apps opened in the last 7 days (to 2026-11-01)
app                                           opens  minutes  days  last used
com.supercell.magic                              22    468.0     3  2026-11-01
com.apple.Preferences                            17     38.0     4  2026-10-30
com.example.vpn                                  11     47.1     2  2026-10-30
```

### Why not Screen Time / knowledgeC?

Home-screen organizers such as [Unjiggle](https://github.com/chungty/unjiggle) rank apps using Screen Time data from `knowledgeC.db`. On a Mac running macOS 26, that database held 10,062 app-usage rows for the Mac itself and none for the phones signed in to the same account. The phone data is in Biome, which is what this tool reads.

## Setup

```bash
git clone https://github.com/runesleo/iphone-usage.git
cd iphone-usage
python3 iphone_usage.py devices
```

Nothing to install. If you use an AI coding agent, point it at [install.md](install.md).

## Requirements

- macOS and Python 3.9+ (the system `python3` is fine).
- On the iPhone: Settings → Screen Time → **Share Across Devices** on, with the same Apple ID as the Mac.
- **Full Disk Access** for your terminal (System Settings → Privacy & Security), because `~/Library/Biome` is protected.
- Optional, only for `unused`: [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) and the phone on USB, to list what is installed.

**Privacy:** everything stays on your Mac. The tool opens the Biome files and the sync database read-only and writes only the JSON files you ask for. The JSON output names the apps you use, so treat it as private.

## Quick start

```bash
python3 iphone_usage.py devices                         # pick your phone's id prefix
python3 iphone_usage.py report A1B2 --days 30           # per-app usage
python3 iphone_usage.py report A1B2 --json usage.json   # same, as JSON

pymobiledevice3 apps list --type User > apps.json       # phone on USB
python3 iphone_usage.py unused A1B2 --installed apps.json --days 30
```

`unused` only prints a list and never deletes anything. Before you remove an app, check that its data does not matter (drafts, saved logins, wallets).

JSON format of `report --json`:

```json
{"com.example.chat": {"launches": 2, "minutes": 15.0, "active_days": 2, "last_used": "2026-10-30"}}
```

- `launches` counts the times the app came to the front.
- `minutes` is time in the foreground. A stretch over 4 hours is treated as a missed end event and counts as 0.
- Lock screen, Face ID sheets and watch-face events are left out.

## Verified

- 3 offline tests on a synthetic Biome folder (`python3 -m pytest -q`).
- Checked on a Mac running macOS 26.5 against two iPhones on iOS 26 and an Apple Watch. The `unused` list for one phone matched an earlier manual review: 4 of the 6 apps it listed had already been uninstalled by hand.
- Runs on Python 3.9 (system) and 3.14.

## Known limitations (v0.1)

- Biome is an undocumented Apple format. The parser looks for the event fields it needs and ignores the rest, so a macOS update can break it. After an update, run it against your own data again.
- History goes back only as far as your Mac keeps it (weeks to months).
- Apps you use only through widgets, notifications or Siri barely show up.
- Device names are not stored in the log. You recognise each device by its top apps.

## Roadmap

- Output that home-screen organizers can read directly as their usage source.
- Per-hour and per-weekday breakdowns (for example, phone use before sleep).
- A plain-language summary of what changed this week.

## About the author

*Leo ([@runes_leo](https://x.com/runes_leo)) — AI × Crypto independent builder. Trading on [Polymarket](https://polymarket.com/?via=runes-leo&r=runesleo&utm_source=github&utm_content=iphone-usage), building data and content pipelines with Claude Code and Codex.*

*[leolabs.me](https://leolabs.me) — writing · community · open-source tools · indie projects · all platforms.*

*[X Subscription](https://x.com/runes_leo/creator-subscriptions/subscribe) — paid content weekly, or just buy me a coffee 😁*

*Learn in public, Build in public.*

## License

MIT
