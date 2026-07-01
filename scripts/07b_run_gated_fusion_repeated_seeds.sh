#!/usr/bin/env bash
set -e

SEEDS="${SEEDS:-2026,2027,2028}"
IFS=',' read -r -a SEED_ARRAY <<< "$SEEDS"

for seed in "${SEED_ARRAY[@]}"; do
  out_dir="results/internal/gated_fusion_repeated/seed_${seed}"
  "${PYTHON:-python3}" -m src.training.train_gated_fusion \
    --config configs/model_gated_fusion.yaml \
    --seed "$seed" \
    --output-dir "$out_dir"
done

"${PYTHON:-python3}" - <<'PY'
from pathlib import Path
import pandas as pd

root = Path(".")
base = root / "results/internal/gated_fusion_repeated"
frames = []
for seed_dir in sorted(base.glob("seed_*")):
    seed = int(seed_dir.name.split("_")[-1])
    table = pd.read_csv(seed_dir / "table_gated_fusion_results.csv")
    default = table[table["threshold_mode"].eq("default_0.5")].copy()
    default.insert(0, "seed", seed)
    frames.append(default)
all_metrics = pd.concat(frames, ignore_index=True)
summary = (
    all_metrics.groupby(["split", "threshold_mode"], as_index=False)
    .agg(
        n_seeds=("seed", "nunique"),
        auroc_mean=("auroc", "mean"),
        auroc_std=("auroc", "std"),
        average_precision_mean=("average_precision", "mean"),
        average_precision_std=("average_precision", "std"),
        f1_mean=("f1", "mean"),
        f1_std=("f1", "std"),
    )
)
base.mkdir(parents=True, exist_ok=True)
all_metrics.to_csv(base / "gated_fusion_repeated_seed_metrics.csv", index=False)
summary.to_csv(base / "gated_fusion_repeated_seed_summary.csv", index=False)
(root / "tables").mkdir(exist_ok=True)
summary.to_csv(root / "tables/table_gated_fusion_repeated_seed_summary.csv", index=False)
print(base / "gated_fusion_repeated_seed_summary.csv")
PY
