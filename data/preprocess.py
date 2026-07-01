"""统一预处理流水线:raw → processed h5ad,供后续 embedding 提取使用。

产出的 h5ad 同时满足三个模型的输入需求:
- scVI       : 需原始 counts → 保存在 layers["counts"]
- Geneformer : 需 var["ensembl_id"] + obs["n_counts"]
- scGPT      : 需 gene symbol(var_names 即 symbol)+ counts

步骤:
1. 基础 QC(最小基因数/细胞数、线粒体比例上限)
2. 保留 raw counts 到 layers["counts"]
3. 标准化 + log1p(供下游可视化/原始特征探测),HVG 标记
4. PCA(作 leakage audit 的原始特征基线 obsm["X_pca"])
5. metadata 标准化:把各数据集异构的列名映射到统一 schema
6. gene symbol → Ensembl id 映射(Geneformer 用);映射资源需外部提供

不臆造数据;映射缺失/QC 过滤都记录到 uns["preprocess_log"]。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

# 统一 metadata schema:把异构列名 → 标准名(各数据集按需在 CLI/配置里补充)
STANDARD_OBS = ["donor_id", "platform", "region", "disease", "age", "cell_type",
                "ancestry", "dataset"]


def standardize_obs(adata, colmap: dict):
    """colmap: {标准名: 原始列名}。缺失的标准列填 'unknown' 并记录。"""
    log = []
    for std in STANDARD_OBS:
        src = colmap.get(std)
        if src and src in adata.obs:
            adata.obs[std] = adata.obs[src].astype(str).values
        else:
            adata.obs[std] = "unknown"
            log.append(f"obs['{std}'] 缺失 → 填 unknown")
    return log


def map_symbol_to_ensembl(adata, mapping: dict | None):
    """mapping: {symbol: ensembl_id}。无映射的基因记录数量,不删除。"""
    if mapping is None:
        adata.var["ensembl_id"] = "unmapped"
        return ["未提供 symbol→ensembl 映射;Geneformer 提取前必须补(见 onstart 说明)"]
    ens = [mapping.get(str(s), "unmapped") for s in adata.var_names]
    adata.var["ensembl_id"] = ens
    n_unmapped = sum(e == "unmapped" for e in ens)
    return [f"symbol→ensembl: {n_unmapped}/{len(ens)} 基因未映射"]


def preprocess(adata, colmap, ensembl_map=None,
               min_genes=200, min_cells=3, max_pct_mt=20.0, n_hvg=2000):
    import scanpy as sc

    log = []
    n0 = adata.n_obs
    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)
    adata.var["mt"] = adata.var_names.str.upper().str.startswith("MT-")
    if adata.var["mt"].any():
        sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True,
                                   percent_top=None)
        adata = adata[adata.obs["pct_counts_mt"] < max_pct_mt].copy()
    log.append(f"QC: {n0} → {adata.n_obs} 细胞")

    adata.layers["counts"] = adata.X.copy()                 # scVI / scGPT
    adata.obs["n_counts"] = np.asarray(adata.X.sum(1)).ravel()  # Geneformer

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=min(n_hvg, adata.n_vars - 1))
    sc.pp.pca(adata, n_comps=min(50, adata.n_vars - 1))      # leakage 原始特征基线

    log += standardize_obs(adata, colmap)
    log += map_symbol_to_ensembl(adata, ensembl_map)
    adata.uns["preprocess_log"] = log
    return adata


def main():
    import anndata as ad
    import scanpy as sc

    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="raw .h5ad")
    p.add_argument("--output", required=True, help="processed .h5ad")
    p.add_argument("--donor-col", default=None)
    p.add_argument("--platform-col", default=None)
    p.add_argument("--region-col", default=None)
    p.add_argument("--disease-col", default=None)
    p.add_argument("--age-col", default=None)
    p.add_argument("--celltype-col", default=None)
    p.add_argument("--dataset-name", default="unknown")
    args = p.parse_args()

    adata = sc.read_h5ad(args.input)
    colmap = {"donor_id": args.donor_col, "platform": args.platform_col,
              "region": args.region_col, "disease": args.disease_col,
              "age": args.age_col, "cell_type": args.celltype_col}
    adata = preprocess(adata, colmap)
    adata.obs["dataset"] = args.dataset_name
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(args.output)
    print("[ok] 预处理完成 →", args.output)
    for line in adata.uns["preprocess_log"]:
        print("  -", line)


if __name__ == "__main__":
    main()
