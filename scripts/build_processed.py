#!/usr/bin/env python3
"""Merge the two raw ^NDX files into one continuous daily series.

  data/raw/index/stooq_ndx_daily_close_1985-2022.csv   close only, 1985-10-01 .. 2022-02-10
  data/raw/index/yahoo_ndx_daily_ohlcv_2019-2026.csv   OHLCV,     2019-01-02 .. latest

Rule: Stooq up to 2018-12-31, Yahoo from 2019-01-02. The 2019-2022 overlap is
used only to check that the two sources agree. A last Yahoo row stamped before
the US close (16:00 New York) is an unfinished session and is dropped.

Output: data/processed/ndx_daily.csv  (date, close, open, high, low, source)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "index"
OUT = ROOT / "data" / "processed"
SPLICE = "2019-01-01"


def main() -> None:
    stooq = pd.read_csv(RAW / "stooq_ndx_daily_close_1985-2022.csv")
    stooq.columns = ["date", "close"]
    stooq["date"] = pd.to_datetime(stooq["date"])
    stooq = stooq.dropna().sort_values("date").drop_duplicates("date")

    yahoo = pd.read_csv(RAW / "yahoo_ndx_daily_ohlcv_2019-2026.csv")
    yahoo = yahoo.rename(columns=str.lower)[["date", "open", "high", "low", "close"]]
    yahoo["date"] = pd.to_datetime(yahoo["date"])
    yahoo = yahoo.dropna(subset=["close"]).sort_values("date").drop_duplicates("date")

    meta = json.loads((RAW / "yahoo_ndx_daily_ohlcv_2019-2026.meta.json").read_text())
    stamp = pd.Timestamp(meta["last_updated_utc"]).tz_convert("America/New_York")
    last = yahoo["date"].iloc[-1]
    if last.date() == stamp.date() and stamp.hour < 16:
        print(f"Dropping {last.date()}: file was written {stamp:%H:%M} New York time, before the close")
        yahoo = yahoo.iloc[:-1]

    both = stooq.merge(yahoo[["date", "close"]], on="date", suffixes=("_stooq", "_yahoo"))
    rel = (both["close_stooq"] / both["close_yahoo"] - 1).abs()
    print(f"Overlap {both['date'].min().date()}..{both['date'].max().date()}: {len(both)} days, "
          f"max |diff| {rel.max():.5%}, mean {rel.mean():.6%}")
    only_s = set(stooq[stooq["date"] >= yahoo["date"].min()]["date"]) - set(yahoo["date"])
    only_y = set(yahoo[yahoo["date"] <= stooq["date"].max()]["date"]) - set(stooq["date"])
    print(f"Dates in only one source during overlap: stooq-only {len(only_s)}, yahoo-only {len(only_y)}")

    a = stooq[stooq["date"] < SPLICE].assign(open=float("nan"), high=float("nan"), low=float("nan"), source="stooq")
    b = yahoo[yahoo["date"] >= SPLICE].assign(source="yahoo")
    out = pd.concat([a, b])[["date", "close", "open", "high", "low", "source"]].reset_index(drop=True)
    for c in ["close", "open", "high", "low"]:
        out[c] = out[c].round(2)

    gaps = out["date"].diff().dt.days
    print(f"Rows {len(out)}, {out['date'].min().date()}..{out['date'].max().date()}; "
          f"longest gap {int(gaps.max())} calendar days ending {out.loc[gaps.idxmax(), 'date'].date()}")
    assert out["date"].is_monotonic_increasing and out["date"].is_unique and (out["close"] > 0).all()

    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "ndx_daily.csv", index=False, date_format="%Y-%m-%d")
    print(f"Wrote {OUT / 'ndx_daily.csv'}")


if __name__ == "__main__":
    main()
