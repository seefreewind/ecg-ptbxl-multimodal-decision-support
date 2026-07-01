# Manuscript-Ready Audit

Date: 2026-06-30

Stage 15 drafting decision: GO for drafting

## Completed files

- `tables/table_stage15_external_signal_per_class_diagnostics.csv`
- `tables/table_stage15_external_signal_calibration.csv`
- `tables/table_stage15_external_signal_reliability.csv`
- `tables/table_manuscript_claim_support.csv`
- `docs/MANUSCRIPT_RESULT_BOUNDARIES.md`
- `docs/MANUSCRIPT_TITLE_ABSTRACT_FRAMING.md`
- `tables/table_figure_table_source_map.csv`
- `MANUSCRIPT_READY_AUDIT.md`

## Diagnostics generated

- External per-class diagnostic rows: 5
- External calibration dataset rows: 2
- CPSC2018 and Chapman-Shaoxing remain signal-only external evaluations.
- Temperature scaling was fitted on internal validation; external data were evaluation-only.

## Missing artifacts

- No required signal-only external prediction artifact was missing.
- Exact PTB-XL+ external 531-column structured feature tables remain unavailable.
- External signal embeddings for fair concat external evaluation were not available and were not fabricated.

## Claims downgraded or forbidden

| claim_id   | manuscript_claim                                                                                    | allowed_location   | final_status   |
|:-----------|:----------------------------------------------------------------------------------------------------|:-------------------|:---------------|
| C08        | DCA provides exploratory internal decision-curve evidence.                                          | supplement         | allowed        |
| C12        | Stage 14L reduced-schema structured-only performance collapses internally.                          | supplement         | allowed        |
| C13        | Stage 14L external reduced-schema coverage is only two records per dataset.                         | audit-only         | allowed        |
| C14        | Exact PTB-XL+ 531-column external reconstruction is NO-GO.                                          | audit-only         | allowed        |
| C15        | External multimodal validation has been completed.                                                  | forbidden          | forbidden      |
| C16        | Gated fusion is superior to fair concat.                                                            | forbidden          | forbidden      |
| C17        | The framework is clinically ready or clinically validated.                                          | forbidden          | forbidden      |
| C18        | Exact 531-column PTB-XL+ external reproduction was achieved.                                        | forbidden          | forbidden      |
| C19        | External signal calibration was evaluated without external tuning.                                  | supplement         | allowed        |
| C20        | Figure source-data files are available for internal performance, calibration, uncertainty, and XAI. | supplement         | allowed        |

## Boundary check

- external multimodal validation is NO-GO.
- current external evidence is signal-only only.
- internal full-schema PTB-XL/PTB-XL+ multimodal evidence is usable.
- Stage 14L is a reproducibility finding / feasibility audit, not an external multimodal result.

## Go/No-Go rule

GO is allowed because `table_manuscript_claim_support.csv` and `docs/MANUSCRIPT_RESULT_BOUNDARIES.md` were generated, and no external multimodal claim is marked as a main-manuscript claim.
