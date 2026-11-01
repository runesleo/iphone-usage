"""Offline tests: a fake ~/Library/Biome built in a temp dir, never the real one."""
import importlib
import json
import sqlite3
import struct
import sys
from pathlib import Path

import pytest

DAY = 86400.0
T0 = 815_000_000.0  # late 2026, in seconds since 2001


def event(t: float, starting: bool, bid: str) -> bytes:
    b = bid.encode()
    return (b"\x0a\x00\x00\x00" + b"\x10\x01\x18" + (b"\x01" if starting else b"\x00") + b"\x21" + struct.pack("<d", t)
            + b"\x32" + bytes([len(b)]) + b + b"J\x041.00h\x01\x00\x00")


@pytest.fixture
def mod(tmp_path, monkeypatch):
    dev = tmp_path / "streams/restricted/App.InFocus/remote/AAAA1111-0000-0000-0000-000000000000"
    dev.mkdir(parents=True)
    (dev / "tombstone").mkdir()
    blob = b"".join([
        event(T0, True, "com.example.chat"), event(T0 + 600, False, "com.example.chat"),              # 10 min
        event(T0 + DAY, True, "com.example.chat"), event(T0 + DAY + 300, False, "com.example.chat"),  # 5 min
        event(T0 + DAY, True, "com.apple.LocalAuthenticationUIService"),                              # system sheet
        event(T0 - 40 * DAY, True, "com.example.old"), event(T0 - 40 * DAY + 60, False, "com.example.old"),
        event(T0 + 2 * DAY, True, "com.example.game"),
        event(T0 + 2 * DAY + 6 * 3600, False, "com.example.game"),                                    # missed end
    ])
    (dev / "809921270077850").write_bytes(blob + blob)  # duplicated records count once
    (tmp_path / "sync").mkdir()
    con = sqlite3.connect(tmp_path / "sync/sync.db")
    con.execute("create table DevicePeer (device_identifier, me, name, model, platform, last_sync_date, protocol_version)")
    con.execute("insert into DevicePeer values ('AAAA1111-0000-0000-0000-000000000000', 0, null, '24B119', 2, 0, 5)")
    con.commit()
    con.close()
    monkeypatch.setenv("BIOME_ROOT", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).parent))
    import iphone_usage
    return importlib.reload(iphone_usage)


def test_report_counts_opens_minutes_and_skips_system_ui(mod, tmp_path):
    out = tmp_path / "r.json"
    assert mod.main(["report", "aaaa", "--days", "30", "--json", str(out)]) == 0
    stats = json.loads(out.read_text())
    assert stats["com.example.chat"]["launches"] == 2
    assert stats["com.example.chat"]["minutes"] == 15.0
    assert stats["com.example.chat"]["active_days"] == 2
    assert stats["com.example.game"]["minutes"] == 0.0
    assert "com.example.old" not in stats  # outside the window
    assert not any(b.startswith("com.apple.LocalAuth") for b in stats)


def test_unused_lists_installed_apps_not_opened(mod, tmp_path):
    installed = tmp_path / "apps.json"
    installed.write_text(json.dumps({"com.example.chat": {}, "com.example.old": {}, "com.example.never": {}}))
    out = tmp_path / "u.json"
    assert mod.main(["unused", "AAAA", "--installed", str(installed), "--json", str(out)]) == 0
    rows = {r["bundle_id"]: r["last_used"] for r in json.loads(out.read_text())}
    assert set(rows) == {"com.example.old", "com.example.never"}
    assert rows["com.example.never"] is None and rows["com.example.old"]


def test_devices_and_bad_prefix(mod, capsys):
    assert mod.main(["devices"]) == 0
    assert "AAAA1111" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        mod.main(["report", "ZZZZ"])
