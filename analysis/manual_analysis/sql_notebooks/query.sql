SELECT COUNT(*) FROM ohlcv;

SELECT *
FROM ohlcv
LIMIT 10;

SELECT
    datetime(open_time / 1000, 'unixepoch') AS open_date,
    datetime(close_time / 1000, 'unixepoch') AS close_date,
    open,
    high,
    low,
    close
FROM ohlcv
LIMIT 10;