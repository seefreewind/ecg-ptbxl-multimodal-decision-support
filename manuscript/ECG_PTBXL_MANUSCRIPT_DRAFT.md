# Reproducibility-Aware Multimodal ECG Risk Stratification with Signal-Level External Validation

## Abstract

**Background:** Multimodal electrocardiogram (ECG) models may combine waveform-derived representations with structured ECG measurements, but their evaluation should distinguish internal multimodal evidence from external validation and from the feasibility of reproducing structured features in new datasets.

**Methods:** We developed a PTB-XL/PTB-XL+ framework for five-superclass cardiac risk stratification using official frozen train, validation, and test splits. Signal embeddings from a one-dimensional ECG model were evaluated alongside released PTB-XL+ structured ECG features, a fair concat multimodal model, and a gated fusion model. Model selection, threshold tuning, and temperature scaling used validation data only. We assessed discrimination, calibration, uncertainty triage, post-hoc interpretability, and exploratory decision-curve analysis. External evaluation was restricted to signal-only validation on CPSC2018 and Chapman-Shaoxing using pre-specified high-confidence label mappings. We also performed a reproducibility audit to determine whether PTB-XL+ compatible structured features could be reconstructed for external WFDB datasets.

**Results:** In the internal PTB-XL/PTB-XL+ test set, fair multimodal concat improved over the strongest signal-embedding comparator in AUROC, average precision, and F1. Gated fusion showed only a small numerical difference from fair concat, and paired bootstrap confidence intervals for AUROC, average precision, and F1 contained zero. Temperature scaling, uncertainty triage, interpretability outputs, and exploratory decision-curve analysis supported a decision-support evaluation framework without establishing clinical readiness. Signal-only external validation achieved macro AUROC 0.907 on CPSC2018 and 0.874 on Chapman-Shaoxing, with lower average precision and F1 in low-prevalence Chapman labels. The Stage 14L concordant-subset audit was NO-GO because reduced structured features did not provide stable internal multimodal gain and external structured-feature coverage was insufficient.

**Conclusions:** The evidence supports internal multimodal complementarity using released PTB-XL+ structured features and signal-level external validation. External multimodal validation remains unavailable until exact PTB-XL+ compatible structured feature reconstruction can be validated on external WFDB datasets.

## Keywords

Electrocardiography; PTB-XL; PTB-XL+; multimodal learning; cardiac risk stratification; calibration; uncertainty; interpretability; signal-level external validation; reproducibility audit.

## Background

Automated ECG interpretation has moved from single-task rhythm classification toward broader multi-label diagnosis across diagnostic, rhythm, and morphology statements. Large public 12-lead ECG resources have made this shift more reproducible by providing waveform data, expert-derived labels, and recommended splits for algorithm development. PTB-XL was introduced as a clinical 12-lead ECG waveform dataset with cardiologist annotations and hierarchical diagnostic labels, and it has become a common resource for benchmarking ECG classification models [1,2]. PTB-XL+ extends this setting by providing harmonized structured features derived from commercial and open-source ECG analysis systems, including ECGdeli-derived measurements [3,4].

These resources create an opportunity to ask a narrower but important question: whether ECG waveform representations and structured ECG-derived measurements provide complementary information under a fair comparison. Prior PTB-XL benchmarking has shown that convolutional and residual time-series models can perform strongly for ECG analysis [5]. At the same time, structured ECG measurements remain attractive because they are closer to familiar clinical descriptors such as intervals, amplitudes, and morphology-derived variables. A multimodal model that combines both sources may therefore improve internal risk stratification, but any such gain should be attributed carefully to the modalities rather than to unequal model capacity or post-hoc tuning.

This distinction matters for decision-support research. A model that improves a discrimination metric inside one benchmark is not automatically useful outside that benchmark, and a complex fusion mechanism is not necessarily responsible for a multimodal gain. For ECG systems, the same surface diagnosis can be encoded differently across datasets, and the same waveform can produce different structured measurements depending on delineation software, preprocessing, lead handling, and feature definitions. A reproducible multimodal study therefore needs more than a high internal AUROC. It needs frozen splits, validation-only thresholding, comparable unimodal and multimodal interfaces, calibration assessment, interpretable outputs, and explicit boundaries around what has and has not been externally validated.

External validation is more difficult. Multi-institutional ECG efforts, including the PhysioNet/Computing in Cardiology Challenge and CPSC2018, highlight that ECG data sources differ in population, label scope, recording format, and diagnostic coding [6,7]. Chapman-Shaoxing provides another large 12-lead ECG resource with rhythm and condition labels, but its label space is not identical to PTB-XL's five-superclass diagnostic task [8]. These differences make a direct multimodal external validation claim unsafe unless structured features can be generated with the same definitions used internally.

We therefore framed this study as a reproducibility-aware multimodal decision-support evaluation. The internal question was whether released PTB-XL+ structured features improve over signal-only and structured-only baselines under frozen PTB-XL splits. The external question was deliberately limited to signal-only validation on CPSC2018 and Chapman-Shaoxing. A separate reproducibility audit evaluated whether ECGdeli-derived PTB-XL+ structured features could be reconstructed for external WFDB datasets, but that audit was not treated as external multimodal validation.

## Methods

### Study design

This was a public-data model development and evaluation study. The primary internal analysis used PTB-XL waveform records and released PTB-XL+ structured features. The external analysis used CPSC2018 and Chapman-Shaoxing waveforms for signal-only validation. No external model training, external threshold tuning, or external model selection was performed.

The study was organized as a staged evaluation rather than a single end-to-end model claim. Stage 0/1 verified the local PTB-XL layout, parsed diagnostic superclass labels, and generated official train, validation, and test files. Subsequent internal stages trained signal-only, structured-only, fair multimodal concat, and gated multimodal models. Later stages evaluated calibration, uncertainty triage, interpretability, decision-curve analysis, external signal-only validation, and structured-feature reproducibility. The manuscript uses these stages to separate model-performance evidence from engineering feasibility findings.

### Datasets and label scope

The internal task used five PTB-XL diagnostic superclasses: NORM, MI, STTC, CD, and HYP. The official PTB-XL train, validation, and test split structure was preserved throughout internal modeling. PTB-XL+ structured features were joined to the PTB-XL records using ECG identifiers.

The external signal-only evaluation used pre-specified high-confidence label mappings. CPSC2018 was evaluated for NORM and CD. Chapman-Shaoxing was evaluated for MI, CD, and HYP. Chapman-Shaoxing sinus rhythm was not treated as main-analysis NORM. Records that could not be read as WFDB waveforms were excluded; no labels or predictions were imputed.

### Internal model families

The internal model set included a strong signal-only waveform model, a signal-embedding MLP, a structured-only MLP using the released PTB-XL+ feature table, a fair concat model combining the signal embedding and structured features, and a gated fusion model using the same signal and structured inputs. The strong signal-only model used 100 Hz 12-lead PTB-XL waveforms and a one-dimensional residual network configured with 12 input channels, five output labels, base channel width 64, three residual stages with two blocks per stage, and dropout 0.2. This model provided both a direct signal-only comparator and the 256-dimensional signal embedding used in the fair multimodal interface.

The fair fusion dataset combined the 256-dimensional signal embedding with 531 released PTB-XL+ structured feature columns after median imputation and standardization defined on the training data. The signal-embedding MLP used hidden dimensions 256 and 128. The structured-only MLP used the 531 structured features with hidden dimensions 512 and 256. The fair concat model used the same signal and structured inputs with hidden dimensions 512 and 256 after concatenation. The gated fusion model used the same input interface, a 256-dimensional hidden representation, and a 256-dimensional classifier hidden layer. The fair-interface comparison used shared splits, shared label scope, validation-only early stopping, and validation-only threshold tuning.

### Calibration, uncertainty, interpretability, and decision-curve analyses

Temperature scaling was fit using validation logits only and then evaluated on frozen test predictions. Reliability curves, Brier score, expected calibration error, and maximum calibration error were generated for the main internal models. Uncertainty triage was evaluated using internal prediction uncertainty to compare retained subsets across coverage levels. Interpretability analyses used post-hoc structured feature attribution, signal attribution case reports, and gated-model gate summaries where available. Decision-curve analysis was exploratory and internal only.

### External signal-only validation

The frozen signal-only model was applied to CPSC2018 and Chapman-Shaoxing. Thresholds were transferred from PTB-XL validation or existing validation-derived rules. Temperature scaling was fit internally and evaluated externally without refitting. Per-class diagnostics included prevalence, AUROC, average precision, F1, support, threshold source, Brier score, ECE, and MCE.

### Structured-feature reproducibility audit

The structured-feature reproducibility audit evaluated whether external structured features could be generated in a way compatible with the PTB-XL+ internal schema. ECGdeli was installed and smoke-tested locally. Direct ECGdeli-derived candidate features were generated for small external samples and compared against PTB-XL+ feature definitions. A concordant subset based on Stage 14H allclose features was evaluated internally and checked for external coverage. The audit deliberately did not continue attempts to reconstruct the full PTB-XL+ structured schema after the NO-GO decision. It was used to define feasibility boundaries and was not treated as an external multimodal validation experiment.

### Statistical analysis

Internal discrimination was summarized using macro AUROC, macro average precision, and macro F1. Per-class thresholds were tuned on the internal validation set when thresholded metrics were required, and the frozen test set was used only for final evaluation. Gated fusion and fair concat were compared using paired bootstrap resampling on the frozen test set. External signal-only diagnostics were reported per dataset and per class. Calibration metrics were reported as macro and micro Brier scores, ECE, and MCE. No external threshold optimization was performed.

## Results

### Internal multimodal performance

The internal full-schema PTB-XL/PTB-XL+ test results supported a multimodal gain over unimodal baselines. The strong signal-only model achieved macro AUROC 0.9098, average precision 0.7721, and F1 0.6998. The signal-embedding MLP achieved macro AUROC 0.9094, average precision 0.7724, and F1 0.7002. The structured-only MLP achieved macro AUROC 0.9046, average precision 0.7652, and F1 0.6899.

Fair concat achieved macro AUROC 0.9193, average precision 0.7953, and F1 0.7208. Compared with the signal-embedding MLP, fair concat increased AUROC by 0.0098, average precision by 0.0229, and F1 by 0.0205. This supported internal complementarity between signal embeddings and released PTB-XL+ structured features (Table 1; Figures 1 and 2).

### Gated fusion did not show a clear advantage over fair concat

Gated fusion achieved macro AUROC 0.9196, average precision 0.7978, and F1 0.7255 on the internal frozen test set. The absolute differences from fair concat were small: AUROC +0.0003, average precision +0.0025, and F1 +0.0047. Paired bootstrap confidence intervals contained zero for AUROC, average precision, and F1. These results did not support a claim that gating was meaningfully superior to simple fair concat (Table 2).

### Calibration and decision-support analyses

After validation-fitted temperature scaling, the strong signal-only model had test macro Brier score 0.0903 and macro ECE 0.0320. The structured MLP had macro Brier score 0.0942 and macro ECE 0.0212. Fair concat had macro Brier score 0.0864 and macro ECE 0.0283. Gated fusion had macro Brier score 0.0844 and macro ECE 0.0193. Calibration metrics supported the inclusion of reliability assessment in the decision-support framework, but they did not establish clinical readiness (Figure 3).

Exploratory internal DCA showed mean macro net benefit of 0.1844 for strong signal-only, 0.1815 for structured MLP, 0.1881 for fair concat, and 0.1895 for gated fusion over the evaluated threshold range. These analyses were retained as exploratory because they were internal and threshold-dependent. Internal uncertainty triage and post-hoc dual-modality explanations were retained as decision-support diagnostics rather than validation endpoints (Figures 4 and 5).

### Signal-only external validation

CPSC2018 signal-only external validation included 9,944 evaluated records after excluding unreadable waveforms. The high-confidence NORM/CD label scope yielded macro AUROC 0.9071, average precision 0.6509, and F1 0.5904. Per-class AUROC was 0.9119 for NORM and 0.9022 for CD. CD had higher average precision and F1 than NORM in this external mapping (Table 3).

Chapman-Shaoxing signal-only external validation included 45,150 evaluated records. The high-confidence MI/CD/HYP label scope yielded macro AUROC 0.8742, average precision 0.1727, and F1 0.1650. Per-class AUROC was 0.9349 for MI, 0.8388 for CD, and 0.8488 for HYP. Average precision and F1 were lower, especially for MI, which had prevalence 0.0027 and support 123. These results indicate preserved ranking performance but limited thresholded classification performance under low prevalence and transferred PTB-XL validation thresholds (Table 3).

### External signal-only calibration

External signal-only calibration was evaluated using stored signal-only predictions. CPSC2018 had macro Brier score 0.1268, micro Brier score 0.1268, macro ECE 0.1262, and macro MCE 0.4099. Chapman-Shaoxing had macro Brier score 0.0855, micro Brier score 0.0855, macro ECE 0.1412, and macro MCE 0.7277. Temperature scaling was fit on internal validation data and was not refit on external labels (Supplementary Table S1).

### Structured-feature reproducibility audit

The PTB-XL+ external structured-feature reconstruction audit did not support external multimodal validation. Stage 14H found that only 138 of 420 direct ECGdeli candidate features were allclose in a PTB-XL internal recomputation audit. Discrepancy analysis showed prominent differences in T-duration and QT-related features. Stage 14J showed that unresolved feature families had semantic descriptions, but those descriptions did not provide a complete executable waveform-to-feature recipe.

Stage 14L evaluated a concordant subset using the 138 allclose features. Internally, the reduced structured-only model performed poorly, with test macro AUROC 0.5704 and average precision 0.3045. Reduced fair concat achieved test macro AUROC 0.9097 and average precision 0.7731, essentially matching the signal-embedding MLP rather than improving on it. The Stage 14L external quality gate also failed because only two candidate structured records per external dataset were available. Stage 14L was therefore classified as NO-GO and was treated as a reproducibility and feasibility audit (Supplementary Table S2).

## Discussion

This study supports an internal multimodal finding rather than an external multimodal validation claim. Using released PTB-XL+ structured features under frozen PTB-XL splits, fair concat improved over signal-only and structured-only comparators. The size and consistency of this internal gain suggest that signal embeddings and structured ECG-derived features contain complementary information in the PTB-XL/PTB-XL+ setting. This interpretation aligns with the design of PTB-XL+ as a structured feature extension to PTB-XL and with prior benchmarking that established PTB-XL as a resource for reproducible ECG model evaluation [1,3,5].

The gating result is also informative. Although gated fusion was numerically close to fair concat, paired bootstrap intervals did not show a statistically clear advantage. This shifts the methodological contribution away from architectural novelty and toward a more conservative finding: a rigorously controlled multimodal comparison can demonstrate modality complementarity, while simple fusion may be sufficient. Negative or near-null ablation findings are useful when they prevent over-attribution of gains to a more complex mechanism.

This result changes how the model should be presented. The evidence does not justify making gated fusion the central contribution, because the observed gated-versus-concat differences were small and compatible with sampling variability. The stronger claim is methodological: when the signal embedding, structured features, classification head, split, and thresholding procedure are held constant, the released PTB-XL+ structured feature resource adds information beyond the ECG signal embedding alone. That statement is narrower than architectural superiority, but it is also more defensible. It gives reviewers a clear path to inspect whether the gain comes from multimodal information rather than from an unfair comparator.

The external results should be interpreted as signal-only validation. CPSC2018 and Chapman-Shaoxing differ from PTB-XL in label scope and source characteristics, and our high-confidence mappings intentionally covered only subsets of the PTB-XL superclass task. The Chapman-Shaoxing results illustrate why AUROC alone can be incomplete in low-prevalence external labels: MI had high AUROC but low average precision and F1, consistent with the combination of low prevalence, label mapping constraints, and thresholds transferred from PTB-XL validation. This does not invalidate the signal-only ranking result, but it limits claims about thresholded external classification.

The external calibration results reinforce this boundary. Temperature scaling was learned internally and carried to the external datasets without refitting, which protects against external test-set optimization but leaves room for calibration shift. The observed external ECE and MCE values indicate that probability estimates should not be treated as deployment-ready clinical risk estimates. In a manuscript, these analyses are best used to show transparent evaluation under distribution shift, not to claim that the model is calibrated for bedside use.

The reproducibility audit clarifies a boundary that could otherwise be misunderstood. Internal multimodal experiments remain reproducible because they use released PTB-XL+ feature values under frozen splits; the reproducibility limitation concerns de novo reconstruction of the same structured feature schema on external WFDB datasets, not reuse of the released PTB-XL+ resource. ECGdeli was callable locally and could generate candidate features, but direct feature names were not sufficient to reproduce official PTB-XL+ values, especially for T-duration and QT-related families. The concordant-subset sensitivity analysis further showed that the small allclose subset did not preserve internal multimodal gain and did not provide enough external feature coverage.

The decision-support components broaden the evaluation beyond discrimination. Temperature scaling is a standard post-hoc approach for neural network calibration, and reliability analysis is important when probabilities may inform downstream decisions [9]. Post-hoc explanation methods such as feature attribution and gradient-based localization can help inspect model behavior, but they should not be interpreted as causal mechanisms [10,11]. Decision-curve analysis can express threshold-dependent net benefit, but our DCA was exploratory and internal only [12]. Together, these components support a trustworthy-evaluation framing without establishing clinical deployment readiness.

The main strength of the study is its explicit separation of evidence types. Internal multimodal performance, signal-only external validation, calibration, uncertainty triage, XAI, DCA, and structured-feature reconstruction were not collapsed into one broad validation claim. This separation reduces the chance of overstating the work and makes the reproducibility problem visible. It also provides a practical template for ECG multimodal studies that rely on released structured feature resources but want to test signal models on external waveform datasets.

Several limitations remain. First, the internal multimodal gain depends on released PTB-XL+ structured features, and exact external reconstruction of those features was not achieved. Second, external validation was signal-only and label-subset based; it did not test multimodal fusion outside PTB-XL/PTB-XL+. Third, thresholds and temperatures were transferred from internal validation, which avoids external test-set tuning but may reduce F1 in external low-prevalence labels. Fourth, XAI and DCA analyses were post-hoc and internal, so they should be treated as interpretive and exploratory rather than confirmatory. Fifth, the current draft reports a public-data retrospective evaluation; it does not assess workflow integration, clinician interaction, prospective performance, or patient outcomes.

Future work should focus on obtaining or reconstructing an exact PTB-XL+ compatible feature-generation pipeline before attempting external multimodal validation. A second priority is prospective or multi-institutional validation with pre-specified label mappings, calibration assessment, and decision thresholds. Until those steps are completed, the appropriate framing is internal multimodal complementarity with signal-level external validation and a transparent reproducibility audit.

## Conclusions

A fair internal PTB-XL/PTB-XL+ evaluation showed that combining ECG signal embeddings with released structured ECG-derived features improved cardiac risk stratification over either modality alone. Simple concat captured the main internal multimodal gain, while gated fusion did not show a statistically clear additional advantage. Signal-only external validation was completed on CPSC2018 and Chapman-Shaoxing, but external multimodal validation remains NO-GO because exact PTB-XL+ compatible structured feature reconstruction was not validated. These findings support a reproducibility-aware decision-support framing and require conservative manuscript wording.

## Supplementary Information

Suggested supplementary materials include external signal calibration tables, Stage 14L concordant-subset audit outputs, structured-feature reproducibility diagnostics, all per-class metrics, all calibration bins, uncertainty triage source data, DCA source data, and XAI case reports.

## Suggested Tables and Figures

**Table 1. Internal model performance.** Source: `tables/table_stage8_ablation_comparison.csv`.

**Table 2. Gated versus fair concat paired bootstrap analysis.** Source: `tables/table_gated_vs_fair_concat_paired_bootstrap.csv`.

**Table 3. Signal-only external validation on CPSC2018 and Chapman-Shaoxing.** Sources: `tables/table_external_signal_results.csv` and `tables/table_stage15_external_signal_per_class_diagnostics.csv`.

**Figure 1. Reproducibility-aware ECG decision-support framework and data flow.** Sources: `figures/source_data/fig1_framework_nodes.csv` and `figures/source_data/fig1_framework_edges.csv`.

**Figure 2. Internal full-schema PTB-XL/PTB-XL+ model performance.** Source: `figures/source_data/fig2_model_performance_long.csv`.

**Figure 3. Internal calibration and reliability analysis.** Sources: `figures/source_data/fig4_calibration_long.csv` and `results/calibration/reliability_curve_source_data.csv`.

**Figure 4. Internal uncertainty triage.** Source: `figures/source_data/fig5_uncertainty_risk_coverage.csv`.

**Figure 5. Dual-modality post-hoc interpretability examples.** Source: `figures/source_data/fig6_xai_case_source_data.csv`.

**Supplementary Table S1. External signal-only calibration.** Sources: `tables/table_stage15_external_signal_calibration.csv` and `tables/table_stage15_external_signal_reliability.csv`.

**Supplementary Table S2. Structured-feature reproducibility audit.** Sources: `tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv` and `tables/stage14l_feature_manifest.csv`.

## Draft Tables

**Table 1. Internal model performance.** Internal PTB-XL/PTB-XL+ performance under frozen splits. AP denotes average precision.

| Model | Validation AUROC | Test AUROC | Test AP | Test F1 |
|:---|---:|---:|---:|---:|
| strong signal-only | 0.9114 | 0.9098 | 0.7721 | 0.6998 |
| signal-embedding MLP | 0.9125 | 0.9094 | 0.7724 | 0.7002 |
| structured MLP | 0.9085 | 0.9046 | 0.7652 | 0.6899 |
| fair MLP-concat | 0.9227 | 0.9193 | 0.7953 | 0.7208 |
| gated fusion MLP | 0.9231 | 0.9196 | 0.7978 | 0.7255 |

**Table 2. Gated versus fair concat paired bootstrap analysis.** Delta is gated fusion minus fair concat on the frozen internal test set.

| Metric | Fair concat | Gated fusion | Delta gated-fair | 95% CI | CI contains 0 |
|:---|---:|---:|---:|:---|:---|
| AUROC | 0.9193 | 0.9196 | 0.0003 | -0.0015 to 0.0021 | yes |
| AP | 0.7953 | 0.7978 | 0.0025 | -0.0014 to 0.0070 | yes |
| F1 | 0.7208 | 0.7255 | 0.0047 | -0.0044 to 0.0142 | yes |

**Table 3. Signal-only external validation.** Macro rows summarize per-class performance and do not correspond to one per-class threshold. Thresholds were transferred from PTB-XL validation or existing validation-derived rules.

| Dataset | Label | N | Positive count | AUROC | AP | F1 | Threshold | Threshold source |
|:---|:---|---:|---:|---:|---:|---:|---:|:---|
| CPSC2018 | macro | 9,944 | 3,776 | 0.9071 | 0.6509 | 0.5904 |  | PTB-XL validation |
| CPSC2018 | NORM | 9,944 | 891 | 0.9119 | 0.5256 | 0.4344 | 0.42 | PTB-XL validation |
| CPSC2018 | CD | 9,944 | 2,885 | 0.9022 | 0.7763 | 0.7464 | 0.51 | PTB-XL validation |
| Chapman-Shaoxing | macro | 45,150 | 3,932 | 0.8742 | 0.1727 | 0.1650 |  | PTB-XL validation |
| Chapman-Shaoxing | MI | 45,150 | 123 | 0.9349 | 0.0796 | 0.0277 | 0.30 | PTB-XL validation |
| Chapman-Shaoxing | CD | 45,150 | 3,058 | 0.8388 | 0.2624 | 0.3319 | 0.51 | PTB-XL validation |
| Chapman-Shaoxing | HYP | 45,150 | 751 | 0.8488 | 0.1760 | 0.1353 | 0.34 | PTB-XL validation |

**Supplementary Table S1. External signal-only calibration.** Temperature scaling was fit on internal validation predictions and evaluated externally without refitting.

| Dataset | N | Labels | Macro Brier | Micro Brier | Macro ECE | Macro MCE | Temperature source |
|:---|---:|:---|---:|---:|---:|---:|:---|
| CPSC2018 | 9,944 | NORM, CD | 0.1268 | 0.1268 | 0.1262 | 0.4099 | internal validation temperature scaling |
| Chapman-Shaoxing | 45,150 | MI, CD, HYP | 0.0855 | 0.0855 | 0.1412 | 0.7277 | internal validation temperature scaling |

**Supplementary Table S2. Structured-feature reproducibility audit.** The reduced schema used 138 allclose features and was classified as NO-GO for external multimodal validation.

| Model | Reduced features | Test AUROC | Test AP | Test F1 |
|:---|---:|---:|---:|---:|
| stage14l_signal_embedding_mlp | 138 | 0.9094 | 0.7722 | 0.6981 |
| stage14l_structured_mlp | 138 | 0.5704 | 0.3045 | 0.0000 |
| stage14l_fair_concat_mlp | 138 | 0.9097 | 0.7731 | 0.6938 |

| Dataset | Signal records | Candidate structured records | Joinable records | Coverage | Status |
|:---|---:|---:|---:|---:|:---|
| CPSC2018 | 9,944 | 2 | 2 | 0.000201 | not evaluated, external coverage NO-GO |
| Chapman-Shaoxing | 45,150 | 2 | 2 | 0.000044 | not evaluated, external coverage NO-GO |

## Acknowledgements

To be completed by the authors.

## Authors' contributions

To be completed by the authors.

## Funding

To be completed by the authors.

## Availability of data and materials

PTB-XL, PTB-XL+, CPSC2018, and Chapman-Shaoxing are public ECG resources. Project scripts, processed result tables, and audit outputs are organized in the local repository. External multimodal structured feature tables are not available because exact PTB-XL+ compatible external reconstruction was not validated.

## Ethics approval and consent to participate

This draft uses public, de-identified datasets. Dataset-specific ethics and consent statements should be checked against the original data descriptors before submission.

## Consent for publication

Not applicable for this public-data analysis draft, pending target-journal requirements.

## Competing interests

The authors declare no competing interests. This statement should be confirmed before submission.

## References

1. Wagner P, Strodthoff N, Bousseljot RD, Kreiseler D, Lunze FI, Samek W, Schaeffter T. PTB-XL, a large publicly available electrocardiography dataset. Scientific Data. 2020;7:154. doi:10.1038/s41597-020-0495-6.
2. Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PCh, Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. PhysioBank, PhysioToolkit, and PhysioNet. Circulation. 2000;101:e215-e220.
3. Strodthoff N, Mehari T, Nagel C, Aston PJ, Sundar A, Graff C, Kanters JK, Haverkamp W, Doessel O, Loewe A, Baer M, Schaeffter T. PTB-XL+, a comprehensive electrocardiographic feature dataset. Scientific Data. 2023;10:279. doi:10.1038/s41597-023-02153-8.
4. Pilia N, Nagel C, Lenis G, Becker S, Doessel O, Loewe A. ECGdeli: An open source ECG delineation toolbox for MATLAB. SoftwareX. 2021;13:100639. doi:10.1016/j.softx.2020.100639.
5. Strodthoff N, Wagner P, Schaeffter T, Samek W. Deep learning for ECG analysis: benchmarks and insights from PTB-XL. IEEE Journal of Biomedical and Health Informatics. 2021;25:1519-1528. doi:10.1109/JBHI.2020.3022989.
6. Alday EAP, Gu A, Shah AJ, Robichaux C, Wong A-KI, Liu C, Liu F, Bahrami Rad A, Elola A, Seyedi S, et al. Classification of 12-lead ECGs: the PhysioNet/Computing in Cardiology Challenge 2020. Physiological Measurement. 2020;41:124003. doi:10.1088/1361-6579/abc960.
7. Liu F, Liu C, Zhao L, Zhang X, Wu X, Xu X, Liu Y, Ma C, Wei S, He Z, Li J, Kwee Ng EYK. An open access database for evaluating the algorithms of electrocardiogram rhythm and morphology abnormality detection. Journal of Medical Imaging and Health Informatics. 2018;8:1368-1373. doi:10.1166/jmihi.2018.2442.
8. Zheng J, Zhang J, Danioko S, Yao H, Guo H, Rakovski C. A 12-lead electrocardiogram database for arrhythmia research covering more than 10,000 patients. Scientific Data. 2020;7:48. doi:10.1038/s41597-020-0386-x.
9. Guo C, Pleiss G, Sun Y, Weinberger KQ. On calibration of modern neural networks. Proceedings of the 34th International Conference on Machine Learning. 2017;70:1321-1330.
10. Selvaraju RR, Cogswell M, Das A, Vedantam R, Parikh D, Batra D. Grad-CAM: Visual explanations from deep networks via gradient-based localization. IEEE International Conference on Computer Vision. 2017:618-626.
11. Lundberg SM, Lee S-I. A unified approach to interpreting model predictions. Advances in Neural Information Processing Systems. 2017;30.
12. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. Medical Decision Making. 2006;26:565-574. doi:10.1177/0272989X06295361.
