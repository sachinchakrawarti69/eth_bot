# HMM Predictor

Hidden Markov Model for **market regime detection**.

Labels each day as **bull**, **bear**, or **chop** — the hidden state the
market is currently in.

## What it does

An HMM assumes the market has N hidden states. Each state has its own
distribution of returns. By observing recent returns, the model infers
which state we're in today.

```
Hidden states:      [ bull ]  [ chop ]  [ bear ]

Each state emits a return distribution:

  bull   → mean +0.4%, std 2.1%
  chop   → mean  0.0%, std 1.8%
  bear   → mean -0.5%, std 3.4%

Transitions (learned from 6 years):
  bull → bull  95%
  bull → chop   4%
  bull → bear   1%
  chop → chop  85%
  chop → bull  10%
  chop → bear   5%
  bear → bear  92%
  bear → chop   6%
  bear → bull   2%
```

At predict time, the model runs the **Viterbi algorithm** over the last
60 days of returns and returns the current state.

## What it outputs

| Field | Meaning |
|---|---|
| `state` | `bull`, `bear`, or `chop` |
| `raw_state` | integer 0/1/2 |
| `state_days` | how many days we've been in this state |

**It does NOT output a probability.** Regime is a label, not a probability.
Use the [hmm_logistic](../hmm_logistic/README.md) predictor if you want
a probability conditioned on the state.

## Folder contents

```
hmm/
├── __init__.py
├── config.py       ← hyperparameters
├── train.py        ← fit HMM on daily returns
├── predict.py      ← infer today's state
└── explain.py      ← show last 30 days of states
```

## Configuration

`config.py`:

```python
MODEL_NAME = "hmm"

HYPERPARAMS = {
    "n_components": 3,       # 3 states: bull / chop / bear
    "covariance_type": "diag",
    "n_iter": 100,
    "random_state": 42,
}

FEATURES = ["close"]         # HMM uses returns, not features
TARGET = "dir_24h"
```

## Train

```powershell
python -m ml.train --symbol ETHUSDT --model hmm
```

Output:

```
[ETHUSDT] hmm
  states      : 3
  state means : {0: -0.0031, 1: 0.0004, 2: 0.0042}
  labels      : {0: 'bear', 1: 'chop', 2: 'bull'}
  samples     : 1996
  saved       : ml/_models/ETHUSDT_hmm.joblib
```

The labels are assigned automatically: **lowest mean = bear, middle = chop, highest = bull.**

## Predict

```powershell
python -m ml.predict --symbol ETHUSDT --model hmm
```

Output:

```
  symbol     : ETHUSDT
  model      : hmm
  state      : bull
  raw state  : 2
  state days : 14
```

## Explain — show the last 30 days

```python
from ml.predictors.hmm.explain import explain

df = explain("ETHUSDT", days=30)
print(df)
```

Output:

```
        date    close      ret    state
2026-09-13  2489.51  -0.0031     bear
2026-09-14  2512.30  +0.0092     chop
2026-09-15  2540.11  +0.0111     chop
...
2026-10-12  2489.51  +0.0055     bull
```

## Direct use

```python
from ml.predictors.hmm.predict import current_state

info = current_state("ETHUSDT")
print(info)
# {'symbol': 'ETHUSDT', 'raw_state': 2, 'state': 'bull', 'state_days': 14}
```

```python
from ml.predictors.hmm.explain import explain

df = explain("ETHUSDT", days=90)
# how many days were bull / bear / chop?
print(df["state"].value_counts())
```

## How states are labeled

After fitting, the model gives 3 raw states numbered 0, 1, 2.
Those numbers are meaningless until we look at what they represent.

The train script computes the mean daily return for each raw state:

```python
means = {
    0: -0.0031,      # average -0.31% per day
    1:  0.0004,      # average +0.04% per day
    2:  0.0042,      # average +0.42% per day
}
```

Then sorts and labels them:

| Raw | Mean return | Label |
|---|---|---|
| 0 | -0.31% | **bear** |
| 1 | +0.04% | **chop** |
| 2 | +0.42% | **bull** |

So when `predict()` returns `state: "bull"`, you know the market is in the
high-mean-return regime.

## When to trust it

| Situation | Read |
|---|---|
| `state = bull`, `state_days > 5` | Uptrend confirmed. Longs have edge. |
| `state = bull`, `state_days < 3` | Just entered bull. Could be a false signal. |
| `state = chop` | Avoid trend-following. Range trades only. |
| `state = bear`, `state_days > 5` | Downtrend confirmed. Shorts have edge. |
| `state = bear`, `state_days < 3` | Just entered bear. Could be a fake-out. |

## Historical context

The same model applied to ETHUSDT 2020-2026 usually shows:

| Year | Dominant state | Notes |
|---|---|---|
| 2020 | chop | pre-rally |
| 2021 | bull | DeFi + NFT cycle |
| 2022 | bear | LUNA / FTX collapse |
| 2023 | chop | sideways recovery |
| 2024 | bull | ETF + halving |
| 2025 | bear | correction |
| 2026 | chop | waiting |

## Limitations

1. **Fixed number of states.** If the market is in an unusual regime (e.g., "range with high vol"), the model still forces it into one of the 3 learned states.

2. **Lag on transitions.** Because the Viterbi path smooths states, the model takes 2-3 days to fully switch from bull to bear.

3. **Only sees returns.** The HMM ignores volume, sentiment, funding. If you want those signals, use `hmm_logistic` which combines HMM + logistic regression.

4. **Assumes Gaussian returns.** Real crypto returns have fat tails. State detection is still useful but not perfect.

5. **Regime != direction.** "Bull regime" means the *last 60 days* looked like bull. It does not mean *tomorrow* is up.

## Related predictors

- **`logistic`** — no regime awareness, just features → probability
- **`hmm_logistic`** — combines this HMM with a state-conditional logistic regression. Usually beats plain logistic by 1-3% AUC.
- **`naive_bayes`** — probability only, no regime

## Testing ideas

```python
# 1. State durations should be long (regimes persist)
df = explain("ETHUSDT", days=500)
runs = (df["state"] != df["state"].shift()).cumsum()
duration = df.groupby(runs).size()
print(duration.describe())   # expect mean 10-20 days

# 2. Bull state should have positive mean return
df["next_ret"] = df["ret"].shift(-1)
print(df.groupby("state")["next_ret"].mean())
# expect: bull > chop > bear

# 3. Check it matches intuition
df.tail(365).groupby("state").size()
# how many days in each state last year?
```

## No train/test split for the HMM itself

Unlike classifiers, HMMs are usually fit on **all available history**.
The model's job is descriptive (what regime is this?), not predictive.
The prediction step is what you test — feed it fresh data, see if the
state makes sense.

The `hmm_logistic` predictor **does** use a holdout — the logistic part
is trained on historical state labels and tested forward.

## Files this README links to

- `config.py` — hyperparameters
- `train.py` — `train(symbol) -> (metrics, path)`
- `predict.py` — `current_state(symbol)`, `predict(symbol, row)`
- `explain.py` — `explain(symbol, days=30) -> DataFrame`

## Dependencies

```powershell
python -m pip install hmmlearn scikit-learn joblib pandas
```