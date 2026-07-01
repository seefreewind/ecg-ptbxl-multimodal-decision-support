#!/usr/bin/env python3
"""Stage 27 robustness audit for structured-feature reproducibility claims.

This stage addresses two reviewer-facing questions without changing the locked
external evidence boundary:

1. How sensitive is the 138-feature concordant subset to the numerical
   allclose tolerance?
2. Does the reduced-schema multimodal collapse look specific to the
   concordance-selected feature set, or is it also seen when 138 features are
   selected randomly or by internal attribution importance?

The analysis is internal only. It does not create any external multimodal claim.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.stage14l_concordant_subset import _paired_bootstrap
from src.features.build_fusion_dataset import run as build_fusion_dataset
from src.training.train_ablation_mlp import train as train_ablation_mlp
from src.training.train_fair_concat_fusion import train as train_fair_concat
from src.utils.io import ensure_dir, safe_to_csv


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
ROOT = Path(".")
STAGE_DIR = Path("results/stage27_robustness")
DATA_DIR = Path("data/processed/stage27")


def _write_yaml(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _structured_names() -> list[str]:
    return [
        line.strip()
        for line in Path("data/processed/structured_feature_names.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def tolerance_sensitivity() -> pd.DataFrame:
    official = pd.read_csv("data/processed/ptbxl_structured_features.csv")
    recomputed = pd.read_csv("data/processed/ptbxl_ecgdeli_direct_recomputed_sample.csv")
    comparison = pd.read_csv("tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv")
    merged = recomputed[["ecg_id"]].merge(official, on="ecg_id", how="inner", suffixes=("_recomputed", "_official"))
    rec = recomputed.set_index("ecg_id")
    off = official.set_index("ecg_id")
    features = [f for f in comparison["feature"].astype(str).tolist() if f in rec.columns and f in off.columns]
    tolerances = [1e-6, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 5.0, 10.0]
    rows = []
    for tol in tolerances:
        passing: list[str] = []
        for feature in features:
            paired = pd.concat([off.loc[rec.index, feature].rename("official"), rec[feature].rename("recomputed")], axis=1).dropna()
            if paired.empty:
                continue
            if np.allclose(paired["official"].to_numpy(float), paired["recomputed"].to_numpy(float), atol=tol, rtol=tol, equal_nan=True):
                passing.append(feature)
        rows.append(
            {
                "atol": tol,
                "rtol": tol,
                "n_features_passing": len(passing),
                "fraction_of_direct_candidates": len(passing) / len(features) if features else np.nan,
                "n_direct_candidates_evaluated": len(features),
                "feature_list": ";".join(passing),
                "note": "Exact per-feature np.allclose on the available PTB-XL recomputation audit sample; sensitivity is limited by n=3 audit records.",
            }
        )
    out = pd.DataFrame(rows)
    safe_to_csv(out, "tables/stage27_tolerance_sensitivity.csv")
    return out


def _select_feature_sets(n_features: int = 138) -> dict[str, list[str]]:
    names = _structured_names()
    rng = np.random.default_rng(2026)
    random_features = sorted(rng.choice(names, size=n_features, replace=False).tolist())
    imp = pd.read_csv("tables/table_top_structured_features_global.csv")
    importance_features = []
    for feature in imp.sort_values("rank")["feature"].astype(str):
        if feature in names and feature not in importance_features:
            importance_features.append(feature)
        if len(importance_features) == n_features:
            break
    if len(importance_features) < n_features:
        missing = [name for name in names if name not in importance_features]
        importance_features.extend(missing[: n_features - len(importance_features)])
    concordance = pd.read_csv("tables/stage14l_feature_manifest.csv")["feature_name"].astype(str).tolist()
    return {
        "concordance_138": concordance[:n_features],
        "random_138_seed2026": random_features,
        "importance_138_internal_xai": importance_features[:n_features],
    }


def _build_subset_dataset(subset_name: str, features: list[str]) -> None:
    subset_dir = DATA_DIR / subset_name
    ensure_dir(subset_dir)
    structured = pd.read_csv("data/processed/ptbxl_structured_features.csv")
    missing = [feature for feature in features if feature not in structured.columns]
    if missing:
        raise ValueError(f"{subset_name} has missing structured features: {missing[:5]}")
    reduced = structured[["ecg_id", *features]].copy()
    safe_to_csv(reduced, subset_dir / "ptbxl_structured_features_subset.csv")
    (subset_dir / "structured_feature_names_subset.txt").write_text("\n".join(features) + "\n", encoding="utf-8")
    config = {
        "data": {
            "signal_train_csv": "data/processed/signal_embeddings_strong_train.csv",
            "signal_val_csv": "data/processed/signal_embeddings_strong_val.csv",
            "signal_test_csv": "data/processed/signal_embeddings_strong_test.csv",
            "structured_features_csv": str(subset_dir / "ptbxl_structured_features_subset.csv"),
            "multimodal_index_csv": "data/processed/ptbxl_multimodal_index.csv",
            "structured_feature_names_txt": str(subset_dir / "structured_feature_names_subset.txt"),
            "labels": LABELS,
        },
        "preprocessing": {"imputation_strategy": "median", "standardize_signal": True, "standardize_structured": True},
        "output": {
            "train_csv": str(subset_dir / "fair_fusion_train.csv"),
            "val_csv": str(subset_dir / "fair_fusion_val.csv"),
            "test_csv": str(subset_dir / "fair_fusion_test.csv"),
            "manifest_csv": str(subset_dir / "fair_fusion_feature_manifest.csv"),
            "preprocessing_artifact": str(STAGE_DIR / subset_name / "preprocessing_artifact.pkl"),
            "report_md": str(STAGE_DIR / subset_name / "fair_fusion_dataset_report.md"),
        },
    }
    cfg_path = Path("configs") / f"stage27_{subset_name}_fair_fusion_dataset.yaml"
    _write_yaml(cfg_path, config)
    build_fusion_dataset(cfg_path)


def _model_config(subset_name: str, model_name: str, modality: str | None, hidden_dims: list[int]) -> dict:
    subset_dir = DATA_DIR / subset_name
    out_dir = STAGE_DIR / subset_name / model_name
    model: dict[str, object] = {"name": model_name, "hidden_dims": hidden_dims, "dropout": 0.3, "num_classes": 5}
    if modality is not None:
        model["modality"] = modality
    model["expected_structured_dim"] = 138
    return {
        "data": {
            "train_csv": str(subset_dir / "fair_fusion_train.csv"),
            "val_csv": str(subset_dir / "fair_fusion_val.csv"),
            "test_csv": str(subset_dir / "fair_fusion_test.csv"),
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
            "val_predictions_csv": str(out_dir / f"{model_name}_val_predictions.csv"),
            "test_predictions_csv": str(out_dir / f"{model_name}_test_predictions.csv"),
            "history_csv": str(out_dir / f"{model_name}_training_history.csv"),
            "metrics_val_csv": str(out_dir / f"{model_name}_metrics_val.csv"),
            "metrics_test_csv": str(out_dir / f"{model_name}_metrics_test.csv"),
            "thresholds_json": str(out_dir / f"{model_name}_thresholds.json"),
            "run_summary_json": str(out_dir / f"{model_name}_run_summary.json"),
            "checkpoint_path": str(out_dir / f"{model_name}_best.pt"),
            "table_csv": str(out_dir / f"table_{model_name}_results.csv"),
            "threshold_comparison_csv": str(out_dir / f"table_{model_name}_threshold_comparison.csv"),
        },
    }


def _train_subset_models(subset_name: str) -> tuple[pd.DataFrame, dict[str, str]]:
    configs = [
        (
            f"stage27_{subset_name}_structured_mlp",
            _model_config(subset_name, f"stage27_{subset_name}_structured_mlp", "structured", [256, 128]),
            train_ablation_mlp,
        ),
        (
            f"stage27_{subset_name}_matched_concat_mlp",
            _model_config(subset_name, f"stage27_{subset_name}_matched_concat_mlp", None, [512, 256]),
            train_fair_concat,
        ),
    ]
    frames = []
    pred_paths = {}
    for model_name, cfg, trainer in configs:
        cfg_path = Path("configs") / f"{model_name}.yaml"
        _write_yaml(cfg_path, cfg)
        table_path = Path(cfg["output"]["table_csv"])
        pred_path = Path(cfg["output"]["test_predictions_csv"])
        if not (table_path.exists() and pred_path.exists()):
            trainer(cfg_path)
        table = pd.read_csv(table_path)
        table.insert(0, "subset_name", subset_name)
        table.insert(1, "feature_selection", subset_name)
        frames.append(table)
        pred_paths[model_name] = str(pred_path)
    return pd.concat(frames, ignore_index=True), pred_paths


def feature_count_controls() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_sets = _select_feature_sets()
    manifest_rows = []
    result_frames = []
    bootstrap_frames = []
    signal_pred = pd.read_csv("results/stage14l/signal_embedding/stage14l_signal_embedding_mlp_test_predictions.csv")
    for subset_name, features in feature_sets.items():
        for rank, feature in enumerate(features, start=1):
            manifest_rows.append({"subset_name": subset_name, "rank": rank, "feature_name": feature})
        if subset_name == "concordance_138":
            concordance_results = pd.read_csv("tables/stage14l_internal_results.csv")
            concordance_results = concordance_results[concordance_results["model"].isin(["stage14l_structured_mlp", "stage14l_fair_concat_mlp"])].copy()
            concordance_results["subset_name"] = subset_name
            concordance_results["feature_selection"] = subset_name
            concordance_results["model"] = concordance_results["model"].replace(
                {
                    "stage14l_structured_mlp": "stage27_concordance_138_structured_mlp",
                    "stage14l_fair_concat_mlp": "stage27_concordance_138_matched_concat_mlp",
                }
            )
            result_frames.append(concordance_results)
            fair_pred = pd.read_csv("results/stage14l/fair_concat/stage14l_fair_concat_mlp_test_predictions.csv")
            struct_pred = pd.read_csv("results/stage14l/structured/stage14l_structured_mlp_test_predictions.csv")
            bootstrap_frames.append(_paired_bootstrap(signal_pred, fair_pred, "stage14l_signal_embedding_mlp", "stage27_concordance_138_matched_concat_mlp", seed=2026, n_bootstrap=300).assign(subset_name=subset_name))
            bootstrap_frames.append(_paired_bootstrap(struct_pred, fair_pred, "stage27_concordance_138_structured_mlp", "stage27_concordance_138_matched_concat_mlp", seed=2027, n_bootstrap=300).assign(subset_name=subset_name))
            continue
        _build_subset_dataset(subset_name, features)
        results, pred_paths = _train_subset_models(subset_name)
        result_frames.append(results)
        fair_model = f"stage27_{subset_name}_matched_concat_mlp"
        struct_model = f"stage27_{subset_name}_structured_mlp"
        fair_pred = pd.read_csv(pred_paths[fair_model])
        struct_pred = pd.read_csv(pred_paths[struct_model])
        bootstrap_frames.append(_paired_bootstrap(signal_pred, fair_pred, "stage14l_signal_embedding_mlp", fair_model, seed=2026, n_bootstrap=300).assign(subset_name=subset_name))
        bootstrap_frames.append(_paired_bootstrap(struct_pred, fair_pred, struct_model, fair_model, seed=2027, n_bootstrap=300).assign(subset_name=subset_name))
    manifest = pd.DataFrame(manifest_rows)
    results = pd.concat(result_frames, ignore_index=True)
    boot = pd.concat(bootstrap_frames, ignore_index=True)
    safe_to_csv(manifest, "tables/stage27_feature_count_control_manifest.csv")
    safe_to_csv(results, "tables/stage27_feature_count_control_results.csv")
    safe_to_csv(boot, "tables/stage27_feature_count_control_bootstrap_ci.csv")
    return manifest, results, boot


def external_join_failure_audit() -> pd.DataFrame:
    rows = []
    for dataset in ["cpsc2018", "chapman"]:
        signal = pd.read_csv(f"results/external/{dataset}_signal_predictions.csv")
        candidate = pd.read_csv(f"data/processed/external/{dataset}_ecgdeli_direct_candidate_features.csv")
        required = pd.read_csv("tables/stage14l_feature_manifest.csv")["feature_name"].astype(str).tolist()
        available = [feature for feature in required if feature in candidate.columns]
        joined = signal[["record_id"]].merge(candidate[["record_id"]].drop_duplicates(), on="record_id", how="inner")
        rows.append(
            {
                "dataset": dataset,
                "n_signal_prediction_records": len(signal),
                "n_candidate_feature_records": len(candidate),
                "n_joinable_records": len(joined),
                "join_coverage": len(joined) / len(signal) if len(signal) else np.nan,
                "n_required_reduced_features": len(required),
                "n_available_reduced_features": len(available),
                "n_missing_reduced_features": len(required) - len(available),
                "feature_schema_coverage": len(available) / len(required) if required else np.nan,
                "dominant_failure_mode": "candidate_feature_record_count_and_external_signal_embedding_coverage_too_low",
                "interpretation": "Engineering feasibility audit only; not evidence that external PTB-XL+ reconstruction is impossible in principle.",
            }
        )
    out = pd.DataFrame(rows)
    safe_to_csv(out, "tables/stage27_external_join_failure_audit.csv")
    return out


def write_summary(tol: pd.DataFrame, results: pd.DataFrame, boot: pd.DataFrame, external: pd.DataFrame) -> None:
    default = results[(results["split"].eq("test")) & (results["threshold_mode"].eq("default_0.5"))].copy()
    md = [
        "# Stage 27 Robustness Audit",
        "",
        "## Scope",
        "",
        "This stage is an internal robustness and engineering-feasibility audit. It does not add external multimodal validation and does not revise the locked signal-only external evidence boundary. Paired bootstrap intervals in this screening audit use 300 record-level resamples to keep the analysis lightweight; confirmatory manuscript CIs can be rerun with more resamples if needed.",
        "",
        "## Tolerance Sensitivity",
        "",
        tol[["atol", "rtol", "n_features_passing", "fraction_of_direct_candidates", "n_direct_candidates_evaluated"]].to_markdown(index=False),
        "",
        "Interpretation: the tolerance check is exact for the available PTB-XL recomputation audit sample, but the sample contains only three recomputed records. It should be used as a sensitivity audit, not as a definitive feature-recipe validation.",
        "",
        "## Feature-Count Controls",
        "",
        default[["subset_name", "model", "auroc", "average_precision", "f1", "positive_count"]].to_markdown(index=False),
        "",
        "## Paired Bootstrap",
        "",
        boot[["subset_name", "comparison", "metric", "left_value", "right_value", "delta_right_minus_left", "paired_bootstrap_ci_lower", "paired_bootstrap_ci_upper", "ci_contains_zero"]].to_markdown(index=False),
        "",
        "## External Join Failure Audit",
        "",
        external.to_markdown(index=False),
        "",
        "## Manuscript Implication",
        "",
        "If random-138 or importance-138 controls recover internal multimodal gain, the manuscript should say that the concordant subset loses information and therefore cannot support external multimodal validation; it should not imply that every 138-feature subset fails. If no 138-feature control recovers gain, the current dimensionality-loss explanation becomes less likely, but the result remains internal only.",
    ]
    Path("docs/STAGE27_ROBUSTNESS_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dir(STAGE_DIR)
    tol = tolerance_sensitivity()
    _manifest, results, boot = feature_count_controls()
    external = external_join_failure_audit()
    write_summary(tol, results, boot, external)
    summary = {
        "stage": "stage27_robustness_audit",
        "outputs": [
            "tables/stage27_tolerance_sensitivity.csv",
            "tables/stage27_feature_count_control_manifest.csv",
            "tables/stage27_feature_count_control_results.csv",
            "tables/stage27_feature_count_control_bootstrap_ci.csv",
            "tables/stage27_external_join_failure_audit.csv",
            "docs/STAGE27_ROBUSTNESS_AUDIT.md",
        ],
        "external_multimodal_claim_added": False,
    }
    Path(STAGE_DIR / "stage27_metadata.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Stage 27 robustness audit complete.")
    for output in summary["outputs"]:
        print(output)


if __name__ == "__main__":
    main()
