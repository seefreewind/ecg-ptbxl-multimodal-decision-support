from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.evaluation.collect_model_predictions import LABELS
from src.evaluation.evaluate_calibration import _apply_temperature_if_available
from src.evaluation.reliability import confidence_histogram_source, reliability_curve_source


MAIN_MODELS = ["strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]


def _plot_single_reliability(source: pd.DataFrame, title: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    for label in LABELS:
        label_data = source[(source["label"] == label) & (source["count"] > 0)]
        ax.plot(label_data["confidence"], label_data["accuracy"], marker="o", linewidth=1.4, label=label)
    ax.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title(title)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def _plot_histogram(source: pd.DataFrame, title: str, output_path: Path) -> None:
    summary = source.groupby(["bin_left", "bin_right"], as_index=False)["count"].sum()
    centers = (summary["bin_left"] + summary["bin_right"]) / 2
    widths = summary["bin_right"] - summary["bin_left"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(centers, summary["count"], width=widths * 0.9, color="#4C78A8")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Count across labels")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def _plot_comparison(source: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model in MAIN_MODELS:
        data = source[
            (source["model_name"] == model)
            & (source["split"] == "test")
            & (source["calibration_mode"] == "raw")
            & (source["count"] > 0)
        ]
        averaged = data.groupby("bin", as_index=False)[["confidence", "accuracy"]].mean()
        ax.plot(averaged["confidence"], averaged["accuracy"], marker="o", linewidth=1.6, label=model)
    ax.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title("Frozen test reliability comparison")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def generate_reliability_outputs() -> None:
    calibration_dir = Path("results/calibration")
    figure_dir = Path("figures/calibration")
    figure_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(calibration_dir / "prediction_manifest.csv")
    reliability_frames = []
    histogram_frames = []
    for row in manifest.to_dict("records"):
        if not bool(row["probability_columns_available"]):
            continue
        model_name = str(row["model_name"])
        for split, path_col in [("val", "val_prediction_path"), ("test", "test_prediction_path")]:
            predictions = pd.read_csv(row[path_col])
            raw_source = reliability_curve_source(predictions, LABELS, model_name, split, "raw")
            raw_hist = confidence_histogram_source(predictions, LABELS, model_name, split, "raw")
            reliability_frames.append(raw_source)
            histogram_frames.append(raw_hist)

            scaled_predictions = _apply_temperature_if_available(predictions, model_name, calibration_dir)
            scaled_source = reliability_curve_source(scaled_predictions, LABELS, model_name, split, "temperature_scaled")
            scaled_hist = confidence_histogram_source(scaled_predictions, LABELS, model_name, split, "temperature_scaled")
            reliability_frames.append(scaled_source)
            histogram_frames.append(scaled_hist)

            if split == "test":
                _plot_single_reliability(raw_source, f"{model_name} raw reliability (test)", figure_dir / f"reliability_raw_{model_name}.png")
                _plot_single_reliability(
                    scaled_source,
                    f"{model_name} temperature-scaled reliability (test)",
                    figure_dir / f"reliability_temperature_scaled_{model_name}.png",
                )
                _plot_histogram(raw_hist, f"{model_name} confidence histogram (test)", figure_dir / f"confidence_histogram_{model_name}.png")

    reliability = pd.concat(reliability_frames, ignore_index=True)
    histograms = pd.concat(histogram_frames, ignore_index=True)
    reliability.to_csv(calibration_dir / "reliability_curve_source_data.csv", index=False)
    histograms.to_csv(calibration_dir / "confidence_histogram_source_data.csv", index=False)
    _plot_comparison(reliability, figure_dir / "reliability_comparison_main_models.png")
    print("Wrote reliability source data and calibration figures.")


if __name__ == "__main__":
    generate_reliability_outputs()
