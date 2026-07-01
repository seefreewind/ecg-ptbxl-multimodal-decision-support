# External Label Mapping Plan

Generated date: 2026-06-29

## Scope

This is a draft compatibility plan for future external validation on CPSC2018 and Chapman-Shaoxing. It is not an external validation result.

Target PTB-XL superclass labels: `NORM`, `MI`, `STTC`, `CD`, `HYP`.

## Conservative Mapping Rules

- Only `high` confidence labels may enter the main external-validation analysis.
- `medium` confidence labels are sensitivity-analysis only.
- `low` and `exclude` labels must not enter the main analysis.
- External validation may use a high-confidence label subset; it must not force all five PTB-XL classes.
- If actual external label files differ from this draft, the audit table must be revised before evaluation.

## Dataset Coverage From Draft Audit

- CPSC2018: high-confidence draft coverage = CD, NORM; not safely covered = HYP, MI, STTC.
- Chapman-Shaoxing: high-confidence draft coverage = CD, HYP, MI, NORM; not safely covered = STTC.

## Notes

- CPSC2018 is expected to support high-confidence `NORM` and `CD` mappings, while MI and HYP are not safely covered by the common nine-label CPSC2018 task.
- Chapman-Shaoxing may support broader mappings, but this remains conditional on the actual annotation dictionary present in the downloaded files.
- ST/T labels should be treated carefully because ischemia, infarction, and nonspecific repolarization abnormalities can be mixed in external datasets.

## Audit Table

See `tables/table_external_label_mapping_audit.csv`.
