-- On-chain metrics (daily granularity typical).
CREATE TABLE IF NOT EXISTS onchain (
    metric TEXT    NOT NULL,
    ts     INTEGER NOT NULL,
    value  REAL    NOT NULL,
    PRIMARY KEY (metric, ts)
);
CREATE INDEX IF NOT EXISTS idx_onchain_ts
    ON onchain (metric, ts DESC);
