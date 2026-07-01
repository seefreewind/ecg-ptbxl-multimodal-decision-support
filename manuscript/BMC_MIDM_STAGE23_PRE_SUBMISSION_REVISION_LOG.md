# BMC MIDM Stage 23 Pre-Submission Revision Log

## Purpose

This revision responds to reviewer-style pre-submission comments on the Stage 22 BMC-compliant manuscript.

## Main Changes Implemented

- Revised abstract Results to report internal fair-concat values and replace engineering terms.
- Replaced paragraph: The evaluation was staged. Stage 0/1 verified PTB-XL local d...
- Replaced paragraph: Stage 14L structured-feature reproducibility audit...
- Replaced paragraph: Stage 14L was treated as a core reproducibility and feasibil...
- Replaced paragraph: The go/no-go rule was conservative. External multimodal vali...
- Replaced paragraph: These results provide statistical support for the internal m...
- Replaced paragraph: Uncertainty triage, XAI, and exploratory decision-curve anal...
- Replaced paragraph: These results should be reported as transparent calibration ...
- Replaced paragraph: Stage 14L found that only 138 structured features were avail...
- Replaced paragraph: The Stage 14L decision was NO-GO for external multimodal val...
- Replaced paragraph: Stage 14L is a key BMC MIDM-compatible contribution because ...
- Replaced paragraph: The study's main strength is transparent boundary-setting. I...
- Replaced paragraph: Several limitations should be emphasized. First, all analyse...
- Added split sizes, macro-metric definition, bootstrap replicates, and CI method.
- Expanded Chapman-Shaoxing low-prevalence and label-comparability caveat.
- Added practical-magnitude interpretation for internal multimodal gain.
- Added label-shift interpretation in Discussion.
- Added supplementary table pointers for uncertainty, DCA, and XAI.
- Replaced 8 remaining occurrence(s) of 'Stage 14L'.
- Replaced 1 remaining occurrence(s) of 'allclose'.
- Replaced 1 remaining occurrence(s) of 'NO-GO'.

## Evidence Boundary Preserved

- Internal PTB-XL/PTB-XL+ full-schema multimodal evidence remains the only multimodal performance evidence.
- External evidence remains signal-only for CPSC2018 and Chapman-Shaoxing.
- The structured-feature reproducibility audit remains a feasibility/reproducibility finding, not an external multimodal result.
- The revision does not claim gated-fusion superiority, exact external PTB-XL+ reconstruction, external multimodal validation, or clinical deployment readiness.

## Items Deliberately Left For Later

- A broader literature-expansion pass was not performed in this stage, because adding new recent ECG/multimodal references requires a separate citation-verification pass.
- No new XAI figure was added; existing XAI outputs are now reported as supplementary audit tables because the previous figure was not readable at submission scale.

## Generated Files

- Revised Word manuscript: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE23_PRE_SUBMISSION_REVISED.docx`
- Revision log: `manuscript/BMC_MIDM_STAGE23_PRE_SUBMISSION_REVISION_LOG.md`
- Supplemental table copy: `manuscript/tables/supp_table_s4_uncertainty_triage.csv`
- Supplemental table copy: `manuscript/tables/supp_table_s5_dca_summary.csv`
- Supplemental table copy: `manuscript/tables/supp_table_s6_xai_case_attribution_audit.csv`
