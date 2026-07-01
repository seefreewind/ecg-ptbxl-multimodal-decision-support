"""统一 embedding 提取流水线(在云端 GPU 实例上运行)。

用法:
    python extract_embeddings.py --input data/<ds>.h5ad --model scvi       --dataset <ds> --out embeddings
    python extract_embeddings.py --input data/<ds>.h5ad --model geneformer --dataset <ds> --out embeddings \
        [--gf-model-dir <权重目录>] [--gf-emb-layer -1]
    python extract_embeddings.py --input data/<ds>.h5ad --model scgpt      --dataset <ds> --out embeddings \
        --scgpt-model-dir /root/autodl-tmp/scgpt_models/whole_human

产出(遵守宪法第 6 节 / 约束 4):
    <out>/<dataset>/<model>/embedding.h5ad   # obsm["X_embedding"]; obs 保留全部 metadata
    <out>/<dataset>/<model>/run_metadata.json

设计约定:
- 统一 obsm 字段名为 "X_embedding"(下游 split/leakage/BGI 只认这个名字)
- donor_id/batch/platform/disease/age/region 等 metadata 原样保留在 obs
- 不在脚本里做任何叙事解读,只产出数据

各模型 API 随版本会变,实现处标了 TODO/版本敏感点;先用 scVI 跑通流水线,再逐个验证 FM。
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import anndata as ad
import numpy as np
import scanpy as sc

SEED = 0
EMB_KEY = "X_embedding"


# ----------------------------- 工具 -----------------------------

def _device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def _reset_peak(device: str) -> None:
    if device == "cuda":
        import torch
        torch.cuda.reset_peak_memory_stats()


def _peak_mb(device: str):
    if device == "cuda":
        import torch
        return round(torch.cuda.max_memory_allocated() / 1024 ** 2, 1)
    return None


def _pip_freeze() -> str:
    try:
        return subprocess.check_output(["pip", "freeze"], text=True)
    except Exception as exc:  # noqa: BLE001
        return f"pip freeze 失败: {exc}"


def _lightning_accelerator(device: str) -> str:
    """torch 设备词 → PyTorch Lightning accelerator 词(scvi-tools train 用)。"""
    return "gpu" if device == "cuda" else "cpu"


def _save(adata: ad.AnnData, emb: np.ndarray, out_dir: Path,
          model: str, dataset: str, extra_meta: dict, wall: float,
          peak_mb, device: str, checkpoint: str) -> None:
    assert emb.shape[0] == adata.n_obs, "embedding 行数与细胞数不一致"
    adata.obsm[EMB_KEY] = np.asarray(emb, dtype=np.float32)
    out_dir.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(out_dir / "embedding.h5ad")

    import torch
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset,
        "model": model,
        "checkpoint": checkpoint,
        "n_cells": int(adata.n_obs),
        "n_genes_input": int(adata.n_vars),
        "embedding_dim": int(emb.shape[1]),
        "seed": SEED,
        "wall_time_s": round(wall, 2),
        "peak_gpu_mem_mb": peak_mb,
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "obs_columns_preserved": list(adata.obs.columns),
        **extra_meta,
        "pip_freeze": _pip_freeze(),
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"[ok] {model}: 写出 {out_dir/'embedding.h5ad'}  dim={emb.shape}")


# ----------------------------- scVI -----------------------------

def extract_scvi(adata: ad.AnnData, device: str):
    """scVI 隐空间。需要原始 counts(adata.X 或 layers['counts'])。

    返回 (adata_used, emb, extra, checkpoint)。scVI 不丢细胞,adata_used 即输入。
    """
    import scvi

    scvi.settings.seed = SEED
    a = adata.copy()
    # scVI 要 counts;若 X 已被 normalize,改用 layers["counts"]
    if "counts" in a.layers:
        a.X = a.layers["counts"].copy()
    scvi.model.SCVI.setup_anndata(a)
    model = scvi.model.SCVI(a, n_latent=30)
    # 修复#1:scvi-tools 底层是 Lightning,accelerator 要 "gpu"/"cpu",不认 "cuda"
    model.train(max_epochs=400, early_stopping=True,
                accelerator=_lightning_accelerator(device), devices=1)
    emb = model.get_latent_representation()
    return adata, emb, {"n_latent": 30, "max_epochs": 400}, "scvi-tools default"


# -------------------------- Geneformer --------------------------

CELL_ID = "bgi_cell_id"  # 唯一细胞 id,用于 Geneformer 过滤后的显式行对齐


def _resolve_geneformer_model_dir(user_dir: str = "") -> str:
    """修复#2:定位真正的预训练权重目录(含 config.json + *.bin/*.safetensors),
    而不是 geneformer 包的安装根目录。

    优先级:
    1. 用户用 --gf-model-dir 显式指定 → 直接用(仅校验存在)
    2. 在 geneformer 包目录下递归找包含 config.json 的子目录(如 Geneformer-V2-104M / gf-12L-*)
    若都找不到,抛错并打印包目录内容,提示用户手动指定。
    """
    import os
    import glob

    if user_dir:
        if not Path(user_dir).is_dir():
            raise ValueError(f"--gf-model-dir 指定的目录不存在:{user_dir}")
        return user_dir

    import geneformer
    pkg_root = Path(geneformer.__file__).parent

    # 找含 config.json 的子目录,即一个可加载的权重目录
    candidates = []
    for cfg in glob.glob(str(pkg_root / "**" / "config.json"), recursive=True):
        d = Path(cfg).parent
        has_weight = any(d.glob("*.bin")) or any(d.glob("*.safetensors")) or any(d.glob("*.ckpt"))
        if has_weight:
            candidates.append(d)

    if not candidates:
        listing = "\n  ".join(sorted(p.name for p in pkg_root.iterdir()))
        raise RuntimeError(
            "未在 geneformer 包目录下自动找到预训练权重(含 config.json + 权重文件)。\n"
            f"包目录:{pkg_root}\n  {listing}\n"
            "请用 --gf-model-dir 显式指定权重子目录(如 .../Geneformer-V2-104M),"
            "或先按 onstart 说明用 git-lfs 拉全权重。")

    # 多个候选时,选名字最长/最具体的一个(通常是带版本/层数的目录),并打印告知
    chosen = sorted(candidates, key=lambda p: len(str(p)))[-1]
    if len(candidates) > 1:
        print(f"[info] 找到多个 Geneformer 权重目录,选用:{chosen}\n"
              f"       全部候选:{[str(c) for c in candidates]}")
    else:
        print(f"[info] Geneformer 权重目录:{chosen}")
    return str(chosen)


def extract_geneformer(adata: ad.AnnData, model_dir: str = "", emb_layer: int = -1):
    """Geneformer cell embedding。返回 (adata_used, emb, extra, checkpoint)。

    前置(版本敏感):
    - adata.var 需含 Ensembl gene id(列名 'ensembl_id');symbol→ensembl 映射须在预处理阶段完成
    - adata.X 为原始 counts;obs 需有 'n_counts'(每个细胞总 counts)
    - 用 TranscriptomeTokenizer 先 token 化为 HF dataset,再用 EmbExtractor 抽 CLS/mean 向量
    流程会写中间文件到 ./_gf_tmp/。

    设备:Geneformer/HF 内部自动探测 GPU,无法在此显式指定;若要强制 CPU 调试,
    在调用本脚本前设 CUDA_VISIBLE_DEVICES=""(见 main 的 --force-cpu)。
    """
    from geneformer import EmbExtractor, TranscriptomeTokenizer

    tmp = Path("_gf_tmp")
    tmp.mkdir(exist_ok=True)
    in_dir, tok_dir = tmp / "in", tmp / "tok"
    in_dir.mkdir(exist_ok=True)

    a = adata.copy()
    if "ensembl_id" not in a.var.columns:
        raise ValueError("Geneformer 需要 var['ensembl_id'](预处理阶段做 symbol→Ensembl 映射)")
    if "n_counts" not in a.obs.columns:
        a.obs["n_counts"] = np.asarray(a.X.sum(axis=1)).ravel()
    # 修复#4:显式唯一 id,token 化时携带,供过滤后按 id 对齐(不假设行序不变)
    a.obs[CELL_ID] = np.arange(a.n_obs)
    metadata_cols = list(a.obs.columns)        # 携带进 dataset 的全部 obs 列
    keep = {c: c for c in metadata_cols}
    a.write_h5ad(in_dir / "input.h5ad")

    tk = TranscriptomeTokenizer(custom_attr_name_dict=keep, nproc=4)
    tk.tokenize_data(str(in_dir), str(tok_dir), "input", file_format="h5ad")

    # 修复#2:把 model_directory 指向真正的权重目录(自动探测或 --gf-model-dir)
    resolved_dir = _resolve_geneformer_model_dir(model_dir)

    # 修复#4(配套):必须把 CELL_ID 放进 emb_label,EmbExtractor 才会把它输出到 emb_df,
    # 否则下面按 id 对齐永远走不到,行序错位会被静默放过。
    # emb_layer 参数化:不同权重常用 -1(倒数第二层)或 0,首次跑可对照确认。
    ee = EmbExtractor(model_type="Pretrained", emb_mode="cell",
                      max_ncells=None, emb_layer=emb_layer,
                      emb_label=[CELL_ID],
                      forward_batch_size=16, nproc=4)
    emb_df = ee.extract_embs(
        model_directory=resolved_dir,
        input_data_file=str(tok_dir / "input.dataset"),
        output_directory=str(tmp), output_prefix="gf_emb",
    )

    # 修复#3:只取真正的 embedding 维度列。Geneformer 的 embedding 列名是整数 0..d-1;
    # 携带的 metadata 列(donor_id/age/n_counts/CELL_ID…)按列名显式排除,
    # 防止数值型 metadata 被 select_dtypes 误当成 embedding 维度污染结果。
    def _is_emb_col(c):
        if c in metadata_cols:
            return False
        return isinstance(c, (int, np.integer)) or (isinstance(c, str) and c.isdigit())
    emb_cols = [c for c in emb_df.columns if _is_emb_col(c)]
    if not emb_cols:  # 兜底:某些版本列名非数字,则取数值列但排除 metadata
        emb_cols = [c for c in emb_df.select_dtypes("number").columns
                    if c not in metadata_cols]
    if not emb_cols:
        raise RuntimeError(f"无法识别 embedding 列;emb_df.columns={list(emb_df.columns)[:20]}")

    # 修复#4:按 CELL_ID 显式对齐。token 化可能过滤细胞 → emb_df 行数/序可变。
    if CELL_ID in emb_df.columns:
        ids = emb_df[CELL_ID].to_numpy().astype(int)
        emb = emb_df[emb_cols].to_numpy()
        adata_used = adata[ids].copy()   # 子集 + 重排到 emb_df 的顺序
        if len(ids) != adata.n_obs:
            print(f"[warn] Geneformer token 化后细胞数 {len(ids)} ≠ 输入 {adata.n_obs},"
                  f"已按 {CELL_ID} 子集对齐")
    else:
        # 没带出 id:退回顺序假设,但显式校验行数并警告
        print(f"[warn] emb_df 未带 {CELL_ID} 列(检查 emb_label 是否生效),回退顺序对齐;请核对行序")
        emb = emb_df[emb_cols].to_numpy()
        adata_used = adata
    return (adata_used, emb,
            {"emb_mode": "cell", "tokenizer": "TranscriptomeTokenizer",
             "n_emb_cols": len(emb_cols), "emb_layer": emb_layer,
             "model_dir_resolved": resolved_dir}, "Geneformer pretrained")


# ----------------------------- scGPT ----------------------------

def extract_scgpt(adata: ad.AnnData, model_dir: str):
    """scGPT cell embedding(whole-human 预训练)。返回 (adata_used, emb, extra, checkpoint)。

    前置:
    - model_dir 含 best_model.pt / args.json / vocab.json(见 onstart 下载说明)
    - adata.var 需有 gene symbol 列(默认用 var_names);adata.X 为原始 counts

    设备:scGPT 内部自动探测 GPU;强制 CPU 调试用 main 的 --force-cpu。
    """
    if not model_dir:
        raise ValueError("scGPT 需 --scgpt-model-dir 指向 checkpoint 目录")
    from scgpt.tasks import embed_data

    a = adata.copy()
    if "gene_name" not in a.var.columns:
        a.var["gene_name"] = a.var_names
    # TODO(验证): 不同 scgpt 版本 embed_data 签名略有差异(gene_col/batch_size/obs_to_save)
    emb_adata = embed_data(
        a, model_dir=model_dir, gene_col="gene_name",
        batch_size=64, return_new_adata=True,
    )
    emb = np.asarray(emb_adata.obsm.get("X_scGPT", emb_adata.X))
    # scGPT 通常不丢细胞;若行数变化则报错而非静默写入
    if emb.shape[0] != a.n_obs:
        raise RuntimeError(f"scGPT 返回 {emb.shape[0]} 行 ≠ 输入 {a.n_obs} 细胞,需核对")
    return adata, emb, {"batch_size": 64, "gene_col": "gene_name"}, model_dir


# ----------------------------- 主流程 ----------------------------

MODELS = ["scvi", "geneformer", "scgpt"]


def main() -> None:
    import os

    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="预处理后的 .h5ad")
    p.add_argument("--model", required=True, choices=MODELS)
    p.add_argument("--dataset", required=True, help="数据集名,用于输出路径")
    p.add_argument("--out", default="embeddings", help="embedding 根目录")
    p.add_argument("--scgpt-model-dir", default="", help="scGPT checkpoint 目录")
    p.add_argument("--gf-model-dir", default="",
                   help="Geneformer 预训练权重目录;留空则自动在包内探测含 config.json 的子目录")
    p.add_argument("--gf-emb-layer", type=int, default=-1,
                   help="Geneformer 取第几层 embedding(默认 -1 倒数第二层;部分权重用 0)")
    p.add_argument("--force-cpu", action="store_true",
                   help="统一强制 CPU(对三个模型都生效;调试用)")
    args = p.parse_args()

    if args.force_cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""  # 必须在 import torch 前;本模块顶部未导 torch

    np.random.seed(SEED)
    device = _device()
    print(f"[info] device={device}  model={args.model}  input={args.input}")
    adata = sc.read_h5ad(args.input)
    print(f"[info] 输入 {adata.shape}")

    _reset_peak(device)
    t0 = time.perf_counter()
    if args.model == "scvi":
        adata_used, emb, extra, ckpt = extract_scvi(adata, device)
    elif args.model == "geneformer":
        adata_used, emb, extra, ckpt = extract_geneformer(
            adata, model_dir=args.gf_model_dir, emb_layer=args.gf_emb_layer)
    else:
        adata_used, emb, extra, ckpt = extract_scgpt(adata, args.scgpt_model_dir)
    wall = time.perf_counter() - t0

    out_dir = Path(args.out) / args.dataset / args.model
    _save(adata_used, emb, out_dir, args.model, args.dataset, extra, wall,
          _peak_mb(device), device, ckpt)


if __name__ == "__main__":
    main()
