# Zenodo Upload Package: ECG/PTB-XL BMC MIDM Manuscript

## Recommended Deposition Type

Use **Software** if uploading the reproducible code repository archive, or **Dataset** if uploading only manuscript-derived tables, figures, and supplementary source data. For this project, the recommended route is:

1. Upload the GitHub release archive through Zenodo's GitHub integration.
2. Add the manuscript-ready tables, figures, and supplementary material archive as an additional file if the journal or repository record benefits from direct artifact access.

GitHub repository: https://github.com/seefreewind/ecg-ptbxl-multimodal-decision-support

GitHub release for Zenodo archiving: https://github.com/seefreewind/ecg-ptbxl-multimodal-decision-support/releases/tag/v0.1.0

## Title

A reproducibility-aware decision-support evaluation framework for multimodal ECG risk stratification

## Creators

- Yi Zha, The Second Affiliated Hospital of Wenzhou Medical University
- Da Lin, The Second Affiliated Hospital of Wenzhou Medical University
- Ying Chen, Wenzhou Medical University
- Yue Liu, Wenzhou Medical University
- Yu Zhang, The Second Affiliated Hospital of Wenzhou Medical University, ORCID: 0000-0001-8579-3692

## Description

This upload contains manuscript-ready code and artifacts for a public-data ECG study evaluating a reproducibility-aware multimodal decision-support framework. Internal experiments use PTB-XL waveforms and released PTB-XL+ structured features. External validation is restricted to signal-only evaluation on CPSC2018 and Chapman-Shaoxing. Stage 14L is included as a structured-feature reproducibility and feasibility audit; it does not constitute external multimodal validation.

## Evidence Boundary

- Internal PTB-XL/PTB-XL+ multimodal evaluation is supported.
- CPSC2018 and Chapman-Shaoxing external evidence is signal-only.
- External multimodal validation was not performed.
- Gated fusion should not be described as superior to fair concat.
- The framework is not clinically ready, clinically validated, or deployable.

## Files to Upload

- `ecg_ptbxl_bmc_midm_zenodo_artifacts.zip`: manuscript draft, cover letter draft, figures, supplementary tables, citation files, and upload audit files.
- GitHub source-code release archive, preferably created from the public GitHub repository release.

## Data Availability Text

PTB-XL is available from PhysioNet at https://physionet.org/content/ptb-xl/. PTB-XL+ is available from PhysioNet at https://physionet.org/content/ptb-xl-plus/. CPSC2018 is available from the China Physiological Signal Challenge 2018 website at http://2018.icbeb.org/Challenge.html. The Chapman-Shaoxing ECG database is available from PhysioNet at https://physionet.org/content/ecg-arrhythmia/. This repository does not redistribute raw ECG data.

## Keywords

electrocardiography; clinical decision support; multimodal fusion; signal-level external validation; calibration; uncertainty estimation; explainable artificial intelligence; reproducibility; PTB-XL; public datasets

## License Recommendation

Use MIT or Apache-2.0 for code if all authors agree. Use CC-BY-4.0 for manuscript artifacts and figures if journal policy permits. Do not apply a license that implies redistribution rights over third-party raw ECG datasets.
