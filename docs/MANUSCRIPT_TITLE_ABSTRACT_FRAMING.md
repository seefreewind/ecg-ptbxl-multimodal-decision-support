# Manuscript Title and Abstract Framing

Date: 2026-06-30

## Safe title options

1. Reproducibility-Aware Multimodal ECG Risk Stratification with Signal-Level External Validation
2. Interpretable Multimodal ECG Risk Stratification Using PTB-XL/PTB-XL+ with Signal-Level External Validation
3. A Reproducibility-Aware Decision-Support Framework for Multimodal ECG Risk Stratification

Recommended direction: use "Reproducibility-Aware" or "Signal-Level External Validation" and avoid a naked "Cross-Dataset Validation" claim.

## Structured abstract skeleton, 250-300 words

**Background:** Multimodal ECG decision-support models can combine raw waveform information with structured ECG-derived measurements, but their evaluation should distinguish internal multimodal evidence from external signal-level validation and from the feasibility of reconstructing structured features in new datasets.

**Methods:** We developed a PTB-XL/PTB-XL+ framework for five-superclass cardiac risk stratification using official train/validation/test splits. Signal embeddings from a one-dimensional ECG model were compared with released PTB-XL+ structured features, a fair concat multimodal model, and a gated fusion model under shared evaluation rules. Thresholds, calibration temperatures, and model selection were determined using validation data only. We assessed discrimination, calibration, uncertainty triage, post-hoc interpretability, and exploratory decision-curve analysis. External evaluation used CPSC2018 and Chapman-Shaoxing as signal-only datasets with pre-specified high-confidence label mappings. We also performed a reproducibility audit of ECGdeli-derived structured features to test whether PTB-XL+ compatible external structured features could be generated.

**Results:** In internal PTB-XL/PTB-XL+ testing, fair multimodal concat improved over unimodal baselines, whereas gated fusion showed no statistically clear advantage over fair concat in paired bootstrap analysis. Calibration and uncertainty analyses supported a decision-support framing but did not establish clinical readiness. Signal-only external validation showed preserved ranking performance in CPSC2018 and Chapman-Shaoxing, with lower AP/F1 in low-prevalence Chapman labels. The Stage 14L concordant-subset audit was NO-GO: internally the reduced structured subset did not provide stable multimodal gain, and externally the structured-feature coverage was insufficient.

**Conclusions:** The evidence supports internal multimodal complementarity and signal-level external validation, while external multimodal validation remains unavailable until exact PTB-XL+ compatible structured feature reconstruction can be validated.
