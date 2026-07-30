import pandas as pd


# ==========================================================
# Remove Duplicate Rows
# ==========================================================

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:

    return df.drop_duplicates().copy()


# ==========================================================
# Remove Missing Values
# ==========================================================

def remove_missing_values(df: pd.DataFrame) -> pd.DataFrame:

    return df.dropna().copy()


# ==========================================================
# Convert Numeric Columns
# ==========================================================

def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:

    for column in df.columns:

        if column in [
            "exchange",
            "symbol",
            "interval",
            "instrument_name",
            "option_type",
            "base_currency",
            "title",
            "url",
            "source",
            "news_source",
            "category",
        ]:
            continue

        try:
            df[column] = pd.to_numeric(df[column])

        except Exception:
            pass

    return df


# ==========================================================
# Convert Date Columns
# ==========================================================

def convert_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:

    timestamp_columns = [
        "created_at",
        "open_datetime",
        "close_datetime",
        "expiration_datetime",
        "published_at",
        "datetime",
        "date",
    ]

    for column in timestamp_columns:

        if column in df.columns:

            try:
                df[column] = pd.to_datetime(df[column])

            except Exception:
                pass

    return df


# ==========================================================
# Sort By Time
# ==========================================================

def sort_by_time(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
        "open_time",
        "timestamp",
        "published_at",
        "created_at",
        "expiration_timestamp",
    ]

    for column in columns:

        if column in df.columns:

            return df.sort_values(column)

    return df


# ==========================================================
# Reset Index
# ==========================================================

def reset_dataframe_index(df: pd.DataFrame) -> pd.DataFrame:

    return df.reset_index(drop=True)


# ==========================================================
# Generic Cleaning Pipeline
# ==========================================================

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = remove_duplicates(df)

    df = remove_missing_values(df)

    df = convert_numeric_columns(df)

    df = convert_datetime_columns(df)

    df = sort_by_time(df)

    df = reset_dataframe_index(df)

    return df


# ==========================================================
# Dataset Specific Cleaning
# ==========================================================

def clean_ohlcv(df):

    return clean_dataframe(df)


def clean_orderbook(df):

    return clean_dataframe(df)


def clean_trades(df):

    return clean_dataframe(df)


def clean_funding_rate(df):

    return clean_dataframe(df)


def clean_open_interest(df):

    return clean_dataframe(df)


def clean_option_chain(df):

    return clean_dataframe(df)


def clean_greeks(df):

    return clean_dataframe(df)


def clean_implied_volatility(df):

    return clean_dataframe(df)


def clean_news(df):

    return clean_dataframe(df)


def clean_onchain(df):

    return clean_dataframe(df)


def clean_whales(df):

    return clean_dataframe(df)


def clean_fear_greed(df):

    return clean_dataframe(df)