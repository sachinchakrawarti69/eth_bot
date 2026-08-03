from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)


class ClassificationMetrics:
    """
    Classification evaluation metrics.
    """

    @staticmethod
    def accuracy(y_true, y_pred):
        return accuracy_score(
            y_true,
            y_pred,
        )

    @staticmethod
    def precision(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    ):
        return precision_score(
            y_true,
            y_pred,
            average=average,
            zero_division=zero_division,
        )

    @staticmethod
    def recall(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    ):
        return recall_score(
            y_true,
            y_pred,
            average=average,
            zero_division=zero_division,
        )

    @staticmethod
    def f1(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    ):
        return f1_score(
            y_true,
            y_pred,
            average=average,
            zero_division=zero_division,
        )

    @staticmethod
    def report(
        y_true,
        y_pred,
    ):
        return classification_report(
            y_true,
            y_pred,
            zero_division=0,
        )