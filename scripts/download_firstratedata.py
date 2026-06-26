#!/usr/bin/env python3
"""
download_firstratedata.py
=========================

Download the 5-minute crypto OHLCV price series from **FirstRate Data** using *your own*
account, and write it under the filenames the replication notebook expects:

    BTC_full_5min.txt   ETH_full_5min.txt

WHY THIS IS A SCRIPT AND NOT A DATA FILE
----------------------------------------
The FirstRate Data licence states the data is "for the private use of the Subscriber only"
and may not be resold or redistributed. We therefore *cannot* ship the price files in this
repository. Published academic research derived from the data is explicitly permitted, with
attribution to FirstRate Data as the source. This script lets you pull the identical series
into your own working copy so you can reproduce the paper's results locally.

  -> You must have your own FirstRate Data subscription and `userid` (sent in your signup
     email). Set it via --userid or the FRD_USERID environment variable.
  -> Do NOT commit the downloaded .txt files to a public repository (the .gitignore in this
     repo already excludes *_full_5min.txt for that reason).

API reference
-------------
FirstRate Data exposes a file API that returns a ZIP archive of the requested series:

    https://firstratedata.com/api/data_file?type=crypto&ticker=<TICKER>&period=full&timeframe=5min&userid=<USERID>

The exact `ticker`, `period`, and `timeframe` codes available to you are listed on your
personalised API docs page (https://firstratedata.com/about/api-docs?type=crypto&userid=<USERID>).
Defaults below target the full-history 5-minute BTC/ETH USD series; adjust if your plan uses
different codes. Stdlib only (urllib + zipfile) - nothing to install.

Output format expected by the notebook
---------------------------------------
The notebook's `load_prices` reads the file with `header=None` and column order
    datetime, open, high, low, close, volume
i.e. NO header row. FirstRate Data crypto files are already headerless CSV in this order; this
script strips a header line if one is present and saves with the expected name.

Usage
-----
    export FRD_USERID=xxxxxxxxxxxxx          # or pass --userid
    python download_firstratedata.py --ticker BTCUSD --out BTC_full_5min.txt
    python download_firstratedata.py --ticker ETHUSD --out ETH_full_5min.txt
"""
from __future__ import annotations
import argparse, io, os, sys, urllib.request, urllib.parse, zipfile

BASE = "https://firstratedata.com/api/data_file"


def build_url(userid: str, ticker: str, period: str, timeframe: str, asset_type: str) -> str:
    return BASE + "?" + urllib.parse.urlencode(dict(
        type=asset_type, ticker=ticker, period=period, timeframe=timeframe, userid=userid))


def looks_like_header(line: str) -> bool:
    """A data row starts with a timestamp digit; a header row starts with a letter."""
    s = line.strip()
    return bool(s) and not (s[0].isdigit())


def download(userid: str, ticker: str, out: str, period: str, timeframe: str, asset_type: str):
    url = build_url(userid, ticker, period, timeframe, asset_type)
    safe = url.replace(userid, "***")
    print(f"  GET {safe}")
    try:
        with urllib.request.urlopen(url, timeout=180) as r:
            blob = r.read()
    except Exception as e:
        raise SystemExit(f"FirstRate Data request failed: {e}\n"
                         f"Check your --userid and that the ticker/timeframe exist on your plan "
                         f"(see your API docs page).")

    # The API returns a ZIP archive of one or more .txt/.csv files.
    if blob[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(blob))
        members = [m for m in zf.namelist() if m.lower().endswith((".txt", ".csv"))]
        if not members:
            raise SystemExit(f"ZIP contained no .txt/.csv data file: {zf.namelist()}")
        raw = zf.read(members[0]).decode("utf-8", errors="replace")
        print(f"  extracted {members[0]} from archive")
    else:
        # Some plans return the file directly (or an error/HTML page).
        raw = blob.decode("utf-8", errors="replace")
        if raw.lstrip().lower().startswith("<"):
            raise SystemExit("Server returned HTML, not data - the userid/ticker is likely wrong.")

    lines = raw.splitlines()
    if lines and looks_like_header(lines[0]):
        print(f"  stripping header row: {lines[0][:60]!r}")
        lines = lines[1:]

    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  wrote {len(lines)} rows (headerless) -> {out}")
    print("  REMINDER: FirstRate Data licence forbids redistributing this file. Keep it local.")


def main(argv=None):
    p = argparse.ArgumentParser(description="Download FirstRate Data 5-min crypto OHLCV (private use).")
    p.add_argument("--userid", default=os.environ.get("FRD_USERID"),
                   help="your FirstRate Data userid (or set FRD_USERID env var)")
    p.add_argument("--ticker", required=True, help="instrument code, e.g. BTCUSD / ETHUSD")
    p.add_argument("--out", required=True, help="output filename, e.g. BTC_full_5min.txt")
    p.add_argument("--period", default="full", help="history span code (default: full)")
    p.add_argument("--timeframe", default="5min", help="bar size code (default: 5min)")
    p.add_argument("--type", dest="asset_type", default="crypto", help="asset class (default: crypto)")
    a = p.parse_args(argv)

    if not a.userid:
        raise SystemExit("No userid. Pass --userid or set FRD_USERID (from your FirstRate Data signup email).")
    print(f"FirstRate Data download | {a.ticker} {a.timeframe} {a.period} -> {a.out}")
    download(a.userid, a.ticker, a.out, a.period, a.timeframe, a.asset_type)
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
