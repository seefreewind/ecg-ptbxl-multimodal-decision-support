from __future__ import annotations

import ast
from typing import Iterable

import pandas as pd

DEFAULT_SUPERCLASSES = ["NORM", "MI", "STTC", "CD", "HYP"]


def parse_scp_codes(value) -> dict:
    """Parse PTB-XL scp_codes safely.

    PTB-XL stores SCP likelihoods as a string representation of a dict. Invalid
    or empty values are treated as no labels so callers can continue and report
    parse issues separately if needed.
    """
    if pd.isna(value):
        return {}
    if isinstance(value, dict):
        return value
    text = str(value).strip()
    if not text:
        return {}
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _normalise_code(value) -> str:
    return str(value).strip()


def _find_code_column(df: pd.DataFrame) -> str:
    candidates = ["scp_code", "SCP Code", "code", "Code", "index", "Unnamed: 0"]
    for col in candidates:
        if col in df.columns:
            return col
    return df.columns[0]


def _prepare_scp_statements(scp_statements_df: pd.DataFrame) -> pd.DataFrame:
    df = scp_statements_df.copy()
    # In the official file, the SCP code is often the CSV index when loaded with
    # index_col=0. Resetting preserves both indexed and ordinary CSV forms.
    if "diagnostic_class" not in df.columns and df.index.name == "diagnostic_class":
        df = df.reset_index()
    elif not any(col in df.columns for col in ["scp_code", "code", "index", "Unnamed: 0"]):
        df = df.reset_index()
    return df


def build_scp_to_superclass_map(scp_statements_df: pd.DataFrame) -> dict[str, str]:
    """Build SCP code -> PTB-XL diagnostic superclass mapping."""
    df = _prepare_scp_statements(scp_statements_df)
    if "diagnostic_class" not in df.columns:
        return {}
    code_col = _find_code_column(df)
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        code = _normalise_code(row.get(code_col, ""))
        superclass = row.get("diagnostic_class", "")
        if pd.isna(superclass):
            continue
        superclass = str(superclass).strip()
        if code and superclass:
            mapping[code] = superclass
    return mapping


def build_ptbxl_superclass_labels(
    metadata_df: pd.DataFrame,
    scp_statements_df: pd.DataFrame,
    classes: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Create PTB-XL diagnostic superclass multi-label dataframe.

    Returns columns: ecg_id, NORM, MI, STTC, CD, HYP by default.
    """
    classes = list(classes or DEFAULT_SUPERCLASSES)
    if "ecg_id" not in metadata_df.columns:
        raise ValueError("metadata_df must contain column 'ecg_id'.")
    if "scp_codes" not in metadata_df.columns:
        raise ValueError("metadata_df must contain column 'scp_codes'.")

    scp_to_superclass = build_scp_to_superclass_map(scp_statements_df)
    rows = []
    for _, row in metadata_df.iterrows():
        labels = {label: 0 for label in classes}
        scp_codes = parse_scp_codes(row.get("scp_codes"))
        for code in scp_codes.keys():
            superclass = scp_to_superclass.get(_normalise_code(code))
            if superclass in labels:
                labels[superclass] = 1
        labels["ecg_id"] = row["ecg_id"]
        rows.append(labels)

    out = pd.DataFrame(rows)
    return out[["ecg_id"] + classes]


def count_scp_parse_failures(metadata_df: pd.DataFrame) -> int:
    """Count non-empty scp_codes values that cannot be parsed into dicts."""
    if "scp_codes" not in metadata_df.columns:
        return 0
    failures = 0
    for value in metadata_df["scp_codes"]:
        if pd.isna(value) or str(value).strip() == "":
            continue
        if parse_scp_codes(value) == {}:
            try:
                parsed = ast.literal_eval(str(value))
            except (ValueError, SyntaxError):
                failures += 1
                continue
            if not isinstance(parsed, dict):
                failures += 1
    return failures
