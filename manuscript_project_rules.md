# Project-level manuscript rules

This checklist applies to the retinal foundation model clinical-readiness benchmark manuscript in this folder.

## Scope

- Default target format: BMC-style public-data research article.
- Article order: Title, Abstract, Keywords, Background/Introduction, Methods, Results, Discussion, Conclusions, Supplementary Information, Acknowledgements, Authors' contributions, Funding, Availability of data and materials, Ethics approval and consent to participate, Consent for publication, Competing interests, References.
- Current manuscript file: `视网膜基础模型临床就绪度benchmark论文初稿.md`.
- Current experiment scaffold: `retinal_fm_benchmark_mvp/`.

## Evidence rules

- Do not invent analyses, samples, statistics, validation experiments, model results, or references.
- Keep all unrun or unavailable results as explicit placeholders.
- Replace placeholders only with outputs generated from `retinal_fm_benchmark_mvp/outputs/` or verified external files.
- Report negative, nonsignificant, failed-validation, heterogeneous, or multiple-testing-negative findings plainly.
- Do not describe a model as clinically ready unless it satisfies external validation, leakage audit, calibration, decision-utility, and failure-mode criteria.

## Citation rules

- Use in-text reference markers in Introduction and Discussion for background, rationale, prior-work comparison, interpretation, and limitation claims.
- Do not place literature citations in Methods or Results unless explicitly overridden later.
- Verify each reference before submission, including title, authors, journal, year, DOI or URL, and whether the cited claim is supported.
- Aim for approximately 50 references in the full submission-ready manuscript unless the final target journal sets a different limit.

## Language rules

- Use restrained wording: "was associated with", "showed evidence of association", "may contribute to", "provides biological clues", "requires further validation", and "warrants further investigation".
- Avoid unsupported causal or deployment claims, including "proved", "confirmed the mechanism", "clinically validated", "highly accurate biomarker", "effective therapeutic target", "revolutionary", and "groundbreaking".
- For public-data, retrospective, benchmark, MR, or machine-learning findings, do not claim clinical utility, causality, therapeutic readiness, or clinical validation without independent prospective evidence.

## Results replacement checklist

- Dataset counts, patient counts, eye counts, metadata availability, and label mappings are filled from dataset cards and manifests.
- Leakage audit results include exact duplicates, near duplicates, split unit, and pretraining contamination risk.
- Internal and external metrics include confidence intervals where possible.
- Calibration results include Brier score, ECE, slope, intercept, and reliability diagrams.
- DR decision-curve analysis includes model-guided referral, refer-all, and refer-none strategies.
- OFM-CRS reports dimension-level scores, total score, gatekeeping flags, and weight-sensitivity analysis.

## Formatting boundary

- This folder is currently in manuscript-draft stage.
- Do not perform Word/PDF rendering, visual QA, submission-package polishing, or AI-use statement insertion unless explicitly requested.
