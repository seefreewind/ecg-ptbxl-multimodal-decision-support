#!/usr/bin/env bash
set -e

"${PYTHON:-python3}" - <<'PY'
from pathlib import Path

required = {
    "strong_checkpoint": Path("results/internal/signal_strong/signal_strong_best.pt"),
    "strong_config": Path("configs/model_signal_resnet_strong.yaml"),
    "strong_val_predictions": Path("results/internal/signal_strong/signal_strong_val_predictions.csv"),
    "strong_test_predictions": Path("results/internal/signal_strong/signal_strong_test_predictions.csv"),
}

lines = ["# Stage 6A Strong Signal Checkpoint Check", "", "## Required Files", ""]
ok = True
for name, path in required.items():
    found = path.exists() and path.stat().st_size > 0
    ok = ok and found
    lines.append(f"- {name}: {'found' if found else 'missing'} (`{path}`)")

lines.extend(["", "## Decision", ""])
if ok:
    lines.append("ready")
    blocker = "none"
else:
    lines.append("blocked")
    blocker = "Strong signal checkpoint or required strong signal outputs are missing. Do not fall back to `results/internal/signal_resnet.pt`."
lines.extend(["", "## Blocking Issue", "", blocker, ""])

out = Path("results/stage6a_checkpoint_check.md")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines), encoding="utf-8")
print(f"strong signal checkpoint found: {'yes' if required['strong_checkpoint'].exists() else 'no'}")
print(f"blocking issue: {blocker}")
raise SystemExit(0 if ok else 1)
PY
