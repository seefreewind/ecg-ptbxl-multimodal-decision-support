from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file with safe defaults."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a mapping: {path}")
    return data


def project_root_from_config(config_path: str | Path) -> Path:
    """Infer project root from configs/data_ptbxl.yaml."""
    config_path = Path(config_path).resolve()
    if config_path.parent.name == "configs":
        return config_path.parent.parent
    return Path.cwd().resolve()


def resolve_path(path_value: Optional[str | Path], root: str | Path) -> Optional[Path]:
    """Resolve a possibly relative path against project root."""
    if path_value is None:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return Path(root).resolve() / path


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as Path."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_markdown(path: str | Path, text: str) -> None:
    """Write markdown text, creating the parent directory."""
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def safe_to_csv(df: pd.DataFrame, path: str | Path, index: bool = False) -> None:
    """Write a dataframe to CSV, creating the parent directory."""
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=index)


def read_table_auto(path: str | Path, nrows: int | None = None) -> pd.DataFrame:
    """Read a tabular file by extension.

    Supports csv, tsv, parquet, feather, and pickle/pkl. For formats that do not
    support nrows directly, the full table is read and then truncated.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return pd.read_csv(path, nrows=nrows)
        if suffix == ".tsv":
            return pd.read_csv(path, sep="\t", nrows=nrows)
        if suffix == ".parquet":
            df = pd.read_parquet(path)
        elif suffix == ".feather":
            df = pd.read_feather(path)
        elif suffix in {".pkl", ".pickle"}:
            df = pd.read_pickle(path)
        else:
            raise ValueError(f"Unsupported table extension: {suffix}")
    except ImportError as exc:
        raise ImportError(
            f"Failed to read {path}. Install the optional dependency required "
            f"for {suffix} files, or provide a CSV/TSV file. Original error: {exc}"
        ) from exc
    if nrows is not None:
        return df.head(nrows)
    return df


def make_empty_csv(path: str | Path, columns: list[str]) -> None:
    """Create an empty CSV with a stable schema."""
    safe_to_csv(pd.DataFrame(columns=columns), path, index=False)
