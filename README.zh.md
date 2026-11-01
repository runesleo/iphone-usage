# iphone-usage

[English](README.md) · ![license](https://img.shields.io/badge/license-MIT-blue) ![python](https://img.shields.io/badge/python-3.9%2B-blue) ![platform](https://img.shields.io/badge/platform-macOS-lightgrey)

看清你的 iPhone 上哪些 App 真的在用，哪些装了从来不打开。数据就是你的 Mac 本来已经同步下来的那份。

## 能得到什么

- 列出所有往这台 Mac 同步使用记录的设备，并附上每台最常打开的 3 个 App，方便你认出哪台是哪台。
- 每个 App 打开了几次、在屏幕上用了多少分钟、用过几天、最后一次是哪天。
- 已经装了、但最近 N 天一次都没打开的 App 清单，整理手机时用。
- 可以输出 JSON，交给整理桌面的工具、表格或你自己的脚本。
- 只读、只在本机：不用插线，不用越狱，不用导出屏幕使用时间，不联网，不装第三方包。

## 原理

iPhone 打开「屏幕使用时间 → 跨设备共享」后，macOS 会把你每台设备上「哪个 App 到了前台」记在 `~/Library/Biome` 下。工具从这份记录里找出每次打开和离开，两两配对，再加总。

```text
$ python3 iphone_usage.py report A1B2 --days 7 --top 3
31 apps opened in the last 7 days (to 2026-11-01)
app                                           opens  minutes  days  last used
com.example.messages                            140    212.5     7  2026-11-01
com.example.maps                                 23     41.0     5  2026-10-31
com.example.notes                                 9      6.2     3  2026-10-29
```

### 为什么不直接用屏幕使用时间的数据库

[Unjiggle](https://github.com/chungty/unjiggle) 这类整理桌面的工具，按使用情况排序时读的是 `knowledgeC.db`。我在开发它的那台 macOS 26 Mac 上查过：这个库里 App 使用记录有 10062 条，全是这台 Mac 自己的，同账号下的 iPhone 一条都没有。手机的使用数据在 Biome 里，这个工具读的就是它。

## 安装

```bash
git clone https://github.com/runesleo/iphone-usage.git
cd iphone-usage
python3 iphone_usage.py devices
```

什么都不用装。用 AI 编程助手的话，把 [install.md](install.md) 交给它就行。

## 需要什么

- macOS、Python 3.9 以上（系统自带的 `python3` 就够）。
- iPhone 上打开「设置 → 屏幕使用时间 → 跨设备共享」，并且和 Mac 登录同一个 Apple ID。
- 给运行它的终端开「完全磁盘访问权限」（系统设置 → 隐私与安全性），因为 `~/Library/Biome` 受系统保护。
- 只有 `unused` 需要：[pymobiledevice3](https://github.com/doronz88/pymobiledevice3)，并且手机插线，用来列出已安装的 App。

**隐私**：所有东西都留在你的 Mac 上。工具只以只读方式打开 Biome 记录和同步数据库，只会写出你指定的 JSON 文件。JSON 里写着你用哪些 App，请当成私人数据保管。

## 快速开始

```bash
python3 iphone_usage.py devices                         # 找到你手机编号的前几位
python3 iphone_usage.py report A1B2 --days 30           # 每个 App 的使用情况
python3 iphone_usage.py report A1B2 --json usage.json   # 同上，输出 JSON

pymobiledevice3 apps list --type User > apps.json       # 手机插线
python3 iphone_usage.py unused A1B2 --installed apps.json --days 30
```

`unused` 只列清单，不会删任何东西。删之前先确认里面没有要紧的数据，比如草稿、登录状态、钱包。

`report --json` 的格式：

```json
{"com.example.chat": {"launches": 2, "minutes": 15.0, "active_days": 2, "last_used": "2026-10-30"}}
```

- `launches` 是这个 App 切到前台的次数。
- `minutes` 是在前台的时间。一次连续超过 4 小时的，当作漏记了结束，按 0 算。
- 系统界面不算在内：锁屏、面容 ID 等系统弹窗（`*UIService`、`*ViewService`）、通话界面和表盘。

## 验证情况

- 3 个离线测试，用临时目录里造的假 Biome 数据（`python3 -m pytest -q`）。
- 在一台 macOS 26.5 的 Mac 上，对两台 iOS 26 的 iPhone 和一块 Apple Watch 实跑过。其中一台手机的 `unused` 清单和之前手工整理的结果对得上：列出的 6 个里，有 4 个早已被手动卸载。
- 系统自带的 Python 3.9 和 Python 3.14 都能跑。

## 已知局限（v0.1）

- Biome 是苹果没有公开的格式。工具只找它需要的几个字段，其余不管，所以 macOS 升级后可能失效。升级后请用你自己的数据再跑一遍。
- 能看多久以前，取决于 Mac 保留了多久的记录，一般是几周到几个月。
- 只通过小组件、通知或 Siri 用的 App，几乎不会出现在记录里。
- 记录里没有设备名，只能靠每台设备最常用的 App 认出它。

## 接下来

- 输出整理桌面工具能直接读的格式，当它们的使用数据来源。
- 按小时、按星期拆分（比如看睡前刷手机多不多）。
- 用一段大白话总结本周和上周相比有什么变化。

## 关于作者

*Leo（[@runes_leo](https://x.com/runes_leo)）— AI × Crypto 独立构建者。在 [Polymarket](https://polymarket.com/?via=runes-leo&r=runesleo&utm_source=github&utm_content=iphone-usage) 做量化，用 Claude Code 和 Codex 搭数据与内容管线。*

*[leolabs.me](https://leolabs.me) — 写作 · 社群 · 开源工具 · 独立项目*

*[X 订阅](https://x.com/runes_leo/creator-subscriptions/subscribe) — 付费内容周刊*

*Learn in public, Build in public.*

## 许可证

MIT
