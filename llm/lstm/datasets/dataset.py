from llm.lstm.preprocessing.pipeline import run_pipeline


# ==========================================================
# Dataset Loader
# ==========================================================

class LSTMDataset:

    def __init__(
        self,
        sequence_length=60,
        target_column="close",
        normalize_method="standard",
    ):

        self.sequence_length = sequence_length
        self.target_column = target_column
        self.normalize_method = normalize_method

        self.dataset = None

    # ======================================================
    # Load Dataset
    # ======================================================

    def load(self):

        self.dataset = run_pipeline(
            sequence_length=self.sequence_length,
            target_column=self.target_column,
            normalize_method=self.normalize_method,
        )

        return self.dataset

    # ======================================================
    # Get Training Data
    # ======================================================

    def train(self):

        return (
            self.dataset["X_train"],
            self.dataset["y_train"],
        )

    # ======================================================
    # Get Validation Data
    # ======================================================

    def validation(self):

        return (
            self.dataset["X_validation"],
            self.dataset["y_validation"],
        )

    # ======================================================
    # Get Test Data
    # ======================================================

    def test(self):

        return (
            self.dataset["X_test"],
            self.dataset["y_test"],
        )

    # ======================================================
    # Feature Names
    # ======================================================

    def feature_names(self):

        return self.dataset["features"]

    # ======================================================
    # Number of Features
    # ======================================================

    def feature_count(self):

        return len(self.dataset["features"])

    # ======================================================
    # Sequence Length
    # ======================================================

    def sequence_length_value(self):

        return self.dataset["X_train"].shape[1]

    # ======================================================
    # Input Shape
    # ======================================================

    def input_shape(self):

        return self.dataset["X_train"].shape[1:]

    # ======================================================
    # Summary
    # ======================================================

    def summary(self):

        print("=" * 70)
        print("LSTM DATASET SUMMARY")
        print("=" * 70)

        print()

        print("Training")

        print(self.dataset["X_train"].shape)

        print(self.dataset["y_train"].shape)

        print()

        print("Validation")

        print(self.dataset["X_validation"].shape)

        print(self.dataset["y_validation"].shape)

        print()

        print("Testing")

        print(self.dataset["X_test"].shape)

        print(self.dataset["y_test"].shape)

        print()

        print("Feature Count")

        print(self.feature_count())

        print()

        print("Input Shape")

        print(self.input_shape())