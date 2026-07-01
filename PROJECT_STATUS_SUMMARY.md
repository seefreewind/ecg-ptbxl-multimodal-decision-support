# Project Status Summary

| Component | Status | Notes |
|---|---|---|
| Raw PTB-XL metadata | missing | `data/raw/ptbxl/ptbxl_database.csv` is not placed. |
| Raw PTB-XL waveform | missing | `data/raw/ptbxl/records100/` is not placed. `records500/` is optional for 100Hz-only work. |
| PTB-XL+ structured features | missing | No valid PTB-XL+ feature candidate has been identified; unrelated structured files are excluded. |
| Local layout validator | completed | `src/data/validate_local_data_layout.py` and `scripts/00b_validate_local_data_layout.sh` exist. |
| Data path discovery | completed | `src/data/discover_data_paths.py` and `scripts/00a_discover_data_paths.sh` exist. |
| Feasibility checker | completed | `src/data/check_data_feasibility.py` exists; current conclusion is failed because raw data are missing. |
| PTB-XL label parser | completed | `src/data/label_mapping.py` exists. |
| PTB-XL split generator | completed skeleton | `src/data/prepare_ptbxl.py` exists but cannot generate real splits until raw metadata and labels are available. |
| README | completed | `README.md` includes raw data preparation and Stage 0/1 commands. |
| DATA_SETUP guide | completed | `docs/DATA_SETUP.md` exists. |
| Signal-only model | not started | Do not start until Stage 0/1 succeeds. |
| Structured-only model | not started | Requires valid PTB-XL+ structured features. |
| Fusion model | not started | Requires both PTB-XL and aligned PTB-XL+ data. |
| Uncertainty module | not started | Out of scope before baseline pipelines. |
| XAI module | not started | Out of scope before baseline pipelines. |
| External validation | not started | Out of scope until core PTB-XL pipeline succeeds. |
