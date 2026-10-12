# analysis/option_notebook/

Options analysis notebooks. All read from `database/options.db`.

## Notebooks

| # | Notebook | Focus |
|---|---|---|
| 01 | chain_snapshot | Full chain for latest snapshot |
| 02 | iv_smile | IV across strikes, one expiry |
| 03 | iv_surface | IV heatmap, strike × expiry |
| 04 | put_call_ratio | PCR over time |
| 05 | skew_term | Skew and term structure |
| 06 | iv_vs_realized | Vol premium |
| 07 | max_pain | Max pain analysis |
| 08 | greeks | Delta, gamma, theta, vega |
| 09 | dashboard | Everything in one view |

## Prerequisites

Data must be in `database/options.db`. Populate with:

    python database/init_options_db.py
    python -m scripts_python.fetchers.options --currency ETH
    python -m scripts_python.fetchers.options --currency ETH --greeks

## Open all

    python -m jupyterlab analysis/option_notebook

## Notebooks that need --greeks

Only `08_greeks.ipynb` needs the `--greeks` flag when fetching.
All others work with the default chain snapshot.
