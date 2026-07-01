# Manuscript Draft Audit

Date: 2026-06-30

## Files Created

- `manuscript/ECG_PTBXL_MANUSCRIPT_DRAFT.md`
- `manuscript/PROJECT_MANUSCRIPT_RULES.md`
- `manuscript/MANUSCRIPT_DRAFT_AUDIT.md`

## Draft Status

- Draft type: BMC-style public-data research article.
- Current title: Reproducibility-Aware Multimodal ECG Risk Stratification with Signal-Level External Validation.
- Current evidence framing: internal PTB-XL/PTB-XL+ multimodal evaluation plus signal-only external validation plus Stage 14L reproducibility audit.
- External multimodal validation: NO-GO and not claimed as completed.

## Boundary Checks

- Abstract contains no literature citation markers.
- Methods contains no literature citation markers.
- Results contains no literature citation markers.
- External evidence is described as signal-only for CPSC2018 and Chapman-Shaoxing.
- Stage 14L is described as a reproducibility and feasibility audit.
- Gated fusion is not described as superior to fair concat.
- Clinical readiness, clinical deployment, and clinical validation are not claimed.
- Exact external PTB-XL+ 531-column reconstruction is not claimed.

## Manuscript Content Checks

- Internal full-schema multimodal gain is reported with frozen PTB-XL/PTB-XL+ test metrics.
- Methods now distinguish the early signal baseline from the strong signal-only model and the fair 256-dimensional signal-embedding interface.
- Methods now state that the fair fusion dataset combines 256 signal-embedding dimensions with 531 released PTB-XL+ structured features.
- Gated versus fair concat paired-bootstrap null result is reported conservatively.
- Internal calibration and exploratory DCA are reported without clinical overclaim.
- CPSC2018 and Chapman-Shaoxing signal-only external metrics are reported.
- Chapman-Shaoxing low AP/F1 caveat is linked to prevalence, label mapping, and validation-threshold transfer.
- Stage 14L reduced-schema internal collapse and external coverage failure are reported as NO-GO.
- Draft tables are embedded for internal performance, gated-versus-concat bootstrap, signal-only external validation, external signal calibration, and Stage 14L reproducibility audit.

## Items Still Requiring Author Completion

- Author list and affiliations.
- Acknowledgements.
- Author contributions.
- Funding statement.
- Competing interest confirmation.
- Target-journal-specific ethics/data availability wording.
- Final reference verification and formatting for the selected journal.
- Figure and table placement after selecting final main and supplementary items.

## Drafting Decision

GO for human review and manuscript drafting refinement. The current draft is content-only and intentionally conservative. It should not yet be treated as submission-ready formatting.
