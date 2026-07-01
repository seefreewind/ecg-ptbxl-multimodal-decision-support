# ECG / PTB-XL 项目当前工作结果汇总

生成日期：2026-06-28

## 1. 当前项目阶段

本项目当前已经完成 PTB-XL 原始数据接入、Stage 0/1 数据验证与准备、signal-only baseline、PTB-XL+ 泄漏安全验证与对齐、structured-only baseline、late-probability concat baseline、Stage 6A fair MLP-concat baseline、Stage 7 gated fusion baseline，以及 Stage 8 ablation 的工程化实验。

当前尚未进入论文正文写作阶段。当前结果可以支持 PTB-XL internal signal-only、structured-only、late-probability concat、fair MLP-concat、gated fusion baseline 与 ablation 的工程记录，但仍不能支持 calibration、XAI、uncertainty、DCA 或 external validation 结论。

## 2. 数据状态

PTB-XL 原始数据已经放置并通过检查：

- `ptbxl_database.csv`: found
- `scp_statements.csv`: found
- `records100/`: found
- `records500/`: found

Stage 0/1 关键验证结果：

- metadata rows: 21799
- waveform files checked/found: 20/20
- SCP parse failures: 0
- strat_fold: available
- train / val / test split: generated

标签阳性样本数：

| label | positive count |
|---|---:|
| NORM | 9514 |
| MI | 5469 |
| STTC | 5235 |
| CD | 4898 |
| HYP | 2649 |

数据划分：

| split | rows |
|---|---:|
| train | 17418 |
| validation | 2183 |
| test | 2198 |

## 3. PTB-XL+ 当前状态

PTB-XL+ 已经补齐并通过泄漏安全验证与对齐：

- PTB-XL+ found: yes
- selected feature file: `features/ecgdeli_features.csv`
- selected feature role: `allowed_feature_table`
- aligned multimodal samples: 21799
- kept structured feature columns: 531

当前已经完成 structured-only baseline、late-probability concat baseline、fair MLP-concat baseline、gated fusion baseline 和 ablation。仍然不能声称以下内容已经完成：

- calibration 结果
- SHAP / Grad-CAM 解释性结果
- uncertainty 结果
- DCA 结果
- external validation 结果
- multimodal ESWA 结论

## 4. 已完成工程模块

新增或完善的主要代码文件：

- `src/models/signal_resnet.py`
- `src/training/train_signal.py`
- `src/training/metrics.py`
- `src/training/run_signal_repeated.py`
- `src/training/bootstrap_signal_metrics.py`
- `configs/model_signal_resnet.yaml`
- `scripts/02_train_signal_baseline.sh`
- `scripts/03_run_signal_repeated_seeds.sh`
- `scripts/04_bootstrap_signal_metrics.sh`
- `tests/test_signal_baseline.py`
- `src/data/validate_ptbxl_plus.py`
- `src/data/align_ptbxl_plus.py`
- `src/training/train_structured.py`
- `configs/model_structured_logistic.yaml`
- `scripts/05_train_structured_baseline.sh`
- `tests/test_structured_baseline.py`
- `src/training/train_concat_fusion.py`
- `configs/model_concat_fusion.yaml`
- `scripts/06_train_concat_fusion_baseline.sh`
- `tests/test_concat_fusion_baseline.py`
- `src/features/extract_signal_embeddings.py`
- `src/features/build_fusion_dataset.py`
- `src/models/fusion_mlp.py`
- `src/training/train_fair_concat_fusion.py`
- `configs/extract_signal_embeddings.yaml`
- `configs/fair_fusion_dataset.yaml`
- `configs/model_fair_concat_mlp.yaml`
- `scripts/06a_check_strong_signal_checkpoint.sh`
- `scripts/06b_extract_signal_embeddings.sh`
- `scripts/06c_build_fair_fusion_dataset.sh`
- `scripts/06d_train_fair_concat_mlp.sh`
- `scripts/06e_run_fair_concat_repeated_seeds.sh`
- `scripts/06f_bootstrap_fair_concat_metrics.sh`
- `tests/test_signal_embedding_extraction.py`
- `tests/test_fair_fusion_dataset.py`
- `tests/test_fair_concat_fusion.py`
- `tests/test_fusion_fairness_audit.py`
- `src/models/gated_fusion.py`
- `src/training/train_gated_fusion.py`
- `configs/model_gated_fusion.yaml`
- `scripts/07_train_gated_fusion_baseline.sh`
- `scripts/07b_run_gated_fusion_repeated_seeds.sh`
- `scripts/07c_bootstrap_gated_fusion_metrics.sh`
- `tests/test_gated_fusion_baseline.py`
- `src/training/train_ablation_mlp.py`
- `configs/model_signal_embedding_mlp.yaml`
- `configs/model_structured_mlp.yaml`
- `scripts/08a_train_signal_embedding_mlp.sh`
- `scripts/08b_train_structured_mlp.sh`
- `scripts/08c_run_ablation_repeated_seeds.sh`
- `scripts/08d_build_ablation_summary.sh`
- `tests/test_ablation_mlp.py`

同时修复了数据阶段脚本对 `python` 命令的硬编码问题，使脚本使用 `${PYTHON:-python3}`。

## 5. Signal-Only Baseline 设置

模型：

- lightweight 1D ResNet
- 输入：PTB-XL 100 Hz 12 导联 ECG waveform
- 输出：NORM / MI / STTC / CD / HYP 五类多标签预测

主实验配置：

- config: `configs/model_signal_resnet.yaml`
- epochs: 2
- max training batches per epoch: 200
- evaluation: full validation and full test splits
- device: CPU
- seeds for repeated run: 2026, 2027, 2028

主运行命令：

```bash
bash scripts/02_train_signal_baseline.sh
bash scripts/03_run_signal_repeated_seeds.sh
bash scripts/04_bootstrap_signal_metrics.sh
```

## 6. 单次 Signal Baseline 结果

输出文件：

- `results/internal/signal_baseline_metrics.csv`
- `tables/table_signal_baseline_results.csv`
- `results/internal/signal_val_predictions.csv`
- `results/internal/signal_test_predictions.csv`
- `results/internal/signal_training_history.csv`
- `results/internal/signal_run_summary.json`
- `results/internal/signal_resnet.pt`

训练历史：

| epoch | train loss |
|---:|---:|
| 1 | 0.398897 |
| 2 | 0.336142 |

Macro 结果：

| split | AUROC | average precision | F1 | positive count |
|---|---:|---:|---:|---:|
| validation | 0.864554 | 0.694140 | 0.594134 | 2786 |
| test | 0.861169 | 0.686688 | 0.587899 | 2792 |

## 7. Repeated-Seed 结果

输出文件：

- `results/internal/repeated_signal/signal_repeated_seed_metrics.csv`
- `results/internal/repeated_signal/signal_repeated_seed_summary.csv`
- `tables/table_signal_repeated_seed_summary.csv`

Seeds:

- 2026
- 2027
- 2028

Macro 汇总：

| split | AUROC mean | AUROC SD | average precision mean | average precision SD | F1 mean | F1 SD |
|---|---:|---:|---:|---:|---:|---:|
| validation | 0.869983 | 0.005805 | 0.693737 | 0.009061 | 0.559386 | 0.046348 |
| test | 0.867312 | 0.005667 | 0.693882 | 0.008971 | 0.556056 | 0.049003 |

## 8. Bootstrap 置信区间

输出文件：

- `results/internal/signal_bootstrap_ci.csv`
- `tables/table_signal_bootstrap_ci.csv`

Bootstrap 设置：

- resamples: 500
- source: single-run validation/test prediction files

结果：

| split | metric | estimate | 95% CI lower | 95% CI upper |
|---|---|---:|---:|---:|
| validation | AUROC | 0.864554 | 0.854467 | 0.874621 |
| validation | average precision | 0.694140 | 0.677014 | 0.716326 |
| validation | F1 | 0.594134 | 0.575028 | 0.614136 |
| test | AUROC | 0.861169 | 0.850141 | 0.871500 |
| test | average precision | 0.686688 | 0.668415 | 0.705445 |
| test | F1 | 0.587899 | 0.567305 | 0.607269 |

## 9. 测试与验证

当前测试命令：

```bash
python3 -m pytest tests/test_signal_baseline.py -q
```

最近一次验证结果：

```text
5 passed
```

测试覆盖内容：

- SignalResNet 输出形状
- multilabel metrics schema
- training dry-run 输出文件
- repeated-seed 汇总
- bootstrap CI 计算

## 10. 目前可用于后续论文准备的内容

可以作为工程结果保存：

- PTB-XL 数据准备流程
- signal-only baseline 模型代码
- signal-only internal validation/test 指标
- repeated-seed 稳定性结果
- bootstrap 置信区间
- checkpoint 和预测明细
- PTB-XL+ 泄漏安全文件筛选结果
- PTB-XL / PTB-XL+ 对齐结果
- structured-only baseline 模型代码与内部验证/测试指标
- late-probability concat baseline 模型代码与内部验证/测试指标
- fair MLP-concat baseline 模型代码、repeated-seed 结果与 bootstrap 置信区间
- gated fusion baseline 模型代码、repeated-seed 结果与 bootstrap 置信区间
- fair-interface ablation 结果

但在 calibration / XAI / uncertainty / DCA / external validation 完成之前，只能谨慎表述为：

```text
PTB-XL internal signal-only, structured-only, late-probability concat, fair MLP-concat, gated fusion, and ablation engineering results.
```

不能表述为：

```text
Interpretable multimodal decision-support framework completed.
```

## 11. 下一步建议

如果继续工程推进，优先级如下：

1. Stage 9B 已补齐五个主模型 validation/test logits，并完成 validation-only temperature scaling。
2. 下一步进入 uncertainty / risk-coverage triage。
3. 之后依次考虑 XAI、DCA 和 external validation。
4. 在上述核心实验完成前，不建议开始写多模态论文结果部分。

## 12. Stage 9 calibration / reliability 当前结果

已完成 Stage 9 raw calibration 和 reliability analysis。

新增总结文件：

- `results/stage9_calibration_summary.md`
- `docs/REVISED_MULTIMODAL_STORY.md`

核心输出：

- `results/calibration/prediction_manifest.csv`
- `results/calibration/calibration_metrics_raw.csv`
- `results/calibration/calibration_metrics_temperature_scaled.csv`
- `results/calibration/calibration_metrics_bins_sensitivity.csv`
- `results/calibration/calibration_bootstrap_ci.csv`
- `results/calibration/reliability_curve_source_data.csv`
- `results/calibration/confidence_histogram_source_data.csv`
- `results/calibration/gated_vs_fair_concat_paired_bootstrap.csv`
- `tables/table_calibration_raw.csv`
- `tables/table_calibration_temperature_scaled.csv`
- `tables/table_calibration_delta.csv`
- `tables/table_calibration_bootstrap_ci.csv`
- `tables/table_gated_vs_fair_concat_calibration.csv`
- `tables/table_gated_vs_fair_concat_paired_bootstrap.csv`
- `figures/calibration/reliability_comparison_main_models.png`
- per-model reliability / confidence histogram PNG files in `figures/calibration/`

主模型 frozen test raw calibration：

| model | macro Brier | macro ECE |
|---|---:|---:|
| strong_signal_only | 0.091046 | 0.037004 |
| signal_embedding_mlp | 0.089572 | 0.038058 |
| structured_mlp | 0.094392 | 0.026258 |
| fair_concat_mlp | 0.088112 | 0.042286 |
| gated_fusion_mlp | 0.085785 | 0.035572 |

Temperature scaling 状态：

- fitted: 0
- skipped: 5
- 原因：当前五个主模型 prediction CSV 只有 probability columns，没有 per-class logits。
- 因此 `temperature_scaled` 表当前是 raw-probability carry-through，不应声称温度缩放改善了校准。

Gated fusion vs fair concat 配对 bootstrap：

| metric | delta gated - fair concat | 95% CI lower | 95% CI upper | CI contains 0 |
|---|---:|---:|---:|---|
| AUROC | 0.000319 | -0.001528 | 0.002108 | yes |
| AP | 0.002489 | -0.001366 | 0.007008 | yes |
| F1 | 0.004702 | -0.004387 | 0.014180 | yes |

Stage 9 结论：

```text
Gated fusion has no statistically clear advantage over fair MLP-concat on the frozen test set.
The paper should not use "gated fusion is superior" as the central claim.
```

当前更稳妥的论文叙事：

```text
Strict fair multimodal evaluation shows that ECG signal embeddings and PTB-XL+ structured features are complementary.
Simple fair concat already captures the main multimodal gain over either single modality.
Gated fusion does not provide a statistically clear additional advantage.
The decision-support novelty should come from calibration, uncertainty, interpretability, DCA, and external validation.
```

最近一次验证：

```bash
python3 -m pytest tests/ -q
```

结果：

```text
44 passed, 110 warnings
```

## 13. Stage 9B logits export / temperature scaling 当前结果

已完成 Stage 9B。

新增总结与设计文件：

- `results/stage9b_logits_temperature_summary.md`
- `docs/UNCERTAINTY_TRIAGE_PLAN.md`

新增/更新代码与脚本：

- `src/evaluation/export_predictions_with_logits.py`
- `scripts/09e_export_main_model_logits.sh`
- `src/evaluation/collect_model_predictions.py`
- `src/evaluation/temperature_scaling.py`
- `src/evaluation/evaluate_calibration.py`
- `src/evaluation/bootstrap_calibration.py`

五个主模型 logits 导出状态：

| model | val rows | test rows | logits | probabilities |
|---|---:|---:|---|---|
| strong_signal_only | 2183 | 2198 | yes | yes |
| signal_embedding_mlp | 2183 | 2198 | yes | yes |
| structured_mlp | 2183 | 2198 | yes | yes |
| fair_concat_mlp | 2183 | 2198 | yes | yes |
| gated_fusion_mlp | 2183 | 2198 | yes | yes |

manifest 当前状态：

- `logit_columns_available = true` for five main models
- `temperature_scaling_eligible = true` for five main models
- `late_probability_concat` remains supplementary and probability-only

Temperature scaling：

- fitted models: 5
- type: per-class temperature
- fitting split: validation
- frozen test role: transform/evaluation only

Frozen test raw vs temperature-scaled calibration：

| model | raw Brier | scaled Brier | raw ECE | scaled ECE |
|---|---:|---:|---:|---:|
| strong_signal_only | 0.091046 | 0.090266 | 0.037004 | 0.031984 |
| signal_embedding_mlp | 0.089572 | 0.088321 | 0.038058 | 0.021689 |
| structured_mlp | 0.094392 | 0.094208 | 0.026258 | 0.021226 |
| fair_concat_mlp | 0.088112 | 0.086356 | 0.042286 | 0.028284 |
| gated_fusion_mlp | 0.085785 | 0.084421 | 0.035572 | 0.019276 |

Best frozen test macro ECE：

- raw: `structured_mlp`, 0.026258
- temperature-scaled: `gated_fusion_mlp`, 0.019276

解释边界：

```text
Temperature scaling improved calibration metrics, especially macro ECE, but this should be treated as methodological completeness for trustworthy decision support.
It does not establish clinical readiness and does not change the earlier paired-bootstrap conclusion that gated fusion has no statistically clear discriminative advantage over fair concat.
```

最近一次验证：

```bash
python3 -m pytest tests/ -q
```

结果：

```text
51 passed, 110 warnings
```

## 14. Stage 10 uncertainty / risk-coverage triage 当前结果

已完成 Stage 10。

本阶段总结文件：

- `results/uncertainty/summary.md`

新增/更新代码：

- `src/evaluation/uncertainty.py`
- `src/evaluation/evaluate_uncertainty_triage.py`
- `src/evaluation/select_triage_cutoffs.py`
- `src/evaluation/risk_coverage.py`
- `src/evaluation/plot_uncertainty_triage.py`
- `src/evaluation/bootstrap_uncertainty_triage.py`

新增脚本：

- `scripts/10_evaluate_uncertainty_triage.sh`
- `scripts/10b_plot_uncertainty_triage.sh`
- `scripts/10c_bootstrap_uncertainty_triage.sh`

主分析模型：

- `strong_signal_only`
- `fair_concat_mlp`
- `gated_fusion_mlp`

补充模型：

- `signal_embedding_mlp`
- `structured_mlp`

主 probability mode：

- `temperature_scaled`

主 uncertainty score：

- `entropy_macro`

coverage levels：

- 100%, 90%, 80%, 70%, 60%, 50%

关键纪律：

- triage cutoffs 只在 validation 选择；
- frozen test 只做最终评估；
- 100% coverage 明确保留全部 test 样本；
- 未做 XAI、DCA、external validation；
- 未写论文正文。

主模型 frozen test risk-coverage 结果：

| model | coverage | retained AUROC | retained F1 | referral fraction | retained Brier | retained ECE |
|---|---:|---:|---:|---:|---:|---:|
| strong_signal_only | 100% | 0.909815 | 0.710207 | 0.000000 | 0.090266 | 0.031984 |
| strong_signal_only | 80% | 0.923722 | 0.741959 | 0.201092 | 0.073534 | 0.025553 |
| fair_concat_mlp | 100% | 0.919251 | 0.724041 | 0.000000 | 0.086356 | 0.028284 |
| fair_concat_mlp | 80% | 0.931531 | 0.757469 | 0.201092 | 0.069775 | 0.022498 |
| gated_fusion_mlp | 100% | 0.919570 | 0.731378 | 0.000000 | 0.084421 | 0.019276 |
| gated_fusion_mlp | 80% | 0.930250 | 0.759668 | 0.200637 | 0.068678 | 0.016064 |

80% coverage 解读：

- `gated_fusion_mlp` retained F1 最高：0.759668；
- `fair_concat_mlp` retained AUROC 最高：0.931531；
- 两个多模态模型均优于 strong signal-only；
- 仍不能把 gated fusion 写成判别性能显著优于 fair concat。

referred subset 结论：

```text
At 80% coverage, referred ECGs show high error rates and enriched abnormal-label prevalence, supporting the workflow interpretation that low-confidence ECGs should be routed to clinician review.
```

生成结果：

- `results/uncertainty/triage_cutoffs_validation.csv`
- `results/uncertainty/risk_coverage_metrics_validation.csv`
- `results/uncertainty/risk_coverage_metrics_test.csv`
- `results/uncertainty/referred_subset_characteristics.csv`
- `results/uncertainty/risk_coverage_curve_source_data.csv`
- `results/uncertainty/uncertainty_triage_bootstrap_ci.csv`
- `tables/table_uncertainty_triage.csv`
- `tables/table_uncertainty_score_comparison.csv`
- `tables/table_referred_subset_characteristics.csv`
- `tables/table_decision_support_triage_summary.csv`
- `tables/table_uncertainty_triage_bootstrap_ci.csv`
- `figures/uncertainty/risk_coverage_macro_f1.png`
- `figures/uncertainty/risk_coverage_macro_auroc.png`
- `figures/uncertainty/risk_coverage_referral_tradeoff.png`
- `figures/uncertainty/risk_coverage_main_models.png`

最近一次验证：

```bash
python3 -m pytest tests/ -q
```

结果：

```text
60 passed, 110 warnings
```

下一步：

```text
Proceed to XAI.
```

## 15. Stage 11 dual-modality XAI 当前结果

已完成 Stage 11。

总结文件：

- `results/stage11_xai_summary.md`

主模型/辅助模型：

- `strong_signal_only`: signal-side waveform attribution
- `structured_mlp`: structured feature attribution
- `fair_concat_mlp`: multimodal structured attribution
- `gated_fusion_mlp`: structured attribution, gate weights, unified case explanations

病例选择：

- total cases: 12
- retained cases: 5
- referred cases: 7
- correct cases: 5
- incorrect cases: 7

病例类型：

- high-confidence retained correct: 3
- high-confidence retained incorrect: 2
- low-confidence referred incorrect: 3
- low-confidence referred multi-label abnormal: 2
- modality-disagreement case: 2

归因方法：

- structured attribution: `gradient_x_input`
- signal attribution: `saliency_gradient_x_input`
- gate weight: frozen gated checkpoint forward export

主要输出：

- `results/xai/xai_case_selection.csv`
- `results/xai/structured_attribution_values.csv`
- `results/xai/structured_case_attributions.csv`
- `results/xai/signal_attribution_values.npz`
- `results/xai/signal_case_attribution_summary.csv`
- `results/xai/gated_gate_weights_test.csv`
- `results/xai/unified_case_explanations.csv`
- `tables/table_xai_case_selection.csv`
- `tables/table_top_structured_features_global.csv`
- `tables/table_top_structured_features_by_label.csv`
- `tables/table_signal_lead_importance.csv`
- `tables/table_gate_weight_summary.csv`
- `tables/table_unified_xai_cases.csv`
- `tables/table_xai_uncertainty_link.csv`
- `figures/xai/fig_xai_representative_cases.png`
- `figures/xai/structured_feature_importance_global.png`
- `figures/xai/structured_feature_importance_by_label.png`
- `figures/xai/gate_weight_distribution.png`
- `figures/xai/xai_uncertainty_examples.png`
- per-case signal heatmaps and structured waterfall plots in `figures/xai/`

Gate weight summary at 80% triage：

| group | n | mean signal gate | mean structured gate |
|---|---:|---:|---:|
| retained | 1757 | 0.694655 | 0.305345 |
| referred | 441 | 0.702257 | 0.297743 |

解释边界：

```text
XAI outputs are post-hoc attributions for transparency and auditing.
They are not causal explanations and do not establish clinical readiness.
```

下一步：

```text
Proceed to DCA.
```

## 16. Stage 11A figure source-data infrastructure 当前结果

已完成 Stage 11A。

总结文件：

- `results/stage11a_figure_source_data_summary.md`

Figure master plan：

- `docs/FIGURE_MASTER_PLAN.md`

新增代码：

- `src/figures/build_figure_source_data.py`
- `src/figures/plot_main_figures.py`
- `src/figures/check_figure_source_data.py`
- `src/figures/ecg_feature_grouping.py`

新增脚本：

- `scripts/12_build_figure_source_data.sh`
- `scripts/12b_plot_main_figures.sh`
- `scripts/12c_check_figure_source_data.sh`

source-data manifest：

- `figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv`

manifest 状态：

- ready source-data entries: 16
- pending DCA entries: 1
- pending external validation entries: 1

主图 source data：

- `figures/source_data/fig1_framework_nodes.csv`
- `figures/source_data/fig1_framework_edges.csv`
- `figures/source_data/fig2_model_performance_long.csv`
- `figures/source_data/fig2_per_class_dotplot.csv`
- `figures/source_data/fig2_paired_bootstrap.csv`
- `figures/source_data/fig3_ablation_long.csv`
- `figures/source_data/fig3_prediction_similarity_matrix.csv`
- `figures/source_data/fig4_calibration_long.csv`
- `figures/source_data/fig4_reliability_curve.csv`
- `figures/source_data/fig4_confidence_histogram.csv`
- `figures/source_data/fig5_uncertainty_risk_coverage.csv`
- `figures/source_data/fig5_referred_subset_characteristics.csv`
- `figures/source_data/fig6_xai_case_source_data.csv`
- `figures/source_data/fig6_structured_feature_group_attribution.csv`
- `figures/source_data/fig6_signal_heatmap_index.csv`
- `figures/source_data/fig7_gate_weight_modality_interaction.csv`

初版主图：

- `figures/main/fig2_model_performance.png`
- `figures/main/fig3_ablation_complementarity.png`
- `figures/main/fig4_calibration.png`
- `figures/main/fig5_uncertainty_triage.png`

补充 source data：

- `figures/source_data/supplementary/supp_table_all_model_metrics.csv`
- `figures/source_data/supplementary/supp_table_all_per_class_metrics.csv`
- `figures/source_data/supplementary/supp_table_all_uncertainty_scores.csv`
- `figures/source_data/supplementary/supp_table_all_calibration_bins.csv`
- `figures/source_data/supplementary/supp_table_all_bootstrap_ci.csv`
- `figures/source_data/supplementary/supp_table_all_thresholds.csv`

QC：

- `results/figure_source_data_qc_report.md`
- `tables/table_figure_source_data_qc.csv`
- failed checks: 0

叙事一致性：

```text
No clinical-readiness claim.
No positive gated-superiority claim.
Late-probability concat remains supplementary.
Uncertainty triage is framed as validation-cutoff / frozen-test decision support.
XAI is framed as post-hoc analysis.
DCA and external validation remain pending.
```

下一步：

```text
Proceed to DCA.
```

## 17. Stage 12 decision curve analysis 当前结果

已完成 Stage 12 DCA。

总结文件：

- `results/stage12_dca_summary.md`

新增代码：

- `src/evaluation/dca.py`
- `src/evaluation/evaluate_dca.py`
- `src/evaluation/plot_dca.py`
- `src/evaluation/bootstrap_dca.py`

新增脚本：

- `scripts/13_evaluate_dca.sh`
- `scripts/13b_plot_dca.sh`
- `scripts/13c_bootstrap_dca.sh`

核心输出：

- `results/dca/dca_threshold_grid.csv`
- `results/dca/dca_results_by_label.csv`
- `results/dca/dca_results_macro.csv`
- `results/dca/dca_results_retained_80_coverage.csv`
- `results/dca/dca_bootstrap_ci.csv`
- `tables/table_dca_summary.csv`
- `tables/table_dca_by_label.csv`
- `tables/table_dca_retained_80_coverage.csv`
- `tables/table_dca_bootstrap_ci.csv`

Figure 8：

- `figures/main/fig8_dca.png`
- `figures/main/fig8_dca.svg`
- `figures/source_data/fig8_dca_macro.csv`
- `figures/source_data/fig8_dca_by_label.csv`
- `figures/source_data/fig8_dca_retained_80_coverage.csv`

主分析范围：

- split: internal frozen PTB-XL test
- probability mode: temperature-scaled
- threshold range: 0.05-0.40 for main summary
- labels: NORM / MI / STTC / CD / HYP
- retained subset: Stage 10 validation-selected uncertainty cutoff at 80% coverage

mean macro net benefit, threshold 0.05-0.40：

| model | mean macro net benefit | max macro net benefit |
|---|---:|---:|
| gated_fusion_mlp | 0.189506 | 0.229864 |
| fair_concat_mlp | 0.188100 | 0.229970 |
| strong_signal_only | 0.184445 | 0.228916 |
| structured_mlp | 0.181541 | 0.228677 |

80% retained subset mean macro net benefit, threshold 0.05-0.40：

| model | mean macro net benefit |
|---|---:|
| fair_concat_mlp | 0.190911 |
| strong_signal_only | 0.190380 |
| gated_fusion_mlp | 0.190046 |
| structured_mlp | 0.182103 |

Bootstrap：

- `tables/table_dca_bootstrap_ci.csv`
- 1000 bootstrap resamples
- thresholds: 0.10 / 0.20 / 0.30 / 0.40
- metrics: macro net benefit, macro net benefit vs treat-all, macro net benefit vs treat-none

QC：

- `bash scripts/12c_check_figure_source_data.sh`
- failed checks: 0
- DCA pending manifest placeholder removed
- external validation remains pending

叙事一致性：

```text
Internal DCA supports the practical value of multimodal prediction, but gated fusion does not show a stable decision-curve advantage over fair concat.
No clinical-readiness claim.
No positive gated-superiority claim.
No external-validation claim yet.
No frozen-test tuning.
```

下一步：

```text
Proceed to external validation only after confirming external cohort label mapping and compatibility.
```

## 18. Stage 13A external validation readiness audit 当前结果

已完成 Stage 13A。该阶段只做 external validation 前置审计，没有运行正式外部验证，没有评价模型外部泛化，也没有写 clinical readiness 结论。

总结文件：

- `results/stage13a_external_readiness_summary.md`

新增 / 更新配置：

- `configs/data_external.yaml`

新增代码：

- `src/data/discover_external_datasets.py`
- `src/data/check_external_waveform_compatibility.py`
- `src/data/prepare_external_waveforms.py`

新增脚本：

- `scripts/14a_discover_external_datasets.sh`
- `scripts/14b_check_external_waveform_compatibility.sh`
- `scripts/14c_prepare_external_waveforms.sh`

外部数据发现：

- `results/external/external_dataset_discovery_report.md`
- `results/external/external_dataset_candidates.csv`

当前状态：

| dataset | found | waveform files | label files | status |
|---|---:|---:|---:|---|
| CPSC2018 | no | 0 | 0 | missing |
| Chapman-Shaoxing | no | 0 | 0 | missing |

标签映射审计：

- `docs/EXTERNAL_LABEL_MAPPING_PLAN.md`
- `tables/table_external_label_mapping_audit.csv`

当前 draft 高置信映射覆盖：

| dataset | draft high-confidence PTB-XL superclasses | not safely covered |
|---|---|---|
| CPSC2018 | NORM / CD | MI / STTC / HYP |
| Chapman-Shaoxing | NORM / MI / CD / HYP | STTC |

注意：

```text
These are draft mapping rules only. Actual external label files must confirm the same semantics before any formal external validation.
```

waveform 兼容性：

- `results/external/external_waveform_compatibility_report.md`
- `tables/table_external_waveform_compatibility.csv`

当前结果：

| dataset | 12-lead confirmed | sampling rate confirmed | duration confirmed | compatible with signal model |
|---|---:|---:|---:|---:|
| CPSC2018 | no | no | no | no |
| Chapman-Shaoxing | no | no | no | no |

structured / multimodal 兼容性：

- `results/external/external_multimodal_feasibility_report.md`
- `tables/table_external_structured_feature_compatibility.csv`

当前结果：

| dataset | structured features available | matches PTB-XL+ 531 features | fair concat allowed | gated fusion allowed |
|---|---:|---:|---:|---:|
| CPSC2018 | no | no | no | no |
| Chapman-Shaoxing | no | no | no | no |

external validation mode decision：

- `results/external/external_validation_mode_decision.md`
- `tables/table_external_validation_mode_decision.csv`

当前推荐模式：

| dataset | recommended mode | blocking issue |
|---|---|---|
| CPSC2018 | not_ready | external_raw_data_missing |
| Chapman-Shaoxing | not_ready | external_raw_data_missing |

外部处理 skeleton：

- `data/processed/external/cpsc2018_index.csv`
- `data/processed/external/cpsc2018_labels_mapped.csv`
- `data/processed/external/cpsc2018_waveform_manifest.csv`
- `data/processed/external/chapman_index.csv`
- `data/processed/external/chapman_labels_mapped.csv`
- `data/processed/external/chapman_waveform_manifest.csv`

当前这些文件均为缺失数据状态模板，不包含伪造样本。

Figure 9 readiness source data：

- `figures/source_data/fig9_external_validation_readiness.csv`
- `figures/source_data/fig9_external_label_mapping.csv`
- `figures/source_data/FIGURE_SOURCE_DATA_MANIFEST.csv`

Figure master plan 已新增：

- Figure 9. External validation readiness and label compatibility

测试：

- `tests/test_external_dataset_discovery.py`
- `tests/test_external_label_mapping.py`
- `tests/test_external_waveform_compatibility.py`
- `tests/test_external_validation_mode_decision.py`

验证命令：

```bash
bash scripts/14a_discover_external_datasets.sh
bash scripts/14b_check_external_waveform_compatibility.sh
bash scripts/14c_prepare_external_waveforms.sh
bash scripts/12c_check_figure_source_data.sh
python3 -m pytest tests/ -q
```

验证结果：

- Figure source-data QC failed checks: 0
- pytest: 95 passed

当前阻塞：

```text
external_raw_data_missing
```

叙事边界：

```text
No external generalization claim.
No clinical-readiness claim.
No multimodal external validation claim.
Do not run fair concat or gated fusion externally unless PTB-XL+ compatible structured features are available or a pre-specified missing-modality pathway is implemented and validated.
```

下一步：

```text
Place CPSC2018 and/or Chapman-Shaoxing raw data under data/raw/external/ before formal external validation.
```

## 19. Stage 13B signal-only external validation 当前结果

已完成 Stage 13B。该阶段只运行 frozen PTB-XL-trained `strong_signal_only` 模型的外部 signal-only evaluation。

重要边界：

```text
No external training.
No external fine-tuning.
No external threshold tuning.
No external model selection.
No multimodal external validation.
No clinical-readiness claim.
```

数据路径：

- CPSC2018: `/Users/zy/csbj/新高分思路/data/raw/external/cpsc2018`
- Chapman-Shaoxing: `/Users/zy/csbj/新高分思路/data/raw/external/chapman_shaoxing`

配置更新：

- `configs/data_external.yaml`

新增代码：

- `src/evaluation/evaluate_external_signal.py`

新增脚本：

- `scripts/15_evaluate_external_signal_only.sh`

新增测试：

- `tests/test_external_signal_validation.py`

核心输出：

- `results/stage13b_signal_external_validation_summary.md`
- `results/external/external_signal_metrics.csv`
- `tables/table_external_signal_results.csv`
- `results/external/cpsc2018_signal_predictions.csv`
- `results/external/chapman_signal_predictions.csv`
- `results/external/cpsc2018_signal_skipped_records.csv`
- `results/external/chapman_signal_skipped_records.csv`

外部 waveform 兼容性：

| dataset | lead count | sampling rate | duration | preprocessing |
|---|---:|---:|---:|---|
| CPSC2018 | 12 | 500 Hz | variable, sampled as 10-15 s | resample to 100 Hz and crop/pad to 1000 |
| Chapman-Shaoxing | 12 | 500 Hz | 10 s | resample to 100 Hz |

主分析标签范围：

| dataset | main external labels | reason |
|---|---|---|
| CPSC2018 | NORM / CD | high-confidence subset only |
| Chapman-Shaoxing | MI / CD / HYP | high-confidence subset only; sinus rhythm is not treated as main-analysis NORM |

可读记录：

| dataset | indexed records | evaluated records | skipped records |
|---|---:|---:|---:|
| CPSC2018 | 10330 | 9944 | 386 |
| Chapman-Shaoxing | 45151 | 45150 | 1 |

跳过记录原因：

```text
WFDB waveform reading failed for those files. No labels or predictions were imputed.
```

signal-only external macro metrics：

| dataset | AUROC | AP | F1 | evaluated records |
|---|---:|---:|---:|---:|
| CPSC2018 | 0.907082 | 0.650903 | 0.590366 | 9944 |
| Chapman-Shaoxing | 0.874167 | 0.172664 | 0.164973 | 45150 |

per-label external metrics：

| dataset | label | AUROC | AP | F1 | positives |
|---|---|---:|---:|---:|---:|
| CPSC2018 | NORM | 0.911938 | 0.525556 | 0.434362 | 891 |
| CPSC2018 | CD | 0.902226 | 0.776250 | 0.746370 | 2885 |
| Chapman-Shaoxing | MI | 0.934916 | 0.079587 | 0.027689 | 123 |
| Chapman-Shaoxing | CD | 0.838783 | 0.262426 | 0.331889 | 3058 |
| Chapman-Shaoxing | HYP | 0.848801 | 0.175980 | 0.135343 | 751 |

解释边界：

```text
These are conservative signal-only external results.
They do not support a multimodal external-validation claim.
They do not establish clinical readiness.
The external label spaces are only partially aligned with PTB-XL five-superclass labels.
```

测试：

```bash
python3 -m pytest tests/ -q
```

结果：

- pytest: 97 passed
- Figure source-data QC failed checks: 0

当前阻塞：

```text
external_structured_features_missing_for_multimodal
```

下一步：

```text
Extract or generate PTB-XL+ compatible structured ECG features for CPSC2018 / Chapman-Shaoxing before attempting multimodal external validation.
Alternatively, proceed to manuscript-level conservative reporting of signal-only external validation as a separate limitation-aware analysis.
```

## 20. Stage 14A external structured feature extraction readiness 当前结果

已完成 Stage 14A。该阶段只做外部 structured feature extraction readiness audit，没有生成伪造 structured features，也没有运行 multimodal external validation。

新增配置：

- `configs/external_structured_features.yaml`

新增代码：

- `src/data/audit_external_structured_feature_extraction.py`

新增脚本：

- `scripts/16a_audit_external_structured_feature_extraction.sh`

新增测试：

- `tests/test_external_structured_feature_extraction.py`

核心输出：

- `results/stage14a_external_structured_feature_summary.md`
- `results/external/external_structured_feature_extraction_audit.md`
- `tables/table_external_structured_feature_extraction_audit.csv`
- `data/processed/external/external_structured_feature_template_columns.txt`
- `data/processed/external/cpsc2018_structured_features_template.csv`
- `data/processed/external/chapman_structured_features_template.csv`

审计结论：

| dataset | exact PTB-XL+ 531 feature match | can run fair concat external | can run gated fusion external | blocker |
|---|---:|---:|---:|---|
| CPSC2018 | no | no | no | ecgdeli_compatible_feature_pipeline_missing |
| Chapman-Shaoxing | no | no | no | ecgdeli_compatible_feature_pipeline_missing |

工具可用性：

| tool | available |
|---|---:|
| Python ecgdeli | no |
| R ecgdeli | no |
| ecgdeli CLI | no |
| neurokit2 | no |

额外检查：

```text
R install.packages("ecgdeli") was attempted, but ecgdeli is not available for the current R version from CRAN.
```

解释边界：

```text
Approximate features from a different extractor must not be treated as PTB-XL+ compatible.
Full multimodal external validation remains blocked until an exact ecgdeli-compatible 531-column feature table is generated or provided.
```

下一步：

```text
Install/configure an exact ECGdeli/PTB-XL+ feature extraction pipeline, or obtain external feature tables with the same 531 PTB-XL+ columns, then rerun Stage 14A before attempting multimodal external validation.
```

## 21. Stage 14B ECGdeli / PTB-XL+ exact pipeline setup 当前结果

已完成 Stage 14B。该阶段已把相关仓库克隆到本地并完成 setup audit，但 exact waveform-to-PTB-XL+ 531-column feature extraction pipeline 仍不可运行。

新增配置：

- `configs/ecgdeli_pipeline.yaml`

新增代码：

- `src/data/setup_ecgdeli_pipeline.py`

新增脚本：

- `scripts/16b_setup_ecgdeli_pipeline.sh`

新增测试：

- `tests/test_ecgdeli_pipeline_setup.py`

本地仓库：

| component | local path | commit | role |
|---|---|---|---|
| PTB-XL+ feature benchmark | `tools/external_feature_extractors/ptbxl_feature_benchmark` | 4c37b775e56d23e2c844fcd0aec52d2cd05cb35e | official benchmark code |
| ECGdeli MATLAB | `tools/external_feature_extractors/ECGdeli` | c3738612771264e4d6c4686898ef7b2d6a700ad3 | official MATLAB delineation toolbox |
| pyECGdeli | `tools/external_feature_extractors/pyECGdeli` | 38d7b762237d004117d9833d32f5326a79451c91 | exploratory Python port |

环境配置更新：

- `PyWavelets` installed via user-level `python3 -m pip install --user PyWavelets`
- pyECGdeli can be imported after installing PyWavelets
- 本机已激活 MATLAB R2025a:
  - executable: `/Applications/MATLAB_R2025a.app/bin/matlab`
  - MATLAB batch smoke: passed
- 用户级 R2025a 工具箱已通过 MathWorks Package Manager 安装到:
  - `/Users/zy/.codex/tools/MATLAB/R2025a.app`
  - products: Image Processing Toolbox, Signal Processing Toolbox, Statistics and Machine Learning Toolbox, Wavelet Toolbox
- 项目采用“已激活系统 MATLAB + 用户级工具箱精确路径”的方式运行 ECGdeli。
- 注意：不要对整棵 toolbox 使用递归 `genpath`，否则会把 `eml` codegen 目录加入路径并触发旧接口错误。

关键发现：

```text
PTB-XL+ benchmark consumes downloaded ecgdeli_features.csv and does not provide the missing waveform-to-feature extraction recipe.
Official ECGdeli is MATLAB-based.
MATLAB R2025a can be called in batch mode.
Required ECGdeli-related toolbox functions are available after adding precise user-level toolbox paths.
pyECGdeli is importable but is not a complete or validated PTB-XL+ 531-feature generator.
```

输出：

- `results/stage14b_ecgdeli_pipeline_setup_summary.md`
- `tables/table_ecgdeli_pipeline_setup_audit.csv`
- `tables/table_ecgdeli_pipeline_decision.csv`

当前 blocker：

```text
ptbxl_plus_exact_feature_generation_recipe_missing
```

已解决的环境 blocker：

```text
matlab_license_missing_for_official_ecgdeli
matlab_required_toolboxes_missing_for_official_ecgdeli
```

## 21b. Stage 14D ECGdeli MATLAB smoke test 当前结果

已完成 Stage 14D。该阶段验证官方 ECGdeli MATLAB toolbox 可以在 batch mode 下运行 repository 自带示例 ECG，并生成 fiducial point table、amplitude features 和 interval features。

新增代码：

- `src/data/run_ecgdeli_smoke.py`

新增脚本：

- `scripts/16d_run_ecgdeli_smoke_test.sh`

更新配置：

- `configs/ecgdeli_pipeline.yaml`

输出：

- `results/stage14d_ecgdeli_smoke_summary.md`
- `tables/table_ecgdeli_smoke_test.csv`

Smoke test 结果：

| item | value |
|---|---:|
| passed | yes |
| samples | 115200 |
| leads | 12 |
| FPT multichannel rows | 197 |
| FPT multichannel columns | 13 |
| FPT cell leads | 12 |
| amplitude dims | [12 197 5] |
| timing dims | [12 197 7] |
| timing sync dims | [197 8] |

关键解释：

```text
This proves the local MATLAB/ECGdeli environment can run filtering, delineation, amplitude-feature, and interval-feature functions.
It does not prove exact PTB-XL+ 531-column feature reproduction.
Full multimodal external validation remains blocked until external structured feature tables pass the frozen 531-column schema gate.
```

## 22. Stage 14C external structured feature schema validation gate 当前结果

已完成 Stage 14C。该阶段建立了外部 structured feature schema validation gate，防止空表、近似特征或非 PTB-XL+ 特征误入 multimodal external validation。

新增代码：

- `src/data/validate_external_structured_features.py`

新增脚本：

- `scripts/16c_validate_external_structured_features.sh`

新增测试：

- `tests/test_external_structured_feature_schema_validation.py`

输出：

- `results/external/external_structured_feature_schema_validation_report.md`
- `tables/table_external_structured_feature_schema_validation.csv`

当前 schema gate：

| dataset | feature table exists | nonempty | exact 531 schema match | multimodal external allowed |
|---|---:|---:|---:|---:|
| CPSC2018 | no | no | no | no |
| Chapman-Shaoxing | no | no | no | no |

当前结论：

```text
Full multimodal external validation is still blocked.
Only signal-only external validation is currently valid.
```

验证：

```bash
bash scripts/16a_audit_external_structured_feature_extraction.sh
bash scripts/16b_setup_ecgdeli_pipeline.sh
bash scripts/16c_validate_external_structured_features.sh
python3 -m pytest tests/ -q
```

结果：

- pytest: 105 passed

下一步：

```text
Obtain or reconstruct the exact PTB-XL+ ECGdeli feature aggregation recipe, or provide nonempty external structured feature tables that exactly match the 531 frozen PTB-XL+ columns. Then rerun scripts/16c_validate_external_structured_features.sh before attempting fair concat or gated fusion external validation.
```

## 23. Stage 14E external ECGdeli feature prototype 当前结果

已完成 Stage 14E。该阶段在外部 CPSC2018 和 Chapman-Shaoxing 数据上运行小样本 ECGdeli feature extraction prototype，用于验证外部 WFDB 波形可以进入 MATLAB/ECGdeli 并产生可汇总的 delineation-derived features。

新增代码：

- `src/data/extract_external_ecgdeli_feature_prototype.py`

新增脚本：

- `scripts/16e_extract_external_ecgdeli_feature_prototype.sh`

新增测试：

- `tests/test_external_ecgdeli_feature_prototype.py`

输出：

- `data/processed/external/cpsc2018_ecgdeli_features_prototype.csv`
- `data/processed/external/chapman_ecgdeli_features_prototype.csv`
- `tables/table_external_ecgdeli_feature_prototype_audit.csv`
- `results/stage14e_external_ecgdeli_feature_prototype_summary.md`

Prototype 结果：

| dataset | sampled records | feature columns | schema exact match | matched PTB-XL+ required features |
|---|---:|---:|---:|---:|
| CPSC2018 | 2 | 456 | no | 0 |
| Chapman-Shaoxing | 2 | 456 | no | 0 |

关键解释：

```text
The generated files are exploratory ECGdeli prototype features only.
They use ecgdeli_proto_* column names.
They do not match the frozen PTB-XL+ 531-column schema.
They must not be used as fair concat or gated-fusion external inputs.
```

当前 blocker：

```text
ptbxl_plus_exact_531_recipe_missing
```

下一步：

```text
Map the frozen PTB-XL+ feature names to ECGdeli amplitude, interval, morphology, and summary-statistic definitions, or obtain the official aggregation recipe. Only after scripts/16c_validate_external_structured_features.sh passes on nonempty 531-column external tables can multimodal external validation proceed.
```

## 24. Stage 14F PTB-XL+ ECGdeli feature mapping audit 当前结果

已完成 Stage 14F。该阶段解析 frozen PTB-XL+ 531 structured feature names，并与已审计的 ECGdeli MATLAB 输出进行 feature-name level mapping audit。

新增代码：

- `src/data/audit_ptbxl_plus_ecgdeli_feature_mapping.py`

新增脚本：

- `scripts/16f_audit_ptbxl_plus_ecgdeli_feature_mapping.sh`

新增测试：

- `tests/test_ptbxl_plus_feature_mapping_audit.py`

输出：

- `tables/table_ptbxl_plus_ecgdeli_feature_mapping_audit.csv`
- `tables/table_ptbxl_plus_ecgdeli_feature_mapping_summary.csv`
- `tables/table_ptbxl_plus_ecgdeli_feature_mapping_decision.csv`
- `results/stage14f_ptbxl_plus_feature_mapping_audit_summary.md`

Derivability audit：

| derivability | n_features | percent |
|---|---:|---:|
| direct_ecgdeli | 420 | 79.10% |
| requires_extra_formula | 36 | 6.78% |
| requires_morphology_function | 36 | 6.78% |
| unknown_recipe | 39 | 7.34% |

解释：

```text
420 features appear structurally derivable from ECGdeli amplitude, interval, or synchronized interval outputs.
36 QT_IntCorr lead-wise features require an exact QT correction formula.
36 P_Morph features require Get_P_Morphology plus exact PTB-XL+ morphology coding/aggregation rules.
39 features remain unknown_recipe, mainly ST_Elev and HA__Global features.
```

关键限制：

```text
This is a feature-name mapping audit only.
It does not establish exact PTB-XL+ aggregation compatibility.
It does not allow multimodal external validation.
```

当前 blocker：

```text
ptbxl_plus_exact_531_recipe_missing
```

下一步：

```text
Implement a guarded candidate generator for direct_ecgdeli features only, compare generated columns against the frozen 531 schema, and leave unresolved columns missing until the exact PTB-XL+ recipe is obtained or faithfully reconstructed.
```

## 25. Stage 14G external ECGdeli direct candidate features 当前结果

已完成 Stage 14G。该阶段实现 guarded candidate generator，仅生成 Stage 14F 中标记为 `direct_ecgdeli` 的 420 个 frozen-schema 候选列。

新增代码：

- `src/data/extract_external_ecgdeli_direct_candidate.py`

新增脚本：

- `scripts/16g_extract_external_ecgdeli_direct_candidate.sh`

新增测试：

- `tests/test_external_ecgdeli_direct_candidate.py`

输出：

- `data/processed/external/cpsc2018_ecgdeli_direct_candidate_features.csv`
- `data/processed/external/chapman_ecgdeli_direct_candidate_features.csv`
- `tables/table_external_ecgdeli_direct_candidate_audit.csv`
- `tables/table_external_ecgdeli_direct_candidate_decision.csv`
- `results/stage14g_external_ecgdeli_direct_candidate_summary.md`
- `results/external/ecgdeli_direct_candidate_mat/*.mat`

候选表结果：

| dataset | sampled records | columns | direct feature columns | status |
|---|---:|---:|---:|---|
| CPSC2018 | 2 | 422 | 420 | generated |
| Chapman-Shaoxing | 2 | 422 | 420 | generated |

关键解释：

```text
The candidate files use real frozen PTB-XL+ column names for direct ECGdeli-derived features.
They intentionally omit 111 unresolved required features.
They are not registered as official external structured feature tables.
They must not be copied to cpsc2018_structured_features.csv or chapman_structured_features.csv.
Full multimodal external validation remains blocked.
```

当前 unresolved features：

```text
QT_IntCorr: 36 features require exact correction formula.
P_Morph: 36 features require exact morphology coding and aggregation rules.
ST_Elev: 36 features require exact ST elevation definition.
HA__Global: 3 features require exact HA definition.
```

当前 blocker：

```text
ptbxl_plus_exact_531_recipe_missing
```

下一步：

```text
Resolve QT_IntCorr, P_Morph, ST_Elev, and HA__Global definitions before generating complete 531-column external structured feature tables. Until then, external multimodal validation must remain blocked.
```

## 26. Stage 14H PTB-XL ECGdeli direct recomputation audit 当前结果

已完成 Stage 14H。该阶段在 PTB-XL 内部样本上重新运行本地 MATLAB/ECGdeli direct candidate generator，并把 420 个 direct feature candidates 与官方 PTB-XL+ `ecgdeli_features.csv` 对齐比较。

新增代码：

- `src/data/audit_ptbxl_ecgdeli_direct_recompute.py`

新增脚本：

- `scripts/16h_audit_ptbxl_ecgdeli_direct_recompute.sh`

新增测试：

- `tests/test_ptbxl_ecgdeli_direct_recompute_audit.py`

输出：

- `data/processed/ptbxl_ecgdeli_direct_recomputed_sample.csv`
- `tables/table_ptbxl_ecgdeli_direct_recompute_audit.csv`
- `tables/table_ptbxl_ecgdeli_direct_recompute_comparison.csv`
- `tables/table_ptbxl_ecgdeli_direct_recompute_decision.csv`
- `results/stage14h_ptbxl_ecgdeli_direct_recompute_audit_summary.md`
- `results/ptbxl_ecgdeli_direct_recompute_mat/*.mat`

关键结果：

| audit item | value |
|---|---:|
| sample PTB-XL records | 3 |
| direct features compared | 420 |
| allclose direct features | 138 |
| median feature MAE | 0.059102 |

解释：

```text
Local ECGdeli can generate the 420 direct candidate columns.
However, the recomputed direct values do not numerically match official PTB-XL+ values closely enough to claim exact reproduction.
The mismatch is not solved by feature-name mapping alone.
```

当前 blocker：

```text
ptbxl_plus_exact_531_recipe_missing
```

## 27. Stage 14I PTB-XL ECGdeli direct discrepancy diagnosis 当前结果

已完成 Stage 14I。该阶段把 Stage 14H 的 direct-feature numeric mismatch 按 feature family 和 summary statistic 聚合，定位主要偏差来源。

新增代码：

- `src/data/diagnose_ptbxl_ecgdeli_direct_discrepancy.py`

新增脚本：

- `scripts/16i_diagnose_ptbxl_ecgdeli_direct_discrepancy.sh`

新增测试：

- `tests/test_ptbxl_ecgdeli_direct_discrepancy_diagnosis.py`

输出：

- `tables/table_ptbxl_ecgdeli_direct_discrepancy_annotated_features.csv`
- `tables/table_ptbxl_ecgdeli_direct_discrepancy_by_family.csv`
- `tables/table_ptbxl_ecgdeli_direct_discrepancy_decision.csv`
- `results/stage14i_ptbxl_ecgdeli_direct_discrepancy_diagnosis_summary.md`

关键结果：

| item | value |
|---|---|
| worst discrepant family | T_DurFull:mean |
| families with any discrepancy | 32 |
| decision | direct 420 is not exact enough |

解释：

```text
Count-type features are often close, but value-type interval features, especially T/QT-related families, show substantial mismatch.
This indicates unresolved preprocessing, fiducial selection, interval definition, beat inclusion, aggregation, or missing-value handling differences.
```

当前 blocker：

```text
direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing
```

## 30. Stage 14L concordant-subset external multimodal validation 当前结果

已完成 Stage 14L。该阶段没有继续尝试完整复现 PTB-XL+ 531-column schema，而是使用 Stage 14H 中通过 PTB-XL internal recomputation allclose 检查的 structured features 构建 reproducibility-validated concordant subset。

新增代码：

- `src/evaluation/stage14l_concordant_subset.py`

新增脚本：

- `scripts/16l_run_concordant_subset_external_multimodal_validation.sh`

新增测试：

- `tests/test_stage14l_concordant_subset.py`
- `tests/test_stage14l_reduced_schema_support.py`

新增/修改的训练支持：

- `src/training/train_ablation_mlp.py` 支持显式 `expected_structured_dim`，默认仍为 531；
- `src/training/train_fair_concat_fusion.py` 支持显式 `expected_structured_dim`，默认仍为 531，并保留配置中的 model name。

主要输出：

- `docs/STAGE14L_CONCORDANT_SUBSET_SPEC.md`
- `tables/stage14l_feature_manifest.csv`
- `tables/stage14l_internal_results.csv`
- `tables/stage14l_internal_paired_bootstrap_ci.csv`
- `tables/stage14l_external_results.csv`
- `tables/stage14l_per_class_diagnostics.csv`
- `docs/STAGE14L_GO_NO_GO_DECISION.md`

reduced structured schema：

| item | value |
|---|---:|
| allclose structured features | 138 |
| source | Stage 14H |
| full 531 schema attempted | no |
| exact PTB-XL+ reproduction claim allowed | no |

内部 PTB-XL frozen test 结果：

| model | test AUROC | test AP | test F1 |
|---|---:|---:|---:|
| stage14l_signal_embedding_mlp | 0.909411 | 0.772200 | 0.698087 |
| stage14l_structured_mlp | 0.570364 | 0.304456 | 0.000000 |
| stage14l_fair_concat_mlp | 0.909666 | 0.773100 | 0.693821 |

paired bootstrap：

```text
stage14l_fair_concat_mlp vs stage14l_signal_embedding_mlp:
AUROC delta = +0.000255, 95% CI includes 0.
AP delta = +0.000899, 95% CI includes 0.
F1 delta = -0.004266, 95% CI includes 0.
```

外部 reduced-schema quality gate：

| dataset | signal prediction records | candidate structured records | joinable records | coverage |
|---|---:|---:|---:|---:|
| CPSC2018 | 9944 | 2 | 2 | 0.000201 |
| Chapman-Shaoxing | 45150 | 2 | 2 | 0.000044 |

GO/NO-GO：

```text
NO-GO
```

原因：

```text
Internal reduced-schema fair concat does not show stable gain over signal-embedding MLP.
External reduced structured feature coverage is far below the acceptable threshold.
External multimodal evaluation was not run.
```

当前允许写入论文：

```text
Internal full-schema multimodal evaluation.
Signal-only external validation.
Stage 14L reduced-schema sensitivity attempt as a NO-GO engineering/supplementary audit, if needed.
```

当前禁止：

```text
exact PTB-XL+ reproduction
full 531-column external multimodal validation
limited external multimodal validation based on Stage 14L
gated fusion superiority
```

## 28. Stage 14J PTB-XL+ feature description audit 当前结果

已完成 Stage 14J。该阶段审计官方 `feature_description.csv` 对 111 个 unresolved frozen structured columns 的覆盖情况。

新增代码：

- `src/data/audit_ptbxl_plus_feature_description.py`

新增脚本：

- `scripts/16j_audit_ptbxl_plus_feature_description.sh`

新增测试：

- `tests/test_ptbxl_plus_feature_description_audit.py`

输出：

- `tables/table_ptbxl_plus_feature_description_unresolved_audit.csv`
- `tables/table_ptbxl_plus_feature_description_family_summary.csv`
- `tables/table_ptbxl_plus_feature_description_decision.csv`
- `results/stage14j_ptbxl_plus_feature_description_audit_summary.md`

unresolved feature families：

| base_feature | n_features | official description status |
|---|---:|---|
| P_Morph | 36 | found |
| QT_IntCorr | 36 | found |
| ST_Elev | 36 | found |
| HA_ / HA__Global | 3 | found |

关键解释：

```text
feature_description.csv provides semantic descriptions for all 111 unresolved columns.
However, semantic descriptions are not an exact waveform-to-feature recipe.
They do not resolve Stage 14H/14I numeric mismatch in the 420 direct-feature subset.
They also do not define complete aggregation, beat inclusion, preprocessing, fiducial, unit, and missing-value rules.
Therefore, external multimodal validation remains blocked.
```

当前 blocker：

```text
direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing
```

下一步：

```text
Prepare a compact recipe-blocker package that lists the missing exact PTB-XL+ reconstruction requirements and separates what is already proven from what is still blocked.
```

## 29. Stage 14K PTB-XL+ recipe blocker package 当前结果

已完成 Stage 14K。该阶段把外部多模态验证的阻塞条件整理成正式 blocker package，用于后续工程交接和论文叙事边界控制。

新增代码：

- `src/data/build_ptbxl_plus_recipe_blocker_package.py`

新增脚本：

- `scripts/16k_build_ptbxl_plus_recipe_blocker_package.sh`

新增测试：

- `tests/test_ptbxl_plus_recipe_blocker_package.py`

输出：

- `results/stage14k_ptbxl_plus_recipe_blocker_package.md`
- `tables/table_ptbxl_plus_recipe_unlock_requirements.csv`
- `tables/table_ptbxl_plus_recipe_blocker_decision.csv`

当前判定：

| decision item | value |
|---|---|
| can claim exact PTB-XL+ reproduction | no |
| can run multimodal external validation | no |
| blocked requirements | 6 |

主要解锁条件：

1. 完整 exact 531-column PTB-XL+ waveform-to-feature recipe；
2. direct ECGdeli candidates 与官方 PTB-XL+ 数值一致；
3. T/QT interval discrepancy mechanism 被解释并消除；
4. QT_IntCorr、P_Morph、ST_Elev、HA__Global 有可执行且验证过的规则；
5. CPSC2018 和 Chapman-Shaoxing 生成非空 531-column external structured tables；
6. candidate/prototype files 继续与 official multimodal inputs 隔离。

当前允许的外部验证范围：

```text
signal-only external validation only
```

当前禁止：

```text
fair concat external validation
gated fusion external validation
any claim of external multimodal validation
```

当前 blocker：

```text
direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing
```
