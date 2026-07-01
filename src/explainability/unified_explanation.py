from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _top_join(frame: pd.DataFrame, col: str, n: int = 5) -> str:
    return "|".join(frame.sort_values("rank").head(n)[col].astype(str))


def build_unified_explanations() -> pd.DataFrame:
    out_dir = Path("results/xai")
    fig_dir = Path("figures/xai")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    cases = pd.read_csv(out_dir / "xai_case_selection.csv")
    structured = pd.read_csv(out_dir / "structured_case_attributions.csv")
    signal = pd.read_csv("tables/table_signal_lead_importance.csv")
    signal_summary = pd.read_csv(out_dir / "signal_case_attribution_summary.csv")
    gates = pd.read_csv(out_dir / "gated_gate_weights_test.csv")
    rows = []
    for _, case in cases.iterrows():
        ecg_id = int(case["ecg_id"])
        struct_case = structured[
            structured["ecg_id"].eq(ecg_id)
            & structured["model_name"].eq("gated_fusion_mlp")
            & structured["label"].eq("NORM")
        ]
        if struct_case.empty:
            struct_case = structured[structured["ecg_id"].eq(ecg_id) & structured["model_name"].eq("gated_fusion_mlp")]
        sig_case = signal[signal["ecg_id"].eq(ecg_id)]
        sig_summary = signal_summary[signal_summary["ecg_id"].eq(ecg_id)].iloc[0]
        gate = gates[gates["ecg_id"].eq(ecg_id)].iloc[0]
        incorrect = str(case["correct_or_incorrect"]) == "incorrect"
        rows.append(
            {
                "ecg_id": ecg_id,
                "case_type": case["case_type"],
                "true_labels": case["true_labels"],
                "predicted_labels": case["predicted_labels"],
                "model_name": case["model_name"],
                "retained_or_referred": case["retained_or_referred"],
                "uncertainty_score": float(case["uncertainty_score"]),
                "confidence_group": "high-confidence retained" if case["retained_or_referred"] == "retained" else "low-confidence referred",
                "top_structured_features": _top_join(struct_case, "feature", 5),
                "top_signal_leads": _top_join(sig_case, "lead", 3),
                "top_signal_segments": "top temporal regions shown in case heatmap",
                "gate_signal": float(gate["gate_signal_mean"]),
                "gate_structured": float(gate["gate_structured_mean"]),
                "interpretation_note": "Post-hoc attribution summarizes waveform leads and structured ECG features associated with the model output.",
                "failure_note": "Prediction error included for failure-mode auditing." if incorrect else "",
            }
        )
    unified = pd.DataFrame(rows)
    unified.to_csv(out_dir / "unified_case_explanations.csv", index=False)
    unified.to_csv("tables/table_unified_xai_cases.csv", index=False)

    for _, row in unified.iterrows():
        _plot_unified_case(row, fig_dir / f"unified_case_{int(row['ecg_id'])}.png")
    _plot_representative(unified, fig_dir / "fig_xai_representative_cases.png")
    _build_uncertainty_link(unified, structured, signal_summary, fig_dir)
    _write_plot_source(unified)
    print(f"Wrote unified XAI reports for {len(unified)} cases.")
    return unified


def _plot_unified_case(row: pd.Series, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    text = (
        f"ECG {int(row['ecg_id'])}\n"
        f"{row['case_type']} | {row['retained_or_referred']}\n"
        f"True: {row['true_labels']} | Predicted: {row['predicted_labels']}\n"
        f"Uncertainty: {row['uncertainty_score']:.3f}\n"
        f"Top structured: {row['top_structured_features']}\n"
        f"Top signal leads: {row['top_signal_leads']}\n"
        f"Gate signal/structured: {row['gate_signal']:.3f} / {row['gate_structured']:.3f}\n"
        f"{row['interpretation_note']}\n{row['failure_note']}"
    )
    ax.text(0.02, 0.95, text, va="top", ha="left", fontsize=10, wrap=True)
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)


def _plot_representative(unified: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(min(6, len(unified)), 1, figsize=(10, min(6, len(unified)) * 1.2))
    if not isinstance(axes, np.ndarray):
        axes = np.asarray([axes])
    for ax, (_, row) in zip(axes, unified.head(len(axes)).iterrows()):
        ax.axis("off")
        ax.text(
            0.01,
            0.5,
            f"ECG {int(row['ecg_id'])}: {row['case_type']} | true {row['true_labels']} | pred {row['predicted_labels']} | leads {row['top_signal_leads']} | features {row['top_structured_features']}",
            va="center",
            fontsize=8,
        )
    fig.suptitle("Representative XAI cases (post-hoc attribution)")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def _build_uncertainty_link(unified: pd.DataFrame, structured: pd.DataFrame, signal_summary: pd.DataFrame, fig_dir: Path) -> None:
    rows = []
    for _, row in unified.iterrows():
        ecg_id = int(row["ecg_id"])
        struct = structured[structured["ecg_id"].eq(ecg_id) & structured["model_name"].eq("gated_fusion_mlp")]
        top_sum = struct[struct["rank"] <= 3]["attribution_abs"].sum()
        total_sum = struct["attribution_abs"].sum()
        signal_row = signal_summary[signal_summary["ecg_id"].eq(ecg_id)].iloc[0]
        rows.append(
            {
                "ecg_id": ecg_id,
                "case_type": row["case_type"],
                "retained_or_referred": row["retained_or_referred"],
                "uncertainty_score": row["uncertainty_score"],
                "top_structured_feature_concentration": float(top_sum / total_sum) if total_sum else np.nan,
                "mean_signal_attribution": float(signal_row["mean_attribution"]),
                "gate_signal_mean": row["gate_signal"],
                "gate_structured_mean": row["gate_structured"],
            }
        )
    link = pd.DataFrame(rows)
    link.to_csv("tables/table_xai_uncertainty_link.csv", index=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    for group, color in [("retained", "#4C78A8"), ("referred", "#E45756")]:
        data = link[link["retained_or_referred"].eq(group)]
        ax.scatter(data["uncertainty_score"], data["top_structured_feature_concentration"], label=group, color=color)
    ax.set_xlabel("Uncertainty score")
    ax.set_ylabel("Top structured attribution concentration")
    ax.set_title("XAI concentration vs uncertainty")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(fig_dir / "xai_uncertainty_examples.png", dpi=300)
    fig.savefig(fig_dir / "xai_uncertainty_examples.svg")
    plt.close(fig)


def _write_plot_source(unified: pd.DataFrame) -> None:
    unified.to_csv("results/xai/xai_plot_source_data.csv", index=False)


if __name__ == "__main__":
    build_unified_explanations()
