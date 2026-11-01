# iphone-usage

[English](README.md)

看清你的 iPhone 上哪些 App 真的在用，哪些装了从来不打开。数据直接读 Mac 本来就同步下来的那份。

iPhone 打开了「屏幕使用时间 → 跨设备共享」后，macOS 会把你每台设备上「哪个 App 到了前台」记在 `~/Library/Biome` 里。这个工具只在本机读这份记录：不用插线，不用越狱，不用导出屏幕使用时间，也不联网。

## 为什么要做这个

[Unjiggle](https://github.com/chungty/unjiggle) 这类整理桌面的工具，按使用情况排序时读的是 `knowledgeC.db`。我在一台 macOS 26 的 Mac 上查过：这个库里 App 使用记录有 10062 条，全是这台 Mac 自己的，同账号下的 iPhone 一条都没有。手机的使用数据其实在 Biome 里，这个工具读的就是它。

## 需要什么

- macOS、Python 3.9 以上，不用装别的东西。
- iPhone 上打开「设置 → 屏幕使用时间 → 跨设备共享」，并且和 Mac 登录同一个 Apple ID。
- 运行它的终端要有「完全磁盘访问权限」（系统设置 → 隐私与安全性），因为 `~/Library/Biome` 受系统保护。

## 用法

```bash
python3 iphone_usage.py devices                  # 列出有同步数据的设备，最近有记录的排在前面
python3 iphone_usage.py report A1B2 --days 30    # 每个 App 的打开次数、使用分钟、用过几天、最后一次使用
python3 iphone_usage.py report A1B2 --json usage.json
```

`devices` 会列出每台设备最常打开的 3 个 App，用来分辨哪台是手机、哪台是 iPad 或手表。设备编号只要输入能唯一认出它的前几位就行。

### 找出装了不用的 App

手机插线后，用 [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) 列出已安装的 App，再对比：

```bash
pymobiledevice3 apps list --type User > apps.json
python3 iphone_usage.py unused A1B2 --installed apps.json --days 30
```

它只列清单，不会删任何东西。删之前先确认里面没有要紧的数据，比如草稿、登录状态、钱包。

## 输出

`report --json` 每个 App 一条：

```json
{"com.example.chat": {"launches": 2, "minutes": 15.0, "active_days": 2, "last_used": "2026-10-30"}}
```

- `launches` 是这个 App 切到前台的次数。
- `minutes` 是在前台的时间。一次连续超过 4 小时的，当作漏记了结束，按 0 算。
- 锁屏、面容 ID 弹窗、表盘这类系统界面不算在内。

## 局限

- Biome 是苹果没有公开的格式。工具只找它需要的那几个字段，其他内容不管。以后 macOS 升级可能让它失效。测试用的是人造数据，所以升级后请用你自己的数据再跑一遍。
- 能看到多久以前，取决于 Mac 保留了多久的记录，一般是几周到几个月。
- 只通过小组件、通知或 Siri 用的 App，几乎不会出现在记录里。

## 测试

```bash
python3 -m pytest -q
```

测试会在临时目录里造一份假的 Biome 数据，不读你的真实数据。

## 许可证

MIT
