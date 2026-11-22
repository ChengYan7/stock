# stock

A data repository for Nasdaq-100 research. Raw data is in `data/raw/`; the merged and cleaned daily index series is in `data/processed/`.

**Live page: <https://chengyan7.github.io/stock/>** — a piecewise straight-line fit of the Nasdaq-100, a fixed-slope scenario from the latest close with a rolling out-of-sample test of that kind of extrapolation, and P/E on three bases. It opens in English by default; the Chinese version is at <https://chengyan7.github.io/stock/#zh>. The page files are on the `gh-pages` branch.

## Layout

```
data/
  raw/                                      Raw data (never edited by hand)
    manifest.json                           Source repo, commit and fetch time for each file
    index/
      stooq_ndx_daily_close_1985-2022.csv   ^NDX daily close, 1985-10-01 → 2022-02-10 (Stooq)
      yahoo_ndx_daily_ohlcv_2019-2026.csv   ^NDX daily OHLCV, 2019-01-02 → 2026-11-19 (Yahoo)
      yahoo_ndx_daily_ohlcv_2019-2026.meta.json
    constituents/
      nasdaq100_constituents.csv            The current 101 constituents (checked 2026-11-15)
      yahoo_adjusted_ohlcv_2y/<TICKER>.csv  All 101, adjusted daily bars for the last 2 years (2024-11-20 → 2026-11-19)
      pubmarks_ohlcv_full_history/<T>.csv   Full daily history since listing, for 10 of them (→ 2026-11-18)
    valuation/
      ndx_pe_trailing.csv                   Trailing P/E, 20 points: Nasdaq for 1999, 2000, 2019-04-30; Siblis 2016-12 → 2026-10 (sparse)
      ndx_annual_pe_nasdaq_approx_2001_2022.csv   Nasdaq's annual FY P/E, 2001–2022, read off a chart (approximate)
      ndx_forward_weekly_2001_2026.csv      12-month forward P/E, weekly, 2001-04-27 → 2026-08-05 (History of Market)
      ndx_forward_daily_separate_2026.csv   Forward P/E on a different method, daily, 2026-08-05 → 2026-11-20 (keep separate)
      historyofmarket_forward_pe.json       The original History of Market file both forward CSVs come from
  processed/
    ndx_daily.csv                           Merged ^NDX daily series, 1985-10-01 → 2026-11-18, 10,364 rows
    oos_trend_errors.csv                    Rolling out-of-sample errors of straight-line extrapolation, from scripts/oos_trend_test.py
scripts/
  fetch_raw.py                              Re-fetches data/raw/ from public GitHub mirrors
  build_processed.py                        Builds processed/ndx_daily.csv from raw
  download_yahoo_full.py                    Pulls the full history of the index and all constituents straight from Yahoo (run it on your own machine)
  oos_trend_test.py                         Rolling out-of-sample test: fit on past data only, extrapolate, compare with what happened
  page_embed.py                             Prints the P/E and test data block that gh-pages index.html embeds
```

## Data sources

The environment used for the first pass could only reach GitHub, not Yahoo Finance, Stooq or FRED, so every raw file was taken from an existing copy in a public GitHub repository. The exact commits are listed in `data/raw/manifest.json`.

| File | Upstream repo | Original source | Modified? |
| --- | --- | --- | --- |
| `index/stooq_ndx_daily_close_1985-2022.csv` | raja-grewal/stooq-commodities (MIT) | Stooq | Unchanged |
| `index/yahoo_ndx_daily_ohlcv_2019-2026.csv` | Chief-rich/nasdaq100-data | Yahoo Finance | Unchanged |
| `constituents/nasdaq100_constituents.csv` | Gary-Strauss/NASDAQ100_Constituents | Wikipedia | Unchanged |
| `constituents/yahoo_adjusted_ohlcv_2y/` | sungholee0221-ops/us-market-data (`data` branch) | Yahoo Finance | Kept only the Nasdaq-100 constituents, split into one CSV per ticker |
| `constituents/pubmarks_ohlcv_full_history/` | Pubmarks/datasets | See upstream notes | Yearly files joined into one CSV per ticker |
| `valuation/ndx_pe_trailing.csv` | (not from GitHub) | [Siblis Research](https://siblisresearch.com/data/nasdaq-100-pe-ratio/) public table and free API; [Nasdaq Index Research](https://www.nasdaq.com/articles/is-ai-another-bubble-for-the-nasdaq-100) for 1999 and 2000; Nasdaq [NDX P/E Research](https://indexes.nasdaqomx.com/docs/NDX%20P-E%20Research.pdf) p.1 for 2019-04-30 | Typed in by hand from those pages, 2026-11-22 |
| `valuation/ndx_annual_pe_nasdaq_approx_2001_2022.csv` | (not from GitHub) | Nasdaq, [NDX Extended Presentation, December 2022](https://indexes.nasdaq.com/docs/NDX_Extended%20Presentation_December%202022.pdf), p.18 | Supplied by the repo owner: 2001 is the printed 208.3, other years extracted from the vector chart; checked against the chart image |
| `valuation/ndx_forward_*.csv`, `historyofmarket_forward_pe.json` | (not from GitHub) | [History of Market](https://historyofmarket.com/nasdaq/ndx-forward-pe/) API, data under CC BY 4.0 | Supplied by the repo owner; the weekly CSV matches the JSON's `forward` array exactly (1,239 rows) |

## Checks done (index)

- Over the 785 overlapping trading days from 2019-01-02 to 2022-02-10, Stooq and Yahoo closes differ by at most 0.00014%, and the trading days match exactly.
- Year-end closes match published values: 132.29 for 1985, 223.84 for 1989 and 4593.27 for 2015.
- The dates of the first closes at 20,000 / 23,000 / 26,000 match public records (2024-07-02, 2025-07-17, 2025-10-28); the 2000 peak is 4704.73 on 2000-03-27.
- Each year has 250–254 trading days (248 in 2001, because of the market closure after 9/11); the longest gap is 7 calendar days, ending 2001-09-17.
- The last row of the Yahoo file (2026-11-19) was written at 11:33 New York time and is intraday data from before the close. It is dropped from `processed` and left as is in `raw`; the upstream mirror replaces it with the final close on its next daily update.
- New rows 2026-11-12 → 11-18 match QQQ's daily moves to within 3.5 basis points, and the 10 tickers in both constituent datasets have identical closes on the new dates.

## Known limitations

- **Index**: there is no data before 1985-10-01 (the index launched on 1985-01-31, but public sources all start in October), and before 2019 there are only closing prices, no open, high or low. This is a price index and does not include dividends.
- **Constituents**: only 10 have full history (AAPL, ADBE, GOOG, INTU, LRCX, META, MSFT, NFLX, NVDA, TSLA); the other 91 currently cover only the last 2 years. To fill this in, run `python scripts/download_yahoo_full.py` on a computer with normal internet access (the script has not yet been tested in an actual run).
- The constituent list is the **current** list, so companies removed from the index in the past are missing (survivorship bias).
- **SNDK**: on 2026-11-19 the upstream snapshot returned only 5 rows for SNDK (from 2026-11-13). `fetch_raw.py` now keeps a ticker's earlier rows from the previous fetch when upstream history is cut short (only rows inside upstream's 2-year window); for SNDK that is 2025-02-13 → 2026-11-11. 2026-11-12 is missing. Details are in `manifest.json` under `backfilled_from_previous_fetch`.
- **P/E**: no free, continuous, same-definition trailing P/E history was found. `valuation/ndx_pe_trailing.csv` has only 20 points (1999, 2000, 2019-04-30, year-ends 2016–2025 and a few 2024–2026 month-ends). The other P/E files use other definitions and must not be joined to it: Nasdaq's annual FY P/E is read off a chart (within about 2 points of Siblis for 2016–2022), and the History of Market forward P/E divides by next-12-month estimates, has a gap from 2004-12-31 to 2006-07-28, and its upstream vendor isn't disclosed, so it is fine for exploring but not for a strict backtest. The separate 2026 forward file uses a different method again. The JSON also holds a 2026 trailing series computed as Σ(w·P)/Σ(w·EPS); it is not used. Siblis's full daily history is paid. Trendonify shows a monthly series from 1990 on its page, but its CSV download only covers recent years, and it appears to use as-reported earnings (Dec 2021: 31.1 vs Siblis 38.0; Dec 2023: 34.6 vs 30.3). Different providers compute index P/E differently (GuruFocus, for example, is several points lower than Siblis in 2026), so don't mix sources in one line. For 2001–2005, earnings collapsed and trailing P/E ran into the hundreds.
- The two sets of constituent prices are adjusted differently: `yahoo_adjusted_ohlcv_2y` is adjusted for both splits and dividends, while `pubmarks_ohlcv_full_history` follows its upstream documentation. Do not splice them together directly.

- **Stages and the calculator**: the five stages on the page were chosen after the fact around the rises, and bear markets aren't fitted, so stage slopes aren't forecasts. `oos_trend_test.py` checks a fixed rule instead: at every month-end since 1985, fit a line to past closes only (3, 4, 5 or 10 years, or all), extend it, and compare with the close 1–36 months later. Extending the past 4 years' slope from the latest close, the actual close one year later fell within −31% to +37% of the extrapolation 80% of the time, and inside the fit's own ±1σ band only 37% of the time. The monthly forecasts overlap, so the effective sample is about 37 years.

## Rebuilding

```bash
pip install pandas pyarrow
python scripts/fetch_raw.py          # re-fetch data/raw/ (both constituent datasets are updated daily upstream, so you get the latest version)
python scripts/build_processed.py    # build data/processed/ndx_daily.csv
python scripts/oos_trend_test.py     # rolling out-of-sample test → data/processed/oos_trend_errors.csv
python scripts/page_embed.py > embed.js   # data block to paste into gh-pages index.html
```
