# Data specification

The notebook reads **six files** from its working directory (two per asset, BTC and ETH), by these exact
names. All timestamps are UTC.

| File (BTC / ETH) | Source | In repo? | Format |
|---|---|---|---|
| `btc_dvol.csv` / `eth_dvol.csv` | Deribit (public) | ✅ included | CSV with header |
| `btc_all_liquidations.csv` / `eth_all_liquidations.csv` | Deribit (public) | ⬇ download | CSV with header |
| `BTC_full_5min.txt` / `ETH_full_5min.txt` | FirstRate Data (licensed) | ⛔ private | CSV, **no header** |

---

## 1. DVOL index — `btc_dvol.csv`, `eth_dvol.csv`  *(included)*

Daily Deribit DVOL implied-volatility index (30-day, forward-looking, annualized in **percent**).

```
date,symbol,open,high,low,close
2021-03-24,BTC,82.13,84.40,81.55,83.97
```

- `date` — UTC date, parseable by `pandas.to_datetime`.
- `symbol` — `BTC` or `ETH` (the loader filters on this).
- `close` — DVOL level in percent (e.g. `47.53` = 47.53%); the loader squares it to implied variance in %².
  (`open/high/low` are kept for convenience but only `close` is used.)

Refresh with: `python scripts/download_deribit.py dvol --currency BTC --start 2018-01-01`.

## 2. Forced liquidations — `btc_all_liquidations.csv`, `eth_all_liquidations.csv`  *(download)*

One row per forced-liquidation print across perpetuals, futures, and options.

```
timestamp,instrument_kind,instrument_name,direction,price,amount,index_price,mark_price,liquidation,tick_direction,trade_seq,iv
1616630400123,perpetual,BTC-PERPETUAL,sell,52000.0,12000,51980.4,51975.0,T,1,884412,
1616630450456,option,BTC-26MAR21-50000-C,buy,0.0123,5.0,51990.1,0.0125,M,0,12,71.4
```

Columns consumed by `clean_liquidations` / the DVOL backcast:

| Column | Meaning |
|---|---|
| `timestamp` | ms since epoch (UTC) |
| `instrument_kind` | `perpetual` / `future` / `option` / `unknown` (`unknown` rows are dropped) |
| `instrument_name` | Deribit symbol; option names are parsed for strike & expiry in the backcast |
| `direction` | `buy` / `sell` (a `sell` liquidation closes a forced **long**, `buy` a forced **short**) |
| `price`, `amount` | execution price and size; `notional = price × amount` |
| `index_price`, `mark_price` | used for slippage and the mark-index basis feature |
| `liquidation` | flag string; contains `T` for forced-**taker** prints (used as a feature) |
| `tick_direction` | 0–3; mapped to an up/down forced-print sign |
| `trade_seq` | trade-sequence id (clustering feature) |
| `iv` | option implied volatility — **option rows only**; feeds the pre-2021 DVOL reconstruction |

Download with: `python scripts/download_deribit.py liq --currency BTC --start 2019-04-01`.

**Historical-depth caveat.** Deribit's public `get_last_trades_by_currency_and_time` endpoint is rate-limited
and its retained depth may not reach back to 2019 for every instrument. If the backfill returns short, source
the full tape from Deribit's historical-data service or a mirror such as tardis.dev and save it with the
columns above. The economic content of the paper depends on the full multi-year liquidation history.

## 3. 5-minute prices — `BTC_full_5min.txt`, `ETH_full_5min.txt`  *(licensed — not in repo)*

5-minute OHLCV bars from **FirstRate Data**. **No header**; fixed column order:

```
2021-03-24 00:00:00,52000.0,52050.0,51980.0,52010.0,134.2
2021-03-24 00:05:00,52010.0,52030.0,51990.0,52001.0,88.7
```

Order: `datetime, open, high, low, close, volume` (datetime parseable as UTC). The loader reindexes onto a
complete 5-minute grid and forward-fills the close (absent bars = zero return), so gaps in the raw file are
handled automatically — but the file itself must be headerless and in this column order.

**Licensing.** FirstRate Data is proprietary: *"the Data is for the private use of the Subscriber only"* and
may not be resold or redistributed, so it is **not** included here and is excluded by `.gitignore`. Published
academic research derived from it is permitted **with attribution to FirstRate Data as the source**. Obtain it
with your own subscription via `scripts/download_firstratedata.py` (needs your `userid`), and keep the files
local.

---

## Where files must live

The notebook uses bare relative paths (`pd.read_csv("btc_dvol.csv")`, etc.), so all six files must sit in the
directory from which you launch the notebook — i.e. the repository root. The download scripts default their
`--outdir` / `--out` to that location.
