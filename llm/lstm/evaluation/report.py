import json
from pathlib import Path


class EvaluationReport:

    def __init__(self, save_dir="storage/reports"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =====================================================
    # Save JSON Report
    # =====================================================

    def save(
        self,
        metrics: dict,
        filename="evaluation_report.json",
    ):
        path = self.save_dir / filename

        with open(path, "w") as f:
            json.dump(
                metrics,
                f,
                indent=4,
            )

        print()
        print("Saved:", path)

        return path

    # =====================================================
    # Load Report
    # =====================================================

    def load(
        self,
        filename="evaluation_report.json",
    ):
        path = self.save_dir / filename

        with open(path, "r") as f:
            return json.load(f)

    # =====================================================
    # Print Report
    # =====================================================

    @staticmethod
    def print(metrics):

        print()

        print("=" * 60)
        print("EVALUATION REPORT")
        print("=" * 60)

        for key, value in metrics.items():
            print(f"{key:20}: {value}")

        print("=" * 60)