| Comparison                                 | Metric   |   Fair concat |   Comparator |   Delta fair-comparator |   CI lower |   CI upper | CI contains 0   |   Bootstrap replicates |
|:-------------------------------------------|:---------|--------------:|-------------:|------------------------:|-----------:|-----------:|:----------------|-----------------------:|
| fair_mlp_concat_minus_signal_embedding_mlp | AUROC    |        0.9193 |       0.9094 |                  0.0098 |     0.0067 |     0.0131 | False           |                   2000 |
| fair_mlp_concat_minus_signal_embedding_mlp | AP       |        0.7953 |       0.7724 |                  0.0229 |     0.0157 |     0.0302 | False           |                   2000 |
| fair_mlp_concat_minus_signal_embedding_mlp | F1       |        0.7208 |       0.7002 |                  0.0205 |     0.0088 |     0.0324 | False           |                   2000 |
| fair_mlp_concat_minus_strong_signal_only   | AUROC    |        0.9193 |       0.9098 |                  0.0094 |     0.0062 |     0.0127 | False           |                   2000 |
| fair_mlp_concat_minus_strong_signal_only   | AP       |        0.7953 |       0.7721 |                  0.0232 |     0.0151 |     0.0308 | False           |                   2000 |
| fair_mlp_concat_minus_strong_signal_only   | F1       |        0.7208 |       0.6998 |                  0.0209 |     0.0098 |     0.0319 | False           |                   2000 |
