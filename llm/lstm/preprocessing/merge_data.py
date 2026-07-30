import pandas as pd

from llm.lstm.preprocessing.load_data import (
    load_ohlcv,
    load_funding_rate,
    load_open_interest,
    load_fear_greed,
    load_onchain,
)

from llm.lstm.preprocessing.clean_data import (
    clean_dataframe,
)


# ==========================================================
# Prepare DataFrame
# ==========================================================

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    df = clean_dataframe(df)

    if "open_time" in df.columns:
        df = df.sort_values("open_time")

    elif "timestamp" in df.columns:
        df = df.sort_values("timestamp")

    elif "created_at" in df.columns:
        df = df.sort_values("created_at")

    return df


# ==========================================================
# Merge Two Tables
# ==========================================================

def merge_two(left: pd.DataFrame,
              right: pd.DataFrame,
              on: str = "open_time") -> pd.DataFrame:

    if left.empty:
        return right

    if right.empty:
        return left

    if on not in left.columns:
        return left

    if on not in right.columns:
        return left

    return pd.merge(
        left,
        right,
        how="left",
        on=on
    )


# ==========================================================
# Merge All Data
# ==========================================================

def merge_all():

    ohlcv = prepare_dataframe(load_ohlcv())

    funding = prepare_dataframe(load_funding_rate())

    open_interest = prepare_dataframe(load_open_interest())

    fear = prepare_dataframe(load_fear_greed())

    onchain = prepare_dataframe(load_onchain())

    merged = ohlcv

    merged = merge_two(merged, funding)

    merged = merge_two(merged, open_interest)

    merged = merge_two(merged, fear)

    merged = merge_two(merged, onchain)

    return merged


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    df = merge_all()

    print(df.shape)

    print(df.head())

    print(df.info())