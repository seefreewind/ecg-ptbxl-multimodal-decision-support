# Communications Biology Scope Note

## Core Reframing

This project should be framed as a biological and translational audit of retinal foundation model representations, not as a conventional model leaderboard.

The central question is:

> Do retinal foundation models learn transferable retinal disease biology, or do they partly rely on dataset-specific shortcuts?

The study should test whether model embeddings reflect disease phenotypes across datasets or whether they also encode acquisition source, device, image style, quality, and dataset identity.

## What Makes the Project Communications Biology-Relevant

Communications Biology will require more than performance comparison. The manuscript needs evidence that model behavior reveals something about disease representation, dataset shift, and the limits of transferring retinal image biology across acquisition settings.

The strongest story is:

1. Foundation models may improve internal or low-label performance.
2. External validation and calibration can still degrade under domain shift.
3. Embeddings may contain both disease phenotype signal and dataset/source signal.
4. Shortcut probes can quantify whether dataset identity is encoded strongly.
5. Clinician-adjudicated error taxonomy can link model failures to disease boundaries, mixed pathology, image quality, and label mismatch.

## What Not To Claim

- Do not claim that any model is clinical-ready.
- Do not claim clinical deployment readiness.
- Do not treat OFM-CRS as a regulatory or approval metric.
- Do not imply external generalization without external data.
- Do not place low-confidence label mappings in the main analysis.
- Do not report any Results values without output files.

## Minimum Evidence Needed

Before this can credibly target Communications Biology, the project needs:

- internal and external metrics for OCT and DR tasks;
- calibration metrics under domain shift;
- embeddings for internal and external data;
- UMAP or equivalent representation analysis;
- disease clustering and dataset clustering scores;
- dataset-source probing accuracy;
- pHash/file-hash leakage audit;
- label mapping sensitivity analysis;
- clinician-adjudicated failure taxonomy.

## Current Best Manuscript Structure

1. Benchmark design and dataset leakage audit.
2. Internal performance versus external generalization.
3. Representation analysis: disease clustering versus dataset clustering.
4. Calibration and decision-curve degradation.
5. Label efficiency and adaptation strategy.
6. Clinician-adjudicated failure taxonomy.
7. Auxiliary robustness summary.

OFM-CRS belongs in item 7 only as a summary, not as the central novelty.
