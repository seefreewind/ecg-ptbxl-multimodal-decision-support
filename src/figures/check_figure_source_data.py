from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_READY_COLUMNS = {
    "fig2_model_performance_long.csv": {"model_name", "split", "metric", "estimate", "is_main_model"},
    "fig5_uncertainty_risk_coverage.csv": {"model_name", "split", "coverage", "cutoff_source", "retained_macro_auroc", "retained_macro_f1"},
}


def check_source_data() -> pd.DataFrame:
    source = Path("figures/source_data")
    manifest_path = source / "FIGURE_SOURCE_DATA_MANIFEST.csv"
    rows = []
    if not manifest_path.exists():
        rows.append({"check": "manifest_exists", "status": "failed", "details": "Missing manifest"})
        return pd.DataFrame(rows)
    manifest = pd.read_csv(manifest_path)
    rows.append({"check": "manifest_exists", "status": "passed", "details": str(manifest_path)})
    for item in manifest.to_dict("records"):
        status = str(item["status"])
        source_file = str(item["source_file"])
        if status.startswith("pending"):
            rows.append({"check": f"pending_allowed:{source_file}", "status": "passed", "details": status})
            continue
        path = Path(source_file)
        if not path.exists():
            rows.append({"check": f"source_exists:{source_file}", "status": "failed", "details": "missing"})
            continue
        try:
            df = pd.read_csv(path)
            nonempty = len(df) > 0
            rows.append({"check": f"source_nonempty:{source_file}", "status": "passed" if nonempty else "failed", "details": f"rows={len(df)}"})
            req = REQUIRED_READY_COLUMNS.get(path.name)
            if req:
                missing = sorted(req - set(df.columns))
                rows.append({"check": f"required_columns:{source_file}", "status": "passed" if not missing else "failed", "details": ",".join(missing)})
        except Exception as exc:
            rows.append({"check": f"source_readable:{source_file}", "status": "failed", "details": str(exc)})
    perf = pd.read_csv(source / "fig2_model_performance_long.csv")
    late = perf[perf["model_name"].eq("late_probability_concat")]
    rows.append({"check": "late_concat_supplementary", "status": "passed" if len(late) and not bool(late["is_main_model"].any()) else "failed", "details": "late_probability_concat must not be main"})
    notes = " ".join(manifest["notes"].fillna("").astype(str).tolist()).lower()
    forbidden_positive = ["gated outperforms concat", "gated is superior", "gated fusion is superior", "gated statistically superior"]
    rows.append({"check": "no_gated_superiority_claim", "status": "passed" if not any(term in notes for term in forbidden_positive) else "failed", "details": "No positive gated-superiority phrasing in manifest notes"})
    fig5 = pd.read_csv(source / "fig5_uncertainty_risk_coverage.csv")
    coverages = set(round(float(v), 1) for v in fig5["coverage"].unique())
    rows.append({"check": "fig5_coverage_complete", "status": "passed" if {1.0, 0.9, 0.8, 0.7, 0.6, 0.5}.issubset(coverages) else "failed", "details": str(sorted(coverages))})
    rows.append({"check": "fig5_validation_cutoff", "status": "passed" if set(fig5["cutoff_source"]) == {"validation"} else "failed", "details": str(set(fig5["cutoff_source"]))})
    if (source / "fig6_xai_case_source_data.csv").exists():
        xai = pd.read_csv(source / "fig6_xai_case_source_data.csv")
        note_text = " ".join(xai.get("notes", pd.Series(dtype=str)).fillna("").astype(str)).lower()
        rows.append({"check": "xai_posthoc_marked", "status": "passed" if "post-hoc" in note_text else "failed", "details": "XAI source notes should mark post-hoc"})
    return pd.DataFrame(rows)


def main() -> None:
    qc = check_source_data()
    Path("tables").mkdir(exist_ok=True)
    Path("results").mkdir(exist_ok=True)
    qc.to_csv("tables/table_figure_source_data_qc.csv", index=False)
    failed = qc[qc["status"].eq("failed")]
    lines = ["# Figure Source-Data QC Report", "", f"Total checks: {len(qc)}", f"Failed checks: {len(failed)}", ""]
    if len(failed):
        lines.append("## Failed Checks")
        lines.extend(f"- {row['check']}: {row['details']}" for _, row in failed.iterrows())
    else:
        lines.append("All checks passed.")
    Path("results/figure_source_data_qc_report.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote figure source-data QC report. failed={len(failed)}")


if __name__ == "__main__":
    main()
