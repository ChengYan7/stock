#!/usr/bin/env python3
"""Download the complete Yahoo Finance history for the Nasdaq-100 index and
every current constituent. Run this on a machine with normal internet access.

    pip install yfinance pandas
    python scripts/download_yahoo_full.py

Writes one CSV per symbol to data/raw/yahoo_full/:
    index/NDX.csv, index/IXIC.csv, index/QQQ.csv
    constituents/<TICKER>.csv
Columns: Date, Open, High, Low, Close, Adj Close, Volume, Dividends, Stock Splits
(Close is split-adjusted; Adj Close is also dividend-adjusted.)

NOTE: written but not yet run - Yahoo Finance was unreachable from the
environment where this repository was first assembled.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "yahoo_full"
INDEXES = {"^NDX": "NDX", "^IXIC": "IXIC", "QQQ": "QQQ"}


def fetch(symbol: str, tries: int = 3) -> pd.DataFrame:
    for attempt in range(1, tries + 1):
        try:
            df = yf.Ticker(symbol).history(period="max", interval="1d", auto_adjust=False, actions=True)
            if not df.empty:
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                df.index.name = "Date"
                return df
        except Exception as exc:  # network hiccup or rate limit: wait and retry
            print(f"    {symbol}: attempt {attempt} failed ({exc})", file=sys.stderr)
        time.sleep(5 * attempt)
    return pd.DataFrame()


def main() -> None:
    tickers = pd.read_csv(ROOT / "data" / "raw" / "constituents" / "nasdaq100_constituents.csv")["Ticker"].astype(str)
    jobs = [(sym, OUT / "index" / f"{name}.csv") for sym, name in INDEXES.items()]
    jobs += [(t, OUT / "constituents" / f"{t}.csv") for t in tickers]
    failed = []
    for i, (sym, dest) in enumerate(jobs, 1):
        df = fetch(sym)
        if df.empty:
            failed.append(sym)
            print(f"[{i}/{len(jobs)}] {sym}: FAILED")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dest, date_format="%Y-%m-%d")
        print(f"[{i}/{len(jobs)}] {sym}: {len(df)} rows, {df.index[0].date()} .. {df.index[-1].date()}")
        time.sleep(0.5)
    print(f"Done. {len(jobs) - len(failed)} ok, {len(failed)} failed: {failed}")


if __name__ == "__main__":
    main()
