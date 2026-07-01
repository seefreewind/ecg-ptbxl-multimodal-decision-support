from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.dca import LABELS, dca_by_label, load_temperature_scaled_predictions, macro_dca


MODELS = ["strong_signal_only", "fair_concat_mlp", "gated_fusion_mlp"]
THRESHOLDS = [0.10, 0.20, 0.30, 0.40]
METRICS = ["macro_net_benefit", "macro_net_benefit_vs_treat_all", "macro_net_benefit_vs_treat_none"]


def bootstrap_dca(n_bootstrap: int = 1000, seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for model in MODELS:
        pred = load_temperature_scaled_predictions(model, "test")
        indices = np.arange(len(pred))
        base = macro_dca(dca_by_label(model, pred, np.asarray(THRESHOLDS)))
        for threshold in THRESHOLDS:
            base_row = base[np.isclose(base["threshold"], threshold)].iloc[0]
            boot = {metric: [] for metric in METRICS}
            for _ in range(n_bootstrap):
                sample = rng.choice(indices, size=len(indices), replace=True)
                sampled = pred.iloc[sample].reset_index(drop=True)
                macro = macro_dca(dca_by_label(model, sampled, np.asarray([threshold])))
                row = macro.iloc[0]
                for metric in METRICS:
                    boot[metric].append(float(row[metric]))
            for metric in METRICS:
                lo, hi = np.nanpercentile(np.asarray(boot[metric], dtype=float), [2.5, 97.5])
                rows.append(
                    {
                        "model_name": model,
                        "probability_mode": "temperature_scaled",
                        "split": "test",
                        "threshold": threshold,
                        "metric": metric,
                        "estimate": float(base_row[metric]),
                        "ci_lower": float(lo),
                        "ci_upper": float(hi),
                        "n_bootstrap": n_bootstrap,
                        "seed": seed,
                    }
                )
    out = pd.DataFrame(rows)
    Path("results/dca").mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    out.to_csv("results/dca/dca_bootstrap_ci.csv", index=False)
    out.to_csv("tables/table_dca_bootstrap_ci.csv", index=False)
    return out


if __name__ == "__main__":
    result = bootstrap_dca()
    print(f"Wrote DCA bootstrap CI table with {len(result)} rows.")
