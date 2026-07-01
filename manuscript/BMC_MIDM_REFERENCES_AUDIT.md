# BMC MIDM References Audit

## Citation-Key Audit

- Citation keys used in manuscript: alday2020physionet2020, brier1950verification, efron1993bootstrap, gal2016dropout, geifman2017selective, ghassemi2021xai, goldberger2000physionet, guo2017calibration, he2016resnet, liu2018cpsc, lundberg2017shap, naeini2015calibration, pilia2021ecgdeli, selvaraju2017gradcam, strodthoff2023ptbxlplus, sundararajan2017integrated, vickers2006dca, wagner2020ptbxl, zheng2020chapman
- BibTeX keys available: alday2020physionet2020, brier1950verification, delong1988roc, efron1993bootstrap, gal2016dropout, geifman2017selective, ghassemi2021xai, goldberger2000physionet, guo2017calibration, he2016resnet, liu2018cpsc, lundberg2017shap, naeini2015calibration, pilia2021ecgdeli, selvaraju2017gradcam, strodthoff2021benchmark, strodthoff2023ptbxlplus, sundararajan2017integrated, vickers2006dca, wagner2020ptbxl, zheng2020chapman
- Missing citation keys: none
- Unused BibTeX keys: delong1988roc, strodthoff2021benchmark

## Claim/Method Citation Audit

| Manuscript section | Claim or method | Inserted citation key(s) | Verification status | Unresolved TODO |
|:---|:---|:---|:---|:---|
| Background | PTB-XL public ECG resource | wagner2020ptbxl; goldberger2000physionet | verified from Stage 16/17 audit | none |
| Background | PTB-XL+ released structured features | strodthoff2023ptbxlplus | verified from Stage 16/17 audit | none |
| Background/Methods | ECGdeli and delineation context | pilia2021ecgdeli | verified from project citation; final DOI formatting check recommended | final DOI/style check |
| Background/Methods | CPSC2018 and Chapman-Shaoxing external datasets | liu2018cpsc; zheng2020chapman; alday2020physionet2020 | verified from Stage 16/17 audit | none |
| Methods | Residual learning architecture | he2016resnet | verified | none |
| Methods | Temperature scaling and calibration metrics | guo2017calibration; brier1950verification; naeini2015calibration | verified | none |
| Methods | Uncertainty and selective prediction | gal2016dropout; geifman2017selective | verified | none |
| Methods | XAI / attribution caution | lundberg2017shap; sundararajan2017integrated; selvaraju2017gradcam; ghassemi2021xai | verified | ensure final text matches exact XAI methods retained |
| Methods | Decision-curve analysis | vickers2006dca | verified | none |
| Methods | Bootstrap confidence intervals | efron1993bootstrap | verified | none |
| Optional | Correlated AUROC comparison background | delong1988roc | verified but unused in current draft | remove from .bib if unused references are not allowed |

## Audit Result

Citation-key audit passed: no manuscript citation key is missing from `references.bib`. `delong1988roc` is currently unused and may be removed if the final reference list must contain cited-only entries.
