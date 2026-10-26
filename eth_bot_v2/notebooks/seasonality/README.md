# Seasonality Notebooks

Time-based patterns in crypto. Each notebook answers a specific question
about WHEN price tends to move.

## Contents

1. **01_day_of_week.ipynb** - Is Monday different from Friday?
2. **02_month_of_year.ipynb** - Is October different from June?
3. **03_intraday_patterns.ipynb** - Which hours of day are most active?
4. **04_hour_x_weekday.ipynb** - Combined hour x weekday heatmap
5. **05_funding_settlement_effect.ipynb** - Price action around funding times
6. **06_option_expiry_effect.ipynb** - Price pinning near max pain
7. **07_turn_of_month.ipynb** - Last/first days of month effect

## Data needed

- **1, 2, 4, 7:** daily candles from database/market.db
- **3:** hourly candles (run scripts_python/fetch_intraday.py first)
- **5:** hourly candles + funding history from Bybit
- **6:** hourly candles + Deribit option chain (live)

## Rule

Every notebook ends with:
- a chart
- a statistical test (t-test or chi-square)
- a plain-text verdict: "This pattern is REAL" or "This is NOISE"

Don't trade on any pattern until the verdict says it's real.
