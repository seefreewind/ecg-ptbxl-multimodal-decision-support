# ECG / PTB-XL 多模态项目当前总结

Date: 2026-06-30

## 1. 当前总体状态

项目已经完成 PTB-XL 内部 signal-only、structured-only、fair concat、gated fusion、消融、校准、不确定性分诊、XAI、DCA 和 signal-only external validation。

当前可以支持的核心结论是：

```text
Signal + structured multimodal fusion improves over either unimodal baseline under a fair shared-interface comparison.
Simple fair concat is essentially sufficient; gated fusion does not show a statistically clear advantage over concat.
```

当前不允许支持的结论是：

```text
Do not claim external multimodal validation.
Do not claim exact PTB-XL+ feature reproduction on external datasets.
Do not claim gated fusion is meaningfully superior to fair concat.
```

## 2. 内部主实验结果

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
- paired bootstrap 显示 gated minus concat 的 AUROC/AP/F1 95% CI 均包含 0，因此不能把 gated 优势作为论文核心卖点。

## 3. 可信决策支持模块

已完成模块：

- calibration：覆盖 signal-only、structured-only、fair concat、gated fusion；
- uncertainty triage：基于不确定性筛查 retained subset；
- XAI：结构化侧 attribution、信号侧 attribution、统一 case report；
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

## 4. 外部验证当前状态

已完成 signal-only external validation，未进行 multimodal external validation。

| dataset | label scope | evaluated records | macro AUROC | macro AP | macro F1 |
|---|---|---:|---:|---:|---:|
| CPSC2018 | NORM/CD | 9944 | 0.907082 | 0.650903 | 0.590366 |
| Chapman-Shaoxing | MI/CD/HYP | 45150 | 0.874167 | 0.172664 | 0.164973 |

解释边界：

- 这些是 signal-only external results。
- 外部数据标签空间只与 PTB-XL 五大 superclass 部分对齐。
- Chapman-Shaoxing 的 sinus rhythm 当前不作为 main-analysis NORM。
- 这些结果不能替代 multimodal external validation。

## 5. PTB-XL+ / ECGdeli 外部多模态阻塞

已确认本机 MATLAB R2025a 可调用，官方 ECGdeli smoke test 通过，外部 WFDB 波形也可以进入 ECGdeli 路径。

但外部 multimodal validation 仍被阻塞，原因不是环境，而是 exact PTB-XL+ feature recipe 和数值一致性：

| evidence | result |
|---|---|
| Stage 14F feature-name mapping | 420 direct candidates；111 unresolved columns |
| Stage 14G external direct candidate | CPSC2018/Chapman 各 2 条样本可生成 420 candidate columns |
| Stage 14H PTB-XL recomputation | 420 direct features 中仅 138 个 allclose |
| Stage 14I discrepancy diagnosis | worst family: T_DurFull:mean；32 个 families 有差异 |
| Stage 14J feature description audit | 111/111 unresolved columns 有语义描述，但没有完整 executable recipe |
| Stage 14K blocker package | 6 条解锁条件全部 blocked |
| Stage 14L concordant subset | 138 allclose features 内部无稳定多模态增益，外部 coverage 过低，NO-GO |

当前 blocker：

```text
direct_feature_numeric_discrepancy;ptbxl_plus_exact_531_recipe_missing;stage14l_concordant_subset_no_go
```

## 6. 下一步

在开始写论文结果正文前，最稳妥的下一步是：

```text
Obtain or reconstruct the exact PTB-XL+ ECGdeli feature-generation recipe,
then rerun internal PTB-XL numeric agreement validation and external structured schema validation.
```

如果短期拿不到 exact PTB-XL+ recipe，则论文外部验证部分只能写：

```text
Signal-only external validation on CPSC2018 and Chapman-Shaoxing was completed.
External multimodal validation was not performed because exact PTB-XL+ compatible structured features could not be validated.
The concordant-subset sensitivity attempt was NO-GO because internal multimodal gain was not stable and external feature coverage was insufficient.
```
