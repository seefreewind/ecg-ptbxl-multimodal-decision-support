from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score

from src.evaluation.calibration import arrays_from_prediction_frame, multilabel_calibration_metrics
from src.evaluation.collect_model_predictions import LABELS


MAIN_COMPARISON_MODELS = ["strong_signal_only", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]


def _safe_metric(fn, *args) -> float:
    try:
        return float(fn(*args))
    except ValueError:
        return math.nan


def _load_temperature_status(model_name: str, calibration_dir: Path) -> str:
    matches = list(calibration_dir.glob("temperature_params_*.json"))
    for path in matches:
        payload = json.loads(path.read_text())
        if payload.get("model_name") == model_name:
            return str(payload.get("status", "unknown"))
    return "missing"


def _apply_temperature_if_available(predictions: pd.DataFrame, model_name: str, calibration_dir: Path) -> pd.DataFrame:
    for path in calibration_dir.glob("temperature_params_*.json"):
        payload = json.loads(path.read_text())
        if payload.get("model_name") != model_name:
            continue
        if payload.get("status") != "fitted":
            return predictions.copy()
        temperatures = payload.get("temperatures") or []
        if all(f"logit_{label}" in predictions.columns for label in LABELS):
            logit_cols = [f"logit_{label}" for label in LABELS]
            prob_cols = [f"prob_{label}" for label in LABELS]
        else:
            logit_cols = [f"{label}_logit" for label in LABELS]
            prob_cols = [f"{label}_prob" for label in LABELS]
        if len(temperatures) != len(LABELS) or any(col not in predictions.columns for col in logit_cols):
            return predictions.copy()
        out = predictions.copy()
        logits = predictions[logit_cols].to_numpy(dtype=np.float32)
        temps = np.asarray(temperatures, dtype=np.float32)
        scaled = 1.0 / (1.0 + np.exp(-(logits / temps)))
        for idx, label in enumerate(LABELS):
            out[prob_cols[idx]] = scaled[:, idx]
        return out
    return predictions.copy()


def _calibration_rows(manifest: pd.DataFrame, calibration_dir: Path, n_bins: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_rows = []
    scaled_rows = []
    for row in manifest.to_dict("records"):
        if not bool(row["probability_columns_available"]):
            continue
        model_name = str(row["model_name"])
        temperature_status = _load_temperature_status(model_name, calibration_dir)
        for split, path_col in [("val", "val_prediction_path"), ("test", "test_prediction_path")]:
            predictions = pd.read_csv(row[path_col])
            y_true, y_prob = arrays_from_prediction_frame(predictions, LABELS)
            raw = {
                "model_name": model_name,
                "split": split,
                "calibration_mode": "raw",
                "temperature_status": temperature_status,
                "n_bins": n_bins,
            }
            raw.update(multilabel_calibration_metrics(y_true, y_prob, LABELS, n_bins=n_bins))
            raw_rows.append(raw)

            scaled_predictions = _apply_temperature_if_available(predictions, model_name, calibration_dir)
            y_true_scaled, y_prob_scaled = arrays_from_prediction_frame(scaled_predictions, LABELS)
            scaled = {
                "model_name": model_name,
                "split": split,
                "calibration_mode": "temperature_scaled",
                "temperature_status": temperature_status,
                "n_bins": n_bins,
            }
            scaled.update(multilabel_calibration_metrics(y_true_scaled, y_prob_scaled, LABELS, n_bins=n_bins))
            scaled_rows.append(scaled)
    return pd.DataFrame(raw_rows), pd.DataFrame(scaled_rows)


def _delta_table(raw: pd.DataFrame, scaled: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [col for col in raw.columns if col.startswith(("macro_", "classwise_"))]
    keys = ["model_name", "split", "n_bins"]
    merged = raw[keys + metric_cols].merge(scaled[keys + metric_cols], on=keys, suffixes=("_raw", "_temperature_scaled"))
    rows = []
    for _, row in merged.iterrows():
        out = {key: row[key] for key in keys}
        out["calibration_mode"] = "temperature_scaled_minus_raw"
        for metric in metric_cols:
            out[metric] = float(row[f"{metric}_temperature_scaled"] - row[f"{metric}_raw"])
        rows.append(out)
    return pd.DataFrame(rows)


def _discrimination_summary(predictions: pd.DataFrame) -> dict[str, float]:
    y_true, y_prob = arrays_from_prediction_frame(predictions, LABELS)
    y_pred = (y_prob >= 0.5).astype(int)
    return {
        "AUROC": float(np.nanmean([_safe_metric(roc_auc_score, y_true[:, idx], y_prob[:, idx]) for idx in range(len(LABELS))])),
        "AP": float(np.nanmean([_safe_metric(average_precision_score, y_true[:, idx], y_prob[:, idx]) for idx in range(len(LABELS))])),
        "F1": float(np.nanmean([_safe_metric(lambda a, b: f1_score(a, b, zero_division=0), y_true[:, idx], y_pred[:, idx]) for idx in range(len(LABELS))])),
    }


def _gated_vs_concat_table(manifest: pd.DataFrame, raw: pd.DataFrame, scaled: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    lookup = {row["model_name"]: row for row in manifest.to_dict("records")}
    fair_pred = pd.read_csv(lookup["fair_concat_mlp"]["test_prediction_path"])
    gated_pred = pd.read_csv(lookup["gated_fusion_mlp"]["test_prediction_path"])
    fair_disc = _discrimination_summary(fair_pred)
    gated_disc = _discrimination_summary(gated_pred)
    rows = []
    for metric in ["AUROC", "AP", "F1"]:
        delta = gated_disc[metric] - fair_disc[metric]
        rows.append(
            {
                "metric": metric,
                "split": "test",
                "calibration_mode": "raw_predictions",
                "fair_concat_value": fair_disc[metric],
                "gated_fusion_value": gated_disc[metric],
                "delta_gated_minus_fair_concat": delta,
                "better_model": "gated_fusion_mlp" if delta > 0 else "fair_concat_mlp",
                "interpretation": "discrimination delta is small and should be interpreted with paired bootstrap uncertainty",
            }
        )
    for source, mode in [(raw, "raw"), (scaled, "temperature_scaled")]:
        test = source[source["split"].eq("test")].set_index("model_name")
        for metric in ["macro_brier", "macro_ece"]:
            fair_value = float(test.loc["fair_concat_mlp", metric])
            gated_value = float(test.loc["gated_fusion_mlp", metric])
            delta = gated_value - fair_value
            rows.append(
                {
                    "metric": metric,
                    "split": "test",
                    "calibration_mode": mode,
                    "fair_concat_value": fair_value,
                    "gated_fusion_value": gated_value,
                    "delta_gated_minus_fair_concat": delta,
                    "better_model": "gated_fusion_mlp" if delta < 0 else "fair_concat_mlp",
                    "interpretation": "lower is better for calibration metrics; temperature scaling may be skipped if logits are unavailable",
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(output_path, index=False)
    return out


def _paired_bootstrap_gated_vs_concat(
    manifest: pd.DataFrame,
    output_path: Path,
    n_bootstrap: int = 1000,
    seed: int = 2026,
) -> pd.DataFrame:
    lookup = {row["model_name"]: row for row in manifest.to_dict("records")}
    fair = pd.read_csv(lookup["fair_concat_mlp"]["test_prediction_path"])
    gated = pd.read_csv(lookup["gated_fusion_mlp"]["test_prediction_path"])
    merged = fair.merge(gated, on="ecg_id", suffixes=("_fair", "_gated"))
    true_cols_fair = [f"y_true_{label}_fair" for label in LABELS] if all(f"y_true_{label}_fair" in merged.columns for label in LABELS) else [f"{label}_true_fair" for label in LABELS]
    prob_cols_fair = [f"prob_{label}_fair" for label in LABELS] if all(f"prob_{label}_fair" in merged.columns for label in LABELS) else [f"{label}_prob_fair" for label in LABELS]
    prob_cols_gated = [f"prob_{label}_gated" for label in LABELS] if all(f"prob_{label}_gated" in merged.columns for label in LABELS) else [f"{label}_prob_gated" for label in LABELS]
    y_true = merged[true_cols_fair].to_numpy(dtype=np.int32)
    fair_prob = merged[prob_cols_fair].to_numpy(dtype=np.float32)
    gated_prob = merged[prob_cols_gated].to_numpy(dtype=np.float32)
    rng = np.random.default_rng(seed)
    indices = np.arange(len(merged))

    def macro_metric(prob: np.ndarray, metric: str, sample: np.ndarray | None = None) -> float:
        yt = y_true if sample is None else y_true[sample]
        yp = prob if sample is None else prob[sample]
        values = []
        for idx in range(len(LABELS)):
            if metric == "AUROC":
                values.append(_safe_metric(roc_auc_score, yt[:, idx], yp[:, idx]))
            elif metric == "AP":
                values.append(_safe_metric(average_precision_score, yt[:, idx], yp[:, idx]))
            else:
                pred = (yp[:, idx] >= 0.5).astype(int)
                values.append(_safe_metric(lambda a, b: f1_score(a, b, zero_division=0), yt[:, idx], pred))
        return float(np.nanmean(values))

    rows = []
    for metric in ["AUROC", "AP", "F1"]:
        fair_est = macro_metric(fair_prob, metric)
        gated_est = macro_metric(gated_prob, metric)
        diffs = []
        for _ in range(n_bootstrap):
            sample = rng.choice(indices, size=len(indices), replace=True)
            diffs.append(macro_metric(gated_prob, metric, sample) - macro_metric(fair_prob, metric, sample))
        lo, hi = np.nanpercentile(diffs, [2.5, 97.5])
        rows.append(
            {
                "comparison": "gated_fusion_mlp_minus_fair_concat_mlp",
                "split": "test",
                "metric": metric,
                "fair_concat_value": fair_est,
                "gated_fusion_value": gated_est,
                "delta_gated_minus_fair_concat": gated_est - fair_est,
                "paired_bootstrap_ci_lower": float(lo),
                "paired_bootstrap_ci_upper": float(hi),
                "ci_contains_zero": bool(lo <= 0 <= hi),
                "n_bootstrap": n_bootstrap,
                "seed": seed,
                "interpretation": "no statistically clear gated advantage" if lo <= 0 <= hi else "paired CI excludes zero",
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(output_path, index=False)
    return out


def evaluate_calibration() -> None:
    calibration_dir = Path("results/calibration")
    calibration_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    manifest = pd.read_csv(calibration_dir / "prediction_manifest.csv")
    raw, scaled = _calibration_rows(manifest, calibration_dir, n_bins=10)
    raw.to_csv(calibration_dir / "calibration_metrics_raw.csv", index=False)
    scaled.to_csv(calibration_dir / "calibration_metrics_temperature_scaled.csv", index=False)
    raw.to_csv("tables/table_calibration_raw.csv", index=False)
    scaled.to_csv("tables/table_calibration_temperature_scaled.csv", index=False)
    delta = _delta_table(raw, scaled)
    delta.to_csv("tables/table_calibration_delta.csv", index=False)

    sensitivity_frames = []
    for bins in [15, 20]:
        raw_s, scaled_s = _calibration_rows(manifest, calibration_dir, n_bins=bins)
        sensitivity_frames.extend([raw_s, scaled_s])
    pd.concat(sensitivity_frames, ignore_index=True).to_csv(calibration_dir / "calibration_metrics_bins_sensitivity.csv", index=False)

    _gated_vs_concat_table(manifest, raw, scaled, Path("tables/table_gated_vs_fair_concat_calibration.csv"))
    paired = _paired_bootstrap_gated_vs_concat(manifest, calibration_dir / "gated_vs_fair_concat_paired_bootstrap.csv")
    paired.to_csv("tables/table_gated_vs_fair_concat_paired_bootstrap.csv", index=False)
    print("Wrote calibration metrics, delta tables, gated-vs-concat tables, and paired bootstrap results.")


if __name__ == "__main__":
    evaluate_calibration()
