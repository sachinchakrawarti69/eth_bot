-- Aggregated options metrics (one row per underlying per hour).

CREATE TABLE IF NOT EXISTS option_summary (
    underlying     TEXT    NOT NULL,
    ts             INTEGER NOT NULL,
    total_oi_call  REAL,
    total_oi_put   REAL,
    pcr_oi         REAL,
    total_vol_call REAL,
    total_vol_put  REAL,
    pcr_vol        REAL,
    atm_iv         REAL,
    iv_25d_skew    REAL,
    term_structure REAL,
    max_pain       REAL,
    PRIMARY KEY (underlying, ts)
);

CREATE INDEX IF NOT EXISTS idx_summary_lookup
    ON option_summary (underlying, ts DESC);
