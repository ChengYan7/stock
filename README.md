# stock

Nasdaq-100 研究用的数据仓库。原始数据在 `data/raw/`，合并清洗后的指数日线在 `data/processed/`。

**在线页面：<https://chengyan7.github.io/stock/>**，内容是 Nasdaq-100 分段直线拟合和现阶段斜率外推。默认显示英文，中文版是 <https://chengyan7.github.io/stock/#zh>。页面文件在 `gh-pages` 分支。

## 目录

```
data/
  raw/                                      原始数据（不手工改动）
    manifest.json                           每个文件的来源仓库、commit、抓取时间
    index/
      stooq_ndx_daily_close_1985-2022.csv   ^NDX 日收盘，1985-10-01 → 2022-02-10（Stooq）
      yahoo_ndx_daily_ohlcv_2019-2026.csv   ^NDX 日线 OHLCV，2019-01-02 → 2026-11-12（Yahoo）
      yahoo_ndx_daily_ohlcv_2019-2026.meta.json
    constituents/
      nasdaq100_constituents.csv            当前 101 只成分股（2026-11-08 核对）
      yahoo_adjusted_ohlcv_2y/<TICKER>.csv  全部 101 只，近 2 年复权日线（2024-11-12 → 2026-11-11）
      pubmarks_ohlcv_full_history/<T>.csv   其中 10 只的完整上市以来日线
  processed/
    ndx_daily.csv                           合并后的 ^NDX 日线，1985-10-01 → 2026-11-11，10,359 行
scripts/
  fetch_raw.py                              从公开 GitHub 镜像重新抓取 data/raw/
  build_processed.py                        由 raw 生成 processed/ndx_daily.csv
  download_yahoo_full.py                    直接从 Yahoo 拉指数 + 全部成分股完整历史（需在本地运行）
```

## 数据来源

首次整理时的运行环境只能访问 GitHub，连不上 Yahoo Finance / Stooq / FRED，所以原始文件都取自公开 GitHub 仓库里已有的副本。精确的 commit 见 `data/raw/manifest.json`。

| 文件 | 上游仓库 | 最初来源 | 是否改动 |
| --- | --- | --- | --- |
| `index/stooq_ndx_daily_close_1985-2022.csv` | raja-grewal/stooq-commodities (MIT) | Stooq | 原样 |
| `index/yahoo_ndx_daily_ohlcv_2019-2026.csv` | Chief-rich/nasdaq100-data | Yahoo Finance | 原样 |
| `constituents/nasdaq100_constituents.csv` | Gary-Strauss/NASDAQ100_Constituents | Wikipedia | 原样 |
| `constituents/yahoo_adjusted_ohlcv_2y/` | sungholee0221-ops/us-market-data（`data` 分支） | Yahoo Finance | 只保留 Nasdaq-100 成分股，按股票拆成 CSV |
| `constituents/pubmarks_ohlcv_full_history/` | Pubmarks/datasets | 见上游说明 | 按年文件拼接成每只一个 CSV |

## 已做的校验（指数）

- Stooq 与 Yahoo 在 2019-01-02 → 2022-02-10 的 785 个重叠交易日里，收盘价最大相对差 0.00014%，交易日完全一致。
- 年末收盘与公开数值一致：1985 年 132.29、1989 年 223.84、2015 年 4593.27。
- 首次收于 20,000 / 23,000 / 26,000 点的日期与公开记录一致（2024-07-02、2025-07-17、2025-10-28）；2000 年高点为 2000-03-27 的 4704.73。
- 每年交易日数 250–254（2001 年 248，因 9·11 休市）；最长间隔是截至 2001-09-17 的 7 个日历日。
- Yahoo 文件的最后一行（2026-11-12）写入于纽约时间 10:58，是未收盘的盘中数据，`processed` 里已剔除，`raw` 里保持原样。

## 已知局限

- **指数**：1985-10-01 之前没有数据（指数 1985-01-31 发布，公开数据源都从 10 月开始）；2019 年之前只有收盘价，没有开高低。这是价格指数，不含股息。
- **成分股**：完整历史只有 10 只（AAPL、ADBE、GOOG、INTU、LRCX、META、MSFT、NFLX、NVDA、TSLA），其余 91 只目前只有近 2 年。要补齐，请在能正常上网的电脑上运行 `python scripts/download_yahoo_full.py`（该脚本尚未实际运行验证）。
- 成分股名单是**当前**名单，历史上被剔除的公司不在其中（幸存者偏差）。
- 两套成分股价格的复权口径不同：`yahoo_adjusted_ohlcv_2y` 同时做了拆股和分红复权，`pubmarks_ohlcv_full_history` 的口径以上游说明为准，不要直接拼接。

## 重新生成

```bash
pip install pandas pyarrow
python scripts/fetch_raw.py          # 重新抓取 data/raw/（两套成分股数据上游每日更新，抓到的是最新版）
python scripts/build_processed.py    # 生成 data/processed/ndx_daily.csv
```
