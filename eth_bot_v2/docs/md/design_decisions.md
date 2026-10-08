
**Reason:** hit rate alone is misleading. A 70% win rate with
3:1 loss:win is worse than a 55% win rate with 1:2 loss:win.

**Threshold:** signals with expectancy > 0.10% (after 0.10%
round-trip cost) are real. Below 0.05% is noise.

**Impact:** all signals in Phase 4 are ranked by expectancy,
not hit rate.

---

## 4. Horizon

**Decision:** C — 24h primary

**Reason:** crypto's natural rhythm is daily. Funding cycles
are 8h, daily close is the anchor. 24h prediction survives
fees; 1h prediction rarely does.

**Impact:** signals scored on next-24h return. 1h and 4h
tested as secondary. Trade plans default to 24h holds.

---

## 5. S/R sources

**Decision:** C — all 8 sources

| # | Source | What |
|---|---|---|
| 1 | swing | pivots with N=2 both sides |
| 2 | ma | SMA20, SMA50, SMA200 |
| 3 | volume | high-volume nodes last 30d |
| 4 | pdh | previous day/week/month H/L |
| 5 | fib | 0.382, 0.5, 0.618 retracements |
| 6 | round | 50s and 100s |
| 7 | options | max pain, put/call OI walls |
| 8 | liq | liquidation clusters last 48h |

**Reason:** confluence is the edge. One source alone is weak.
When 4 sources agree, level is real.

**Impact:** `sr_levels` table has one row per (level, source).
Confluence is computed as the count of sources within 0.3%.

---

## 6. Level strength

**Decision:** D — combined score

**Formula:**

strength = 0.4 × min(touches, 5) / 5

0.4 × min(confluence, 5) / 5

0.2 × recency_score

recency_score = 1.0 if last_test < 7d
0.8 if < 30d
0.5 if < 90d
0.2 if < 365d
0.0 otherwise



**Thresholds:**

| Strength | Meaning |
|---|---|
| > 0.70 | strong |
| 0.40–0.70 | moderate |
| < 0.40 | weak (ignore) |

**Impact:** only levels with strength > 0.4 are used in
trade plans.

---

## 7. Level use in trades

**Decision:** A — entry @ level, stop behind next level

**Example:**


entry 2575 (at S1)
stop 2548 (just below S2 2545)
target 2650 (at R2)


**Reason:** stops have a story. If S2 breaks, the premise is
invalid — you exit for a reason, not a distance.

**Impact:** trade plans always reference two levels: the
entry level and the stop level.

---

## 8. S/R refresh

**Decision:** A+B — daily static + hourly dynamic

| Level | Refresh |
|---|---|
| swing, MA, volume, PDH/PDL, Fib, round | daily at 00:05 UTC |
| options, liq | hourly at :05 |
| price vs level | live in GUI |

**Reason:** static levels don't change hourly. Only dynamic
ones do.

**Impact:** two tables: `sr_levels_static` and `sr_levels_dynamic`.

---

## Architecture locked

USD-M perpetual: BTCUSDT, ETHUSDT
Clock: 1h bars
Data: ohlcv + funding + OI + LS ratio + taker + liq
Features: 1h base, 4h and 1d forward-filled
S/R: 8 sources, combined score
Stats: expectancy on 24h horizon, ranked
Backtest: walk-forward, 0.10% round-trip cost
Trade plan: entry@level, stop behind next level
GUI: live levels, alerts


## What changes if we revise

| Decision | Cost to revise |
|---|---|
| symbols | low — add rows |
| market | medium — new fetch scripts |
| success | low — recompute |
| horizon | low — recompute |
| sources | low — add 1 file |
| strength | low — recompute |
| level use | high — rewrite trade logic |
| refresh | low |


