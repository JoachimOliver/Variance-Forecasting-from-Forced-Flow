#!/usr/bin/env python3
"""
download_deribit.py
===================

Download the two *public* Deribit inputs used by the replication notebook:

  1. The daily **DVOL** implied-volatility index   -> btc_dvol.csv / eth_dvol.csv
  2. The tick-level **forced-liquidation** tape     -> btc_all_liquidations.csv / eth_all_liquidations.csv
     (perpetual + future + option prints; option rows carry the `iv` used for the DVOL backcast)

Everything here uses Deribit's public REST API (https://docs.deribit.com), so no account or
API key is required. Only the Python standard library is used (urllib + json), so there is
nothing to install beyond a normal Python 3.9+ interpreter.

Usage
-----
    # DVOL index (fast):
    python download_deribit.py dvol  --currency BTC --start 2018-01-01 --end 2024-01-01
    python download_deribit.py dvol  --currency ETH --start 2019-01-01 --end 2024-01-01

    # Forced liquidations (slow; paginates the public trade history):
    python download_deribit.py liq   --currency BTC --start 2019-04-01 --end 2024-01-01
    python download_deribit.py liq   --currency ETH --start 2019-04-01 --end 2024-01-01

    # Both, for both assets:
    python download_deribit.py all   --start 2018-01-01 --end 2024-01-01

Files are written into --outdir (default: the current directory, i.e. next to the notebook)
under exactly the names the notebook expects.

IMPORTANT - historical depth
----------------------------
The public `get_last_trades_by_currency_and_time` endpoint is the documented way to page
through historical trades, but Deribit rate-limits it and the retained public depth does not
always reach back to 2019 for every instrument. If a deep backfill returns short, obtain the
full multi-year tape from Deribit's historical-data service or a vendor that mirrors it
(e.g. tardis.dev), then save it with the same columns listed in DATA.md. The columns this
script writes are exactly the ones the notebook's `clean_liquidations` / DVOL loaders read.
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone

API = "https://www.deribit.com/api/v2/public/"


def _get(method: str, params: dict, retries: int = 5):
    """Call a public Deribit endpoint and return the `result` payload (with simple backoff)."""
    url = API + method + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                payload = json.loads(r.read().decode("utf-8"))
            if "error" in payload and payload["error"]:
                raise RuntimeError(payload["error"])
            return payload["result"]
        except Exception as e:  # network hiccup or 429 -> exponential backoff
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Deribit call failed after {retries} tries: {method} ({last})")


def _ms(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _kind_of(instrument_name: str, queried_kind: str) -> str:
    """Map a Deribit instrument to the notebook's `instrument_kind` vocabulary."""
    n = instrument_name.upper()
    if "PERPETUAL" in n:
        return "perpetual"
    if queried_kind == "option":
        return "option"
    return "future"


def download_dvol(currency: str, start: str, end: str, outdir: str) -> str:
    """Daily DVOL OHLC -> <cur>_dvol.csv with columns: date,symbol,open,high,low,close."""
    res = _get("get_volatility_index_data", dict(
        currency=currency, start_timestamp=_ms(start), end_timestamp=_ms(end), resolution="1D"))
    rows = res.get("data", [])
    out = f"{outdir.rstrip('/')}/{currency.lower()}_dvol.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("date,symbol,open,high,low,close\n")
        for ts, o, h, l, c in rows:
            d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            f.write(f"{d},{currency},{o},{h},{l},{c}\n")
    print(f"  DVOL {currency}: {len(rows)} daily rows -> {out}")
    return out


def download_liquidations(currency: str, start: str, end: str, outdir: str) -> str:
    """Tick-level forced liquidations -> <cur>_all_liquidations.csv.

    We page `get_last_trades_by_currency_and_time` over kind in {future, option} (future covers
    perpetuals) ascending in time, and keep only trades that carry a `liquidation` flag.
    """
    cols = ["timestamp", "instrument_kind", "instrument_name", "direction", "price", "amount",
            "index_price", "mark_price", "liquidation", "tick_direction", "trade_seq", "iv"]
    out = f"{outdir.rstrip('/')}/{currency.lower()}_all_liquidations.csv"
    t0, t1 = _ms(start), _ms(end)
    n_kept = 0
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(cols) + "\n")
        for kind in ("future", "option"):
            cursor = t0
            while cursor < t1:
                res = _get("get_last_trades_by_currency_and_time", dict(
                    currency=currency, kind=kind, start_timestamp=cursor, end_timestamp=t1,
                    count=10000, sorting="asc"))
                trades = res.get("trades", [])
                if not trades:
                    break
                for tr in trades:
                    if not tr.get("liquidation"):
                        continue  # keep forced-liquidation prints only
                    name = tr.get("instrument_name", "")
                    row = [
                        tr.get("timestamp", ""),
                        _kind_of(name, kind),
                        name,
                        tr.get("direction", ""),
                        tr.get("price", ""),
                        tr.get("amount", ""),
                        tr.get("index_price", ""),
                        tr.get("mark_price", ""),
                        tr.get("liquidation", ""),
                        tr.get("tick_direction", ""),
                        tr.get("trade_seq", ""),
                        tr.get("iv", ""),  # present on option rows only
                    ]
                    f.write(",".join(str(x) for x in row) + "\n")
                    n_kept += 1
                last_ts = trades[-1]["timestamp"]
                if not res.get("has_more") or last_ts <= cursor:
                    break
                cursor = last_ts + 1
                time.sleep(0.2)  # be polite to the public API
            print(f"  liq {currency}/{kind}: cumulative kept={n_kept}")
    print(f"  liquidations {currency}: {n_kept} forced prints -> {out}")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Download public Deribit DVOL and liquidation data.")
    p.add_argument("what", choices=["dvol", "liq", "all"], help="which dataset to fetch")
    p.add_argument("--currency", choices=["BTC", "ETH"], help="asset (omit with 'all' to do both)")
    p.add_argument("--start", default="2018-01-01", help="UTC start date YYYY-MM-DD")
    p.add_argument("--end", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                   help="UTC end date YYYY-MM-DD (default: today)")
    p.add_argument("--outdir", default=".", help="output directory (default: current dir)")
    a = p.parse_args(argv)

    currencies = [a.currency] if a.currency else ["BTC", "ETH"]
    print(f"Deribit download | {a.what} | {currencies} | {a.start} -> {a.end} | -> {a.outdir}/")
    for cur in currencies:
        if a.what in ("dvol", "all"):
            download_dvol(cur, a.start, a.end, a.outdir)
        if a.what in ("liq", "all"):
            download_liquidations(cur, a.start, a.end, a.outdir)
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
