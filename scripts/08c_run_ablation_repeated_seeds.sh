#!/usr/bin/env bash
set -e

SEEDS="${SEEDS:-2026,2027,2028}"
IFS=',' read -r -a SEED_ARRAY <<< "$SEEDS"

for config in configs/model_signal_embedding_mlp.yaml configs/model_structured_mlp.yaml; do
  name=$("${PYTHON:-python3}" - <<PY
from src.utils.io import load_yaml
print(load_yaml("$config")["model"]["name"])
PY
)
  for seed in "${SEED_ARRAY[@]}"; do
    out_dir="results/internal/ablation_repeated/${name}/seed_${seed}"
    "${PYTHON:-python3}" -m src.training.train_ablation_mlp \
      --config "$config" \
      --seed "$seed" \
      --output-dir "$out_dir"
  done
done

"${PYTHON:-python3}" - <<'PY'
from pathlib import Path
import pandas as pd

root = Path(".")
base = root / "results/internal/ablation_repeated"
all_frames = []
summary_frames = []
for model_dir in sorted(base.iterdir()):
    if not model_dir.is_dir():
        continue
    frames = []
    for seed_dir in sorted(model_dir.glob("seed_*")):
        seed = int(seed_dir.name.split("_")[-1])
        table = pd.read_csv(seed_dir / f"table_{model_dir.name}_results.csv")
        default = table[table["threshold_mode"].eq("default_0.5")].copy()
        default.insert(0, "seed", seed)
        frames.append(default)
    metrics = pd.concat(frames, ignore_index=True)
    metrics.insert(0, "ablation_model", model_dir.name)
    all_frames.append(metrics)
    summary = (
        metrics.groupby(["ablation_model", "split", "threshold_mode"], as_index=False)
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
    summary_frames.append(summary)
all_metrics = pd.concat(all_frames, ignore_index=True)
all_summary = pd.concat(summary_frames, ignore_index=True)
all_metrics.to_csv(base / "ablation_repeated_seed_metrics.csv", index=False)
all_summary.to_csv(base / "ablation_repeated_seed_summary.csv", index=False)
(root / "tables").mkdir(exist_ok=True)
all_summary.to_csv(root / "tables/table_ablation_repeated_seed_summary.csv", index=False)
print(base / "ablation_repeated_seed_summary.csv")
PY
