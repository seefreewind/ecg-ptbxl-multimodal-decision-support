from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score

from src.figures.ecg_feature_grouping import group_ecg_feature


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
MAIN_MODELS = ["strong_signal_only", "signal_embedding_mlp", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]
MODEL_META = {
    "strong_signal_only": ("signal", "waveform", "none"),
    "signal_embedding_mlp": ("signal embedding", "signal embedding", "none"),
    "structured_mlp": ("structured", "PTB-XL+ structured", "none"),
    "fair_concat_mlp": ("multimodal", "signal embedding + structured", "fair concat"),
    "gated_fusion_mlp": ("multimodal", "signal embedding + structured", "gated fusion"),
    "late_probability_concat": ("supplementary", "late probabilities", "late probability concat"),
}


def _out_dirs() -> tuple[Path, Path, Path]:
    source = Path("figures/source_data")
    supp = source / "supplementary"
    main = Path("figures/main")
    for path in [source, supp, main]:
        path.mkdir(parents=True, exist_ok=True)
    return source, supp, main


def _write(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def _metric_file(model: str) -> Path:
    return {
        "strong_signal_only": Path("results/internal/signal_strong/signal_strong_metrics_test.csv"),
        "signal_embedding_mlp": Path("results/internal/ablation_signal_embedding/signal_embedding_mlp_metrics_test.csv"),
        "structured_mlp": Path("results/internal/ablation_structured/structured_mlp_metrics_test.csv"),
        "fair_concat_mlp": Path("results/internal/fair_concat/fair_concat_metrics_test.csv"),
        "gated_fusion_mlp": Path("results/internal/gated_fusion/gated_fusion_metrics_test.csv"),
    }[model]


def _prediction_file(model: str) -> Path:
    manifest = pd.read_csv("results/calibration/prediction_manifest.csv")
    row = manifest[manifest["model_name"].eq(model)].iloc[0]
    return Path(row["test_prediction_path"])


def _prob_cols(df: pd.DataFrame) -> list[str]:
    return [f"prob_{label}" for label in LABELS] if f"prob_{LABELS[0]}" in df.columns else [f"{label}_prob" for label in LABELS]


def _true_cols(df: pd.DataFrame) -> list[str]:
    return [f"y_true_{label}" for label in LABELS] if f"y_true_{LABELS[0]}" in df.columns else [f"{label}_true" for label in LABELS]


def _safe_auc(y, p):
    try:
        return float(roc_auc_score(y, p))
    except ValueError:
        return np.nan


def _safe_ap(y, p):
    try:
        return float(average_precision_score(y, p))
    except ValueError:
        return np.nan


def fig1(source: Path) -> list[dict[str, str]]:
    nodes = pd.DataFrame(
        [
            ("waveform", "PTB-XL waveform", "data", "100 Hz 12-lead ECG waveform records", "data resource"),
            ("structured", "PTB-XL+ structured ECG features", "data", "Leakage-safe ecgdeli structured ECG features", "data resource"),
            ("leakage", "leakage-safe feature selection", "processing", "Remove diagnostic/statement/target-like columns", "preprocessing"),
            ("signal", "strong signal encoder", "model", "Signal-only ResNet baseline and embeddings", "modeling"),
            ("structured_mlp", "structured MLP", "model", "Structured-only baseline", "modeling"),
            ("fair_concat", "fair MLP-concat", "model", "Fair multimodal concat using shared representation interface", "modeling"),
            ("gated", "gated fusion", "model", "Gated multimodal model; not claimed statistically superior to concat", "modeling"),
            ("calibration", "calibration", "decision_support", "Validation-only temperature scaling and reliability analysis", "trustworthy AI"),
            ("uncertainty", "uncertainty triage", "decision_support", "Validation cutoffs and frozen-test risk-coverage", "trustworthy AI"),
            ("xai", "XAI", "decision_support", "Post-hoc dual-modality attribution", "trustworthy AI"),
            ("dca", "DCA", "pending", "Decision-curve analysis placeholder", "pending"),
            ("external", "external validation", "pending", "Cross-dataset validation placeholder", "pending"),
            ("referral", "clinician referral", "workflow", "Low-confidence ECGs routed to clinician review", "decision support"),
        ],
        columns=["node_id", "node_label", "node_type", "description", "stage"],
    )
    edges = pd.DataFrame(
        [
            ("waveform", "signal", "input", "Waveform branch"),
            ("structured", "leakage", "processing", "Leakage-safe structured preprocessing"),
            ("leakage", "structured_mlp", "input", "Structured-only model"),
            ("signal", "fair_concat", "embedding", "Signal embedding branch"),
            ("leakage", "fair_concat", "features", "Structured branch"),
            ("signal", "gated", "embedding", "Signal embedding branch"),
            ("leakage", "gated", "features", "Structured branch"),
            ("fair_concat", "calibration", "evaluation", "Temperature scaling and reliability"),
            ("gated", "calibration", "evaluation", "Temperature scaling and reliability"),
            ("calibration", "uncertainty", "workflow", "Calibrated probabilities for triage"),
            ("uncertainty", "referral", "workflow", "Low-confidence referral"),
            ("uncertainty", "xai", "audit", "Explain retained and referred cases"),
            ("xai", "dca", "pending", "Decision-curve analysis planned"),
            ("dca", "external", "pending", "External validation planned"),
        ],
        columns=["source", "target", "edge_type", "description"],
    )
    _write(nodes, source / "fig1_framework_nodes.csv")
    _write(edges, source / "fig1_framework_edges.csv")
    mmd = ["flowchart LR"]
    for row in nodes.to_dict("records"):
        mmd.append(f'  {row["node_id"]}["{row["node_label"]}"]')
    for row in edges.to_dict("records"):
        mmd.append(f'  {row["source"]} -->|{row["edge_type"]}| {row["target"]}')
    Path("figures/fig1_framework_draft.mmd").write_text("\n".join(mmd) + "\n")
    return [
        manifest_row("Figure 1", "A-D", "figures/source_data/fig1_framework_nodes.csv", "Framework nodes", "manual stage design", "scripts/12_build_figure_source_data.sh", "ready", ""),
        manifest_row("Figure 1", "A-D", "figures/source_data/fig1_framework_edges.csv", "Framework edges", "manual stage design", "scripts/12_build_figure_source_data.sh", "ready", ""),
    ]


def fig2(source: Path) -> list[dict[str, str]]:
    rows = []
    per_rows = []
    ci = pd.read_csv("tables/table_calibration_bootstrap_ci.csv")
    for model in MAIN_MODELS:
        df = pd.read_csv(_metric_file(model))
        macro = df[df["label"].eq("macro")].iloc[0]
        group, modality, fusion = MODEL_META[model]
        for metric, col in [("AUROC", "auroc"), ("average_precision", "average_precision"), ("F1", "f1")]:
            rows.append(base_perf_row(model, group, modality, fusion, "test", metric, float(macro[col]), np.nan, np.nan, True))
        cal = pd.read_csv("tables/table_calibration_temperature_scaled.csv")
        calrow = cal[cal["model_name"].eq(model) & cal["split"].eq("test")].iloc[0]
        for metric, col in [("Brier", "macro_brier"), ("ECE", "macro_ece")]:
            cirow = ci[(ci["model_name"].eq(model)) & (ci["calibration_mode"].eq("temperature_scaled")) & (ci["metric"].eq("macro_" + metric.lower()))]
            lo = float(cirow["ci_lower"].iloc[0]) if len(cirow) else np.nan
            hi = float(cirow["ci_upper"].iloc[0]) if len(cirow) else np.nan
            rows.append(base_perf_row(model, group, modality, fusion, "test", metric, float(calrow[col]), lo, hi, True))
        for _, r in df[~df["label"].eq("macro")].iterrows():
            for metric, col in [("AUROC", "auroc"), ("average_precision", "average_precision"), ("F1", "f1")]:
                per_rows.append({"model_name": model, "label": r["label"], "metric": metric, "estimate": float(r[col]), "positive_count": int(r["positive_count"]), "split": "test", "is_main_model": True})
    late = pd.read_csv("results/internal/concat_fusion_metrics.csv")
    if "label" in late.columns:
        macro = late[late["label"].eq("macro")].iloc[0]
        for metric, col in [("AUROC", "auroc"), ("average_precision", "average_precision"), ("F1", "f1")]:
            rows.append(base_perf_row("late_probability_concat", *MODEL_META["late_probability_concat"], "test", metric, float(macro[col]), np.nan, np.nan, False, "supplementary only"))
    perf = pd.DataFrame(rows)
    perf.to_csv(source / "fig2_model_performance_long.csv", index=False)
    pd.DataFrame(per_rows).to_csv(source / "fig2_per_class_dotplot.csv", index=False)
    pd.read_csv("tables/table_gated_vs_fair_concat_paired_bootstrap.csv").to_csv(source / "fig2_paired_bootstrap.csv", index=False)
    return [
        manifest_row("Figure 2", "A/D", "figures/source_data/fig2_model_performance_long.csv", "Main model performance long table", "Stage 8/9/9B metrics", "scripts/12_build_figure_source_data.sh", "ready", "Late concat marked supplementary"),
        manifest_row("Figure 2", "B", "figures/source_data/fig2_per_class_dotplot.csv", "Per-class model metrics", "model metric files", "scripts/12_build_figure_source_data.sh", "ready", ""),
        manifest_row("Figure 2", "C", "figures/source_data/fig2_paired_bootstrap.csv", "Gated vs fair concat paired bootstrap", "Stage 9 paired bootstrap", "scripts/12_build_figure_source_data.sh", "ready", "CI contains zero; no gated superiority claim"),
    ]


def base_perf_row(model, group, modality, fusion, split, metric, estimate, lo, hi, main, notes=""):
    return {
        "model_name": model,
        "model_group": group,
        "input_modality": modality,
        "fusion_type": fusion,
        "split": split,
        "metric": metric,
        "estimate": estimate,
        "ci_lower": lo,
        "ci_upper": hi,
        "seed_mean": np.nan,
        "seed_sd": np.nan,
        "is_main_model": bool(main),
        "is_fair_comparator": model in {"fair_concat_mlp", "gated_fusion_mlp", "strong_signal_only"},
        "notes": notes,
    }


def fig3(source: Path) -> list[dict[str, str]]:
    perf = pd.read_csv(source / "fig2_model_performance_long.csv")
    rows = []
    for _, r in perf[perf["model_name"].isin(MAIN_MODELS)].iterrows():
        rows.append({
            "model_name": r["model_name"],
            "modality": MODEL_META[r["model_name"]][1],
            "input_features": MODEL_META[r["model_name"]][1],
            "fusion_mechanism": MODEL_META[r["model_name"]][2],
            "split": r["split"],
            "metric": r["metric"],
            "estimate": r["estimate"],
            "ci_lower": r["ci_lower"],
            "ci_upper": r["ci_upper"],
            "notes": "Fair-interface ablation; multimodal gain attributed to complementarity, not gated superiority.",
        })
    _write(pd.DataFrame(rows), source / "fig3_ablation_long.csv")
    sim_rows = []
    preds = {}
    errors = {}
    uncertainties = {}
    for model in MAIN_MODELS:
        df = pd.read_csv(_prediction_file(model))
        prob = df[_prob_cols(df)].to_numpy(float)
        true = df[_true_cols(df)].to_numpy(int)
        preds[model] = prob.mean(axis=1)
        errors[model] = (np.any((prob >= 0.5).astype(int) != true, axis=1)).astype(float)
    u = pd.read_csv("results/uncertainty/uncertainty_scores_test.csv")
    for model in MAIN_MODELS:
        row = u[u["model_name"].eq(model) & u["probability_mode"].eq("temperature_scaled")]
        uncertainties[model] = row.sort_values("ecg_id")["entropy_macro"].to_numpy(float)
    for i in MAIN_MODELS:
        for j in MAIN_MODELS:
            for kind, values in [("prediction correlation", preds), ("error overlap", errors), ("uncertainty correlation", uncertainties)]:
                if kind == "error overlap":
                    a, b = values[i] > 0, values[j] > 0
                    val = float((a & b).sum() / max(1, (a | b).sum()))
                else:
                    val = float(np.corrcoef(values[i], values[j])[0, 1])
                sim_rows.append({"model_i": i, "model_j": j, "similarity_type": kind, "value": val, "split": "test", "probability_mode": "temperature_scaled"})
    _write(pd.DataFrame(sim_rows), source / "fig3_prediction_similarity_matrix.csv")
    return [
        manifest_row("Figure 3", "A-D", "figures/source_data/fig3_ablation_long.csv", "Ablation and complementarity metrics", "Stage 8/9B outputs", "scripts/12_build_figure_source_data.sh", "ready", ""),
        manifest_row("Figure 3", "E", "figures/source_data/fig3_prediction_similarity_matrix.csv", "Prediction/error/uncertainty similarity", "Stage 9B predictions and Stage 10 uncertainty", "scripts/12_build_figure_source_data.sh", "ready", ""),
    ]


def fig4(source: Path) -> list[dict[str, str]]:
    raw = pd.read_csv("tables/table_calibration_raw.csv")
    scaled = pd.read_csv("tables/table_calibration_temperature_scaled.csv")
    ci = pd.read_csv("tables/table_calibration_bootstrap_ci.csv")
    rows = []
    for df in [raw, scaled]:
        for _, r in df.iterrows():
            for metric, col in [("macro_brier", "macro_brier"), ("macro_ece", "macro_ece"), ("macro_mce", "macro_mce")]:
                cirow = ci[(ci["model_name"].eq(r["model_name"])) & (ci["calibration_mode"].eq(r["calibration_mode"])) & (ci["metric"].eq(metric))]
                rows.append({
                    "model_name": r["model_name"],
                    "split": r["split"],
                    "calibration_mode": r["calibration_mode"],
                    "metric": metric,
                    "estimate": float(r[col]),
                    "ci_lower": float(cirow["ci_lower"].iloc[0]) if len(cirow) else np.nan,
                    "ci_upper": float(cirow["ci_upper"].iloc[0]) if len(cirow) else np.nan,
                    "delta_vs_raw": np.nan,
                    "notes": "Stage 9B supersedes Stage 9 skipped-temperature interpretation.",
                })
    out = pd.DataFrame(rows)
    for idx, r in out.iterrows():
        if r["calibration_mode"] == "temperature_scaled":
            base = out[(out["model_name"].eq(r["model_name"])) & (out["split"].eq(r["split"])) & (out["metric"].eq(r["metric"])) & (out["calibration_mode"].eq("raw"))]
            if len(base):
                out.loc[idx, "delta_vs_raw"] = r["estimate"] - float(base["estimate"].iloc[0])
    _write(out, source / "fig4_calibration_long.csv")
    pd.read_csv("results/calibration/reliability_curve_source_data.csv").to_csv(source / "fig4_reliability_curve.csv", index=False)
    pd.read_csv("results/calibration/confidence_histogram_source_data.csv").to_csv(source / "fig4_confidence_histogram.csv", index=False)
    return [
        manifest_row("Figure 4", "A/B", "figures/source_data/fig4_calibration_long.csv", "Calibration metrics raw vs temperature scaled", "Stage 9B calibration", "scripts/12_build_figure_source_data.sh", "ready", ""),
        manifest_row("Figure 4", "C", "figures/source_data/fig4_reliability_curve.csv", "Reliability curve bins", "Stage 9B reliability", "scripts/12_build_figure_source_data.sh", "ready", ""),
        manifest_row("Figure 4", "D", "figures/source_data/fig4_confidence_histogram.csv", "Confidence histogram bins", "Stage 9B reliability", "scripts/12_build_figure_source_data.sh", "ready", ""),
    ]


def fig5(source: Path) -> list[dict[str, str]]:
    risk = pd.read_csv("tables/table_decision_support_triage_summary.csv")
    ci = pd.read_csv("tables/table_uncertainty_triage_bootstrap_ci.csv")
    rows = []
    for _, r in risk.iterrows():
        for metric in ["retained_macro_auroc", "retained_macro_f1", "retained_brier", "retained_ece"]:
            cirow = ci[(ci["model_name"].eq(r["model_name"])) & np.isclose(ci["coverage"], r["coverage"]) & (ci["metric"].eq(metric))]
            payload = {**r.to_dict(), "metric": metric, "metric_estimate": r[metric], "ci_lower": float(cirow["ci_lower"].iloc[0]) if len(cirow) else np.nan, "ci_upper": float(cirow["ci_upper"].iloc[0]) if len(cirow) else np.nan, "split": "test", "cutoff_source": "validation"}
            payload["referral_fraction"] = float(r.get("referral_fraction", r.get("referred_fraction", np.nan)))
            rows.append(payload)
    _write(pd.DataFrame(rows), source / "fig5_uncertainty_risk_coverage.csv")
    pd.read_csv("tables/table_referred_subset_characteristics.csv").to_csv(source / "fig5_referred_subset_characteristics.csv", index=False)
    return [
        manifest_row("Figure 5", "A-C", "figures/source_data/fig5_uncertainty_risk_coverage.csv", "Risk-coverage metrics with validation cutoffs", "Stage 10 uncertainty", "scripts/12_build_figure_source_data.sh", "ready", "Frozen test evaluation"),
        manifest_row("Figure 5", "D", "figures/source_data/fig5_referred_subset_characteristics.csv", "Referred subset characteristics", "Stage 10 uncertainty", "scripts/12_build_figure_source_data.sh", "ready", ""),
    ]


def fig6_fig7(source: Path) -> list[dict[str, str]]:
    manifest = []
    unified_path = Path("results/xai/unified_case_explanations.csv")
    if unified_path.exists():
        unified = pd.read_csv(unified_path)
        unified["figure_panel"] = np.where(unified["retained_or_referred"].eq("retained"), "A", "B")
        unified["notes"] = "post-hoc XAI case source data"
        _write(unified, source / "fig6_xai_case_source_data.csv")
        feat = pd.read_csv("tables/table_top_structured_features_by_label.csv").rename(columns={"feature": "feature_name", "attribution_mean_abs": "mean_abs_attribution"})
        feat["feature_group"] = feat["feature_name"].map(group_ecg_feature)
        _write(feat[["model_name", "label", "feature_name", "feature_group", "mean_abs_attribution", "rank"]], source / "fig6_structured_feature_group_attribution.csv")
        signal = pd.read_csv("results/xai/signal_case_attribution_summary.csv")
        signal["heatmap_file"] = signal["ecg_id"].map(lambda x: f"figures/xai/case_{int(x)}_signal_heatmap.png")
        _write(signal, source / "fig6_signal_heatmap_index.csv")
        manifest.extend([
            manifest_row("Figure 6", "A-D", "figures/source_data/fig6_xai_case_source_data.csv", "Unified XAI case source data", "Stage 11 XAI", "scripts/12_build_figure_source_data.sh", "ready", "post-hoc analysis"),
            manifest_row("Figure 6", "C", "figures/source_data/fig6_structured_feature_group_attribution.csv", "Grouped structured attributions", "Stage 11 XAI", "scripts/12_build_figure_source_data.sh", "ready", "post-hoc analysis"),
            manifest_row("Figure 6", "D", "figures/source_data/fig6_signal_heatmap_index.csv", "Signal heatmap file index", "Stage 11 XAI", "scripts/12_build_figure_source_data.sh", "ready", "post-hoc analysis"),
        ])
    gates_path = Path("results/xai/gated_gate_weights_test.csv")
    if gates_path.exists() and unified_path.exists():
        gates = pd.read_csv(gates_path)
        unified = pd.read_csv(unified_path)
        out = gates.merge(unified[["ecg_id", "true_labels", "predicted_labels", "correct_or_incorrect"]] if "correct_or_incorrect" in unified.columns else pd.read_csv("results/xai/xai_case_selection.csv")[["ecg_id", "true_labels", "predicted_labels", "correct_or_incorrect"]], on="ecg_id", how="left")
        out["model_name"] = "gated_fusion_mlp"
        out["split"] = "test"
        out["gate_signal"] = out["gate_signal_mean"]
        out["gate_structured"] = out["gate_structured_mean"]
        out["retained_or_referred"] = out["retained_or_referred_80"]
        out["uncertainty_score"] = out["entropy_macro"]
        out["label_group"] = out["true_labels"].fillna("not_selected")
        _write(out[["ecg_id", "model_name", "split", "gate_signal", "gate_structured", "retained_or_referred", "correct_or_incorrect", "uncertainty_score", "true_labels", "predicted_labels", "label_group"]], source / "fig7_gate_weight_modality_interaction.csv")
        manifest.append(manifest_row("Figure 7", "A-D", "figures/source_data/fig7_gate_weight_modality_interaction.csv", "Gate weight modality interaction", "Stage 11 gate weights", "scripts/12_build_figure_source_data.sh", "ready", "Gate weights are branch weighting, not causal clinical weights"))
    return manifest


def supplementary(source: Path, supp: Path) -> None:
    pd.read_csv(source / "fig2_model_performance_long.csv").to_csv(supp / "supp_table_all_model_metrics.csv", index=False)
    pd.read_csv(source / "fig2_per_class_dotplot.csv").to_csv(supp / "supp_table_all_per_class_metrics.csv", index=False)
    pd.read_csv("results/uncertainty/uncertainty_scores_test.csv").to_csv(supp / "supp_table_all_uncertainty_scores.csv", index=False)
    pd.read_csv("results/calibration/reliability_curve_source_data.csv").to_csv(supp / "supp_table_all_calibration_bins.csv", index=False)
    pd.concat([pd.read_csv("tables/table_calibration_bootstrap_ci.csv"), pd.read_csv("tables/table_uncertainty_triage_bootstrap_ci.csv")], ignore_index=True, sort=False).to_csv(supp / "supp_table_all_bootstrap_ci.csv", index=False)
    rows = []
    for path in Path("results/internal").glob("**/*threshold*.json"):
        try:
            data = json.loads(path.read_text())
            for label, threshold in data.items():
                rows.append({"threshold_file": str(path), "label": label, "threshold": threshold})
        except Exception:
            pass
    pd.DataFrame(rows).to_csv(supp / "supp_table_all_thresholds.csv", index=False)


def manifest_row(figure, panel, source_file, description, generated_from, script, status, notes):
    return {"figure": figure, "panel": panel, "source_file": source_file, "description": description, "generated_from": generated_from, "script": script, "status": status, "last_updated": date.today().isoformat(), "notes": notes}


def build_all() -> None:
    source, supp, _main = _out_dirs()
    manifest = []
    manifest += fig1(source)
    manifest += fig2(source)
    manifest += fig3(source)
    manifest += fig4(source)
    manifest += fig5(source)
    manifest += fig6_fig7(source)
    manifest += [
        manifest_row("DCA", "pending", "pending", "Decision-curve analysis source data", "not yet run", "pending", "pending_dca", "Reserved interface"),
        manifest_row("External validation", "pending", "pending", "External validation source data", "not yet run", "pending", "pending_external_validation", "Reserved interface"),
    ]
    supplementary(source, supp)
    _write(pd.DataFrame(manifest), source / "FIGURE_SOURCE_DATA_MANIFEST.csv")
    print(f"Wrote figure source data manifest with {len(manifest)} rows.")


if __name__ == "__main__":
    build_all()
