from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import wfdb

from src.models.signal_resnet import SignalResNet


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def _load_model() -> SignalResNet:
    checkpoint = torch.load("results/internal/signal_strong/signal_strong_best.pt", map_location="cpu")
    cfg = checkpoint.get("config", {}).get("model", {})
    model = SignalResNet(
        in_channels=int(cfg.get("input_channels", 12)),
        num_classes=len(LABELS),
        base_channels=int(cfg.get("base_channels", 64)),
        blocks_per_stage=tuple(cfg.get("blocks_per_stage", [2, 2, 2])),
        dropout=float(cfg.get("dropout", 0.2)),
    )
    state = checkpoint["model_state_dict"]
    remapped = {}
    for key, value in state.items():
        if key == "head.3.weight":
            remapped["classifier.weight"] = value
        elif key == "head.3.bias":
            remapped["classifier.bias"] = value
        elif key.startswith("head."):
            continue
        else:
            remapped[key] = value
    model.load_state_dict(remapped, strict=False)
    model.eval()
    return model


def _waveform(filename_lr: str) -> np.ndarray:
    signal, _meta = wfdb.rdsamp(str(Path("data/raw/ptbxl") / filename_lr))
    x = np.asarray(signal, dtype=np.float32).T
    mean = x.mean(axis=1, keepdims=True)
    std = x.std(axis=1, keepdims=True)
    return (x - mean) / np.maximum(std, 1e-6)


def _plot_heatmap(ecg_id: int, x: np.ndarray, attr: np.ndarray, title: str, output: Path) -> None:
    fig, axes = plt.subplots(12, 1, figsize=(11, 10), sharex=True)
    t = np.arange(x.shape[1]) / 100.0
    for idx, ax in enumerate(axes):
        norm_attr = attr[idx] / (np.max(attr[idx]) + 1e-8)
        ax.imshow(norm_attr.reshape(1, -1), extent=[t[0], t[-1], -2.8, 2.8], aspect="auto", cmap="Reds", alpha=0.45)
        ax.plot(t, x[idx], color="black", linewidth=0.6)
        ax.set_ylabel(LEADS[idx], rotation=0, labelpad=15, fontsize=8)
        ax.set_yticks([])
    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output, dpi=300)
    plt.close(fig)


def run_signal_attribution() -> None:
    out_dir = Path("results/xai")
    fig_dir = Path("figures/xai")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    cases = pd.read_csv(out_dir / "xai_case_selection.csv")
    index = pd.read_csv("data/processed/ptbxl_multimodal_index.csv")
    scores = pd.read_csv("results/uncertainty/uncertainty_scores_test.csv")
    primary_scores = scores[scores["model_name"].eq("gated_fusion_mlp") & scores["probability_mode"].eq("temperature_scaled")]
    model = _load_model()
    arrays = {}
    lead_rows = []
    summary_rows = []
    for _, case in cases.iterrows():
        ecg_id = int(case["ecg_id"])
        filename = str(index[index["ecg_id"].eq(ecg_id)]["filename_lr"].iloc[0])
        x_np = _waveform(filename)
        x = torch.tensor(x_np[None, :, :], requires_grad=True)
        logits = model(x)
        label_idx = int(torch.argmax(torch.sigmoid(logits), dim=1).item())
        score = logits[0, label_idx]
        model.zero_grad(set_to_none=True)
        score.backward()
        attr = np.abs(x.grad.detach().numpy()[0] * x_np)
        arrays[f"ecg_{ecg_id}_waveform"] = x_np
        arrays[f"ecg_{ecg_id}_attribution"] = attr
        lead_importance = attr.mean(axis=1)
        order = np.argsort(-lead_importance)
        for rank, lead_idx in enumerate(order, start=1):
            lead_rows.append(
                {
                    "ecg_id": ecg_id,
                    "model_name": "strong_signal_only",
                    "label": LABELS[label_idx],
                    "lead": LEADS[lead_idx],
                    "importance_score": float(lead_importance[lead_idx]),
                    "rank": rank,
                    "method": "saliency_gradient_x_input",
                }
            )
        score_row = primary_scores[primary_scores["ecg_id"].eq(ecg_id)].iloc[0]
        summary_rows.append(
            {
                "ecg_id": ecg_id,
                "model_name": "strong_signal_only",
                "explained_label": LABELS[label_idx],
                "top_signal_leads": "|".join([LEADS[i] for i in order[:3]]),
                "mean_attribution": float(attr.mean()),
                "max_attribution": float(attr.max()),
                "uncertainty_score": float(score_row["entropy_macro"]),
                "method": "saliency_gradient_x_input",
            }
        )
        _plot_heatmap(
            ecg_id,
            x_np,
            attr,
            f"Case {ecg_id}: signal saliency heatmap (post-hoc)",
            fig_dir / f"case_{ecg_id}_signal_heatmap.png",
        )
    np.savez_compressed(out_dir / "signal_attribution_values.npz", **arrays)
    pd.DataFrame(summary_rows).to_csv(out_dir / "signal_case_attribution_summary.csv", index=False)
    pd.DataFrame(lead_rows).to_csv("tables/table_signal_lead_importance.csv", index=False)
    (out_dir / "signal_attribution_metadata.json").write_text(json.dumps({"method": "saliency_gradient_x_input"}, indent=2) + "\n")
    print(f"Wrote signal attribution for {len(cases)} cases.")


if __name__ == "__main__":
    run_signal_attribution()
