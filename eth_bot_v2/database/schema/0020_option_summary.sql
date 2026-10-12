-- ETH/BTC options summary (aggregated from option_chain).

CREATE TABLE IF NOT EXISTS option_summary (
    underlying     TEXT    NOT NULL,   -- 'ETH', 'BTC'
    ts             INTEGER NOT NULL,   -- ms epoch, aligned to snapshot time
    total_oi_call  REAL,               -- sum of OI across all calls
    total_oi_put   REAL,               -- sum of OI across all puts
    pcr_oi         REAL,               -- put/call ratio by OI
    total_vol_call REAL,               -- total volume today (calls)
    total_vol_put  REAL,               -- total volume today (puts)
    pcr_vol        REAL,               -- put/call ratio by volume
    atm_iv         REAL,               -- ATM implied vol (nearest expiry)
    iv_25d_skew    REAL,               -- 25-delta risk reversal
    term_structure REAL,               -- 7d IV - 30d IV
    max_pain       REAL,               -- strike with max total OI
    PRIMARY KEY (underlying, ts)
);

CREATE INDEX IF NOT EXISTS idx_option_summary_lookup
    ON option_summary (underlying, ts DESC);
