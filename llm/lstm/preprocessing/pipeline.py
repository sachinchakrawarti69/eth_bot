from llm.lstm.preprocessing.load_data import load_ohlcv
from llm.lstm.preprocessing.clean_data import clean_ohlcv
from llm.lstm.preprocessing.technical_indicators import add_all_indicators
from llm.lstm.preprocessing.feature_engineering import add_all_features
from llm.lstm.preprocessing.normalize import normalize
from llm.lstm.preprocessing.create_sequences import create_sequences
from llm.lstm.preprocessing.split_dataset import split_dataset


# ==========================================================
# Complete Preprocessing Pipeline
# ==========================================================

def run_pipeline(
    sequence_length=60,
    target_column="close",
    normalize_method="standard",
):

    print("=" * 70)
    print("LSTM PREPROCESSING PIPELINE")
    print("=" * 70)

    # ------------------------------------------------------
    # Load
    # ------------------------------------------------------

    print("\n[1/7] Loading OHLCV...")

    df = load_ohlcv()

    print("Shape :", df.shape)

    # ------------------------------------------------------
    # Clean
    # ------------------------------------------------------

    print("\n[2/7] Cleaning Data...")

    df = clean_ohlcv(df)

    print("Shape :", df.shape)

    # ------------------------------------------------------
    # Technical Indicators
    # ------------------------------------------------------

    print("\n[3/7] Technical Indicators...")

    df = add_all_indicators(df)

    print("Shape :", df.shape)

    # ------------------------------------------------------
    # Feature Engineering
    # ------------------------------------------------------

    print("\n[4/7] Feature Engineering...")

    df = add_all_features(df)

    print("Shape :", df.shape)

    # ------------------------------------------------------
    # Remove NaN
    # ------------------------------------------------------

    print("\nRemoving NaN values...")

    df = df.dropna().reset_index(drop=True)

    print("Shape :", df.shape)

    # ------------------------------------------------------
    # Normalize
    # ------------------------------------------------------

    print("\n[5/7] Normalization...")

    df, scaler = normalize(
        df,
        method=normalize_method,
    )

    print("Shape :", df.shape)

    # ------------------------------------------------------
    # Create Sequences
    # ------------------------------------------------------

    print("\n[6/7] Creating Sequences...")

    X, y = create_sequences(
        df,
        sequence_length=sequence_length,
        target_column=target_column,
    )

    print("X :", X.shape)
    print("y :", y.shape)

    # ------------------------------------------------------
    # Split Dataset
    # ------------------------------------------------------

    print("\n[7/7] Splitting Dataset...")

    (
        X_train,
        X_validation,
        X_test,
        y_train,
        y_validation,
        y_test,
    ) = split_dataset(X, y)

    print()

    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    return {

        "X_train": X_train,
        "X_validation": X_validation,
        "X_test": X_test,

        "y_train": y_train,
        "y_validation": y_validation,
        "y_test": y_test,

        "scaler": scaler,

        "features": df.columns.tolist(),

        "dataframe": df,

    }


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    dataset = run_pipeline()

    print(dataset["X_train"].shape)