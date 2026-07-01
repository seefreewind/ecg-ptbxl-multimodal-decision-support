# BMC MIDM Stage 20 Final Upload Audit

## Output Files

- Final Word file: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE20_FINAL.docx`
- Audit file: `manuscript/BMC_MIDM_STAGE20_FINAL_UPLOAD_AUDIT.md`

## Citation-Order Fixes

- `[12,3]` remaining: 0; `[3,12]` present: 1.
- `[13–14]` remaining: 0; `[13,14]` present: 1.
- Reference order was not changed.

## Reference 15 Fix

- `Seyedi S, others` remaining: 0.
- `Seyedi S, et al.` present: 1.

## Author-Date Citation Search

- `et al.` in manuscript body before References: 0.
- Year-in-parentheses patterns in body: none.
- Author-date patterns such as `(Wagner...)`, `(Guo...)`, `(Vickers...)`: none.
- Result: no author-date citations remain in the manuscript body.

## Word Table Integrity

- Real Word table count: 7.
- Required tables present:
  - Table 1 Internal full-schema model performance: yes
  - Table 2 Statistical support for the internal multimodal gain: yes
  - Table 3 Gated fusion versus fair concat: yes
  - Table 4 Signal-only external validation: yes
  - Table 5 External signal-only calibration: yes
  - Table 6a Stage 14L reduced-schema internal results: yes
  - Table 6b Stage 14L external structured-feature coverage: yes
- Paragraph-level pipe-table artifact search: no Markdown pipe tables remain in the Word body.
- Note: audit scripts may display table cells joined by `|` for machine-readable inspection; these are real Word table cells, not Markdown table syntax.

## Figure File Audit

| Figure stem | Path | Format | Resolution | Readable | Suitable for separate upload |
|:---|:---|:---|:---|:---|:---|
| figure1_study_design_evidence_boundary | `manuscript/figures/figure1_study_design_evidence_boundary.png` | png | 3311x1530 | yes | yes |
| figure1_study_design_evidence_boundary | `manuscript/figures/figure1_study_design_evidence_boundary.pdf` | pdf | vector/pdf | yes | yes |
| figure1_study_design_evidence_boundary | `manuscript/figures/figure1_study_design_evidence_boundary.svg` | svg | vector/pdf | yes | yes |
| figure2_internal_model_performance | `manuscript/figures/figure2_internal_model_performance.png` | png | 3271x1645 | yes | yes |
| figure2_internal_model_performance | `manuscript/figures/figure2_internal_model_performance.pdf` | pdf | vector/pdf | yes | yes |
| figure2_internal_model_performance | `manuscript/figures/figure2_internal_model_performance.svg` | svg | vector/pdf | yes | yes |
| figure3_external_signal_only_validation | `manuscript/figures/figure3_external_signal_only_validation.png` | png | 2728x1604 | yes | yes |
| figure3_external_signal_only_validation | `manuscript/figures/figure3_external_signal_only_validation.pdf` | pdf | vector/pdf | yes | yes |
| figure3_external_signal_only_validation | `manuscript/figures/figure3_external_signal_only_validation.svg` | svg | vector/pdf | yes | yes |
| figure4_calibration_reliability | `manuscript/figures/figure4_calibration_reliability.png` | png | 4171x1254 | yes | yes |
| figure4_calibration_reliability | `manuscript/figures/figure4_calibration_reliability.pdf` | pdf | vector/pdf | yes | yes |
| figure4_calibration_reliability | `manuscript/figures/figure4_calibration_reliability.svg` | svg | vector/pdf | yes | yes |
| supp_figure_s1_stage14l_audit | `manuscript/figures/supp_figure_s1_stage14l_audit.png` | png | 4171x1384 | yes | yes |
| supp_figure_s1_stage14l_audit | `manuscript/figures/supp_figure_s1_stage14l_audit.pdf` | pdf | vector/pdf | yes | yes |
| supp_figure_s1_stage14l_audit | `manuscript/figures/supp_figure_s1_stage14l_audit.svg` | svg | vector/pdf | yes | yes |

- Result: no figure-file blocker detected for Figure 1-4 or Supplementary Figure S1.

## Supplementary Material Audit

- Supplementary Table S1: ready
  - `manuscript/tables/supp_table_external_per_class_diagnostics.csv`: exists
  - `manuscript/tables/supp_table_external_per_class_diagnostics.md`: exists
- Supplementary Table S2: ready
  - `tables/table_stage15_external_signal_calibration.csv`: exists
  - `tables/table_stage15_external_signal_reliability.csv`: exists
- Supplementary Table S3: ready
  - `tables/stage14l_feature_manifest.csv`: exists
  - `tables/stage14l_internal_results.csv`: exists
  - `tables/stage14l_external_results.csv`: exists
- Supplementary Figure S1: ready
  - `manuscript/figures/supp_figure_s1_stage14l_audit.png`: exists
  - `manuscript/figures/supp_figure_s1_stage14l_audit.pdf`: exists
  - `manuscript/figures/supp_figure_s1_stage14l_audit.svg`: exists
- Supplementary Figure S2 removed from final Word package: yes.

## Link Audit

- https://physionet.org/content/ptb-xl/: present
- https://physionet.org/content/ptb-xl-plus/: present
- http://2018.icbeb.org/Challenge.html: present
- https://physionet.org/content/ecg-arrhythmia/: present
- https://github.com/seefreewind/ecg-ptbxl-multimodal-decision-support: present
- https://doi.org/10.5281/zenodo.21091784: present

## Claim Audit

| Phrase | Count | Status |
|:---|---:|:---|
| external multimodal validation | 11 | acceptable; explicitly negated or framed as NO-GO/limitation |
| clinically ready | 0 | not present |
| clinically validated | 0 | not present |
| clinical deployment | 2 | acceptable; used only to state no deployment claim |
| deployable | 0 | not present |
| real-world deployment | 0 | not present |
| clinical utility proven | 0 | not present |
| clinically meaningful improvement | 0 | not present |
| gated fusion superiority | 0 | not present |
| superior gated fusion | 0 | not present |
| robust clinical utility | 0 | not present |
| infeasible | 0 | not present |

- Required boundary sentence retained: yes.

## BMC Compliance Audit

- Required sections missing: none.
- Required declaration subsections missing: none.
- Structured abstract contains Background, Methods, Results, and Conclusions.
- Keywords are present and within the 3-10 keyword range.

## Remaining Upload Blockers

- No figure-file or scientific-content blocker detected.
- Remaining items are administrative: final manual author confirmation and BMC portal upload details.

## Final Quality Gate

Stage 20 is GO for BMC MIDM portal upload, subject to final author confirmation and portal-specific upload steps.
