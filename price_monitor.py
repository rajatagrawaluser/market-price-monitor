#!/usr/bin/env python3
"""
Monitor the US Dollar Index (DXY), gold and silver prices.

Data source: Yahoo Finance via the `yfinance` package (free; quotes may be
delayed, and this is an unofficial API meant for personal use).

  DXY    -> DX-Y.NYB  (ICE U.S. Dollar Index futures)
  Gold   -> GC=F      (COMEX gold futures, USD per troy oz)
  Silver -> SI=F      (COMEX silver futures, USD per troy oz)

Setup:
  pip install yfinance

Examples:
  python price_monitor.py                        # refresh every 60 s until Ctrl+C
  python price_monitor.py --once                 # one snapshot and exit
  python price_monitor.py --interval 300 --csv prices.csv
  python price_monitor.py --alert gold>2500 --alert silver<30 --alert dxy>105
"""

import argparse
import csv
import os
import re
import sys
import time
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    sys.exit("Missing dependency. Install it with: pip install yfinance")

SYMBOLS = {
    "dxy": ("US Dollar Index", "DX-Y.NYB"),
    "gold": ("Gold (USD/oz)", "GC=F"),
    "silver": ("Silver (USD/oz)", "SI=F"),
}

ALERT_RE = re.compile(r"^(dxy|gold|silver)([<>])([\d.]+)$", re.IGNORECASE)


def fetch_quotes():
    """Return {key: (last_price, previous_close)}; value is None if a fetch fails."""
    quotes = {}
    for key, (_, ticker) in SYMBOLS.items():
        try:
            fi = yf.Ticker(ticker).fast_info
            quotes[key] = (float(fi.last_price), float(fi.previous_close))
        except Exception as exc:  # network errors, bad ticker, missing data
            print(f"  ! could not fetch {key} ({ticker}): {exc}", file=sys.stderr)
            quotes[key] = None
    return quotes


def render(quotes):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]")
    for key, (name, _) in SYMBOLS.items():
        q = quotes.get(key)
        if q is None:
            print(f"  {name:<18} n/a")
            continue
        price, prev = q
        change = price - prev
        pct = (change / prev * 100) if prev else 0.0
        print(f"  {name:<18} {price:>10,.2f}  {change:+9.2f}  ({pct:+.2f}%)")
    print(flush=True)


def log_csv(path, quotes):
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "dxy", "gold", "silver"])
        row = [datetime.now().isoformat(timespec="seconds")]
        for key in SYMBOLS:
            q = quotes.get(key)
            row.append(f"{q[0]:.4f}" if q else "")
        writer.writerow(row)


def parse_alerts(specs):
    alerts = []
    for spec in specs or []:
        m = ALERT_RE.match(spec.replace(" ", ""))
        if not m:
            sys.exit(f"Bad --alert '{spec}'. Use forms like gold>2500, silver<30, dxy>105")
        alerts.append((m.group(1).lower(), m.group(2), float(m.group(3))))
    return alerts


def check_alerts(alerts, quotes):
    for key, op, level in alerts:
        q = quotes.get(key)
        if q is None:
            continue
        price = q[0]
        triggered = price > level if op == ">" else price < level
        if triggered:
            name = SYMBOLS[key][0]
            print(f"  >>> ALERT: {name} at {price:,.2f} is {op} {level:,.2f}", flush=True)
            print("\a", end="", flush=True)  # terminal bell


def main():
    ap = argparse.ArgumentParser(description="Monitor DXY, gold and silver prices.")
    ap.add_argument("--interval", type=int, default=60,
                    help="seconds between refreshes (default: 60, minimum: 10)")
    ap.add_argument("--once", action="store_true", help="print one snapshot and exit")
    ap.add_argument("--csv", metavar="FILE", help="append each snapshot to a CSV file")
    ap.add_argument("--alert", action="append", metavar="RULE",
                    help="e.g. gold>2500, silver<30, dxy>105 (repeatable)")
    args = ap.parse_args()

    if args.interval < 10:
        ap.error("--interval must be at least 10 seconds to avoid hammering the data source")

    alerts = parse_alerts(args.alert)

    print("Monitoring DXY, gold and silver. Press Ctrl+C to stop.\n")
    try:
        while True:
            quotes = fetch_quotes()
            render(quotes)
            if args.csv:
                log_csv(args.csv, quotes)
            check_alerts(alerts, quotes)
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
