# ECG/PTB-XL Multimodal Project Current Work Summary

Date: 2026-06-30

## 1. Current Project Position

The project has advanced from raw PTB-XL data setup through internal modeling, calibration, uncertainty, XAI, DCA, signal-only external validation, external structured-feature feasibility auditing, Stage 15 manuscript-readiness auditing, and a first manuscript draft.

The current manuscript framing is:

**Internal PTB-XL/PTB-XL+ multimodal evaluation + signal-only external validation + structured-feature reproducibility audit.**

The safest working title is:

**Reproducibility-Aware Multimodal ECG Risk Stratification with Signal-Level External Validation**

## 2. Core Evidence Boundary

The most important boundary remains:

**External multimodal validation is NO-GO.**

Current evidence supports:

- Internal full-schema PTB-XL/PTB-XL+ multimodal evaluation.
- Signal-only external validation on CPSC2018 and Chapman-Shaoxing.
- Stage 14L as a structured-feature reproducibility and feasibility audit.
- Conservative decision-support evaluation using calibration, uncertainty, XAI, and exploratory DCA.

Current evidence does **not** support:

- External multimodal validation.
- Exact external PTB-XL+ 531-column structured-feature reconstruction.
- Gated fusion superiority over fair concat.
- Clinical readiness, clinical deployment, or clinical validation.
- Treating candidate/prototype ECGdeli features as official PTB-XL+ external structured features.

## 3. Main Internal Results

Internal full-schema PTB-XL/PTB-XL+ results support a multimodal gain under frozen splits.

| Model | Test AUROC | Test AP | Test F1 |
|:---|---:|---:|---:|
| strong signal-only | 0.9098 | 0.7721 | 0.6998 |
| signal-embedding MLP | 0.9094 | 0.7724 | 0.7002 |
| structured MLP | 0.9046 | 0.7652 | 0.6899 |
| fair MLP-concat | 0.9193 | 0.7953 | 0.7208 |
| gated fusion MLP | 0.9196 | 0.7978 | 0.7255 |

Main interpretation:

- Fair concat improves over the strongest signal-embedding comparator.
- The gain supports internal multimodal complementarity between signal embeddings and released PTB-XL+ structured features.
- Gated fusion is numerically close to fair concat but does not show a statistically clear advantage.

## 4. Gated Versus Fair Concat

Paired bootstrap comparison on the frozen internal test set:

| Metric | Delta gated-fair | 95% CI | Interpretation |
|:---|---:|:---|:---|
| AUROC | +0.0003 | -0.0015 to 0.0021 | CI contains 0 |
| AP | +0.0025 | -0.0014 to 0.0070 | CI contains 0 |
| F1 | +0.0047 | -0.0044 to 0.0142 | CI contains 0 |

Manuscript implication:

The paper should not claim gated fusion superiority. The stronger and safer story is that strict fair multimodal evaluation shows modality complementarity, while simple concat already captures most of the gain.

## 5. External Validation Status

External validation is signal-only only.

| Dataset | Label scope | N | Macro AUROC | Macro AP | Macro F1 |
|:---|:---|---:|---:|---:|---:|
| CPSC2018 | NORM, CD | 9,944 | 0.9071 | 0.6509 | 0.5904 |
| Chapman-Shaoxing | MI, CD, HYP | 45,150 | 0.8742 | 0.1727 | 0.1650 |

Important interpretation:

- CPSC2018 supports limited signal-level external transportability for the NORM/CD high-confidence label subset.
- Chapman-Shaoxing shows preserved ranking performance but low AP/F1, especially for low-prevalence labels.
- Chapman MI has high AUROC but very low AP/F1, consistent with low prevalence, label mapping constraints, and PTB-XL validation-threshold transfer.
- No external threshold tuning was performed.

## 6. External Signal Calibration

External signal-only calibration was evaluated without external refitting.

| Dataset | Macro Brier | Micro Brier | Macro ECE | Macro MCE | Temperature source |
|:---|---:|---:|---:|---:|:---|
| CPSC2018 | 0.1268 | 0.1268 | 0.1262 | 0.4099 | internal validation |
| Chapman-Shaoxing | 0.0855 | 0.0855 | 0.1412 | 0.7277 | internal validation |

Manuscript implication:

These results can support transparent calibration reporting under distribution shift, but they must not be framed as clinical calibration readiness.

## 7. Stage 14L Reproducibility Audit

Stage 14L intentionally stopped trying to reproduce the full PTB-XL+ 531-column external schema and instead used a reproducibility-validated concordant subset based on Stage 14H allclose features.

Key facts:

- Allclose structured features: 138.
- Reduced structured-only internal performance collapsed.
- Reduced fair concat did not show stable gain over signal-embedding MLP.
- External candidate structured coverage was only two joinable records per external dataset.

Internal reduced-schema results:

| Model | Test AUROC | Test AP | Test F1 |
|:---|---:|---:|---:|
| stage14l_signal_embedding_mlp | 0.9094 | 0.7722 | 0.6981 |
| stage14l_structured_mlp | 0.5704 | 0.3045 | 0.0000 |
| stage14l_fair_concat_mlp | 0.9097 | 0.7731 | 0.6938 |

External coverage:

| Dataset | Signal records | Candidate structured records | Joinable records | Coverage |
|:---|---:|---:|---:|---:|
| CPSC2018 | 9,944 | 2 | 2 | 0.000201 |
| Chapman-Shaoxing | 45,150 | 2 | 2 | 0.000044 |

Stage 14L decision:

**NO-GO for external multimodal validation.**

Use Stage 14L only as a reproducibility and feasibility finding.

## 8. Manuscript Draft Status

Current manuscript files:

- `manuscript/ECG_PTBXL_MANUSCRIPT_DRAFT.md`
- `manuscript/PROJECT_MANUSCRIPT_RULES.md`
- `manuscript/MANUSCRIPT_DRAFT_AUDIT.md`

Current draft status:

- BMC-style public-data research article draft.
- Approximate length: 4,320 words.
- Abstract, Methods, and Results contain no literature citation markers.
- Main tables and supplementary table drafts are embedded.
- The draft is content-ready for human review but not submission-ready formatting.

Embedded draft tables:

- Table 1: internal model performance.
- Table 2: gated versus fair concat paired bootstrap.
- Table 3: signal-only external validation.
- Supplementary Table S1: external signal-only calibration.
- Supplementary Table S2: structured-feature reproducibility audit.

## 9. Main Manuscript Claims Allowed

Allowed main claims:

- Internal full-schema PTB-XL/PTB-XL+ multimodal fusion improves over unimodal baselines under frozen splits.
- Fair concat captures the main internal multimodal gain.
- Gated fusion does not show a statistically clear advantage over fair concat.
- Signal-only external validation was completed on CPSC2018 and Chapman-Shaoxing.
- Calibration, uncertainty triage, XAI, and exploratory DCA support a conservative decision-support evaluation framework.

Allowed supplement-only or audit-only claims:

- External signal-only calibration can be reported as supplementary.
- Internal DCA should remain exploratory and threshold-dependent.
- Stage 14L reduced-schema findings can be included as a feasibility or reproducibility audit.
- Exact PTB-XL+ external reconstruction remains unresolved.

## 10. Forbidden Manuscript Claims

Do not write:

- External multimodal validation was completed.
- Exact PTB-XL+ 531-column external reproduction was achieved.
- Gated fusion is superior to fair concat.
- The framework is clinically ready, clinically validated, or deployable.
- Candidate ECGdeli/prototype features are official PTB-XL+ external structured features.
- Stage 14L provides limited external multimodal validation.

## 11. Remaining Work Before Submission-Ready Manuscript

Recommended next steps:

1. Verify all references and convert them into target-journal format.
2. Refine Introduction and Discussion with stronger but conservative literature positioning.
3. Decide target journal and adjust title/abstract/section order accordingly.
4. Finalize figure files corresponding to the existing source-data map.
5. Add author list, affiliations, funding, acknowledgements, author contributions, and conflict-of-interest statements.
6. Check original dataset ethics and consent statements for PTB-XL, PTB-XL+, CPSC2018, and Chapman-Shaoxing.
7. Convert the Markdown draft to LaTeX or Word only after content review.

## 12. Current Go/No-Go Decision

Current status:

**GO for manuscript drafting refinement.**

Reason:

- Claim boundaries are explicit.
- External multimodal claims are not used.
- Internal multimodal evidence is usable.
- Signal-only external validation is available.
- Stage 14L is correctly framed as a reproducibility audit.

Not yet ready:

**NO-GO for final submission package.**

Reason:

- References still need formal verification.
- Figures need final rendering and placement.
- Author/declaration sections remain incomplete.
- Target-journal formatting has not been applied.
