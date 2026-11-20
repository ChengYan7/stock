#!/usr/bin/env python3
"""Re-fetch the raw Nasdaq-100 data in data/raw/ from public GitHub mirrors.

Why GitHub mirrors: the environment this was first built in could only reach
GitHub, not Yahoo Finance / Stooq / FRED directly. Every file below is an
unmodified copy of a file in a public repository (or, where noted, a
row-subset / concatenation of one), so the provenance is checkable.

For a direct, complete pull from Yahoo Finance (index + full history of every
constituent) run scripts/download_yahoo_full.py on a machine with normal
internet access instead.

Usage:  python scripts/fetch_raw.py            # writes into data/raw/
Needs:  pandas, pyarrow, git
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

RAW_GH = "https://raw.githubusercontent.com"

# Pinned commits. The Stooq file is a closed archive (ends 2022-02-10) and stays
# on the 2026-11-12 commit; the other two were current on 2026-11-20.
STOOQ_REPO, STOOQ_SHA = "raja-grewal/stooq-commodities", "c97a6147e9239d7bd6b5defddc353fc973972426"
YAHOO_NDX_REPO, YAHOO_NDX_SHA = "Chief-rich/nasdaq100-data", "7dbc0384b8502137d5b4dc1f368342d3eba55a76"
CONSTITUENTS_REPO, CONSTITUENTS_SHA = "Gary-Strauss/NASDAQ100_Constituents", "8fe3553eba9d3bebc851d2fe40c3710f5cc6442a"
# These two are refreshed daily upstream, so "latest" is fetched, not a pinned commit.
SNAPSHOT_REPO, SNAPSHOT_BRANCH = "sungholee0221-ops/us-market-data", "data"
PUBMARKS_REPO = "Pubmarks/datasets"


def get(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as r:
        dest.write_bytes(r.read())
    print(f"  {dest}  ({dest.stat().st_size:,} bytes)")


def clone(repo: str, dest: Path, branch: str | None = None) -> str:
    cmd = ["git", "clone", "-q", "--depth", "1"]
    if branch:
        cmd += ["-b", branch]
    subprocess.run(cmd + [f"https://github.com/{repo}", str(dest)], check=True)
    return subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "data" / "raw"))
    out = Path(ap.parse_args().out)
    manifest: dict = {"fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "sources": {}}

    print("Index: ^NDX daily close 1985-10-01..2022-02-10 (Stooq archive)")
    get(f"{RAW_GH}/{STOOQ_REPO}/{STOOQ_SHA}/market_data/singles/stooq_NDX.csv",
        out / "index" / "stooq_ndx_daily_close_1985-2022.csv")
    manifest["sources"]["index/stooq_ndx_daily_close_1985-2022.csv"] = {
        "repo": STOOQ_REPO, "commit": STOOQ_SHA, "path": "market_data/singles/stooq_NDX.csv",
        "original_source": "Stooq (^NDX)", "modified": False}

    print("Index: ^NDX daily OHLCV 2019-01-02..latest (Yahoo Finance via yfinance)")
    get(f"{RAW_GH}/{YAHOO_NDX_REPO}/{YAHOO_NDX_SHA}/data/ndx_daily/history.csv",
        out / "index" / "yahoo_ndx_daily_ohlcv_2019-2026.csv")
    get(f"{RAW_GH}/{YAHOO_NDX_REPO}/{YAHOO_NDX_SHA}/data/ndx_daily/meta.json",
        out / "index" / "yahoo_ndx_daily_ohlcv_2019-2026.meta.json")
    manifest["sources"]["index/yahoo_ndx_daily_ohlcv_2019-2026.csv"] = {
        "repo": YAHOO_NDX_REPO, "commit": YAHOO_NDX_SHA, "path": "data/ndx_daily/history.csv",
        "original_source": "Yahoo Finance (^NDX)", "modified": False}

    print("Constituent list (scraped from Wikipedia upstream)")
    get(f"{RAW_GH}/{CONSTITUENTS_REPO}/{CONSTITUENTS_SHA}/data/nasdaq100_constituents.csv",
        out / "constituents" / "nasdaq100_constituents.csv")
    manifest["sources"]["constituents/nasdaq100_constituents.csv"] = {
        "repo": CONSTITUENTS_REPO, "commit": CONSTITUENTS_SHA, "path": "data/nasdaq100_constituents.csv",
        "original_source": "Wikipedia: Nasdaq-100 components", "modified": False}

    import pandas as pd  # imported late so the index-only part works without it

    tickers = pd.read_csv(out / "constituents" / "nasdaq100_constituents.csv")["Ticker"].astype(str).tolist()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        print("Constituents: ~2 years of adjusted daily OHLCV for every member (Yahoo via yfinance)")
        sha = clone(SNAPSHOT_REPO, tmp / "snap", SNAPSHOT_BRANCH)
        px = pd.read_parquet(tmp / "snap" / "prices.parquet")
        px["date"] = pd.to_datetime(px["date"]).dt.strftime("%Y-%m-%d")
        dest = out / "constituents" / "yahoo_adjusted_ohlcv_2y"
        dest.mkdir(parents=True, exist_ok=True)
        # Upstream rewrites its data branch every day and occasionally loses a
        # ticker's history (SNDK on 2026-11-19 came back with only 5 rows). Keep
        # the previous fetch so such a gap can be filled from it, but only with
        # rows inside upstream's own 2-year window.
        previous = {old.stem: pd.read_csv(old) for old in dest.glob("*.csv")}
        for old in dest.glob("*.csv"):
            old.unlink()
        window_start = px["date"].min()
        cols = ["date", "open", "high", "low", "close", "volume"]
        have, backfilled = [], {}
        for t in tickers:
            sub = px[px["ticker"] == t].sort_values("date")[cols]
            if sub.empty:
                continue
            prev = previous.get(t)
            if prev is not None:
                keep = prev[(prev["date"] >= window_start) & (prev["date"] < sub["date"].iloc[0])]
                if not keep.empty:
                    backfilled[t] = {"rows": len(keep), "from": keep["date"].iloc[0], "to": keep["date"].iloc[-1],
                                     "upstream_starts": sub["date"].iloc[0]}
                    print(f"  {t}: upstream starts {sub['date'].iloc[0]}; kept {len(keep)} earlier rows from the previous fetch")
                    sub = pd.concat([keep[cols], sub])
            sub.to_csv(dest / f"{t}.csv", index=False)
            have.append(t)
        missing = sorted(set(tickers) - set(have))
        print(f"  {len(have)} tickers written to {dest}; missing upstream: {missing or 'none'}")
        manifest["sources"]["constituents/yahoo_adjusted_ohlcv_2y/"] = {
            "repo": SNAPSHOT_REPO, "branch": SNAPSHOT_BRANCH, "commit_at_fetch": sha, "path": "prices.parquet",
            "original_source": "Yahoo Finance (split- and dividend-adjusted)",
            "modified": "row subset: Nasdaq-100 members only; parquet split into one CSV per ticker",
            "upstream_meta": json.loads((tmp / "snap" / "meta.json").read_text()),
            "tickers": len(have), "missing": missing}
        if backfilled:
            manifest["sources"]["constituents/yahoo_adjusted_ohlcv_2y/"]["backfilled_from_previous_fetch"] = {
                "note": "upstream history for these tickers was truncated; the earlier rows are carried over from "
                        "this repo's previous fetch (adjusted as of that fetch)",
                "tickers": backfilled}

        print("Constituents: full daily history for the members Pubmarks publishes")
        sha = clone(PUBMARKS_REPO, tmp / "pub")
        dest = out / "constituents" / "pubmarks_ohlcv_full_history"
        dest.mkdir(parents=True, exist_ok=True)
        for old in dest.glob("*.csv"):
            old.unlink()
        have = []
        for t in tickers:
            years = sorted((tmp / "pub" / "data" / "stocks" / t).glob("[0-9][0-9][0-9][0-9]/ohlcv.csv"))
            if not years:
                continue
            pd.concat([pd.read_csv(y) for y in years]).sort_values("date").to_csv(dest / f"{t}.csv", index=False)
            have.append(t)
        print(f"  {len(have)} tickers written to {dest}: {have}")
        manifest["sources"]["constituents/pubmarks_ohlcv_full_history/"] = {
            "repo": PUBMARKS_REPO, "commit_at_fetch": sha, "path": "data/stocks/<TICKER>/<YEAR>/ohlcv.csv",
            "original_source": "see upstream README", "modified": "per-year files concatenated into one CSV per ticker",
            "tickers": have}

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
