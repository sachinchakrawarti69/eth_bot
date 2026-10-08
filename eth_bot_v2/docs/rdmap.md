Here's the complete roadmap, laid out end to end.

# ETH Bot v2 — Complete Roadmap

## The goal

A self-contained trading system for **BTC + ETH futures** that:

1. Studies 6 years of data and reports what actually predicts
2. Backtests a strategy honestly
3. Identifies key support/resistance levels
4. Predicts opportunity windows (e.g. "18:00–21:00 UTC")
5. Gives entry, stop, target, size for each setup
6. Runs from a GUI + terminal + Excel
7. Only trades when the statistical edge is real

---

## The 8 phases

```
┌────────────────────────────────────────────────────────────────┐
│   PHASE 0    DECISIONS                        (today)          │
│              answer the 8 design questions                     │
├────────────────────────────────────────────────────────────────┤
│   PHASE 1    DATA                             (1 day)          │
│              futures ohlcv + funding + OI + LS ratio           │
├────────────────────────────────────────────────────────────────┤
│   PHASE 2    FEATURES                         (1 day)          │
│              indicators per timeframe, aligned to 1h           │
├────────────────────────────────────────────────────────────────┤
│   PHASE 3    SUPPORT / RESISTANCE             (1 day)          │
│              8 sources → sr_levels table                       │
├────────────────────────────────────────────────────────────────┤
│   PHASE 4    STATISTICAL MODE                 (2 days)         │
│              test every signal, rank by expectancy             │
├────────────────────────────────────────────────────────────────┤
│   PHASE 5    BACKTEST                         (2 days)         │
│              walk-forward validation                           │
├────────────────────────────────────────────────────────────────┤
│   PHASE 6    OPPORTUNITY SCANNER              (1 day)          │
│              today's setups + timed entries                    │
├────────────────────────────────────────────────────────────────┤
│   PHASE 7    GUI + LIVE                       (1 day)          │
│              live levels, alerts, timed orders                 │
└────────────────────────────────────────────────────────────────┘

Total: ~10 days of focused work
```

---

## Phase 0 — Decisions

**Status: waiting on you.**

8 answers needed:

```
1. symbols      = A | B | C          BTC only / BTC+ETH / 4 symbols
2. market       = A | B | C          USD-M perp / COIN-M / both
3. success      = A | B | C          hit rate / expectancy / Sharpe
4. horizon      = A | B | C          1h / 4h / 24h
5. sr sources   = A | B | C | D      swing / +MA+vol / all 8 / weighted
6. strength     = A | B | C | D      touches / confluence / recency / all
7. levels use   = A | B | C | D      entry@level / stop behind / ATR / config
8. sr refresh   = A | B | C          daily / hourly / live
```

**My picks:** B, A, B, C, C, D, A, A+B

**Deliverable:** a filled-in `docs/design_decisions.md`.

---

## Phase 1 — Data

**Purpose:** get futures-specific data into `market.db`.

**New tables:**

```
market.db
├── ohlcv                    (existing) — add ETHUSDT.P, BTCUSDT.P
├── funding_rate             (existing) — populate for BTC + ETH perp
├── open_interest            (existing) — add 1h granularity
├── long_short_ratio         (NEW)      — Binance's ratio, 1h
├── taker_volume             (NEW)      — buy vs sell, 1h
├── mark_price               (NEW)      — mark + index, 1h
└── liquidations             (existing) — real data (websocket or history)
```

**New scripts:**

| Script | What | When |
|---|---|---|
| `fetch_futures.py` | ohlcv (1h, 4h, 1d) for BTC + ETH perpetuals | daily + hourly |
| `fetch_funding.py` | funding rate history | hourly |
| `fetch_oi.py` | open interest snapshots | hourly |
| `fetch_ls_ratio.py` | long/short ratio | hourly |
| `fetch_taker.py` | taker buy/sell volume | hourly |
| `fetch_liquidations.py` | recent liquidation events | daily |

**Deliverable:** all data in `market.db`, updatable with one command.

**Verification:**
```sql
SELECT COUNT(*) FROM ohlcv WHERE symbol LIKE '%.P';       -- > 50000
SELECT COUNT(*) FROM funding_rate;                        -- > 5000
SELECT COUNT(*) FROM open_interest;                       -- > 5000
SELECT COUNT(*) FROM long_short_ratio;                    -- > 5000
```

---

## Phase 2 — Features

**Purpose:** compute every indicator once, aligned to a single 1h clock.

**New file:** `scripts_python/build_features.py`

**New table:**

```sql
CREATE TABLE IF NOT EXISTS features (
    symbol     TEXT NOT NULL,
    ts         INTEGER NOT NULL,     -- 1h aligned, ms epoch
    -- price
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    -- returns
    ret_1 REAL, ret_5 REAL, ret_20 REAL, vol_20 REAL,
    -- 1h indicators
    rsi_14 REAL, macd_hist REAL, atr_14 REAL, sma_50 REAL, sma_200 REAL,
    -- 4h indicators (forward-filled)
    rsi_14_4h REAL, macd_hist_4h REAL,
    -- 1d indicators (forward-filled)
    rsi_14_1d REAL, sma_50_1d REAL, sma_200_1d REAL,
    -- futures
    funding REAL, oi REAL, oi_chg_24h REAL, ls_ratio REAL,
    taker_ratio REAL, mark_index_spread REAL,
    -- regime
    regime TEXT,                     -- 'bull','bear','chop'
    vol_regime TEXT,                 -- 'high','normal','low'
    -- calendar
    hour INTEGER, weekday INTEGER,
    -- S/R proximity (Phase 3 joins later)
    dist_to_support REAL, dist_to_resistance REAL,
    -- targets for backtesting
    target_1h REAL, target_4h REAL, target_24h REAL,
    PRIMARY KEY (symbol, ts)
);
```

**Join rules:**
- 1h bars → base clock
- 4h indicators → forward-fill to next 4h bar
- 1d indicators → forward-fill to next day
- funding → forward-fill until next 8h funding
- OI → interpolate between snapshots

**Deliverable:** `features` table with one row per (symbol, hour).

**Verification:**
```sql
SELECT COUNT(*) FROM features;
SELECT * FROM features LIMIT 5;
-- every row has values in every column (no NULLs except first N bars)
```

---

## Phase 3 — Support/Resistance

**Purpose:** detect the price levels that actually matter.

**New file:** `scripts_python/compute_sr.py`

**New table:**

```sql
CREATE TABLE IF NOT EXISTS sr_levels (
    symbol      TEXT NOT NULL,
    ts          INTEGER NOT NULL,      -- when computed
    timeframe   TEXT NOT NULL,         -- '1h','4h','1d'
    level       REAL NOT NULL,
    kind        TEXT NOT NULL,         -- 'support' | 'resistance'
    source      TEXT NOT NULL,         -- 'swing','ma50','volume','options','round','pdh','fib','liq'
    strength    REAL NOT NULL,         -- 0.0 to 1.0
    touches     INTEGER,
    last_test   INTEGER,
    confluence  INTEGER,               -- sources agreeing at this level
    PRIMARY KEY (symbol, ts, timeframe, level, source)
);
```

**8 sources:**

| # | Source | What it detects |
|---|---|---|
| 1 | swing | local high/low pivots, clustered |
| 2 | ma50 | SMA/EMA levels that repeatedly held |
| 3 | volume | high-volume nodes in last 30d |
| 4 | pdh | previous day/week/month high/low |
| 5 | fib | 0.382, 0.5, 0.618 retracements |
| 6 | round | 2500, 2550, 2600... |
| 7 | options | max pain, put/call OI walls |
| 8 | liq | clusters of recent liquidations |

**Confluence score:** for each price, count how many sources produce a level within 0.3%.

**Deliverable:** `sr_levels` table refreshed daily + hourly.

**Verification:**
```sql
SELECT level, kind, strength, confluence, source
FROM sr_levels
WHERE symbol='ETHUSDT' AND ts = (SELECT MAX(ts) FROM sr_levels)
ORDER BY level DESC;
-- looks like a chart of real levels
```

---

## Phase 4 — Statistical Mode

**Purpose:** which signals actually predict?

**New file:** `scripts_python/statistical_mode.py`

**New table:**

```sql
CREATE TABLE IF NOT EXISTS signal_stats (
    signal_name    TEXT NOT NULL,
    timeframe      TEXT NOT NULL,       -- '1h','4h','1d'
    horizon        TEXT NOT NULL,       -- '1h','4h','24h'
    ts             INTEGER NOT NULL,
    n_samples      INTEGER,
    hit_rate       REAL,
    avg_win        REAL,
    avg_loss       REAL,
    expectancy     REAL,                -- hit*avg_win - (1-hit)*avg_loss
    sharpe         REAL,
    max_dd         REAL,
    -- year-by-year stability
    yr1_expectancy REAL,
    yr2_expectancy REAL,
    yr3_expectancy REAL,
    verdict        TEXT,                -- 'edge' | 'weak' | 'none'
    PRIMARY KEY (signal_name, timeframe, horizon, ts)
);
```

**Signals to test:**

By timeframe:

**1d (regime):**
- price > SMA50
- price > SMA200
- SMA50 > SMA200
- RSI < 30 / > 70
- vol percentile

**4h (setup):**
- structure (HH/HL)
- funding extremes
- OI 24h change
- distance from MA

**1h (trigger):**
- RSI cross
- MACD cross
- volume spike
- taker imbalance
- hour-of-day
- day-of-week

**Composite:**
- regime + setup agree
- regime + trigger + S/R proximity
- funding + OI + RSI together

**Deliverable:** ranking table printed to console + saved to DB.

```
SIGNAL                         TF   N    HIT   EXP     SHARPE  VERDICT
RSI<30 + regime bull           1h   34   64%   +0.42%  1.5     edge
funding > 0.05%                4h   82   41%   -0.62%  -1.1    edge(short)
price near 4-touch support     1h   240  62%   +0.34%  1.2     edge
OI drop > 5% + price up        4h   61   55%   +0.31%  1.2     weak
hour 18 UTC                    1h   1200 53%   +0.06%  0.3     none
```

**Verification:** the table has 20+ rows with realistic edge.

---

## Phase 5 — Backtest

**Purpose:** does a strategy using the winning signals actually make money?

**New file:** `scripts_python/backtest.py`

**Strategy definition:**

```
IF regime (1d) = bull
AND setup (4h) = valid
AND trigger (1h) = fires
AND S/R proximity = within 0.5%
THEN enter LONG
     size   = 1% risk
     stop   = below nearest support
     target = next resistance
     max hold = 24h
```

**Output:**

```
STRATEGY: regime + trigger + S/R
Period:   2023-01-01 → 2026-01-01
Trades:   340
Win rate: 54%
Avg win:  +0.82%
Avg loss: -0.41%
Expectancy: +0.28%
Sharpe:   1.4
Max DD:   -14%
Profit factor: 2.1

Year-by-year:
  2023  +34%   Sharpe 1.6
  2024  +22%   Sharpe 1.2
  2025  +18%   Sharpe 1.1
  2026  -2%    Sharpe -0.2

Walk-forward (6-month windows):
  6/8 windows profitable
```

**Verdict rule:** Sharpe > 1.0 AND DD < 25% AND > 60% windows positive.

**Deliverable:** `reports/backtest/<strategy>_<date>.json` + printed report.

---

## Phase 6 — Opportunity Scanner

**Purpose:** for *today*, produce the conditional orders.

**New file:** `scripts_python/opportunity.py`

**What it does:**

1. Load current features + S/R
2. Run strategy rules → is there a setup?
3. If yes: compute entry, stop, target, size
4. Time it: which window today?
5. Set trigger: what price?
6. Set expiry: when to cancel
7. Save to `reports/orders/YYYY-MM-DD.json`

**Output for the day:**

```json
{
  "date": "2026-10-08",
  "regime": "bull",
  "setups": [
    {
      "id": "ETH-LONG-1",
      "symbol": "ETHUSDT",
      "direction": "LONG",
      "window": ["2026-10-08T18:00Z", "2026-10-08T21:00Z"],
      "trigger": "price <= 2575",
      "entry": 2575,
      "stop": 2538,
      "target": 2650,
      "rr": 2.02,
      "size": 0.0210,
      "risk_usd": 10,
      "invalidation": [
        "BTC drops > 1.5% in 1h",
        "price breaks below 2530",
        "RSI > 60 before entry",
        "window expires"
      ]
    }
  ]
}
```

**Deliverable:** a fresh JSON every day + list on console.

---

## Phase 7 — GUI + Live

**Purpose:** show the plan, watch for triggers, alert.

**Updated GUI tabs:**

| Tab | Content |
|---|---|
| **Dashboard** | current action, score, levels |
| **Today's Plan** | conditional orders for the day |
| **Levels** | chart of S/R levels + current price |
| **Signals** | which signals are firing right now |
| **History** | past orders + outcomes |

**Live updates:**
- every 10s: refresh price
- every 60s: check if any trigger fired
- every 5 min: refresh S/R proximity
- alert on trigger fired (sound + popup)

**Deliverable:** one GUI window showing everything.

---

## What each phase produces

```
Phase 0  →  docs/design_decisions.md
Phase 1  →  market.db + fetch scripts
Phase 2  →  features table
Phase 3  →  sr_levels table + daily S/R map
Phase 4  →  signal_stats table + ranking
Phase 5  →  reports/backtest/*.json
Phase 6  →  reports/orders/YYYY-MM-DD.json
Phase 7  →  GUI with live plan
```

---

## Directory layout at the end

```
eth_bot_v2/
├── database/
│   ├── market.db                     futures data
│   ├── options.db                    options data
│   └── schema/
│       ├── 0001..0013.sql            existing
│       ├── 0014_features.sql         Phase 2
│       ├── 0015_sr_levels.sql        Phase 3
│       ├── 0016_signal_stats.sql     Phase 4
│       └── options/                  existing
│
├── scripts_python/
│   ├── update_multi.py               existing
│   ├── fetch_futures.py              Phase 1
│   ├── fetch_funding.py              Phase 1
│   ├── fetch_oi.py                   Phase 1
│   ├── fetch_ls_ratio.py             Phase 1
│   ├── fetch_taker.py                Phase 1
│   ├── fetch_options.py              existing
│   ├── build_features.py             Phase 2
│   ├── compute_sr.py                 Phase 3
│   ├── statistical_mode.py           Phase 4
│   ├── backtest.py                   Phase 5
│   ├── opportunity.py                Phase 6
│   ├── cmd/take_trade.py             existing
│   └── gui/take_trade.py             Phase 7
│
├── analysis/
│   ├── notebooks/                    existing
│   ├── prediction_notebooks/         existing
│   ├── forecast_notebooks/           existing
│   └── option_notebook/              existing
│
├── excel/
│   ├── export_ohlcv.py               existing
│   ├── export_multi.py               existing
│   ├── export_forecasts.py           existing
│   └── export_signals.py             Phase 4
│
├── reports/
│   ├── forecasts/                    existing
│   ├── backtest/                     Phase 5
│   └── orders/                       Phase 6
│
└── docs/
    ├── design_decisions.md           Phase 0
    ├── architecture/                 existing
    └── signals.md                    Phase 4
```

---

## Timeline

| Day | Phase | Output |
|---|---|---|
| 1 | Phase 0 | decisions doc |
| 2 | Phase 1 | futures data in DB |
| 3 | Phase 2 | features table |
| 4 | Phase 3 | sr_levels table |
| 5-6 | Phase 4 | signal ranking |
| 7-8 | Phase 5 | backtest results |
| 9 | Phase 6 | today's plan |
| 10 | Phase 7 | live GUI |

**Realistic:** 10 focused days. Can stretch to 3 weeks at part-time.

---

## Milestones

| Milestone | Trigger | Meaning |
|---|---|---|
| **M1** | Phase 1 done | You have futures data |
| **M2** | Phase 3 done | You know the levels |
| **M3** | Phase 4 done | You know which signals work |
| **M4** | Phase 5 done | You have a strategy with real Sharpe |
| **M5** | Phase 6 done | You have today's trade plan |
| **M6** | Phase 7 done | Live alerts + automation |

**M4 is the "go / no-go" point.** If the backtest shows Sharpe < 1 after all this work, either the strategy needs different signals or the market doesn't have the edge you hoped. It's better to know at Day 8 than Day 100.

---

## Success criteria

**The system works if:**

- [ ] Phase 4 shows 3+ signals with expectancy > 0.1%
- [ ] Phase 5 backtest has Sharpe > 1.0 over 3 years
- [ ] Phase 5 walk-forward has > 60% positive windows
- [ ] Phase 6 produces a plan every day with clear levels
- [ ] Phase 7 shows live triggers and alerts
- [ ] You can run daily in < 5 minutes manually
- [ ] You can also automate it fully

**The system fails if:**

- All signals show expectancy ≈ 0
- Backtest Sharpe < 0.5
- The best backtest comes from a single year (overfit)
- You can't explain *why* any signal works

In failure, the correct move is **not more models** — it's better data (funding, OI, liquidations) or a different horizon (intraday).

---

## Risks and mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **Overfitting** | Backtest looks great, live loses | Walk-forward + intuition check |
| **Data gaps** | Signals broken | Phase 1 has gap checks |
| **Fees eat edge** | Real profit ≈ 0 | Model 0.1% per side in Phase 5 |
| **Regime change** | Strategy stops working | Regime detection in Phase 2 |
| **Slippage** | Entries worse than expected | Model 0.05% per side |
| **Emotional override** | Skip signals | Automation + logging |
| **API limits** | Data missing | Batched requests + caching |

---

## What to do first

**Answer Phase 0.**

Reply with:

```
1. symbols      = B
2. market       = A
3. success      = B
4. horizon      = C
5. sr sources   = C
6. strength     = D
7. levels use   = A
8. sr refresh   = A+B
```

(or your own choices)

Then I'll:

1. Write `docs/design_decisions.md` — locks the plan
2. Write Phase 1 scripts — `fetch_futures.py`, `fetch_funding.py`, etc.
3. Test on your existing setup
4. Move to Phase 2

**Nothing gets built until Phase 0 is answered.** Wrong decisions here cost days later.

---

## The one-sentence summary

> Roadmap is 8 phases: decisions → data → features → S/R → statistics → backtest → opportunity → GUI. Answer Phase 0 (8 choices), then build in order. Stop at Phase 5 if the backtest shows no Sharpe > 1. Everything else is scaffolding around those 8 phases.