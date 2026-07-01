# BMC MIDM Stage 26 Reviewer-Risk Revision Log

## Output
- Revised Word manuscript: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE26_REVIEWER_RISK_REVISED.docx`
- This summary: `manuscript/BMC_MIDM_STAGE26_REVIEWER_RISK_REVISION_LOG.md`
- Added threshold diagnostic table: `manuscript/tables/supp_table_s10_reduced_schema_internal_threshold_diagnostics.csv`

## Changes made
- Softened abstract wording so the two-record external structured joinability result is not over-positioned as a biological or algorithmic proof.
- Reframed the external structured-feature result as a current extraction-and-joining feasibility boundary, not proof that external PTB-XL+-compatible reconstruction is impossible in principle.
- Added a strict-tolerance caveat for the 1e-6 concordance rule and explicitly named tolerance-sensitivity and 138-feature control analyses as future checks rather than completed results.
- Clarified that reduced-schema degradation may reflect information loss from feature removal as well as reproducibility constraints.
- Added an explicit gated-fusion F1 note distinguishing Table 1 default-threshold F1, temperature-scaled full-coverage F1, and retained-subset uncertainty F1.
- Added a Discussion sentence noting that internal multimodal gain is concentrated most clearly in HYP.
- Replaced internal code names in Table 6a with manuscript-readable model names.
- Unified residual `fair` terminology toward `matched concat` / `matched comparison`.
- Replaced `Risk stratification` keyword with `Evidence boundary`.
- Added supported training details: sigmoid multi-label outputs, BCE-with-logits, AdamW, max epochs, early-stopping patience, and seeds.

- Added waveform preprocessing details for WFDB loading, per-record lead standardization, and ECGdeli audit filtering/delineation steps.

## Not done
- No new ECGdeli external extraction was claimed.
- No tolerance-sensitivity result was fabricated.
- No random-138 or importance-138 feature-control result was fabricated.
- No external multimodal validation claim was added.
