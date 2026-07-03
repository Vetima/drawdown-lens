#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drawdown-lens — Understand the downside of any crypto asset before it hits you.

A tiny, zero-dependency tool that pulls public Binance price history (no API key,
no account) and answers the only question that matters in a crash:

    "How far down did this asset go, for how long, and how long did it take to recover?"

Most people look at returns. Almost nobody looks at drawdown — the peak-to-trough
pain you actually have to live through. This tool puts that number in front of you.

Usage:
    python drawdown_lens.py BTCUSDT
    python drawdown_lens.py ETHUSDT --days 730 --interval 1d
    python drawdown_lens.py SOLUSDT --json

No API key. No dependencies beyond the Python standard library.

Made by Vetima — https://vetima.trade
Licensed MIT. Not financial advice.
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
# Binance caps klines at 1000 rows per call; we page backwards if needed.
_MAX_PER_CALL = 1000
_INTERVAL_MS = {
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000,
    "6h": 21_600_000, "12h": 43_200_000, "1d": 86_400_000,
    "3d": 259_200_000, "1w": 604_800_000,
}


def _fetch_closes(symbol, interval, days):
    """Return list of (timestamp_ms, close_price) oldest->newest, spanning `days`."""
    if interval not in _INTERVAL_MS:
        raise ValueError(f"interval must be one of {', '.join(_INTERVAL_MS)}")
    step = _INTERVAL_MS[interval]
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - days * 86_400_000
    rows = []
    cursor = start_ms
    while cursor < now_ms:
        url = (f"{BINANCE_KLINES}?symbol={symbol.upper()}&interval={interval}"
               f"&startTime={cursor}&limit={_MAX_PER_CALL}")
        req = urllib.request.Request(url, headers={"User-Agent": "drawdown-lens"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                batch = json.load(r)
        except urllib.error.HTTPError as e:
            raise SystemExit(f"Binance API error {e.code} for '{symbol}'. "
                             f"Is the symbol spelled right (e.g. BTCUSDT)?")
        except urllib.error.URLError as e:
            raise SystemExit(f"Network error reaching Binance: {e.reason}")
        if not batch:
            break
        for k in batch:
            rows.append((int(k[0]), float(k[4])))  # open time, close
        cursor = batch[-1][0] + step
        if len(batch) < _MAX_PER_CALL:
            break
    if not rows:
        raise SystemExit(f"No data returned for '{symbol}'. Check the symbol.")
    return rows


def analyze_drawdown(series):
    """series: list of (ts_ms, price) oldest->newest. Returns a metrics dict."""
    peak_price = series[0][1]
    peak_ts = series[0][0]
    max_dd = 0.0            # most negative drawdown (as a positive %)
    max_dd_peak_ts = peak_ts
    max_dd_trough_ts = peak_ts
    max_dd_trough_price = peak_price
    max_dd_peak_price = peak_price

    # underwater tracking: how long price stayed below a prior peak
    underwater_start = None
    longest_underwater_ms = 0
    longest_underwater_span = (None, None)

    for ts, price in series:
        if price >= peak_price:
            # new peak -> any underwater stretch just ended (recovered)
            if underwater_start is not None:
                span = ts - underwater_start
                if span > longest_underwater_ms:
                    longest_underwater_ms = span
                    longest_underwater_span = (underwater_start, ts)
                underwater_start = None
            peak_price = price
            peak_ts = ts
        else:
            if underwater_start is None:
                underwater_start = peak_ts
            dd = (peak_price - price) / peak_price * 100.0
            if dd > max_dd:
                max_dd = dd
                max_dd_peak_ts = peak_ts
                max_dd_peak_price = peak_price
                max_dd_trough_ts = ts
                max_dd_trough_price = price

    # if still underwater at the end, count it
    if underwater_start is not None:
        span = series[-1][0] - underwater_start
        if span > longest_underwater_ms:
            longest_underwater_ms = span
            longest_underwater_span = (underwater_start, series[-1][0])

    last_ts, last_price = series[-1]
    current_dd = (peak_price - last_price) / peak_price * 100.0 if last_price < peak_price else 0.0

    return {
        "max_drawdown_pct": round(max_dd, 2),
        "max_dd_peak": {"date": _fmt(max_dd_peak_ts), "price": max_dd_peak_price},
        "max_dd_trough": {"date": _fmt(max_dd_trough_ts), "price": max_dd_trough_price},
        "max_dd_duration_days": round((max_dd_trough_ts - max_dd_peak_ts) / 86_400_000, 1),
        "longest_underwater_days": round(longest_underwater_ms / 86_400_000, 1),
        "longest_underwater_span": [
            _fmt(longest_underwater_span[0]) if longest_underwater_span[0] else None,
            _fmt(longest_underwater_span[1]) if longest_underwater_span[1] else None,
        ],
        "current_drawdown_pct": round(current_dd, 2),
        "samples": len(series),
        "first_date": _fmt(series[0][0]),
        "last_date": _fmt(last_ts),
    }


def _fmt(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _bar(pct, width=30):
    filled = min(width, int(round(pct / 100.0 * width)))
    return "#" * filled + "." * (width - filled)


def print_report(symbol, interval, m):
    print()
    print(f"  drawdown-lens | {symbol.upper()} | {interval} | {m['first_date']} -> {m['last_date']}")
    print("  " + "-" * 56)
    print(f"  Worst drawdown ....... -{m['max_drawdown_pct']:.2f}%   {_bar(m['max_drawdown_pct'])}")
    print(f"    from peak .......... {m['max_dd_peak']['date']}  ({m['max_dd_peak']['price']:g})")
    print(f"    to trough .......... {m['max_dd_trough']['date']}  ({m['max_dd_trough']['price']:g})")
    print(f"    fall took .......... {m['max_dd_duration_days']:g} days")
    print(f"  Longest underwater ... {m['longest_underwater_days']:g} days below a prior peak")
    if m["current_drawdown_pct"] > 0:
        print(f"  Right now ............ -{m['current_drawdown_pct']:.2f}% below its high (this window)")
    else:
        print(f"  Right now ............ at/near its high for this window")
    print("  " + "-" * 56)
    print("  Returns are the story you're sold. Drawdown is the one you live through.")
    print("  Made by Vetima | https://vetima.trade | not financial advice")
    print()


def main():
    p = argparse.ArgumentParser(
        description="Measure the real downside (drawdown) of any crypto asset, from public Binance data.")
    p.add_argument("symbol", help="Binance pair, e.g. BTCUSDT, ETHUSDT, SOLUSDT")
    p.add_argument("--days", type=int, default=365, help="lookback window in days (default 365)")
    p.add_argument("--interval", default="1d",
                   help="candle size: 1h,2h,4h,6h,12h,1d,3d,1w (default 1d)")
    p.add_argument("--json", action="store_true", help="print raw JSON instead of a report")
    args = p.parse_args()

    series = _fetch_closes(args.symbol, args.interval, args.days)
    metrics = analyze_drawdown(series)
    metrics["symbol"] = args.symbol.upper()
    metrics["interval"] = args.interval

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print_report(args.symbol, args.interval, metrics)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
