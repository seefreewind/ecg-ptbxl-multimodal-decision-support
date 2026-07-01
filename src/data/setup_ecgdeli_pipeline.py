from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import ensure_dir, load_yaml, safe_to_csv, write_markdown


COLUMNS = [
    "component",
    "path",
    "available",
    "commit",
    "role",
    "exact_ptbxl_plus_feature_generator",
    "validation_status",
    "notes",
]


def _git_commit(path: Path) -> str:
    if not (path / ".git").exists():
        return ""
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def _command_available(name: str) -> bool:
    return shutil.which(name) is not None


def _matlab_executable(cfg: dict[str, Any]) -> str:
    configured = str(cfg.get("runtime_requirements", {}).get("matlab_executable", "") or "")
    if configured and Path(configured).exists():
        return configured
    return shutil.which("matlab") or ""


def _matlab_smoke(matlab: str) -> tuple[bool, str]:
    if not matlab:
        return False, "MATLAB executable not found"
    try:
        out = subprocess.run(
            [matlab, "-batch", "disp(version)"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return False, str(exc)
    text = (out.stdout + "\n" + out.stderr).strip()
    if out.returncode == 0:
        return True, text.splitlines()[0] if text else "MATLAB smoke test passed"
    return False, text.replace("\n", " ")[:500]


def _matlab_path_prefix(cfg: dict[str, Any]) -> str:
    paths = cfg.get("runtime_requirements", {}).get("matlab_extra_paths", []) or []
    commands = []
    for item in paths:
        path = str(item)
        if path and Path(path).exists():
            commands.append(f"addpath('{path.replace(chr(39), chr(39) + chr(39))}');")
    return " ".join(commands)


def _matlab_toolbox_smoke(matlab: str, cfg: dict[str, Any]) -> tuple[bool, str]:
    if not matlab:
        return False, "MATLAB executable not found"
    probe = (
        _matlab_path_prefix(cfg)
        + " "
        "funcs={'butter','filtfilt','wavedec','fitcsvm','imresize'}; "
        "for i=1:numel(funcs), fprintf('%s=%d\\n',funcs{i},exist(funcs{i},'file')); end"
    )
    try:
        out = subprocess.run(
            [matlab, "-batch", probe],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return False, str(exc)
    text = (out.stdout + "\n" + out.stderr).strip()
    if out.returncode != 0:
        return False, text.replace("\n", " ")[:500]
    available: dict[str, bool] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        name, value = line.strip().split("=", 1)
        try:
            available[name] = int(value) > 0
        except ValueError:
            available[name] = False
    missing = [name for name in ["butter", "filtfilt", "wavedec", "fitcsvm"] if not available.get(name, False)]
    note = "; ".join(f"{name}={'available' if ok else 'missing'}" for name, ok in sorted(available.items()))
    if missing:
        return False, f"missing required toolbox functions: {', '.join(missing)}. {note}"
    return True, note or "required toolbox function smoke test passed"


def _python_import_from_path(module_path: Path, module_name: str) -> tuple[bool, str]:
    if not module_path.exists():
        return False, "module file missing"
    sys.path.insert(0, str(module_path.parent))
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            return False, "could not build module spec"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:
        return False, str(exc)
    finally:
        try:
            sys.path.remove(str(module_path.parent))
        except ValueError:
            pass
    return True, "import ok"


def _scan_ptbxl_benchmark(path: Path) -> tuple[bool, str]:
    readme = path / "README.md"
    utils = path / "code/feature_utils/utils.py"
    text = (readme.read_text(errors="ignore") if readme.exists() else "") + "\n" + (utils.read_text(errors="ignore") if utils.exists() else "")
    reads_existing = "features/ecgdeli_features.csv" in text and "pd.read_csv" in text
    mentions_download = "Download the features files" in text
    if reads_existing and mentions_download:
        return False, "benchmark consumes downloaded ecgdeli_features.csv; no waveform-to-feature extraction recipe found"
    return False, "no exact waveform-to-531-feature recipe detected"


def setup_audit() -> pd.DataFrame:
    cfg = load_yaml("configs/ecgdeli_pipeline.yaml")
    repos = cfg["repositories"]
    ptb = Path(repos["ptbxl_feature_benchmark"])
    ecgdeli = Path(repos["ecgdeli_matlab"])
    pyecgdeli = Path(repos["pyecgdeli"])
    benchmark_exact, benchmark_note = _scan_ptbxl_benchmark(ptb)
    py_import_ok, py_note = _python_import_from_path(pyecgdeli / "ECGdeli.py", "ECGdeli")
    matlab_path = _matlab_executable(cfg)
    matlab_license_ok, matlab_note = _matlab_smoke(matlab_path)
    matlab_toolboxes_ok, matlab_toolbox_note = _matlab_toolbox_smoke(matlab_path, cfg) if matlab_license_ok else (False, "MATLAB smoke test did not pass")
    required_features = [line.strip() for line in Path("data/processed/structured_feature_names.txt").read_text().splitlines() if line.strip()]
    rows: list[dict[str, Any]] = [
        {
            "component": "ptbxl_feature_benchmark",
            "path": str(ptb),
            "available": ptb.exists(),
            "commit": _git_commit(ptb),
            "role": "official PTB-XL+ benchmark code",
            "exact_ptbxl_plus_feature_generator": benchmark_exact,
            "validation_status": "not_exact_generator",
            "notes": benchmark_note,
        },
        {
            "component": "ECGdeli_MATLAB",
            "path": str(ecgdeli),
            "available": ecgdeli.exists(),
            "commit": _git_commit(ecgdeli),
            "role": "official ECGdeli MATLAB delineation toolbox",
            "exact_ptbxl_plus_feature_generator": False,
            "validation_status": "matlab_license_missing" if matlab_path and not matlab_license_ok else ("runtime_missing" if not matlab_path else ("matlab_toolboxes_missing" if not matlab_toolboxes_ok else "matlab_available_needs_schema_recipe")),
            "notes": f"ECGdeli requires MATLAB image/signal/statistics/wavelet toolboxes. MATLAB smoke: {matlab_note}. Toolbox smoke: {matlab_toolbox_note}",
        },
        {
            "component": "pyECGdeli",
            "path": str(pyecgdeli),
            "available": pyecgdeli.exists() and py_import_ok,
            "commit": _git_commit(pyecgdeli),
            "role": "Python ECGdeli port for exploratory audit only",
            "exact_ptbxl_plus_feature_generator": False,
            "validation_status": "not_exact_generator",
            "notes": f"{py_note}; README says work in progress and not a complete PTB-XL+ 531-feature generator.",
        },
        {
            "component": "MATLAB_runtime",
            "path": matlab_path,
            "available": bool(matlab_path and matlab_license_ok),
            "commit": "",
            "role": "required runtime for official ECGdeli",
            "exact_ptbxl_plus_feature_generator": False,
            "validation_status": "licensed" if matlab_license_ok else ("license_missing" if matlab_path else "missing"),
            "notes": matlab_note,
        },
        {
            "component": "MATLAB_required_toolboxes",
            "path": matlab_path,
            "available": bool(matlab_toolboxes_ok),
            "commit": "",
            "role": "required MATLAB toolbox functions for ECGdeli feature extraction",
            "exact_ptbxl_plus_feature_generator": False,
            "validation_status": "available" if matlab_toolboxes_ok else "missing",
            "notes": matlab_toolbox_note,
        },
        {
            "component": "Octave_runtime",
            "path": shutil.which("octave") or "",
            "available": _command_available("octave"),
            "commit": "",
            "role": "possible smoke-test runtime only",
            "exact_ptbxl_plus_feature_generator": False,
            "validation_status": "missing" if not _command_available("octave") else "available_not_validated_as_exact",
            "notes": "Octave is not treated as validated replacement for MATLAB ECGdeli plus required toolboxes.",
        },
        {
            "component": "target_schema",
            "path": "data/processed/structured_feature_names.txt",
            "available": len(required_features) == 531,
            "commit": "",
            "role": "required frozen structured feature schema",
            "exact_ptbxl_plus_feature_generator": False,
            "validation_status": "schema_available" if len(required_features) == 531 else "schema_missing",
            "notes": f"{len(required_features)} required PTB-XL+ structured feature names loaded.",
        },
    ]
    return pd.DataFrame(rows, columns=COLUMNS)


def _decision(audit: pd.DataFrame) -> pd.DataFrame:
    exact_generator = bool(audit["exact_ptbxl_plus_feature_generator"].astype(bool).any())
    matlab_available = bool(audit[audit["component"].eq("MATLAB_runtime")]["available"].astype(bool).any())
    toolboxes_available = bool(audit[audit["component"].eq("MATLAB_required_toolboxes")]["available"].astype(bool).any())
    matlab_installed = bool(str(audit[audit["component"].eq("MATLAB_runtime")]["path"].iloc[0] or ""))
    schema_ok = bool(audit[audit["component"].eq("target_schema")]["available"].astype(bool).any())
    can_run = bool(exact_generator and matlab_available and toolboxes_available and schema_ok)
    blocker = []
    if not exact_generator:
        blocker.append("ptbxl_plus_exact_feature_generation_recipe_missing")
    if not matlab_available and matlab_installed:
        blocker.append("matlab_license_missing_for_official_ecgdeli")
    elif not matlab_available:
        blocker.append("matlab_runtime_missing_for_official_ecgdeli")
    if matlab_available and not toolboxes_available:
        blocker.append("matlab_required_toolboxes_missing_for_official_ecgdeli")
    if not schema_ok:
        blocker.append("target_531_feature_schema_missing")
    return pd.DataFrame(
        [
            {
                "can_run_exact_external_feature_extraction": can_run,
                "can_run_full_multimodal_external_validation": False,
                "recommended_next_action": "obtain PTB-XL+ ecgdeli extraction recipe and MATLAB runtime/toolboxes, then validate 531-column schema",
                "blocking_issue": ";".join(blocker),
            }
        ]
    )


def _write_summary(audit: pd.DataFrame, decision: pd.DataFrame) -> None:
    matlab_available = bool(audit[audit["component"].eq("MATLAB_runtime")]["available"].astype(bool).any())
    toolboxes_available = bool(audit[audit["component"].eq("MATLAB_required_toolboxes")]["available"].astype(bool).any())
    if matlab_available and toolboxes_available:
        matlab_interpretation = "The configured MATLAB runtime and required toolbox function smoke tests are available."
    elif matlab_available:
        matlab_interpretation = "The configured MATLAB runtime can be called, but required ECGdeli-related toolbox functions are missing."
    else:
        matlab_interpretation = "The official ECGdeli implementation is MATLAB-based and MATLAB is not available in the current environment."

    text = "\n".join(
        [
            "# Stage 14B ECGdeli / PTB-XL+ Exact Pipeline Setup Summary",
            "",
            "Date: " + date.today().isoformat(),
            "",
            "## Status",
            "",
            "The relevant repositories were cloned and audited locally. PyWavelets was installed so the Python ECGdeli port can be imported for exploratory checks. However, an exact waveform-to-PTB-XL+ 531-column feature extraction pipeline is not yet runnable.",
            "",
            "## Components",
            "",
            audit.to_markdown(index=False),
            "",
            "## Decision",
            "",
            decision.to_markdown(index=False),
            "",
            "## Interpretation",
            "",
            "- The PTB-XL+ benchmark repository consumes downloaded `ecgdeli_features.csv`; it does not provide the missing waveform-to-feature extraction recipe.",
            f"- {matlab_interpretation}",
            "- pyECGdeli is importable after installing PyWavelets, but it is not a complete or validated PTB-XL+ 531-feature generator.",
            "- Therefore, full multimodal external validation remains blocked.",
            "",
            "## Next Step",
            "",
            "Obtain a MATLAB runtime with the required toolboxes and the exact PTB-XL+ ECGdeli feature aggregation recipe, or obtain external structured feature tables already matching the 531 frozen PTB-XL+ columns.",
        ]
    )
    write_markdown("results/stage14b_ecgdeli_pipeline_setup_summary.md", text + "\n")


def main() -> None:
    ensure_dir("results/external")
    ensure_dir("tables")
    audit = setup_audit()
    decision = _decision(audit)
    safe_to_csv(audit, "tables/table_ecgdeli_pipeline_setup_audit.csv")
    safe_to_csv(decision, "tables/table_ecgdeli_pipeline_decision.csv")
    _write_summary(audit, decision)
    print("Wrote ECGdeli/PTB-XL+ exact pipeline setup audit.")


if __name__ == "__main__":
    main()
