from __future__ import annotations

import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


KEYS = [
    "SMOKE_STATUS",
    "N_SAMPLES",
    "N_LEADS",
    "FPT_MULTICHANNEL_ROWS",
    "FPT_MULTICHANNEL_COLS",
    "FPT_CELL_LEADS",
    "AMPLITUDE_DIMS",
    "TIMING_DIMS",
    "TIMING_SYNC_DIMS",
]


def _matlab_escape(path: str | Path) -> str:
    return str(path).replace("'", "''")


def _matlab_path_prefix(cfg: dict[str, Any]) -> str:
    paths = cfg.get("runtime_requirements", {}).get("matlab_extra_paths", []) or []
    commands = []
    for item in paths:
        path = Path(str(item))
        if path.exists():
            commands.append(f"addpath('{_matlab_escape(path)}');")
    return "\n".join(commands)


def _smoke_script(cfg: dict[str, Any]) -> str:
    ecgdeli_dir = Path(cfg["repositories"]["ecgdeli_matlab"]).resolve()
    return "\n".join(
        [
            "try",
            _matlab_path_prefix(cfg),
            f"addpath(genpath('{_matlab_escape(ecgdeli_dir)}'));",
            f"load(fullfile('{_matlab_escape(ecgdeli_dir)}','Example','s0273lre_signal.mat'));",
            "ecg = signal;",
            "Fs = 1000;",
            "[ecg_filtered_frq] = ECG_High_Low_Filter(ecg, Fs, 1, 40);",
            "ecg_filtered_frq = Notch_Filter(ecg_filtered_frq, Fs, 50, 1);",
            "[ecg_filtered_isoline, ~, ~, ~] = Isoline_Correction(ecg_filtered_frq);",
            "[FPT_MultiChannel, FPT_Cell] = Annotate_ECG_Multi(ecg_filtered_isoline, Fs);",
            "[Amplitude_feature_12leads] = ExtractAmplitudeFeaturesFromFPT(FPT_Cell, ecg_filtered_isoline);",
            "[Timing_feature_12leads, Timing_feature_sync] = ExtractIntervalFeaturesFromFPT(FPT_Cell, FPT_MultiChannel);",
            "fprintf('SMOKE_STATUS=passed\\n');",
            "fprintf('N_SAMPLES=%d\\n', size(ecg, 1));",
            "fprintf('N_LEADS=%d\\n', size(ecg, 2));",
            "fprintf('FPT_MULTICHANNEL_ROWS=%d\\n', size(FPT_MultiChannel, 1));",
            "fprintf('FPT_MULTICHANNEL_COLS=%d\\n', size(FPT_MultiChannel, 2));",
            "fprintf('FPT_CELL_LEADS=%d\\n', numel(FPT_Cell));",
            "fprintf('AMPLITUDE_DIMS=%s\\n', mat2str(size(Amplitude_feature_12leads)));",
            "fprintf('TIMING_DIMS=%s\\n', mat2str(size(Timing_feature_12leads)));",
            "fprintf('TIMING_SYNC_DIMS=%s\\n', mat2str(size(Timing_feature_sync)));",
            "catch ME",
            "fprintf('SMOKE_STATUS=failed\\n');",
            "fprintf('ERROR_IDENTIFIER=%s\\n', ME.identifier);",
            "fprintf('ERROR_MESSAGE=%s\\n', regexprep(ME.message, '\\n', ' '));",
            "exit(1);",
            "end",
        ]
    )


def _parse_stdout(stdout: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in stdout.splitlines():
        match = re.match(r"^([A-Z0-9_]+)=(.*)$", line.strip())
        if match:
            parsed[match.group(1)] = match.group(2).strip()
    return parsed


def run_smoke() -> tuple[pd.DataFrame, str]:
    cfg = load_yaml("configs/ecgdeli_pipeline.yaml")
    matlab = str(cfg.get("runtime_requirements", {}).get("matlab_executable", "") or "")
    if not matlab or not Path(matlab).exists():
        row = {
            "smoke_test": "ecgdeli_official_example_batch",
            "passed": False,
            "matlab_executable": matlab,
            "blocking_issue": "matlab_executable_missing",
            "notes": "Configured MATLAB executable is missing.",
        }
        return pd.DataFrame([row]), ""

    ensure_dir("results/external")
    script_text = _smoke_script(cfg)
    with tempfile.TemporaryDirectory(prefix="ecgdeli_smoke_") as tmp:
        script_path = Path(tmp) / "run_ecgdeli_smoke.m"
        script_path.write_text(script_text, encoding="utf-8")
        proc = subprocess.run(
            [matlab, "-batch", f"run('{_matlab_escape(script_path)}')"],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    parsed = _parse_stdout(stdout)
    passed = proc.returncode == 0 and parsed.get("SMOKE_STATUS") == "passed"
    blockers = []
    if not passed:
        blockers.append("ecgdeli_smoke_test_failed")
    if parsed.get("FPT_MULTICHANNEL_ROWS") in {None, "0"}:
        blockers.append("ecgdeli_no_fiducial_points_detected")
    row = {
        "smoke_test": "ecgdeli_official_example_batch",
        "passed": passed,
        "matlab_executable": matlab,
        "n_samples": parsed.get("N_SAMPLES", ""),
        "n_leads": parsed.get("N_LEADS", ""),
        "fpt_multichannel_rows": parsed.get("FPT_MULTICHANNEL_ROWS", ""),
        "fpt_multichannel_cols": parsed.get("FPT_MULTICHANNEL_COLS", ""),
        "fpt_cell_leads": parsed.get("FPT_CELL_LEADS", ""),
        "amplitude_dims": parsed.get("AMPLITUDE_DIMS", ""),
        "timing_dims": parsed.get("TIMING_DIMS", ""),
        "timing_sync_dims": parsed.get("TIMING_SYNC_DIMS", ""),
        "blocking_issue": ";".join(blockers),
        "notes": parsed.get("ERROR_MESSAGE", "") or "Official ECGdeli example ECG completed without figures.",
    }
    log_text = "\n".join(
        [
            "# MATLAB stdout",
            "",
            "```text",
            stdout.strip(),
            "```",
            "",
            "# MATLAB stderr",
            "",
            "```text",
            stderr.strip(),
            "```",
            "",
        ]
    )
    return pd.DataFrame([row]), log_text


def _write_summary(result: pd.DataFrame, log_text: str) -> None:
    row = result.iloc[0].to_dict()
    passed = bool(row["passed"])
    text = "\n".join(
        [
            "# Stage 14D ECGdeli MATLAB Smoke Test Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "The official ECGdeli MATLAB code was tested in batch mode using the repository's bundled example ECG. This is an environment and function-level smoke test only; it is not a PTB-XL+ 531-feature reproduction.",
            "",
            "## Result",
            "",
            result.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- MATLAB can call ECGdeli filtering, delineation, amplitude-feature, and interval-feature functions in batch mode." if passed else "- ECGdeli batch-mode smoke test failed.",
            "- The current result does not yet provide the exact PTB-XL+ waveform-to-531-column aggregation recipe.",
            "- Full multimodal external validation remains blocked until external CPSC2018 and Chapman-Shaoxing structured feature tables pass the frozen 531-column schema gate.",
            "",
            "## Next Step",
            "",
            "Attempt a small external-record ECGdeli extraction prototype, then compare any generated feature names against `data/processed/structured_feature_names.txt`. Do not run fair concat or gated-fusion external validation until the schema gate passes.",
            "",
            "## Logs",
            "",
            log_text,
        ]
    )
    write_markdown("results/stage14d_ecgdeli_smoke_summary.md", text + "\n")


def main() -> None:
    ensure_dir("tables")
    result, log_text = run_smoke()
    safe_to_csv(result, "tables/table_ecgdeli_smoke_test.csv")
    _write_summary(result, log_text)
    print("Wrote ECGdeli MATLAB smoke-test outputs.")


if __name__ == "__main__":
    main()
