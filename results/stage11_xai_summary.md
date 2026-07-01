# Stage 11 Dual-Modality XAI Summary

## 1. Stage Status

- status: completed
- DCA performed: no
- external validation performed: no
- manuscript writing performed: no
- model retraining performed: no

Stage 11 generated post-hoc explanations for selected high-confidence retained cases and low-confidence referred cases. The outputs support model transparency and auditing under the decision-support workflow, but they do not establish clinical readiness or causal explanations.

## 2. Models Explained

Main/auxiliary models:

- `strong_signal_only`: signal-side waveform attribution
- `structured_mlp`: structured-only feature attribution
- `fair_concat_mlp`: structured branch attribution within fair multimodal concat
- `gated_fusion_mlp`: structured branch attribution, unified case explanations, and gate weight analysis

## 3. Case Selection

Output:

- `results/xai/xai_case_selection.csv`
- `tables/table_xai_case_selection.csv`

Selected cases:

- total cases: 12
- retained cases: 5
- referred cases: 7
- correct cases: 5
- incorrect cases: 7

Case types:

- high-confidence retained correct: 3
- high-confidence retained incorrect: 2
- low-confidence referred incorrect: 3
- low-confidence referred multi-label abnormal: 2
- modality-disagreement case: 2

The selected set intentionally includes errors and referred cases for failure-mode auditing rather than only successful examples.

## 4. Structured Feature Attribution

Method used:

- `gradient_x_input`

Reason:

- This is a deterministic fallback method that works directly with the frozen PyTorch checkpoints.
- SHAP was not required for this stage.

Outputs:

- `results/xai/structured_attribution_values.csv`
- `results/xai/structured_case_attributions.csv`
- `tables/table_top_structured_features_global.csv`
- `tables/table_top_structured_features_by_label.csv`
- `figures/xai/structured_feature_importance_global.png`
- `figures/xai/structured_feature_importance_by_label.png`
- per-case structured waterfall plots in `figures/xai/`

Top global gated-fusion structured features among selected cases:

| rank | feature | mean absolute attribution |
|---:|---|---:|
| 1 | R_Amp_V6 | 0.052918 |
| 2 | R_Amp_V5 | 0.044989 |
| 3 | P_Morph_V2_iqr | 0.037353 |
| 4 | R_Amp_I | 0.035150 |
| 5 | T_Amp_V4_iqr | 0.034019 |
| 6 | S_Amp_V5 | 0.033907 |
| 7 | R_Amp_aVL | 0.033897 |
| 8 | S_Amp_aVR | 0.033399 |
| 9 | P_Amp_II | 0.032839 |
| 10 | R_Amp_V1 | 0.032510 |

Leakage note:

- The structured attribution code uses the 531 `struct_` ecgdeli feature columns from the leakage-safe processed table.
- Label, diagnostic statement, SNOMED, SCP, and target-style columns are not included in the attribution feature set.

## 5. Signal Attribution

Method used:

- `saliency_gradient_x_input`

Outputs:

- `results/xai/signal_attribution_values.npz`
- `results/xai/signal_case_attribution_summary.csv`
- `tables/table_signal_lead_importance.csv`
- per-case 12-lead signal heatmaps in `figures/xai/case_<ecg_id>_signal_heatmap.png`

Each signal heatmap contains the 12-lead ECG waveform with a post-hoc attribution overlay. These saliency maps are useful for model auditing but should not be interpreted as causal physiological proof.

## 6. Gate Weight Analysis

Gate weights exported:

- yes

Outputs:

- `results/xai/gated_gate_weights_test.csv`
- `tables/table_gate_weight_summary.csv`
- `figures/xai/gate_weight_distribution.png`

Gate summary at 80% uncertainty triage:

| group | n | mean signal gate | signal gate SD | mean structured gate |
|---|---:|---:|---:|---:|
| retained | 1757 | 0.694655 | 0.043220 | 0.305345 |
| referred | 441 | 0.702257 | 0.044736 | 0.297743 |

Interpretation:

- The gated model shows a higher average signal-branch weight than structured-branch weight in both retained and referred groups.
- The retained vs referred difference is small.
- Gate weights indicate relative model branch weighting, not clinical causal importance.

## 7. Unified Case Explanations

Outputs:

- `results/xai/unified_case_explanations.csv`
- `tables/table_unified_xai_cases.csv`
- `figures/xai/unified_case_<ecg_id>.png`
- `figures/xai/fig_xai_representative_cases.png`
- `results/xai/xai_plot_source_data.csv`

Each unified case includes:

- true labels
- predicted labels
- retained/referred status
- uncertainty score
- top structured features
- top signal leads
- gate signal/structured weights
- interpretation note
- failure note for incorrect cases

## 8. XAI and Uncertainty Link

Outputs:

- `tables/table_xai_uncertainty_link.csv`
- `figures/xai/xai_uncertainty_examples.png`

Observed pattern:

- High-confidence retained cases and low-confidence referred cases both produce identifiable structured and signal attributions.
- Low-confidence referred examples include more prediction errors and multi-label abnormal ECGs, matching the Stage 10 triage finding that referred ECGs are harder.
- Attribution concentration and gate weights do not by themselves prove clinical interpretability; they provide audit evidence for the decision-support workflow.

## 9. Generated Files

Code:

- `src/explainability/select_xai_cases.py`
- `src/explainability/structured_attribution.py`
- `src/explainability/signal_attribution.py`
- `src/explainability/unified_explanation.py`
- `src/explainability/export_gate_weights.py`

Scripts:

- `scripts/11a_select_xai_cases.sh`
- `scripts/11b_run_structured_attribution.sh`
- `scripts/11c_run_signal_attribution.sh`
- `scripts/11d_build_unified_xai_reports.sh`
- `scripts/11e_export_gated_gate_weights.sh`

Results and tables:

- `results/xai/xai_case_selection.csv`
- `results/xai/structured_attribution_values.csv`
- `results/xai/structured_case_attributions.csv`
- `results/xai/signal_attribution_values.npz`
- `results/xai/signal_case_attribution_summary.csv`
- `results/xai/gated_gate_weights_test.csv`
- `results/xai/unified_case_explanations.csv`
- `tables/table_xai_case_selection.csv`
- `tables/table_top_structured_features_global.csv`
- `tables/table_top_structured_features_by_label.csv`
- `tables/table_signal_lead_importance.csv`
- `tables/table_gate_weight_summary.csv`
- `tables/table_unified_xai_cases.csv`
- `tables/table_xai_uncertainty_link.csv`

Figures:

- `figures/xai/fig_xai_representative_cases.png`
- `figures/xai/structured_feature_importance_global.png`
- `figures/xai/structured_feature_importance_by_label.png`
- `figures/xai/gate_weight_distribution.png`
- `figures/xai/xai_uncertainty_examples.png`
- per-case signal heatmaps and structured waterfall plots in `figures/xai/`

## 10. Interpretation

The XAI analysis provides post-hoc evidence about which waveform leads/segments and structured ECG features contributed to selected model predictions. It supports transparency and model auditing within the proposed decision-support workflow.

Attribution does not prove causality. The outputs should not be described as clinically validated explanations, and no clinical-readiness claim is made.

The results are consistent with the revised project narrative:

- multimodal models provide useful decision-support behavior;
- uncertainty triage identifies high-confidence and low-confidence groups;
- XAI gives audit trails for representative retained and referred cases;
- gated fusion should still not be framed as definitively superior to fair concat.

## 11. Next Recommended Step

Proceed to DCA.

Before DCA, optionally inspect the representative XAI figures manually and choose the cleanest cases for eventual manuscript figures.
