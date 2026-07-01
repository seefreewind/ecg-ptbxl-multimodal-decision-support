# ECG / PTB-XL 多模态项目合并状态文档

Date: 2026-06-30

## 1. 项目定位

当前项目方向为：

```text
An Interpretable Multimodal Decision-Support Framework for ECG-Based Cardiac Risk Stratification with Cross-Dataset Validation
```

项目已经完成从 PTB-XL 原始数据准备、内部模型训练、消融、校准、不确定性、XAI、DCA 到外部 signal-only validation 的主要工程流程。

当前最重要的边界是：

```text
Internal multimodal evidence is usable.
External multimodal validation is still NO-GO.
Current external evidence is signal-only only.
```

## 2. 当前可以支持的核心结论

当前可以支持：

```text
Signal + structured multimodal fusion improves over either unimodal baseline under the full internal PTB-XL/PTB-XL+ setting.
The main value comes from multimodal complementarity rather than a complex fusion mechanism.
Simple fair concat is already sufficient to capture most of the internal multimodal gain.
```

当前不能支持：

```text
External multimodal validation has been completed.
Exact PTB-XL+ feature reproduction has been achieved on external datasets.
Gated fusion is meaningfully or statistically clearly superior to fair concat.
```

## 3. 已完成的主要工作

已完成模块：

- PTB-XL raw data layout validation and Stage 0/1 preparation；
- PTB-XL+ structured features alignment；
- signal-only baseline；
- structured-only baseline；
- fair concat multimodal baseline；
- gated fusion baseline；
- fair-interface ablation；
- gated vs concat paired bootstrap；
- calibration；
- uncertainty triage；
- XAI case reports；
- DCA；
- CPSC2018 and Chapman-Shaoxing signal-only external validation；
- MATLAB / ECGdeli setup and smoke test；
- PTB-XL+ external structured feature extraction audit；
- Stage 14L concordant-subset sensitivity attempt。

## 4. 内部 PTB-XL 主实验结果

PTB-XL frozen test set 单次结果：

| model | test AUROC | test AP | test F1 |
|---|---:|---:|---:|
| strong signal-only | 0.909815 | 0.772057 | 0.699812 |
| signal-embedding MLP | 0.909437 | 0.772363 | 0.700216 |
| structured MLP | 0.904558 | 0.765152 | 0.689893 |
| fair MLP-concat | 0.919251 | 0.795289 | 0.720762 |
| gated fusion MLP | 0.919570 | 0.797779 | 0.725463 |

关键解释：

- fair concat 相比最强单模态 signal-embedding MLP：AUROC +0.009814，AP +0.022926，F1 +0.020546。
- gated fusion 相比 fair concat：AUROC +0.000319，AP +0.002489，F1 +0.004702。
- paired bootstrap 显示 gated minus concat 的 AUROC/AP/F1 95% CI 均包含 0。

因此论文主线应强调：

```text
Multimodal complementarity and trustworthy decision support,
not gated fusion superiority.
```

## 5. 可信决策支持模块

已完成：

- calibration：覆盖 signal-only、structured-only、fair concat、gated fusion；
- uncertainty triage：分析低不确定性 retained subset；
- XAI：structured attribution、signal attribution、unified case report；
- DCA：内部 exploratory decision curve analysis；
- figure source data：已生成主图源数据和检查表。

校准测试集简要结果：

| model | temperature-scaled macro Brier | temperature-scaled macro ECE |
|---|---:|---:|
| strong signal-only | 0.090266 | 0.031984 |
| structured MLP | 0.094208 | 0.021226 |
| fair concat MLP | 0.086356 | 0.028284 |
| gated fusion MLP | 0.084421 | 0.019276 |

内部 DCA 简要结果：

| model | mean macro net benefit |
|---|---:|
| strong signal-only | 0.184445 |
| structured MLP | 0.181541 |
| fair concat MLP | 0.188100 |
| gated fusion MLP | 0.189506 |

## 6. 外部 signal-only validation

已完成 signal-only external validation。

| dataset | label scope | evaluated records | macro AUROC | macro AP | macro F1 |
|---|---|---:|---:|---:|---:|
| CPSC2018 | NORM/CD | 9944 | 0.907082 | 0.650903 | 0.590366 |
| Chapman-Shaoxing | MI/CD/HYP | 45150 | 0.874167 | 0.172664 | 0.164973 |

解释边界：

- 这些是 signal-only external results；
- 不是 multimodal external validation；
- 外部标签空间与 PTB-XL 五大 superclass 只是部分对齐；
- Chapman-Shaoxing 的 sinus rhythm 当前不作为 main-analysis NORM；
- 不应据此声称完整多模态跨数据集验证已经完成。

## 7. 外部多模态阻塞原因

外部 multimodal validation 仍被阻塞，原因不是 MATLAB/ECGdeli 环境，而是 exact PTB-XL+ feature recipe 与数值一致性。

已经确认：

- 本机 MATLAB R2025a 可调用；
- 官方 ECGdeli smoke test 通过；
- 外部 WFDB 波形可以进入 ECGdeli extraction path；
- 可生成 420-column direct candidate features；
- 但不能将 candidate/prototype features 当作正式 PTB-XL+ external structured features。

阻塞证据：

| stage | evidence |
|---|---|
| Stage 14F | 420 direct candidates；111 unresolved columns |
| Stage 14G | 外部样本可生成 420 candidate columns |
| Stage 14H | PTB-XL 内部 recomputation 中 420 direct features 只有 138 个 allclose |
| Stage 14I | T/QT 相关 interval features 存在明显数值差异 |
| Stage 14J | 111 unresolved columns 虽有语义描述，但没有完整 executable recipe |
| Stage 14K | 6 条 external multimodal 解锁条件均 blocked |
| Stage 14L | concordant subset sensitivity attempt 结果为 NO-GO |

当前 blocker：

```text
direct_feature_numeric_discrepancy;
ptbxl_plus_exact_531_recipe_missing;
stage14l_concordant_subset_no_go
```

## 8. Stage 14L: Concordant-subset External Multimodal Validation

Stage 14L 没有继续尝试完整复现 PTB-XL+ 531-column schema，而是使用 Stage 14H 中通过 allclose 的 structured features 构建 reproducibility-validated concordant subset。

### 8.1 Reduced Structured Schema

| item | value |
|---|---:|
| allclose structured features | 138 |
| source | Stage 14H |
| full 531 schema attempted | no |
| exact PTB-XL+ reproduction claim allowed | no |

排除内容：

- all non-allclose direct candidates；
- unresolved QT_IntCorr；
- unresolved P_Morph；
- unresolved ST_Elev；
- unresolved HA / HA__Global；
- any feature without Stage 14H allclose support。

### 8.2 Internal Protocol

- train/val/test split：unchanged PTB-XL official split；
- label scope：NORM, MI, STTC, CD, HYP；
- comparators：signal-embedding MLP, reduced structured MLP, reduced fair concat MLP；
- model selection：validation only；
- threshold tuning：validation only；
- test set：frozen final evaluation only。

### 8.3 Internal Reduced-schema Results

| model | test AUROC | test AP | test F1 |
|---|---:|---:|---:|
| stage14l_signal_embedding_mlp | 0.909411 | 0.772200 | 0.698087 |
| stage14l_structured_mlp | 0.570364 | 0.304456 | 0.000000 |
| stage14l_fair_concat_mlp | 0.909666 | 0.773100 | 0.693821 |

paired bootstrap:

| comparison | metric | delta | 95% CI status |
|---|---:|---:|---|
| fair concat minus signal-embedding | AUROC | +0.000255 | contains 0 |
| fair concat minus signal-embedding | AP | +0.000899 | contains 0 |
| fair concat minus signal-embedding | F1 | -0.004266 | contains 0 |

内部判定：

```text
Reduced-schema fair concat does not show stable gain over signal-embedding MLP.
```

### 8.4 External Quality Gate

| dataset | signal prediction records | candidate structured records | joinable records | coverage |
|---|---:|---:|---:|---:|
| CPSC2018 | 9944 | 2 | 2 | 0.000201 |
| Chapman-Shaoxing | 45150 | 2 | 2 | 0.000044 |

外部判定：

```text
External reduced structured feature coverage is far below the acceptable threshold.
External multimodal evaluation was not run.
```

### 8.5 Stage 14L GO/NO-GO

Stage 14L 结论：

```text
NO-GO
```

原因：

- reduced-schema structured-only 内部表现明显不足；
- reduced-schema fair concat 相比 signal-embedding MLP 的内部增益极小；
- paired bootstrap CI 包含 0；
- 外部 CPSC2018 和 Chapman-Shaoxing 目前各只有 2 条 reduced structured candidate records；
- external coverage 远低于可评估阈值。

## 9. 当前论文叙事建议

论文主叙事应从：

```text
Our gated fusion model is superior.
```

调整为：

```text
A rigorously controlled multimodal evaluation shows that ECG signal and structured ECG-derived features provide complementary information.
Simple fair concat already captures most of this benefit, while gated fusion does not provide a statistically clear additional gain.
The framework is strengthened by calibration, uncertainty triage, interpretability, DCA, and conservative signal-only external validation.
```

中文概括：

```text
严格公平的多模态评估证明了信号与结构化 ECG 特征的互补价值；
复杂门控并不是主要增益来源；
真正的论文亮点应放在多模态互补性、可信决策支持、解释性、不确定性、校准和保守外部验证上。
```

## 10. 当前允许和禁止的论文表述

当前允许写：

```text
Internal full-schema multimodal evaluation.
Signal-only external validation.
Calibration, uncertainty triage, XAI, and DCA as trustworthy decision-support components.
Stage 14L reduced-schema sensitivity attempt as a NO-GO engineering/supplementary audit, if needed.
```

当前禁止写：

```text
exact PTB-XL+ reproduction
full 531-column external multimodal validation
limited external multimodal validation based on Stage 14L
gated fusion superiority
clinical readiness
```

## 11. 下一步建议

下一步建议进入：

```text
Stage 15: Manuscript-readiness audit before writing.
```

目标不是直接写论文正文，而是先锁定：

- 哪些结果可以进入 main manuscript；
- 哪些结果只能进入 supplement；
- 哪些结果只能作为工程审计记录；
- 哪些结论必须明确禁止；
- 每个 claims 对应哪些 tables / figures / scripts。

建议产物：

- `MANUSCRIPT_READY_AUDIT.md`
- `docs/MANUSCRIPT_RESULT_BOUNDARIES.md`
- `tables/table_manuscript_claim_support.csv`
- `tables/table_figure_table_source_map.csv`

## 12. 一句话总结

```text
Internal multimodal evidence is strong enough to support a fair multimodal decision-support story, but both full-schema and concordant-subset external multimodal validation are currently NO-GO; current external evidence should be reported as signal-only validation only.
```
