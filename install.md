# Install (for AI agents)

Goal: get the user a per-app usage report for their iPhone, read-only, on their Mac.

1. Check the platform: `uname -s` must print `Darwin`. Otherwise stop: this tool is macOS-only.
2. Clone: `git clone https://github.com/runesleo/iphone-usage.git && cd iphone-usage`. No dependencies to install.
3. Self-check (read-only): `python3 iphone_usage.py devices`
   - Lists devices → continue.
   - "macOS blocked reading ~/Library/Biome" → ask the user to grant Full Disk Access to their terminal app, then rerun. Do not try to work around the permission.
   - "No synced device usage found" → ask the user to turn on Settings → Screen Time → Share Across Devices on the iPhone (same Apple ID), wait for a sync, rerun.
4. Ask the user which row is their phone (the top apps help). Then run `python3 iphone_usage.py report <id-prefix> --days 30`.
5. Optional cleanup list: only if the user wants it and has `pymobiledevice3` with the phone on USB:
   `pymobiledevice3 apps list --type User > apps.json && python3 iphone_usage.py unused <id-prefix> --installed apps.json`.
   Present it as a list. Never uninstall anything without the user's explicit confirmation for each app.

The JSON output reveals which apps the user uses; do not upload or share it.
