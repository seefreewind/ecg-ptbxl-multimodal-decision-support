from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from src.models.fusion_mlp import FusionMLP
from src.models.gated_fusion import GatedFusionMLP


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
MODELS = ["structured_mlp", "fair_concat_mlp", "gated_fusion_mlp"]


def _checkpoint(model_name: str) -> tuple[dict[str, Any], Path]:
    paths = {
        "structured_mlp": Path("results/internal/ablation_structured/structured_mlp_best.pt"),
        "fair_concat_mlp": Path("results/internal/fair_concat/fair_concat_best.pt"),
        "gated_fusion_mlp": Path("results/internal/gated_fusion/gated_fusion_best.pt"),
    }
    path = paths[model_name]
    return torch.load(path, map_location="cpu"), path


def _feature_sets(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    signal_cols = [col for col in frame.columns if col.startswith("signal_emb_")]
    struct_cols = [col for col in frame.columns if col.startswith("struct_")]
    return signal_cols, struct_cols


def _load_model(model_name: str, frame: pd.DataFrame) -> torch.nn.Module:
    checkpoint, _path = _checkpoint(model_name)
    cfg = checkpoint.get("config", {})
    model_cfg = cfg.get("model", {})
    signal_cols, struct_cols = _feature_sets(frame)
    if model_name == "structured_mlp":
        model = FusionMLP(
            input_dim=len(struct_cols),
            hidden_dims=model_cfg.get("hidden_dims", [512, 256]),
            num_classes=len(LABELS),
            dropout=float(model_cfg.get("dropout", 0.3)),
        )
    elif model_name == "fair_concat_mlp":
        model = FusionMLP(
            input_dim=len(signal_cols) + len(struct_cols),
            hidden_dims=model_cfg.get("hidden_dims", [512, 256]),
            num_classes=len(LABELS),
            dropout=float(model_cfg.get("dropout", 0.3)),
        )
    else:
        model = GatedFusionMLP(
            signal_dim=len(signal_cols),
            structured_dim=len(struct_cols),
            hidden_dim=int(model_cfg.get("hidden_dim", 256)),
            classifier_hidden_dim=int(model_cfg.get("classifier_hidden_dim", 256)),
            num_classes=len(LABELS),
            dropout=float(model_cfg.get("dropout", 0.3)),
        )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def _forward(model_name: str, model: torch.nn.Module, x_signal: torch.Tensor, x_struct: torch.Tensor) -> torch.Tensor:
    if model_name == "structured_mlp":
        return model(x_struct)
    if model_name == "fair_concat_mlp":
        return model(torch.cat([x_signal, x_struct], dim=1))
    return model(x_signal, x_struct)


def _plot_global(global_df: pd.DataFrame, output: Path) -> None:
    top = global_df[global_df["model_name"].eq("gated_fusion_mlp")].head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["feature"], top["attribution_mean_abs"], color="#4C78A8")
    ax.set_xlabel("Mean absolute gradient x input")
    ax.set_title("Top structured feature attributions (post-hoc)")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def _plot_by_label(by_label: pd.DataFrame, output: Path) -> None:
    top = by_label[by_label["rank"] <= 8]
    fig, axes = plt.subplots(1, len(LABELS), figsize=(16, 5), sharex=False)
    for ax, label in zip(axes, LABELS):
        data = top[(top["model_name"].eq("gated_fusion_mlp")) & (top["label"].eq(label))].iloc[::-1]
        ax.barh(data["feature"], data["attribution_mean_abs"], color="#72B7B2")
        ax.set_title(label)
        ax.tick_params(axis="y", labelsize=6)
    fig.suptitle("Structured feature attribution by label (post-hoc)")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def _plot_case(case_df: pd.DataFrame, ecg_id: int, output: Path) -> None:
    top = case_df[case_df["rank"] <= 10].iloc[::-1]
    colors = np.where(top["attribution_signed"] >= 0, "#E45756", "#4C78A8")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(top["feature"], top["attribution_signed"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title(f"Case {ecg_id} structured attribution (post-hoc)")
    ax.set_xlabel("Gradient x input")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)


def run_structured_attribution() -> None:
    out_dir = Path("results/xai")
    fig_dir = Path("figures/xai")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    cases = pd.read_csv(out_dir / "xai_case_selection.csv")
    data = pd.read_csv("data/processed/fair_fusion_test.csv")
    data = data[data["ecg_id"].isin(cases["ecg_id"])].reset_index(drop=True)
    signal_cols, struct_cols = _feature_sets(data)
    rows = []
    case_rows = []
    for model_name in MODELS:
        model = _load_model(model_name, data)
        x_signal_np = data[signal_cols].to_numpy(dtype=np.float32)
        x_struct_np = data[struct_cols].to_numpy(dtype=np.float32)
        for label_idx, label in enumerate(LABELS):
            x_signal = torch.tensor(x_signal_np, requires_grad=True)
            x_struct = torch.tensor(x_struct_np, requires_grad=True)
            logits = _forward(model_name, model, x_signal, x_struct)
            score = logits[:, label_idx].sum()
            model.zero_grad(set_to_none=True)
            score.backward()
            attribution = (x_struct.grad.detach().numpy() * x_struct_np)
            mean_abs = np.mean(np.abs(attribution), axis=0)
            signed_mean = np.mean(attribution, axis=0)
            order = np.argsort(-mean_abs)
            for rank, feat_idx in enumerate(order[:50], start=1):
                rows.append(
                    {
                        "model_name": model_name,
                        "label": label,
                        "feature": struct_cols[feat_idx].replace("struct_", "", 1),
                        "attribution_mean_abs": float(mean_abs[feat_idx]),
                        "attribution_signed_mean": float(signed_mean[feat_idx]),
                        "rank": rank,
                        "method": "gradient_x_input",
                    }
                )
            for row_idx, ecg_id in enumerate(data["ecg_id"].astype(int)):
                case_attr = attribution[row_idx]
                case_order = np.argsort(-np.abs(case_attr))
                for rank, feat_idx in enumerate(case_order[:10], start=1):
                    case_rows.append(
                        {
                            "ecg_id": int(ecg_id),
                            "model_name": model_name,
                            "label": label,
                            "feature": struct_cols[feat_idx].replace("struct_", "", 1),
                            "attribution_signed": float(case_attr[feat_idx]),
                            "attribution_abs": float(abs(case_attr[feat_idx])),
                            "rank": rank,
                            "method": "gradient_x_input",
                        }
                    )
    attrib = pd.DataFrame(rows)
    case_attrib = pd.DataFrame(case_rows)
    attrib.to_csv(out_dir / "structured_attribution_values.csv", index=False)
    case_attrib.to_csv(out_dir / "structured_case_attributions.csv", index=False)
    global_df = (
        attrib.groupby(["model_name", "feature"], as_index=False)
        .agg(attribution_mean_abs=("attribution_mean_abs", "mean"), attribution_signed_mean=("attribution_signed_mean", "mean"))
        .sort_values(["model_name", "attribution_mean_abs"], ascending=[True, False])
    )
    global_df["rank"] = global_df.groupby("model_name")["attribution_mean_abs"].rank(method="first", ascending=False).astype(int)
    by_label = attrib.copy()
    global_df.to_csv("tables/table_top_structured_features_global.csv", index=False)
    by_label.to_csv("tables/table_top_structured_features_by_label.csv", index=False)
    _plot_global(global_df, fig_dir / "structured_feature_importance_global.png")
    _plot_by_label(by_label, fig_dir / "structured_feature_importance_by_label.png")
    for ecg_id in cases["ecg_id"].astype(int):
        one = case_attrib[(case_attrib["ecg_id"].eq(ecg_id)) & (case_attrib["model_name"].eq("gated_fusion_mlp")) & (case_attrib["label"].eq("NORM"))]
        if len(one):
            _plot_case(one, ecg_id, fig_dir / f"case_{ecg_id}_structured_waterfall.png")
    (out_dir / "structured_attribution_metadata.json").write_text(json.dumps({"method": "gradient_x_input", "feature_count": len(struct_cols)}, indent=2) + "\n")
    print(f"Wrote structured attribution for {len(cases)} cases using gradient_x_input.")


if __name__ == "__main__":
    run_structured_attribution()
