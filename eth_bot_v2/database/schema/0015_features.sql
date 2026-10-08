-- Phase 2 - feature store.
-- One row per (symbol, 1h bar). Every column is a signal
-- available at or before that bar. No forward-looking values.

CREATE TABLE IF NOT EXISTS features (
    symbol          TEXT    NOT NULL,
    ts              INTEGER NOT NULL,     -- 1h aligned, ms epoch

    -- raw price (for reference / debugging)
    open            REAL,
    high            REAL,
    low             REAL,
    close           REAL,
    volume          REAL,

    -- 1h returns
    ret_1           REAL,
    ret_5           REAL,
    ret_20          REAL,
    vol_20          REAL,

    -- 1h indicators
    rsi_14          REAL,
    macd_hist       REAL,
    atr_14          REAL,
    sma_20          REAL,
    sma_50          REAL,
    sma_200         REAL,
    ema_12          REAL,
    ema_26          REAL,

    -- 4h indicators (forward-filled to 1h)
    rsi_14_4h       REAL,
    macd_hist_4h    REAL,
    sma_50_4h       REAL,

    -- 1d indicators (forward-filled to 1h)
    rsi_14_1d       REAL,
    sma_50_1d       REAL,
    sma_200_1d      REAL,

    -- futures: funding rate
    funding         REAL,
    funding_3d_avg  REAL,

    -- futures: open interest
    oi              REAL,
    oi_chg_24h      REAL,

    -- futures: long/short ratio
    ls_ratio        REAL,
    ls_ratio_7d_avg REAL,

    -- futures: taker flow
    taker_ratio     REAL,

    -- regime
    regime          TEXT,       -- 'bull' | 'bear' | 'chop'
    vol_regime      TEXT,       -- 'high' | 'normal' | 'low'
    trend_up        INTEGER,    -- 0/1: close > sma_50 > sma_200
    trend_down      INTEGER,    -- 0/1: close < sma_50 < sma_200

    -- distance from moving averages (%)
    dist_sma50      REAL,
    dist_sma200     REAL,
    dist_sma50_1d   REAL,

    -- calendar
    hour            INTEGER,    -- 0-23 UTC
    weekday         INTEGER,    -- 0=Mon, 6=Sun

    -- targets (future returns) — computed for backtesting only
    target_1h       REAL,       -- close[t+1h] / close[t] - 1
    target_4h       REAL,
    target_24h      REAL,

    -- target directions (for classification)
    dir_1h          INTEGER,    -- +1 if target_1h > 0 else -1
    dir_4h          INTEGER,
    dir_24h         INTEGER,

    PRIMARY KEY (symbol, ts)
);

CREATE INDEX IF NOT EXISTS idx_features_lookup
    ON features (symbol, ts DESC);

CREATE INDEX IF NOT EXISTS idx_features_regime
    ON features (symbol, regime, ts DESC);
