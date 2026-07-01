from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.evaluation.evaluator import evaluate_multilabel_predictions
from src.features.build_fusion_dataset import run as build_fusion_dataset
from src.training.train_ablation_mlp import train as train_ablation_mlp
from src.training.train_fair_concat_fusion import train as train_fair_concat
from src.utils.io import ensure_dir, safe_to_csv, write_markdown


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
MAIN_EXTERNAL_LABELS = {
    "cpsc2018": ["NORM", "CD"],
    "chapman": ["MI", "CD", "HYP"],
}
STAGE_DIR = Path("results/stage14l")


def _write_yaml(path: str | Path, data: dict) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _prediction_arrays(pred: pd.DataFrame, labels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    y_true = pred[[f"{label}_true" for label in labels]].to_numpy(dtype=int)
    y_prob = pred[[f"{label}_prob" for label in labels]].to_numpy(dtype=float)
    return y_true, y_prob


def _macro_metric(y_true: np.ndarray, y_prob: np.ndarray, labels: list[str], metric: str) -> float:
    frame = evaluate_multilabel_predictions(y_true, y_prob, label_names=labels)
    macro = frame[frame["label"].eq("macro")].iloc[0]
    return float(macro[metric])


def _paired_bootstrap(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_model: str,
    right_model: str,
    labels: list[str] = LABELS,
    n_bootstrap: int = 1000,
    seed: int = 2026,
) -> pd.DataFrame:
    merged = left.merge(right, on=["ecg_id", "split"], suffixes=("_left", "_right"))
    y_true = merged[[f"{label}_true_left" for label in labels]].to_numpy(dtype=int)
    left_prob = merged[[f"{label}_prob_left" for label in labels]].to_numpy(dtype=float)
    right_prob = merged[[f"{label}_prob_right" for label in labels]].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    rows = []
    for metric in ["auroc", "average_precision", "f1"]:
        left_value = _macro_metric(y_true, left_prob, labels, metric)
        right_value = _macro_metric(y_true, right_prob, labels, metric)
        deltas = []
        for _ in range(n_bootstrap):
            idx = rng.integers(0, len(merged), size=len(merged))
            deltas.append(_macro_metric(y_true[idx], right_prob[idx], labels, metric) - _macro_metric(y_true[idx], left_prob[idx], labels, metric))
        rows.append(
            {
                "comparison": f"{right_model}_minus_{left_model}",
                "split": "test",
                "metric": metric,
                "left_model": left_model,
                "right_model": right_model,
                "left_value": left_value,
                "right_value": right_value,
                "delta_right_minus_left": right_value - left_value,
                "paired_bootstrap_ci_lower": float(np.nanpercentile(deltas, 2.5)),
                "paired_bootstrap_ci_upper": float(np.nanpercentile(deltas, 97.5)),
                "ci_contains_zero": bool(float(np.nanpercentile(deltas, 2.5)) <= 0 <= float(np.nanpercentile(deltas, 97.5))),
                "n_bootstrap": n_bootstrap,
            }
        )
    return pd.DataFrame(rows)


def build_manifest() -> list[str]:
    comparison = pd.read_csv("tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv")
    structured = pd.read_csv("data/processed/ptbxl_structured_features.csv")
    allclose = comparison[comparison["allclose_atol_1e_6"].astype(bool)].copy()
    feature_names = allclose["feature"].tolist()
    rows = []
    for _, row in allclose.iterrows():
        feature = str(row["feature"])
        missing_fraction = float(structured[feature].isna().mean()) if feature in structured.columns else math.nan
        rows.append(
            {
                "feature_name": feature,
                "source_stage": "Stage 14H PTB-XL internal ECGdeli direct recomputation audit",
                "allclose_status": "allclose_atol_1e-6_rtol_1e-6",
                "missingness": missing_fraction,
                "numeric_stability_summary": (
                    f"n_pairs={int(row['n_pairs'])}; "
                    f"mean_abs_error={float(row['mean_abs_error']):.6g}; "
                    f"median_abs_error={float(row['median_abs_error']):.6g}; "
                    f"max_abs_error={float(row['max_abs_error']):.6g}"
                ),
                "official_nonmissing": int(row["official_nonmissing"]),
                "recomputed_nonmissing": int(row["recomputed_nonmissing"]),
                "mean_abs_error": float(row["mean_abs_error"]),
                "max_abs_error": float(row["max_abs_error"]),
            }
        )
    manifest = pd.DataFrame(rows)
    safe_to_csv(manifest, "tables/stage14l_feature_manifest.csv")
    return feature_names


def build_reduced_internal_inputs(feature_names: list[str]) -> None:
    ensure_dir("data/processed/stage14l")
    structured = pd.read_csv("data/processed/ptbxl_structured_features.csv")
    reduced = structured[["ecg_id", *feature_names]].copy()
    safe_to_csv(reduced, "data/processed/stage14l/ptbxl_structured_features_concordant_subset.csv")
    Path("data/processed/stage14l/structured_feature_names_concordant_subset.txt").write_text("\n".join(feature_names) + "\n", encoding="utf-8")
    _write_yaml(
        "configs/stage14l_fair_fusion_dataset.yaml",
        {
            "data": {
                "signal_train_csv": "data/processed/signal_embeddings_strong_train.csv",
                "signal_val_csv": "data/processed/signal_embeddings_strong_val.csv",
                "signal_test_csv": "data/processed/signal_embeddings_strong_test.csv",
                "structured_features_csv": "data/processed/stage14l/ptbxl_structured_features_concordant_subset.csv",
                "multimodal_index_csv": "data/processed/ptbxl_multimodal_index.csv",
                "structured_feature_names_txt": "data/processed/stage14l/structured_feature_names_concordant_subset.txt",
                "labels": LABELS,
            },
            "preprocessing": {"imputation_strategy": "median", "standardize_signal": True, "standardize_structured": True},
            "output": {
                "train_csv": "data/processed/stage14l/fair_fusion_train.csv",
                "val_csv": "data/processed/stage14l/fair_fusion_val.csv",
                "test_csv": "data/processed/stage14l/fair_fusion_test.csv",
                "manifest_csv": "data/processed/stage14l/fair_fusion_feature_manifest.csv",
                "preprocessing_artifact": "results/stage14l/preprocessing_artifact.pkl",
                "report_md": "results/stage14l/fair_fusion_dataset_report.md",
            },
        },
    )
    build_fusion_dataset("configs/stage14l_fair_fusion_dataset.yaml")


def _model_config(model_name: str, modality: str | None, hidden_dims: list[int], out_dir: str, n_structured: int) -> dict:
    model: dict[str, object] = {"name": model_name, "hidden_dims": hidden_dims, "dropout": 0.3, "num_classes": 5}
    if modality is not None:
        model["modality"] = modality
    if modality == "structured" or modality is None:
        model["expected_structured_dim"] = n_structured
    return {
        "data": {
            "train_csv": "data/processed/stage14l/fair_fusion_train.csv",
            "val_csv": "data/processed/stage14l/fair_fusion_val.csv",
            "test_csv": "data/processed/stage14l/fair_fusion_test.csv",
            "labels": LABELS,
        },
        "model": model,
        "training": {
            "epochs": 60,
            "batch_size": 128,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "patience": 8,
            "min_delta": 0.0005,
            "seed": 2026,
            "device": "auto",
        },
        "output": {
            "val_predictions_csv": f"{out_dir}/{model_name}_val_predictions.csv",
            "test_predictions_csv": f"{out_dir}/{model_name}_test_predictions.csv",
            "history_csv": f"{out_dir}/{model_name}_training_history.csv",
            "metrics_val_csv": f"{out_dir}/{model_name}_metrics_val.csv",
            "metrics_test_csv": f"{out_dir}/{model_name}_metrics_test.csv",
            "thresholds_json": f"{out_dir}/{model_name}_thresholds.json",
            "run_summary_json": f"{out_dir}/{model_name}_run_summary.json",
            "checkpoint_path": f"{out_dir}/{model_name}_best.pt",
            "table_csv": f"{out_dir}/table_{model_name}_results.csv",
            "threshold_comparison_csv": f"{out_dir}/table_{model_name}_threshold_comparison.csv",
        },
    }


def train_internal_models(n_structured: int) -> pd.DataFrame:
    ensure_dir(STAGE_DIR)
    configs = [
        ("configs/stage14l_signal_embedding_mlp.yaml", _model_config("stage14l_signal_embedding_mlp", "signal_embedding", [512, 256], "results/stage14l/signal_embedding", n_structured), train_ablation_mlp),
        ("configs/stage14l_structured_mlp.yaml", _model_config("stage14l_structured_mlp", "structured", [256, 128], "results/stage14l/structured", n_structured), train_ablation_mlp),
        ("configs/stage14l_fair_concat_mlp.yaml", _model_config("stage14l_fair_concat_mlp", None, [512, 256], "results/stage14l/fair_concat", n_structured), train_fair_concat),
    ]
    frames = []
    for path, cfg, trainer in configs:
        _write_yaml(path, cfg)
        table_path = Path(cfg["output"]["table_csv"])
        test_pred_path = Path(cfg["output"]["test_predictions_csv"])
        if not (table_path.exists() and test_pred_path.exists()):
            trainer(path)
        table = pd.read_csv(cfg["output"]["table_csv"])
        frames.append(table)
    internal = pd.concat(frames, ignore_index=True)
    internal.insert(0, "stage", "stage14l_concordant_subset")
    internal["structured_feature_dim"] = n_structured
    safe_to_csv(internal, "tables/stage14l_internal_results.csv")
    return internal


def build_internal_bootstrap() -> pd.DataFrame:
    pred_paths = {
        "stage14l_signal_embedding_mlp": "results/stage14l/signal_embedding/stage14l_signal_embedding_mlp_test_predictions.csv",
        "stage14l_structured_mlp": "results/stage14l/structured/stage14l_structured_mlp_test_predictions.csv",
        "stage14l_fair_concat_mlp": "results/stage14l/fair_concat/stage14l_fair_concat_mlp_test_predictions.csv",
    }
    fair = pd.read_csv(pred_paths["stage14l_fair_concat_mlp"])
    signal = pd.read_csv(pred_paths["stage14l_signal_embedding_mlp"])
    structured = pd.read_csv(pred_paths["stage14l_structured_mlp"])
    boot = pd.concat(
        [
            _paired_bootstrap(signal, fair, "stage14l_signal_embedding_mlp", "stage14l_fair_concat_mlp"),
            _paired_bootstrap(structured, fair, "stage14l_structured_mlp", "stage14l_fair_concat_mlp", seed=2027),
        ],
        ignore_index=True,
    )
    safe_to_csv(boot, "tables/stage14l_internal_paired_bootstrap_ci.csv")
    return boot


def external_diagnostics(feature_names: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    signal_metrics = pd.read_csv("tables/table_external_signal_results.csv")
    rows = []
    per_class_rows = []
    for dataset, labels in MAIN_EXTERNAL_LABELS.items():
        index = pd.read_csv(f"data/processed/external/{dataset}_index.csv")
        signal_pred = pd.read_csv(f"results/external/{dataset}_signal_predictions.csv")
        candidate_path = Path(f"data/processed/external/{dataset}_ecgdeli_direct_candidate_features.csv")
        candidates = pd.read_csv(candidate_path) if candidate_path.exists() else pd.DataFrame()
        if not candidates.empty and "record_id" in candidates.columns:
            reduced_available = [feature for feature in feature_names if feature in candidates.columns]
            reduced = candidates[["record_id", *reduced_available]].copy()
            missing_fraction = float(reduced[reduced_available].isna().mean().mean()) if reduced_available else 1.0
            candidate_records = int(len(reduced))
            signal_join_records = int(signal_pred.merge(reduced[["record_id"]], on="record_id", how="inner").shape[0])
        else:
            reduced_available = []
            missing_fraction = 1.0
            candidate_records = 0
            signal_join_records = 0
        expected_records = int(len(signal_pred))
        coverage = float(signal_join_records / expected_records) if expected_records else 0.0
        quality_ok = bool(len(reduced_available) == len(feature_names) and missing_fraction <= 0.2 and coverage >= 0.8)
        signal_macro = signal_metrics[(signal_metrics["dataset"].eq(dataset)) & (signal_metrics["label"].eq("macro"))].iloc[0]
        rows.append(
            {
                "dataset": dataset,
                "model": "stage14l_fair_concat_mlp",
                "evaluation_status": "not_evaluated_external_coverage_no_go" if not quality_ok else "ready_for_external_evaluation",
                "n_signal_prediction_records": expected_records,
                "n_candidate_structured_records": candidate_records,
                "n_joinable_signal_structured_records": signal_join_records,
                "record_coverage_fraction": coverage,
                "n_required_reduced_features": len(feature_names),
                "n_available_reduced_features": len(reduced_available),
                "structured_missing_fraction": missing_fraction,
                "macro_auroc": math.nan,
                "macro_average_precision": math.nan,
                "macro_f1": math.nan,
                "signal_only_macro_auroc": float(signal_macro["auroc"]),
                "signal_only_macro_average_precision": float(signal_macro["average_precision"]),
                "signal_only_macro_f1": float(signal_macro["f1"]),
                "blocking_issue": "" if quality_ok else "external_reduced_structured_feature_coverage_too_low_or_embeddings_missing",
            }
        )
        for label in labels:
            sig = signal_metrics[(signal_metrics["dataset"].eq(dataset)) & (signal_metrics["label"].eq(label))].iloc[0]
            prevalence = float(index[f"mapped_{label}"].mean()) if f"mapped_{label}" in index.columns else math.nan
            per_class_rows.append(
                {
                    "dataset": dataset,
                    "model": "stage14l_fair_concat_mlp",
                    "label": label,
                    "evaluation_status": "not_evaluated_external_coverage_no_go" if not quality_ok else "ready_for_external_evaluation",
                    "auroc": math.nan,
                    "average_precision": math.nan,
                    "f1": math.nan,
                    "prevalence": prevalence,
                    "positive_count": int(index[f"mapped_{label}"].sum()) if f"mapped_{label}" in index.columns else 0,
                    "signal_only_auroc": float(sig["auroc"]),
                    "signal_only_average_precision": float(sig["average_precision"]),
                    "signal_only_f1": float(sig["f1"]),
                    "n_joinable_signal_structured_records": signal_join_records,
                    "record_coverage_fraction": coverage,
                }
            )
    external = pd.DataFrame(rows)
    diagnostics = pd.DataFrame(per_class_rows)
    safe_to_csv(external, "tables/stage14l_external_results.csv")
    safe_to_csv(diagnostics, "tables/stage14l_per_class_diagnostics.csv")
    return external, diagnostics


def _internal_gain_decision(internal: pd.DataFrame, boot: pd.DataFrame) -> tuple[bool, str]:
    test = internal[(internal["split"].eq("test")) & (internal["threshold_mode"].eq("default_0.5"))].set_index("model")
    fair = test.loc["stage14l_fair_concat_mlp"]
    signal = test.loc["stage14l_signal_embedding_mlp"]
    structured = test.loc["stage14l_structured_mlp"]
    auroc_gain = min(float(fair["auroc"] - signal["auroc"]), float(fair["auroc"] - structured["auroc"]))
    ap_gain = min(float(fair["average_precision"] - signal["average_precision"]), float(fair["average_precision"] - structured["average_precision"]))
    fair_boot = boot[boot["metric"].eq("auroc")]
    ci_support = bool((fair_boot["paired_bootstrap_ci_lower"] > 0).all())
    ok = bool(auroc_gain > 0.002 and ap_gain > 0.002 and ci_support)
    reason = f"min_auroc_gain={auroc_gain:.6f}; min_ap_gain={ap_gain:.6f}; auroc_ci_lower_all_positive={ci_support}"
    return ok, reason


def write_docs(feature_names: list[str], internal: pd.DataFrame, boot: pd.DataFrame, external: pd.DataFrame) -> None:
    spec = "\n".join(
        [
            "# Stage 14L Concordant-Subset External Multimodal Validation Spec",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Scope",
            "",
            "Stage 14L uses only structured features that passed Stage 14H PTB-XL internal ECGdeli recomputation allclose checks. It intentionally does not attempt full PTB-XL+ 531-column reproduction.",
            "",
            "## Reduced Structured Schema",
            "",
            f"- feature count: {len(feature_names)}",
            "- source: Stage 14H allclose direct ECGdeli candidate features",
            "- excluded: all non-allclose direct candidates and all unresolved QT_IntCorr/P_Morph/ST_Elev/HA features",
            "",
            "## Internal Protocol",
            "",
            "- train/val/test split: unchanged PTB-XL official split",
            "- label scope: NORM, MI, STTC, CD, HYP",
            "- comparators: signal-embedding MLP, reduced structured MLP, reduced fair concat MLP",
            "- model selection and threshold tuning: validation only",
            "- test set: frozen final evaluation only",
            "",
            "## External Protocol",
            "",
            "External multimodal evaluation is allowed only if reduced structured features and signal embeddings are available for a sufficient fraction of CPSC2018 and Chapman-Shaoxing records. Candidate/prototype features are not treated as exact PTB-XL+ reproduction.",
            "",
            "## Forbidden Claims",
            "",
            "- exact PTB-XL+ reproduction",
            "- full 531-column external multimodal validation",
            "- gated fusion superiority",
        ]
    )
    write_markdown("docs/STAGE14L_CONCORDANT_SUBSET_SPEC.md", spec + "\n")

    internal_ok, internal_reason = _internal_gain_decision(internal, boot)
    external_ok = bool(external["evaluation_status"].eq("ready_for_external_evaluation").all())
    decision = "GO" if internal_ok and external_ok else "NO-GO"
    decision_text = "\n".join(
        [
            "# Stage 14L GO/NO-GO Decision",
            "",
            "Date: " + date.today().isoformat(),
            "",
            f"Decision: **{decision}**",
            "",
            "## Internal Reduced-Schema Result",
            "",
            internal[(internal["split"].eq("test")) & (internal["threshold_mode"].eq("default_0.5"))][["model", "auroc", "average_precision", "f1"]].to_markdown(index=False),
            "",
            "## Internal Paired Bootstrap",
            "",
            boot.to_markdown(index=False),
            "",
            "## External Quality Gate",
            "",
            external.to_markdown(index=False),
            "",
            "## Rationale",
            "",
            f"- internal gain gate: {internal_ok} ({internal_reason})",
            f"- external generation quality gate: {external_ok}",
            "",
            "## Interpretation",
            "",
            "If NO-GO, manuscript framing should remain internal multimodal evaluation plus signal-only external validation. Stage 14L does not authorize external multimodal claims.",
            "",
            "## Forbidden Claims",
            "",
            "- exact PTB-XL+ reproduction",
            "- full 531-column external multimodal validation",
            "- gated fusion superiority",
        ]
    )
    write_markdown("docs/STAGE14L_GO_NO_GO_DECISION.md", decision_text + "\n")


def main() -> None:
    ensure_dir("docs")
    ensure_dir("tables")
    ensure_dir(STAGE_DIR)
    feature_names = build_manifest()
    build_reduced_internal_inputs(feature_names)
    internal = train_internal_models(len(feature_names))
    boot = build_internal_bootstrap()
    external, _diagnostics = external_diagnostics(feature_names)
    write_docs(feature_names, internal, boot, external)
    metadata = {
        "stage": "Stage 14L",
        "feature_count": len(feature_names),
        "decision_doc": "docs/STAGE14L_GO_NO_GO_DECISION.md",
        "forbidden_claims": [
            "exact PTB-XL+ reproduction",
            "full 531-column external multimodal validation",
            "gated fusion superiority",
        ],
    }
    (STAGE_DIR / "stage14l_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Stage 14L concordant-subset validation completed.")


if __name__ == "__main__":
    main()
