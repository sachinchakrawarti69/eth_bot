-- Add date column + extra fields.

ALTER TABLE option_chain         ADD COLUMN date TEXT;
ALTER TABLE greeks               ADD COLUMN date TEXT;
ALTER TABLE implied_volatility   ADD COLUMN date TEXT;
ALTER TABLE option_summary       ADD COLUMN date TEXT;

ALTER TABLE option_summary       ADD COLUMN n_instruments INTEGER;
ALTER TABLE option_summary       ADD COLUMN underlying_px REAL;
ALTER TABLE option_summary       ADD COLUMN put_oi_max_strike  REAL;
ALTER TABLE option_summary       ADD COLUMN call_oi_max_strike REAL;

CREATE INDEX IF NOT EXISTS idx_chain_date   ON option_chain (underlying, date);
CREATE INDEX IF NOT EXISTS idx_greeks_date  ON greeks (underlying, date);
CREATE INDEX IF NOT EXISTS idx_iv_date      ON implied_volatility (underlying, date);
CREATE INDEX IF NOT EXISTS idx_summary_date ON option_summary (underlying, date);
