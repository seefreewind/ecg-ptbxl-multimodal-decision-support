from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


LABELS = ["NORM", "MI", "STTC", "CD", "HYP"]
PRIMARY_MODEL = "gated_fusion_mlp"
PRIMARY_MODE = "temperature_scaled"
PRIMARY_SCORE = "entropy_macro"


def _thresholds() -> dict[str, float]:
    return json.loads(Path("results/internal/gated_fusion/gated_fusion_thresholds.json").read_text())


def _label_text(values: pd.Series) -> str:
    labels = [label for label in LABELS if int(values[f"y_true_{label}"]) == 1]
    return "|".join(labels) if labels else "none"


def _pred_text(values: pd.Series, thresholds: dict[str, float]) -> str:
    labels = [label for label in LABELS if float(values[f"prob_{label}"]) >= float(thresholds[label])]
    return "|".join(labels) if labels else "none"


def _is_correct(row: pd.Series, thresholds: dict[str, float]) -> bool:
    true = np.asarray([int(row[f"y_true_{label}"]) for label in LABELS])
    pred = np.asarray([float(row[f"prob_{label}"]) >= float(thresholds[label]) for label in LABELS], dtype=int)
    return bool(np.array_equal(true, pred))


def _append_cases(rows: list[dict[str, object]], frame: pd.DataFrame, case_type: str, n: int, reason: str, thresholds: dict[str, float]) -> None:
    existing = {int(row["ecg_id"]) for row in rows}
    for _, row in frame.iterrows():
        ecg_id = int(row["ecg_id"])
        if ecg_id in existing:
            continue
        correct = _is_correct(row, thresholds)
        rows.append(
            {
                "ecg_id": ecg_id,
                "case_type": case_type,
                "true_labels": _label_text(row),
                "predicted_labels": _pred_text(row, thresholds),
                "model_name": PRIMARY_MODEL,
                "probability_mode": PRIMARY_MODE,
                "uncertainty_score": float(row[PRIMARY_SCORE]),
                "confidence": float(row[f"confidence_from_{PRIMARY_SCORE}"]),
                "coverage_group": "80% validation-cutoff triage",
                "retained_or_referred": "retained" if bool(row["retained_80"]) else "referred",
                "correct_or_incorrect": "correct" if correct else "incorrect",
                "reason_for_selection": reason,
            }
        )
        existing.add(ecg_id)
        if sum(1 for item in rows if item["case_type"] == case_type) >= n:
            break


def select_xai_cases() -> pd.DataFrame:
    out_dir = Path("results/xai")
    out_dir.mkdir(parents=True, exist_ok=True)
    Path("tables").mkdir(exist_ok=True)
    scores = pd.read_csv("results/uncertainty/uncertainty_scores_test.csv")
    cutoffs = pd.read_csv("results/uncertainty/triage_cutoffs_validation.csv")
    thresholds = _thresholds()
    primary = scores[
        scores["model_name"].eq(PRIMARY_MODEL)
        & scores["probability_mode"].eq(PRIMARY_MODE)
    ].copy()
    cutoff80 = float(
        cutoffs[
            cutoffs["model_name"].eq(PRIMARY_MODEL)
            & cutoffs["probability_mode"].eq(PRIMARY_MODE)
            & cutoffs["uncertainty_score"].eq(PRIMARY_SCORE)
            & np.isclose(cutoffs["coverage"], 0.8)
        ]["validation_uncertainty_cutoff"].iloc[0]
    )
    primary["retained_80"] = primary[PRIMARY_SCORE] <= cutoff80
    primary["is_correct"] = primary.apply(lambda row: _is_correct(row, thresholds), axis=1)
    primary["n_true_labels"] = primary[[f"y_true_{label}" for label in LABELS]].sum(axis=1)

    fair = scores[scores["model_name"].eq("fair_concat_mlp") & scores["probability_mode"].eq(PRIMARY_MODE)].copy()
    fair_preds = fair.set_index("ecg_id")[[f"prob_{label}" for label in LABELS]]
    rows: list[dict[str, object]] = []
    retained = primary[primary["retained_80"]].sort_values(PRIMARY_SCORE, ascending=True)
    referred = primary[~primary["retained_80"]].sort_values(PRIMARY_SCORE, ascending=False)
    _append_cases(rows, retained[retained["is_correct"]], "high-confidence retained correct", 3, "Lowest-uncertainty retained correct examples.", thresholds)
    _append_cases(rows, retained[~retained["is_correct"]], "high-confidence retained incorrect", 2, "Retained examples with prediction errors for failure-mode auditing.", thresholds)
    _append_cases(rows, referred[~referred["is_correct"]], "low-confidence referred incorrect", 3, "Highest-uncertainty referred incorrect examples.", thresholds)
    _append_cases(rows, referred[referred["n_true_labels"] >= 2], "low-confidence referred multi-label abnormal", 2, "Referred multi-label abnormal ECGs.", thresholds)

    disagreement_ids = []
    for _, row in primary.iterrows():
        ecg_id = int(row["ecg_id"])
        if ecg_id not in fair_preds.index:
            continue
        gated_pred = np.asarray([float(row[f"prob_{label}"]) >= thresholds[label] for label in LABELS], dtype=int)
        fair_row = fair_preds.loc[ecg_id]
        fair_thresholds = json.loads(Path("results/internal/fair_concat/fair_concat_thresholds.json").read_text())
        fair_pred = np.asarray([float(fair_row[f"prob_{label}"]) >= fair_thresholds[label] for label in LABELS], dtype=int)
        if not np.array_equal(gated_pred, fair_pred):
            disagreement_ids.append(ecg_id)
    disagreement = primary[primary["ecg_id"].isin(disagreement_ids)].sort_values(PRIMARY_SCORE, ascending=False)
    _append_cases(rows, disagreement, "modality-disagreement case", 2, "Fair concat and gated fusion predicted different label sets.", thresholds)

    selected = pd.DataFrame(rows).head(12)
    selected.to_csv(out_dir / "xai_case_selection.csv", index=False)
    selected.to_csv("tables/table_xai_case_selection.csv", index=False)
    return selected


if __name__ == "__main__":
    out = select_xai_cases()
    print(f"Selected {len(out)} XAI cases.")
