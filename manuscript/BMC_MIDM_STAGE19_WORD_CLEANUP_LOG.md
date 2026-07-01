# BMC MIDM Stage 19 Word Cleanup Log

## Output

- Clean Word file: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE19_CLEAN.docx`

## Tables Converted

All Stage 19 result tables were generated as real Word tables rather than Markdown table text.

- Table 1 Internal full-schema model performance on the frozen PTB-XL/PTB-XL+ test set
- Table 2 Statistical support for the internal multimodal gain
- Table 3 Gated fusion versus fair concat on the frozen internal test set
- Table 4 Signal-only external validation
- Table 5 External signal-only calibration
- Table 6a Stage 14L reduced-schema internal results
- Table 6b Stage 14L external structured-feature coverage

## Citation Style Conversion

- In-text citations were converted from Markdown/BibTeX keys to Vancouver-style numerical square brackets.
- Reference list order was rebuilt by first appearance in the manuscript.
- No mixed author-date citation style is intended in the clean Word draft.

Reference order:

1. `wagner2020ptbxl`
2. `goldberger2000physionet`
3. `strodthoff2023ptbxlplus`
4. `guo2017calibration`
5. `brier1950verification`
6. `naeini2015calibration`
7. `gal2016dropout`
8. `geifman2017selective`
9. `lundberg2017shap`
10. `sundararajan2017integrated`
11. `vickers2006dca`
12. `pilia2021ecgdeli`
13. `liu2018cpsc`
14. `zheng2020chapman`
15. `alday2020physionet2020`
16. `he2016resnet`
17. `selvaraju2017gradcam`
18. `ghassemi2021xai`
19. `efron1993bootstrap`

## Figure Readability and File Readiness

- Figure 1 through Figure 4 and Supplementary Figure S1 were retained as embedded review figures.
- Separate high-resolution figure files exist as follows:

- `figure1_study_design_evidence_boundary`: figure1_study_design_evidence_boundary.png; figure1_study_design_evidence_boundary.pdf; figure1_study_design_evidence_boundary.svg
- `figure2_internal_model_performance`: figure2_internal_model_performance.png; figure2_internal_model_performance.pdf; figure2_internal_model_performance.svg
- `figure3_external_signal_only_validation`: figure3_external_signal_only_validation.png; figure3_external_signal_only_validation.pdf; figure3_external_signal_only_validation.svg
- `figure4_calibration_reliability`: figure4_calibration_reliability.png; figure4_calibration_reliability.pdf; figure4_calibration_reliability.svg
- `supp_figure_s1_stage14l_audit`: supp_figure_s1_stage14l_audit.png; supp_figure_s1_stage14l_audit.pdf; supp_figure_s1_stage14l_audit.svg

## Supplementary Figure S2 Decision

- Source file exists: `manuscript/figures/supp_figure_s2_xai_example.png` (yes).
- Decision: removed from the Stage 19 embedded clean submission copy because the review-copy image text is difficult to read at Word page scale.
- Status: optional, not retained in current submission package.

## Section Order and Declarations

- Required BMC section order was preserved: title page, structured abstract, keywords, background, methods, results, discussion, conclusions, abbreviations, declarations, references, figure legends, supplementary material list.
- Required declaration subsections are present: ethics approval and consent to participate; consent for publication; availability of data and materials; competing interests; funding; authors' contributions; acknowledgements.

## Claim Audit

| Phrase | Count | Status |
|:---|---:|:---|
| external multimodal validation | 11 | acceptable; explicitly stated as not performed/NO-GO |
| clinically ready | 0 | not present |
| clinically validated | 0 | not present |
| clinical deployment | 2 | acceptable boundary/limitation context |
| deployable | 0 | not present |
| real-world deployment | 0 | not present |
| clinical utility proven | 0 | not present |
| clinically meaningful improvement | 0 | not present |
| gated fusion superiority | 0 | not present |
| superior gated fusion | 0 | not present |
| robust clinical utility | 0 | not present |
| infeasible | 0 | not present |

The explicit statement `No external multimodal validation was performed.` was retained.

## Remaining Blockers Before Submission

- Final manual author confirmation.
- Journal portal upload details.
