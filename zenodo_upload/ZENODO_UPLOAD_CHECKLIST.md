# Zenodo Upload Checklist

## Recommended Route

1. Log in to Zenodo.
2. Connect Zenodo to the GitHub account `seefreewind` if not already connected.
3. Enable the repository `ecg-ptbxl-multimodal-decision-support`.
4. Archive the GitHub release `v0.1.0`.
5. Upload `zenodo_upload/ecg_ptbxl_bmc_midm_zenodo_artifacts.zip` as an additional artifact if a manuscript-specific artifact bundle is desired.
6. Copy metadata from `zenodo_upload/zenodo_metadata.json`.
7. Confirm that raw ECG datasets are not redistributed.
8. Publish the Zenodo record and copy the DOI URL back into the manuscript data-availability statement.

## Files Prepared Locally

- `zenodo_upload/ecg_ptbxl_bmc_midm_zenodo_artifacts.zip`
- `zenodo_upload/README_ZENODO_UPLOAD.md`
- `zenodo_upload/zenodo_metadata.json`
- `zenodo_upload/MANIFEST.txt`

## Evidence-Boundary Note to Keep in Zenodo Description

Internal PTB-XL/PTB-XL+ multimodal evaluation is supported. External validation evidence is signal-only for CPSC2018 and Chapman-Shaoxing. Stage 14L is a structured-feature reproducibility and feasibility audit. External multimodal validation was not performed and should not be claimed.
