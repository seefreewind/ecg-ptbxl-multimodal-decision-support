# BMC MIDM Stage 22 Official Requirements Audit

This audit maps the provided BMC Medical Informatics and Decision Making official requirements to the current ECG/PTB-XL manuscript package.

## Locked Evidence Boundary

- Internal PTB-XL/PTB-XL+ multimodal evidence remains usable.
- External evidence remains signal-only for CPSC2018 and Chapman-Shaoxing.
- Stage 14L remains a structured-feature reproducibility/feasibility audit, not an external multimodal result.
- The manuscript must not claim external multimodal validation, exact external PTB-XL+ reconstruction, gated-fusion superiority, or clinical deployment/readiness.

## Generated Stage 22 Files

- BMC-compliant Word draft: `manuscript/ECG_PTBXL_BMC_MIDM_SUBMISSION_DRAFT_STAGE22_BMC_COMPLIANT.docx`
- This audit: `manuscript/BMC_MIDM_STAGE22_OFFICIAL_REQUIREMENTS_AUDIT.md`
- Figure upload files remain in `manuscript/figures_redesigned/`.

## Requirement Mapping

| BMC requirement area | Official requirement interpreted for this manuscript | Stage 22 status | Note/action |
|---|---|---|---|
| Article type | Research article reporting computational/public-data model evaluation | Aligned | Keep as Research article; not a clinical trial. |
| Title page | Title, full author names, affiliations, corresponding author | Aligned | Affiliations are institutional and city/province/country level. |
| LLM documentation | BMC requires LLM use to be documented in Methods or equivalent section | Updated | Inserted an AI-assisted tools paragraph in Methods. |
| Abstract structure | Background, Methods, Results, Conclusions; <=350 words; no references | Aligned | No literature citations were added to the abstract. |
| Trial registration | Required for health-care intervention trials | Not applicable | This is a secondary public-data computational study, not an intervention trial. |
| Keywords | Three to ten keywords | Aligned | Ten keywords are present. |
| Background | Context, aim, literature summary, study necessity | Aligned | Evidence-boundary rationale retained. |
| Methods | Aim/design/setting, data/materials, processes, comparisons, statistics | Aligned with update | Public-data design, datasets, frozen splits, models, metrics, calibration, uncertainty, XAI, DCA, external signal-only validation, and audit stages are described. |
| Results | Findings with statistical results in text/tables/figures | Aligned | Internal multimodal, calibration, uncertainty, XAI/DCA, external signal-only, and Stage 14L audit results are reported. |
| Discussion | Interpretation in context and limitations | Aligned | External multimodal NO-GO and clinical-readiness boundaries are retained. |
| Conclusions | Clear main conclusions and relevance | Aligned | Conservative conclusion retained. |
| Abbreviations | List required when abbreviations are used | Aligned | List of Abbreviations is present. |
| Declarations heading | All required subheadings must be present | Aligned | Ethics, consent, data/materials, competing interests, funding, contributions, acknowledgements are present. |
| Ethics approval and consent | Required even if approval was waived/not newly required | Aligned | States public de-identified data and no new participants. |
| Consent for publication | Required section; Not applicable if no individual person data | Aligned | States Not applicable. |
| Data availability | Must include dataset/repository information and persistent identifiers where available | Aligned | PhysioNet/external dataset links, GitHub repository, and Zenodo DOI are included. |
| Competing interests | Declare financial/non-financial interests | Aligned | No competing interests declared. |
| Funding | Declare all funding sources | Aligned | No specific funding declared. |
| Authors' contributions | Use author initials and state roles | Aligned | Author contribution statement is present. |
| Acknowledgements | Required section; Not applicable if none | Aligned | States Not applicable. |
| References | Vancouver style; URLs preferably referenced rather than only free text | Partly aligned | Core references are present. Final editorial pass may add formal dataset/software repository references if required by submission checks. |
| Figures | Numbered in order, composite multi-panel files, titles/legends in manuscript, files <10 MB | Aligned | Stage 21 redesigned figures are available as PNG/PDF/SVG, all <10 MB. |
| Tables | Numbered/cited sequentially, table objects in manuscript, legends present | Aligned | Main manuscript contains Word table objects; machine-readable supplemental CSVs are available. |
| Additional files | List file name, format, title, description; cite in sequence | Partly aligned | Supplementary material list is present. Submission portal names should be checked when uploading final Additional files. |
| Review formatting | Double-line spacing, page and line numbering | Updated | Stage 22 DOCX applies double spacing, footer page fields, and Word line numbering. |

## Remaining Pre-Submission Checks

1. Confirm that the submission system accepts the current author affiliations as full institutional addresses.
2. During upload, name supplementary materials as `Additional file 1`, `Additional file 2`, etc., if the portal requires BMC-style naming.
3. If the portal flags URLs in the data-availability statement, add formal dataset/software repository references for PTB-XL, PTB-XL+, CPSC2018, Chapman-Shaoxing, GitHub, and Zenodo in Vancouver style.
4. Use the separate high-resolution PNG/PDF/SVG files for figure upload rather than relying only on Word-embedded previews.
5. Do not add any external multimodal, clinical deployment, or gated-superiority wording during final portal edits.

## Render QA

- Stage 22 DOCX was rendered to page images in `manuscript/render_qa/stage22/`.
- Final rendered length: 26 pages.
- A blank page caused by empty section-break paragraphs before the embedded figure preview section was removed.
- No retained Supplementary Figure S2, page-level figure overlap, or obvious table/figure truncation was detected in the rendered preview.

## Compliance Decision

Stage 22 is GO for BMC-style submission preparation, subject to final portal-specific upload naming and any automated reference/URL checks.
