# Variance Forecasting from Forced Flow — Replication

Replication code and data-access tooling for the paper

> **Variance Forecasting from Forced Flow: Liquidations, the Variance Risk Premium, and Crypto Volatility**
> Joachim Oliver Mampouya & Tomáš Plíhal — Department of Finance, Faculty of Economics and Administration,
> Masaryk University, Brno, Czech Republic.

The paper forecasts Bitcoin and Ether realized variance from the exchange-published stream of **forced
perpetual-swap liquidations**, and trades a replicated **variance swap** against the Deribit DVOL strike. A
two-stage CNN–LSTM that first times intraday liquidation bursts and then forecasts forward log variance,
combined with a HAR benchmark, is the only model never excluded from the 75% Model Confidence Set under
squared-error loss for either asset. Separately, we reconstruct the DVOL implied-volatility index back before
its 2021 inception from option-liquidation prints (correlation 0.94 / 0.96 with the published index).

This repository contains the **exact pipeline notebook** plus scripts to obtain the input data from source.
The notebook code is identical to the version used for the published results; only its narrative cells were
expanded for readers.

---

## Repository contents

```
.
├── Notebook-replication-submission.ipynb   # the full pipeline (data → models → tables/figures)
├── requirements.txt                        # pinned Python environment
├── btc_dvol.csv  eth_dvol.csv              # daily Deribit DVOL index (public; small; included)
├── scripts/
│   ├── download_deribit.py                 # fetch DVOL + forced-liquidation tape (public API, no key)
│   ├── download_firstratedata.py           # fetch 5-min OHLCV using YOUR FirstRate Data key
│   └── README.md
├── DATA.md                                 # full data catalogue: files, formats, provenance, licensing
├── CITATION.cff                            # how to cite this work
├── LICENSE                                 # MIT — covers the CODE only (not the data)
└── .gitignore                              # excludes large/licensed data and run outputs
```

Two of the six required inputs (the small public DVOL files) are included. The large public liquidation tapes
(130–190 MB, above GitHub's 100 MB file limit) and the **licensed** FirstRate Data price files are **not**
committed — fetch them with the scripts below. See [DATA.md](DATA.md) for the complete specification.

---

## Quick start

```bash
# 1. Environment (Python 3.10–3.12; a CUDA GPU is recommended for the full run)
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Data — into the repo root (next to the notebook), using the names the notebook expects
#    (a) Deribit DVOL is already included. To refresh or extend it:
python scripts/download_deribit.py dvol --currency BTC --start 2018-01-01
python scripts/download_deribit.py dvol --currency ETH --start 2019-01-01
#    (b) Deribit forced-liquidation tape (public API; slow — see depth note in DATA.md):
python scripts/download_deribit.py liq  --currency BTC --start 2019-04-01
python scripts/download_deribit.py liq  --currency ETH --start 2019-04-01
#    (c) FirstRate Data 5-minute prices — requires YOUR own subscription/userid:
export FRD_USERID=xxxxxxxxxxxxx
python scripts/download_firstratedata.py --ticker BTCUSD --out BTC_full_5min.txt
python scripts/download_firstratedata.py --ticker ETHUSD --out ETH_full_5min.txt

# 3. Run
jupyter lab Notebook-replication-submission.ipynb
```

In the notebook's setup cell, leave `FAST_MODE = True` for a quick wiring check, or set `FAST_MODE = False`
to reproduce the paper (seven seeds, horizons H ∈ {7, 14, 30}, headline H = 30). The full run is
GPU-intensive and writes all tables, figures, curves, per-trade series, and `metrics.json` into `output1/`,
`output2/` (headline), and `output3/`. The notebook reads the data files by their bare names, so run it from
the directory that holds them (the repo root).

---

## Data sources & licensing (please read)

| Source | Datasets | Licence / sharing |
|---|---|---|
| **Deribit** (public API) | DVOL index; tick-level forced liquidations (incl. option `iv`) | Public market data. Included (DVOL) / downloadable (liquidations). |
| **FirstRate Data** | 5-minute BTC/ETH OHLCV | **Proprietary.** *"For the private use of the Subscriber only"*; redistribution prohibited. **Not** included — download with your own key. Published research derived from it is permitted **with attribution to FirstRate Data**. |

Because of the FirstRate Data terms, this repository never stores or transmits their raw files, and
`.gitignore` blocks `*_full_5min.txt` so they cannot be committed by accident. If you publish work using this
pipeline, please attribute FirstRate Data as the source of the 5-minute price series. Full details in
[DATA.md](DATA.md).

---

## Citing

If you use this code, please cite the paper (see [CITATION.cff](CITATION.cff)).

## License

The **code** in this repository (notebook and scripts) is released under the [MIT License](LICENSE). It does
**not** license any third-party data; the Deribit and FirstRate Data datasets remain under their respective
providers' terms.

## Acknowledgements

Computational resources were provided by the e-INFRA CZ project (ID:90254), supported by the Ministry of
Education, Youth and Sports of the Czech Republic.
"Variance-Forecasting-from-Forced-Flow" 
