# Figure Master Plan

## Figure 1. Overall framework

Purpose:
Show the ECG waveform branch, PTB-XL+ structured feature branch, fair fusion interface, calibration, uncertainty triage, and XAI decision-support workflow.

Panels:

- A. Dataset resource: PTB-XL waveform + PTB-XL+ structured ECG features
- B. Official split and leakage-safe processing
- C. Fair model comparison pipeline
- D. Decision-support layer: calibration, uncertainty triage, XAI, DCA, external validation

Required source data:

- `figures/source_data/fig1_framework_nodes.csv`
- `figures/source_data/fig1_framework_edges.csv`

## Figure 2. Fair multimodal performance

Panels:

- A. Main model performance with bootstrap CI
- B. Per-class dot plot
- C. Paired bootstrap gated vs fair concat
- D. Strong signal-only vs fair concat vs gated fusion

Required source data:

- `figures/source_data/fig2_model_performance_long.csv`
- `figures/source_data/fig2_per_class_dotplot.csv`
- `figures/source_data/fig2_paired_bootstrap.csv`

## Figure 3. Ablation and modality complementarity

Panels:

- A. Signal embedding MLP
- B. Structured MLP
- C. Fair MLP-concat
- D. Gated fusion
- E. Prediction and error similarity matrix

Required source data:

- `figures/source_data/fig3_ablation_long.csv`
- `figures/source_data/fig3_prediction_similarity_matrix.csv`

## Figure 4. Calibration and reliability

Panels:

- A. Raw vs temperature-scaled ECE
- B. Raw vs temperature-scaled Brier
- C. Reliability curve
- D. Confidence histogram

Required source data:

- `figures/source_data/fig4_calibration_long.csv`
- `figures/source_data/fig4_reliability_curve.csv`
- `figures/source_data/fig4_confidence_histogram.csv`

## Figure 5. Uncertainty triage

Panels:

- A. Risk-coverage AUROC
- B. Risk-coverage F1
- C. Referral fraction vs retained performance
- D. Referred subset characteristics

Required source data:

- `figures/source_data/fig5_uncertainty_risk_coverage.csv`
- `figures/source_data/fig5_referred_subset_characteristics.csv`

## Figure 6. Dual-modality XAI cases

Panels:

- A. High-confidence retained correct case
- B. Low-confidence referred incorrect case
- C. Structured feature attribution
- D. Signal waveform heatmap

Required source data:

- `figures/source_data/fig6_xai_case_source_data.csv`
- `figures/source_data/fig6_structured_feature_group_attribution.csv`
- `figures/source_data/fig6_signal_heatmap_index.csv`

## Figure 7. Modality interaction and gate analysis

Panels:

- A. Gate weight distribution
- B. Gate weight retained vs referred
- C. Gate weight correct vs incorrect
- D. Label-specific modality reliance

Required source data:

- `figures/source_data/fig7_gate_weight_modality_interaction.csv`

## Supplementary Source Data

Supplementary tables retain all-class, all-model, all-coverage, and all-feature details for later manuscript and supplementary-material assembly.

Required source data:

- `figures/source_data/supplementary/supp_table_all_model_metrics.csv`
- `figures/source_data/supplementary/supp_table_all_per_class_metrics.csv`
- `figures/source_data/supplementary/supp_table_all_uncertainty_scores.csv`
- `figures/source_data/supplementary/supp_table_all_calibration_bins.csv`
- `figures/source_data/supplementary/supp_table_all_bootstrap_ci.csv`
- `figures/source_data/supplementary/supp_table_all_thresholds.csv`

## Narrative Guardrails

- Do not claim clinical readiness.
- Do not claim gated fusion is statistically superior to fair concat.
- Emphasize fair multimodal complementarity.
- Frame uncertainty triage as decision support with clinician referral.
- Frame XAI as post-hoc attribution for transparency and auditing.

## Figure 8. Decision curve analysis

Panels:

- A. Macro net benefit across threshold probabilities
- B. Label-wise DCA
- C. Fair concat vs gated fusion DCA
- D. DCA in 80% high-confidence retained subset

Required source data:

- `figures/source_data/fig8_dca_macro.csv`
- `figures/source_data/fig8_dca_by_label.csv`
- `figures/source_data/fig8_dca_retained_80_coverage.csv`

## Figure 9. External validation readiness and label compatibility

Panels:
A. External dataset availability
B. Label mapping confidence
C. Waveform compatibility
D. Recommended validation mode

Required source data:
- figures/source_data/fig9_external_validation_readiness.csv
- figures/source_data/fig9_external_label_mapping.csv

Note:
Figure 9 is a readiness and compatibility audit, not an external validation result figure.

