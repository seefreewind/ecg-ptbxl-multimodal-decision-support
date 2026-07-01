from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SOURCE = Path("figures/source_data")
OUT = Path("figures/main")
MAIN = ["strong_signal_only", "signal_embedding_mlp", "structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    fig.savefig(path.with_suffix(".svg"))
    plt.close(fig)


def fig2() -> None:
    df = pd.read_csv(SOURCE / "fig2_model_performance_long.csv")
    data = df[df["model_name"].isin(MAIN) & df["metric"].isin(["AUROC", "average_precision", "F1"])].copy()
    piv = data.pivot(index="model_name", columns="metric", values="estimate").loc[MAIN]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    piv.plot(kind="bar", ax=ax)
    ax.set_ylim(0.65, 0.95)
    ax.set_ylabel("Internal PTB-XL frozen test metric")
    ax.set_title("Fair multimodal performance comparison")
    ax.legend(frameon=False)
    _save(fig, OUT / "fig2_model_performance.png")


def fig3() -> None:
    sim = pd.read_csv(SOURCE / "fig3_prediction_similarity_matrix.csv")
    data = sim[sim["similarity_type"].eq("prediction correlation")].pivot(index="model_i", columns="model_j", values="value").loc[MAIN, MAIN]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(data.values, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(MAIN)), MAIN, rotation=45, ha="right")
    ax.set_yticks(range(len(MAIN)), MAIN)
    ax.set_title("Prediction similarity and modality complementarity")
    fig.colorbar(im, ax=ax, label="Correlation")
    _save(fig, OUT / "fig3_ablation_complementarity.png")


def fig4() -> None:
    df = pd.read_csv(SOURCE / "fig4_calibration_long.csv")
    data = df[df["model_name"].isin(MAIN) & df["split"].eq("test") & df["metric"].isin(["macro_ece", "macro_brier"])]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharex=False)
    for ax, metric, title in zip(axes, ["macro_ece", "macro_brier"], ["ECE", "Brier"]):
        sub = data[data["metric"].eq(metric)].pivot(index="model_name", columns="calibration_mode", values="estimate").loc[MAIN]
        sub.plot(kind="bar", ax=ax)
        ax.set_title(f"Raw vs temperature-scaled {title}")
        ax.set_ylabel(title)
        ax.legend(frameon=False)
    fig.suptitle("Calibration and reliability on frozen test")
    _save(fig, OUT / "fig4_calibration.png")


def fig5() -> None:
    df = pd.read_csv(SOURCE / "fig5_uncertainty_risk_coverage.csv")
    data = df[
        df["model_name"].isin(["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"])
        & df["probability_mode"].eq("temperature_scaled")
        & df["uncertainty_score"].eq("entropy_macro")
    ].drop_duplicates(["model_name", "coverage"])
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for model in ["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"]:
        g = data[data["model_name"].eq(model)].sort_values("coverage")
        axes[0].plot(g["coverage"] * 100, g["retained_macro_auroc"], marker="o", label=model)
        axes[1].plot(g["coverage"] * 100, g["retained_macro_f1"], marker="o", label=model)
        referral_col = "referral_fraction" if "referral_fraction" in g.columns else "referred_fraction"
        axes[2].plot(g["coverage"] * 100, g[referral_col], marker="o", label=model)
    axes[0].set_title("Retained AUROC")
    axes[1].set_title("Retained F1")
    axes[2].set_title("Referral fraction")
    for ax in axes:
        ax.set_xlabel("Coverage retained (%)")
    axes[0].set_ylabel("Metric")
    axes[2].legend(frameon=False, fontsize=7)
    fig.suptitle("Uncertainty triage decision-support workflow")
    _save(fig, OUT / "fig5_uncertainty_triage.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig2()
    fig3()
    fig4()
    fig5()
    print("Wrote draft main figures Fig2-Fig5.")


if __name__ == "__main__":
    main()
