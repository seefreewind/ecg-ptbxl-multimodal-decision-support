from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from src.models.gated_fusion import GatedFusionMLP


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]


def export_gate_weights() -> pd.DataFrame:
    out_dir = Path("results/xai")
    fig_dir = Path("figures/xai")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    data = pd.read_csv("data/processed/fair_fusion_test.csv")
    signal_cols = [col for col in data.columns if col.startswith("signal_emb_")]
    struct_cols = [col for col in data.columns if col.startswith("struct_")]
    checkpoint = torch.load("results/internal/gated_fusion/gated_fusion_best.pt", map_location="cpu")
    cfg = checkpoint.get("config", {}).get("model", {})
    model = GatedFusionMLP(
        signal_dim=len(signal_cols),
        structured_dim=len(struct_cols),
        hidden_dim=int(cfg.get("hidden_dim", 256)),
        classifier_hidden_dim=int(cfg.get("classifier_hidden_dim", 256)),
        num_classes=len(LABELS),
        dropout=float(cfg.get("dropout", 0.3)),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    gates = []
    batch_size = 256
    with torch.no_grad():
        for start in range(0, len(data), batch_size):
            batch = data.iloc[start : start + batch_size]
            signal = torch.tensor(batch[signal_cols].to_numpy(dtype=np.float32))
            structured = torch.tensor(batch[struct_cols].to_numpy(dtype=np.float32))
            _logits, gate = model(signal, structured, return_gate=True)
            gates.append(gate.numpy())
    gate_arr = np.concatenate(gates, axis=0)
    out = pd.DataFrame(
        {
            "ecg_id": data["ecg_id"].astype(int),
            "gate_signal_mean": gate_arr.mean(axis=1),
            "gate_signal_std": gate_arr.std(axis=1),
            "gate_structured_mean": 1.0 - gate_arr.mean(axis=1),
        }
    )
    scores = pd.read_csv("results/uncertainty/uncertainty_scores_test.csv")
    cutoffs = pd.read_csv("results/uncertainty/triage_cutoffs_validation.csv")
    primary = scores[scores["model_name"].eq("gated_fusion_mlp") & scores["probability_mode"].eq("temperature_scaled")][["ecg_id", "entropy_macro"]]
    cutoff80 = float(
        cutoffs[
            cutoffs["model_name"].eq("gated_fusion_mlp")
            & cutoffs["probability_mode"].eq("temperature_scaled")
            & cutoffs["uncertainty_score"].eq("entropy_macro")
            & np.isclose(cutoffs["coverage"], 0.8)
        ]["validation_uncertainty_cutoff"].iloc[0]
    )
    out = out.merge(primary, on="ecg_id", how="left")
    out["retained_or_referred_80"] = np.where(out["entropy_macro"] <= cutoff80, "retained", "referred")
    out.to_csv(out_dir / "gated_gate_weights_test.csv", index=False)
    summary = (
        out.groupby("retained_or_referred_80", as_index=False)
        .agg(
            n=("ecg_id", "count"),
            gate_signal_mean=("gate_signal_mean", "mean"),
            gate_signal_std=("gate_signal_mean", "std"),
            gate_structured_mean=("gate_structured_mean", "mean"),
        )
    )
    summary.to_csv("tables/table_gate_weight_summary.csv", index=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    for group, color in [("retained", "#4C78A8"), ("referred", "#E45756")]:
        vals = out[out["retained_or_referred_80"].eq(group)]["gate_signal_mean"]
        ax.hist(vals, bins=30, alpha=0.6, label=group, color=color)
    ax.set_xlabel("Mean gate weight toward signal branch")
    ax.set_ylabel("Count")
    ax.set_title("Gated fusion branch weighting (post-hoc)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(fig_dir / "gate_weight_distribution.png", dpi=300)
    fig.savefig(fig_dir / "gate_weight_distribution.svg")
    plt.close(fig)
    (out_dir / "gate_weight_metadata.json").write_text(json.dumps({"interpretation": "gate weights indicate relative model branch weighting, not clinical causality"}, indent=2) + "\n")
    print("Wrote gated fusion gate weights.")
    return out


if __name__ == "__main__":
    export_gate_weights()
