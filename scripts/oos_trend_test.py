"""Rolling out-of-sample test of "extend a straight log trend" forecasts.

At every month-end t, using only closes up to t:
  - fit ln(close) = a + b*time by least squares over a trailing window
    (3, 4, 5 or 10 years, or everything since 1985-10-01);
  - "trend" rule: forecast = the fitted line's value at t+h
    (what the old calculator showed for future dates);
  - "close" rule: forecast = close(t) * exp(b*h), the same slope started
    from the latest close (what the calculator shows now).
Then compare with the actual close h months later (the last close on or
before t+h). Bull and bear markets are all included; nothing is chosen
after the fact. Windows that start before 1985-10-01 are skipped.

The forecast error is ln(actual / forecast). For each rule, window and
horizon the script writes the 10th, 50th and 90th percentiles of the
error and the share of outcomes that landed inside forecast ± the fit's
own in-sample residual sigma (a "±1σ band" would hold about 68% if it
were a forecast interval).

Usage: python scripts/oos_trend_test.py   (writes data/processed/oos_trend_errors.csv)
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "processed", "ndx_daily.csv")
OUT = os.path.join(ROOT, "data", "processed", "oos_trend_errors.csv")

WINDOWS = {"3y": 3, "4y": 4, "5y": 5, "10y": 10, "all": None}
HORIZONS = list(range(1, 37))          # months ahead
YEAR = 365.25


def main():
    d = pd.read_csv(SRC, parse_dates=["date"])[["date", "close"]].dropna()
    t_days = (d["date"] - d["date"].iloc[0]).dt.days.to_numpy(dtype=float)
    lnc = np.log(d["close"].to_numpy())
    last = t_days[-1]
    # forecast origins: the last trading day of each month
    origins = d.groupby(d["date"].dt.to_period("M")).tail(1).index.to_numpy()

    def close_at(day):
        """index of the last trading day on or before `day`"""
        return np.searchsorted(t_days, day, side="right") - 1

    rows = []
    for wname, wyears in WINDOWS.items():
        errs = {(rule, h): [] for rule in ("trend", "close") for h in HORIZONS}
        inband = {(rule, h): [] for rule in ("trend", "close") for h in HORIZONS}
        for i in origins:
            t0 = t_days[i]
            if wyears is None:
                if t0 < 3 * YEAR:            # need some history even for "all"
                    continue
                j0 = 0
            else:
                if t0 < wyears * YEAR:
                    continue
                j0 = close_at(t0 - wyears * YEAR) + 1
            x, y = t_days[j0:i + 1], lnc[j0:i + 1]
            b, a = np.polyfit(x, y, 1)
            sigma = np.std(y - (a + b * x))
            for h in HORIZONS:
                td = t0 + h * YEAR / 12
                if td > last:
                    break
                actual = lnc[close_at(td)]
                for rule, fc in (("trend", a + b * td), ("close", lnc[i] + b * (td - t0))):
                    e = actual - fc
                    errs[(rule, h)].append(e)
                    inband[(rule, h)].append(abs(e) <= sigma)
        for (rule, h), e in errs.items():
            if not e:
                continue
            e = np.array(e)
            q10, q50, q90 = np.percentile(e, [10, 50, 90])
            rows.append({
                "rule": rule, "window": wname, "horizon_months": h, "n": len(e),
                "err_p10": q10, "err_p50": q50, "err_p90": q90,
                "share_within_insample_1sigma": float(np.mean(inband[(rule, h)])),
            })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, float_format="%.5f")
    print("wrote", OUT, len(out), "rows")
    show = out[out.horizon_months.isin([12, 24])].copy()
    for c in ("err_p10", "err_p50", "err_p90"):
        show[c] = (np.exp(show[c]) - 1) * 100
    show["share_within_insample_1sigma"] *= 100
    print(show.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
