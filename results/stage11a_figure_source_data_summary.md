# Stage 11A Figure Source-Data Summary

## 1. Stage Status

- status: completed
- new model training: no
- model retuning: no
- DCA performed: no
- external validation performed: no
- manuscript writing performed: no

Stage 11A organized the existing PTB-XL/PTB-XL+ results into a resource-style figure system: data resource, fair multimodal comparison, calibration, uncertainty triage, and post-hoc XAI source data.

## 2. Figure Master Plan

Output:

- `docs/FIGURE_MASTER_PLAN.md`

Planned main figures:

- Figure 1. Overall framework
- Figure 2. Fair multimodal performance
- Figure 3. Ablation and modality complementarity
- Figure 4. Calibration and reliability
- Figure 5. Uncertainty triage
- Figure 6. Dual-modality XAI cases
- Figure 7. Modality interaction and gate analysis

Planned supplementary tables:

- all model metrics
- all per-class metrics
- all uncertainty scores
- all calibration bins
- all bootstrap CIs
- all thresholds

Current ready figures/source data:

- Figures 1-7 source data: ready
- Draft Figures 2-5: generated

Pending figure interfaces:

- DCA: pending
- external validation: pending

## 3. Source Data Generated

Manifest:

- `figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv`

Main source-data files:

- `figures/source_data/fig1_framework_nodes.csv`
- `figures/source_data/fig1_framework_edges.csv`
- `figures/source_data/fig2_model_performance_long.csv`
- `figures/source_data/fig2_per_class_dotplot.csv`
- `figures/source_data/fig2_paired_bootstrap.csv`
- `figures/source_data/fig3_ablation_long.csv`
- `figures/source_data/fig3_prediction_similarity_matrix.csv`
- `figures/source_data/fig4_calibration_long.csv`
- `figures/source_data/fig4_reliability_curve.csv`
- `figures/source_data/fig4_confidence_histogram.csv`
- `figures/source_data/fig5_uncertainty_risk_coverage.csv`
- `figures/source_data/fig5_referred_subset_characteristics.csv`
- `figures/source_data/fig6_xai_case_source_data.csv`
- `figures/source_data/fig6_structured_feature_group_attribution.csv`
- `figures/source_data/fig6_signal_heatmap_index.csv`
- `figures/source_data/fig7_gate_weight_modality_interaction.csv`

Supplementary source-data files:

- `figures/source_data/supplementary/supp_table_all_model_metrics.csv`
- `figures/source_data/supplementary/supp_table_all_per_class_metrics.csv`
- `figures/source_data/supplementary/supp_table_all_uncertainty_scores.csv`
- `figures/source_data/supplementary/supp_table_all_calibration_bins.csv`
- `figures/source_data/supplementary/supp_table_all_bootstrap_ci.csv`
- `figures/source_data/supplementary/supp_table_all_thresholds.csv`

## 4. Main Figures Generated

Draft figures:

- `figures/main/fig2_model_performance.png`
- `figures/main/fig2_model_performance.svg`
- `figures/main/fig3_ablation_complementarity.png`
- `figures/main/fig3_ablation_complementarity.svg`
- `figures/main/fig4_calibration.png`
- `figures/main/fig4_calibration.svg`
- `figures/main/fig5_uncertainty_triage.png`
- `figures/main/fig5_uncertainty_triage.svg`

Framework draft:

- `figures/fig1_framework_draft.mmd`

Figure 6 and Figure 7 source data are ready because Stage 11 XAI and gate weights are complete. Draft assembled figures can be refined later from the generated source-data tables and existing XAI panels.

## 5. Pending Inputs

Ready:

- XAI source data
- gate weights
- calibration source data
- uncertainty triage source data

Pending:

- DCA
- external validation

## 6. Narrative Consistency Check

QC outputs:

- `results/figure_source_data_qc_report.md`
- `tables/table_figure_source_data_qc.csv`

QC status:

- failed checks: 0

Confirmed:

- no clinical-readiness claim
- no positive gated-superiority claim
- late-probability concat marked supplementary
- fair multimodal complementarity emphasized
- uncertainty triage framed as validation-cutoff / frozen-test decision support
- XAI framed as post-hoc analysis
- DCA and external validation explicitly marked pending

## 7. Code and Scripts

Code:

- `src/figures/build_figure_source_data.py`
- `src/figures/plot_main_figures.py`
- `src/figures/check_figure_source_data.py`
- `src/figures/ecg_feature_grouping.py`

Scripts:

- `scripts/12_build_figure_source_data.sh`
- `scripts/12b_plot_main_figures.sh`
- `scripts/12c_check_figure_source_data.sh`

## 8. Verification

Commands run:

```bash
bash scripts/12_build_figure_source_data.sh
bash scripts/12b_plot_main_figures.sh
bash scripts/12c_check_figure_source_data.sh
```

QC result:

```text
failed=0
```

## 9. Next Recommended Step

Proceed to DCA.

The figure source-data infrastructure is ready, and XAI is already complete. DCA should be added next as a decision-support utility analysis, still using conservative language and without clinical-readiness claims.
