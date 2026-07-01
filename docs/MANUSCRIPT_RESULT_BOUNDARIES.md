# Manuscript Result Boundaries

Date: 2026-06-30

## Core Boundary

internal multimodal experiments remain reproducible because they use released PTB-XL+ feature values under frozen splits; the reproducibility limitation concerns de novo reconstruction of the same structured feature schema on external WFDB datasets, not reuse of the released PTB-XL+ resource.

External multimodal validation is NO-GO. Current external evidence is signal-only only. Stage 14L is a reproducibility finding and feasibility audit, not an external multimodal result.

## Allowed main claims

- Internal full-schema PTB-XL/PTB-XL+ multimodal fusion improves over unimodal baselines under frozen splits.
- Fair concat captures the main internal multimodal gain.
- Gated fusion does not show a statistically clear advantage over fair concat.
- Signal-only external validation was completed on CPSC2018 and Chapman-Shaoxing.
- Calibration, uncertainty triage, XAI, and DCA support a trustworthy decision-support framing, with conservative interpretation.

## Supplement-only claims

- Internal DCA is exploratory and threshold-dependent.
- External signal-only calibration may be reported as supplementary because temperature scaling was fit internally and only evaluated externally.
- Stage 14L concordant-subset results may be included as a sensitivity or feasibility audit, not as a validation result.

## Engineering-audit-only findings

- PTB-XL+ exact 531-column external reconstruction remains unresolved.
- ECGdeli candidate/prototype files are incomplete and cannot be used as official external structured features.
- Stage 14L external coverage was two joinable records per dataset and therefore failed the external quality gate.

## Forbidden claims

- External multimodal validation was completed.
- Exact PTB-XL+ 531-column external reproduction was achieved.
- Gated fusion is superior to fair concat.
- The model is clinically ready, clinically validated, or deployable.
- Candidate/prototype structured features are valid PTB-XL+ external structured features.

## Required wording constraints

- Use "internal multimodal evaluation" for PTB-XL/PTB-XL+ full-schema experiments.
- Use "signal-only external validation" for CPSC2018 and Chapman-Shaoxing.
- Use "reproducibility audit" or "feasibility audit" for Stage 14L.
- State that validation-only thresholds and validation-fitted temperatures were used; no external test-set tuning was performed.
- For Chapman-Shaoxing, report prevalence/support and note that low AP/F1 can coexist with high AUROC under low prevalence and threshold transfer.

## Reviewer attack points and preemptive responses

1. Attack: "The title suggests cross-dataset multimodal validation."
   Response: Avoid naked "Cross-Dataset Validation" in the title. Use "Signal-Level External Validation" or "Reproducibility-Aware" wording.

2. Attack: "External multimodal validation is missing."
   Response: State this limitation directly. External validation is signal-only because exact PTB-XL+ compatible structured features could not be validated externally.

3. Attack: "PTB-XL+ feature reconstruction failed, so internal multimodal results are invalid."
   Response: The internal experiments use released PTB-XL+ feature values under frozen splits. The limitation concerns de novo reconstruction of the same schema on external WFDB datasets.

4. Attack: "Gated fusion does not improve over concat."
   Response: Treat this as a fair negative ablation. The supported contribution is multimodal complementarity and trustworthy evaluation, not gate superiority.

5. Attack: "Chapman AUROC is high but AP/F1 are low."
   Response: Report prevalence and support. Low-prevalence labels and transferred thresholds can yield low AP/F1 despite preserved ranking performance.
