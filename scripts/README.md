# Data-download scripts

Both scripts use the Python standard library only — nothing to install beyond a normal Python 3.9+
interpreter. They write files under the names the notebook expects; run them from (or point `--outdir`/`--out`
at) the repository root so the notebook's bare relative paths resolve.

## `download_deribit.py` — public Deribit data (no account needed)

```bash
# Daily DVOL index
python download_deribit.py dvol --currency BTC --start 2018-01-01
python download_deribit.py dvol --currency ETH --start 2019-01-01

# Tick-level forced liquidations (perp + future + option, incl. option iv)
python download_deribit.py liq  --currency BTC --start 2019-04-01
python download_deribit.py liq  --currency ETH --start 2019-04-01

# Everything, both assets
python download_deribit.py all  --start 2018-01-01
```

Uses Deribit's public REST API. See the depth caveat in [../DATA.md](../DATA.md): the public trade endpoint
is rate-limited and may not reach the earliest history for every instrument; for a full multi-year tape use
Deribit's historical-data service or a vendor mirror and keep the documented column layout.

## `download_firstratedata.py` — licensed 5-minute prices (your own key)

```bash
export FRD_USERID=xxxxxxxxxxxxx     # from your FirstRate Data signup email (or pass --userid)
python download_firstratedata.py --ticker BTCUSD --out BTC_full_5min.txt
python download_firstratedata.py --ticker ETHUSD --out ETH_full_5min.txt
```

Requires your **own** FirstRate Data subscription. The licence forbids redistributing the raw files, so they
are excluded by `.gitignore` — keep them local. Confirm the exact `--ticker`, `--period`, and `--timeframe`
codes on your personalised API docs page:
`https://firstratedata.com/about/api-docs?type=crypto&userid=<USERID>`.
