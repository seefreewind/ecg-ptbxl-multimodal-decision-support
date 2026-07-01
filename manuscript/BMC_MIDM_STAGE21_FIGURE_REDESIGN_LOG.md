# BMC MIDM Stage 21 Figure Redesign Log

## Figure Contract

- Core conclusion: the manuscript supports internal multimodal complementarity, signal-only external validation, and a structured-feature reproducibility NO-GO boundary for external multimodal validation.
- Backend: Python/matplotlib only.
- Evidence boundary unchanged: no external multimodal validation, no gated fusion superiority, and no clinical deployment/readiness claim.

## Redesigned Figures

### Figure 1

- Source data used: Manuscript evidence-boundary design, PTB-XL/PTB-XL+ and external validation role definitions.
- Output files:
  - `manuscript/figures_redesigned/figure1_evidence_boundary_graphical_abstract.png` (5000x3003px)
  - `manuscript/figures_redesigned/figure1_evidence_boundary_graphical_abstract.pdf`
  - `manuscript/figures_redesigned/figure1_evidence_boundary_graphical_abstract.svg`
- Submission-ready: yes.

### Figure 2

- Source data used: Internal model performance values and paired bootstrap CIs from manuscript/tables/table_internal_multimodal_gain_bootstrap.csv plus locked manuscript values.
- Output files:
  - `manuscript/figures_redesigned/figure2_internal_performance_bootstrap.png` (4625x2725px)
  - `manuscript/figures_redesigned/figure2_internal_performance_bootstrap.pdf`
  - `manuscript/figures_redesigned/figure2_internal_performance_bootstrap.svg`
- Submission-ready: yes.

### Figure 3

- Source data used: tables/table_external_signal_results.csv and manuscript/tables/supp_table_external_per_class_diagnostics.csv.
- Output files:
  - `manuscript/figures_redesigned/figure3_external_signal_validation_diagnostics.png` (4459x2229px)
  - `manuscript/figures_redesigned/figure3_external_signal_validation_diagnostics.pdf`
  - `manuscript/figures_redesigned/figure3_external_signal_validation_diagnostics.svg`
- Submission-ready: yes.

### Figure 4

- Source data used: figures/source_data/fig4_calibration_long.csv, results/calibration/reliability_curve_source_data.csv, and tables/table_stage15_external_signal_calibration.csv.
- Output files:
  - `manuscript/figures_redesigned/figure4_calibration_reliability_distribution_shift.png` (4780x2005px)
  - `manuscript/figures_redesigned/figure4_calibration_reliability_distribution_shift.pdf`
  - `manuscript/figures_redesigned/figure4_calibration_reliability_distribution_shift.svg`
- Submission-ready: yes.

### Supplementary Figure S1

- Source data used: tables/stage14l_internal_results.csv, tables/stage14l_external_results.csv, and Stage 14L locked audit values.
- Output files:
  - `manuscript/figures_redesigned/supp_figure_s1_stage14l_reproducibility_audit.png` (4492x2350px)
  - `manuscript/figures_redesigned/supp_figure_s1_stage14l_reproducibility_audit.pdf`
  - `manuscript/figures_redesigned/supp_figure_s1_stage14l_reproducibility_audit.svg`
- Submission-ready: yes.

## XAI Figure Decision

- Supplementary Figure S2 was not retained in the redesigned submission package.
- Existing XAI source data and heatmap images remain available, but the prior review-copy figure was not sufficiently readable at Word/page scale.
- No speculative XAI figure was created.

## Updated Word Manuscript

- Updated Word file with redesigned embedded previews: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE21_FIGURE_REDESIGNED.docx`
- Figure legends were updated to match the redesigned figures.
- Informal wording such as optional, draft, candidate, or review copy was not used in figure headings.
- Word render QA completed in `manuscript/render_qa/stage21/`; no page-level figure overlap or retained Supplementary Figure S2 was detected.
- Embedded Word figures are preview versions for manuscript readability. Separate high-resolution PNG/PDF/SVG files in `manuscript/figures_redesigned/` should be used for journal figure upload.

## Missing Source Data

- None for redesigned Figure 1-4 or Supplementary Figure S1.

## Remaining Figure Blockers

- None for the required redesigned figure package.
