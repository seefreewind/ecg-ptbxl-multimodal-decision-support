# Data Feasibility Report

## 1. PTB-XL Metadata Check

- ptbxl_database.csv found: yes
- scp_statements.csv found: yes
- metadata rows: 21799
- metadata columns: 28
- missing required columns: none
- SCP parse failures: 0

## 2. Waveform File Check

- waveform column: filename_lr
- first records checked: 20
- waveform files found: 20
- waveform files missing: 0
- waveform status: success
- missing examples: none
- wfdb installed: yes
- wfdb probe: wfdb header ok: fs=100, sig_len=1000, n_sig=12

## 3. Diagnostic Superclass Label Distribution

| label   |   positive_count | metadata_missing   | status   |
|:--------|-----------------:|:-------------------|:---------|
| NORM    |             9514 | False              | success  |
| MI      |             5469 | False              | success  |
| STTC    |             5235 | False              | success  |
| CD      |             4898 | False              | success  |
| HYP     |             2649 | False              | success  |

## 4. PTB-XL+ Structured Feature Check

- PTB-XL+ found: no
- selected feature file: none
- candidate files:
No candidate files found.
- total structured rows: 0
- structured feature columns: 0
- non-numeric columns: none
- has age: no
- has sex: no
- has interval features: no
- has axis features: no
- has amplitude features: no

PTB-XL+ structured features not found. Current project can only run signal-only baseline until structured features are provided.

See `tables/table_structured_missingness.csv` for missingness details.

## 5. PTB-XL and PTB-XL+ Alignment

- ID column: none
- aligned multimodal samples: 0
- alignment reason: PTB-XL+ structured features not found. Current project can only run signal-only baseline until structured features are provided.

## 6. Official Fold Split Check

| split   |   n_samples | status   | NORM   | MI   | STTC   | CD   | HYP   |
|:--------|------------:|:---------|:-------|:-----|:-------|:-----|:------|
| train   |       17418 | success  | 7596   | 4379 | 4186   | 3907 | 2119  |
| val     |        2183 | success  | 955    | 540  | 528    | 495  | 268   |
| test    |        2198 | success  | 963    | 550  | 521    | 496  | 262   |
| fold_1  |        2175 | success  |        |      |        |      |       |
| fold_2  |        2181 | success  |        |      |        |      |       |
| fold_3  |        2192 | success  |        |      |        |      |       |
| fold_4  |        2174 | success  |        |      |        |      |       |
| fold_5  |        2174 | success  |        |      |        |      |       |
| fold_6  |        2173 | success  |        |      |        |      |       |
| fold_7  |        2176 | success  |        |      |        |      |       |
| fold_8  |        2173 | success  |        |      |        |      |       |
| fold_9  |        2183 | success  |        |      |        |      |       |
| fold_10 |        2198 | success  |        |      |        |      |       |

## 7. Feasibility Conclusion

Conclusion: Feasible for signal-only ECG modeling, but not yet feasible for multimodal modeling.

## 8. Recommended Next Step

Recommended next step: provide PTB-XL+ structured feature files.
