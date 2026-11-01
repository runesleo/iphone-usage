# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-11-01

### Added
- `devices`: list every device that syncs App.InFocus usage to the Mac, with its top apps.
- `report`: per-app opens, foreground minutes, active days and last use, as a table or JSON.
- `unused`: installed apps (from a `pymobiledevice3 apps list` export) not opened in N days.
- Hardened after review: corrupt sync.db, rotated segments, empty device folders and permission errors no longer crash; sync.db opened immutable.
- Offline tests on a synthetic Biome folder.
