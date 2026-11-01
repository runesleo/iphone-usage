# iphone-usage

[中文](README.zh.md)

See which iPhone apps you actually open, and which ones you never do — read straight from the copy your Mac already keeps.

If your iPhone shares Screen Time across devices, macOS stores a log of every app that comes to the front on each of your devices in `~/Library/Biome`. This tool reads that log locally. No cable, no jailbreak, no Screen Time export, no network.

## Why this exists

Home-screen organizers like [Unjiggle](https://github.com/chungty/unjiggle) can rank apps by Screen Time, but they read `knowledgeC.db`. On a Mac running macOS 26, that database held 10,062 app-usage rows for the Mac itself and none for the phones signed in to the same account. The phone data lives in Biome instead. That is what this tool reads.

## Requirements

- macOS, Python 3.9+, nothing else to install.
- On the iPhone: Settings → Screen Time → **Share Across Devices** on, same Apple ID as the Mac.
- Your terminal needs **Full Disk Access** (System Settings → Privacy & Security), because `~/Library/Biome` is protected.

## Use

```bash
python3 iphone_usage.py devices                  # every device with synced usage, newest first
python3 iphone_usage.py report A1B2 --days 30    # per-app opens, minutes, active days, last used
python3 iphone_usage.py report A1B2 --json usage.json
```

`devices` shows the three most-opened apps per device, so you can tell your phones, iPad and Watch apart. Pass any unique prefix of the id.

### Find apps you never open

With the phone on USB, list what is installed using [pymobiledevice3](https://github.com/doronz88/pymobiledevice3), then compare:

```bash
pymobiledevice3 apps list --type User > apps.json
python3 iphone_usage.py unused A1B2 --installed apps.json --days 30
```

This only produces a list. Nothing is deleted. Before you remove an app, check that its data does not matter (drafts, saved logins, wallets).

## Output

`report --json` writes one entry per bundle id:

```json
{"com.example.chat": {"launches": 2, "minutes": 15.0, "active_days": 2, "last_used": "2026-10-30"}}
```

- `launches` counts the times the app came to the front.
- `minutes` is time in the foreground. A stretch over 4 hours is treated as a missed end event and counted as 0.
- Lock screen, Face ID sheets and watch-face events are left out.

## Limits

- Biome is an undocumented Apple format. The parser looks for the event fields it needs and ignores everything else. A future macOS update can break it. The tests use a synthetic log, so run the tool against your own data after an update.
- History only goes back as far as your Mac has kept (a few weeks to months).
- Apps you only use through widgets, notifications or Siri barely show up.

## Tests

```bash
python3 -m pytest -q
```

The tests build a fake Biome folder in a temp directory and never read your real data.

## License

MIT
