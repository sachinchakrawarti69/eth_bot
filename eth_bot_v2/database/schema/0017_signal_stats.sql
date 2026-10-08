-- Phase 4 - statistical test results.
-- One row per (signal, horizon, run_ts).

CREATE TABLE IF NOT EXISTS signal_stats (
    signal_name      TEXT    NOT NULL,
    horizon          TEXT    NOT NULL,     -- '1h' | '4h' | '24h'
    ts               INTEGER NOT NULL,     -- when computed
    symbol           TEXT,                 -- 'ALL' or a specific symbol
    n_samples        INTEGER,
    hit_rate         REAL,                 -- fraction of positive returns
    avg_win          REAL,                 -- mean of positive returns
    avg_loss         REAL,                 -- mean of negative returns (negative)
    expectancy       REAL,                 -- hit*win - (1-hit)*|loss|
    expectancy_net   REAL,                 -- after 0.10% round-trip fee
    sharpe           REAL,                 -- annualized
    max_dd           REAL,                 -- max drawdown of the signal's cumulative return
    profit_factor    REAL,                 -- gross profit / gross loss
    stability        REAL,                 -- fraction of years with positive expectancy
    verdict          TEXT,                 -- 'strong' | 'edge' | 'weak' | 'none'
    PRIMARY KEY (signal_name, horizon, ts, symbol)
);

CREATE INDEX IF NOT EXISTS idx_signal_stats_lookup
    ON signal_stats (signal_name, horizon, ts DESC);

CREATE INDEX IF NOT EXISTS idx_signal_stats_verdict
    ON signal_stats (verdict, expectancy_net DESC);
