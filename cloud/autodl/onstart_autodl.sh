#!/usr/bin/env bash
# 在 AutoDL 实例上一键装环境(实测镜像:PyTorch 2.3.0 / Python 3.12 / CUDA 12.1)。
# 注意:Python 3.12 下 scVI、Geneformer 正常;scGPT 官方包钉老依赖,大概率装不上,
#       本脚本对 scGPT 失败做了容错(只警告不中断),不影响 scVI/Geneformer 主流程。
# 用法:
#   cd /root/autodl-tmp
#   source /etc/network_turbo     # ★ 先开学术加速(本脚本也会再尝试一次)
#   bash onstart_autodl.sh
#
# 与 Vast.ai 版 onstart.sh 的差异:
#   1) 工作目录 /root/autodl-tmp(AutoDL 数据盘),不是 /workspace
#   2) 先开 AutoDL 学术加速 + 用 hf-mirror.com 镜像拉 HuggingFace(Geneformer)
#   3) pip 用国内源(清华),避免跨境慢/超时
set -euo pipefail

echo "==== 0. 学术加速 + 国内源 ===="
# AutoDL 学术加速(拉 GitHub/HuggingFace 必需);非 AutoDL 环境则跳过不致命
if [ -f /etc/network_turbo ]; then
    source /etc/network_turbo && echo "  已开启 AutoDL 学术加速"
else
    echo "  (未发现 /etc/network_turbo,可能不在 AutoDL 环境;继续)"
fi
# HuggingFace 国内镜像(Geneformer 从 HF 拉权重/字典时走这里)
export HF_ENDPOINT="https://hf-mirror.com"
# pip 国内源
PIP_SRC="-i https://pypi.tuna.tsinghua.edu.cn/simple"

echo "==== 0b. GPU 自检 ===="
# 无卡模式下没有 GPU 属正常:此时只装环境,跑提取前请改成带卡开机
nvidia-smi || echo "!! 当前看不到 GPU(可能是无卡模式)。装环境可继续;跑提取前务必带卡开机。"

WORK=/root/autodl-tmp
mkdir -p "$WORK/data" "$WORK/embeddings" "$WORK/scgpt_models"
cd "$WORK"

echo "==== 1. 基础科学栈 ===="
pip install -q --upgrade pip $PIP_SRC
pip install -q $PIP_SRC \
    scanpy anndata scikit-learn xgboost lightgbm \
    pandas numpy matplotlib seaborn

echo "==== 2. scVI ===="
pip install -q $PIP_SRC scvi-tools

echo "==== 3. Geneformer ===="
# 官方在 HuggingFace 仓库;走镜像 + git-lfs 拉模型权重与字典。
apt-get update -qq && apt-get install -y -qq git git-lfs
git lfs install
# 用 hf-mirror 域名替换官方域名拉取
pip install -q $PIP_SRC git+https://hf-mirror.com/ctheodoris/Geneformer || \
    pip install -q $PIP_SRC git+https://huggingface.co/ctheodoris/Geneformer || \
    echo "!! Geneformer 安装失败,登录后手动排查(确认已 source /etc/network_turbo 与 HF_ENDPOINT)"

echo "==== 4. scGPT ===="
# flash-attn 在部分卡/驱动上编译失败;失败时 scGPT 仍可用非 flash 路径。
pip install -q $PIP_SRC scgpt || echo "!! scgpt pip 安装失败,见下方手动方案"
pip install -q $PIP_SRC flash-attn --no-build-isolation || echo "(flash-attn 跳过,scGPT 用普通注意力)"

echo "==== 5. scGPT whole-human checkpoint ===="
# 官方 checkpoint 放在 Google Drive(国内直连难)。两种获取方式:
#   (a) 国内:把权重先传到 AutoDL 网盘/阿里云盘,再下到 /root/autodl-tmp/scgpt_models/whole_human/
#   (b) 开学术加速后用 gdown 试拉(可能仍受限):
pip install -q $PIP_SRC gdown
echo "  -> 登录后执行(链接以 scGPT README 为准 https://github.com/bowang-lab/scGPT):"
echo "     mkdir -p /root/autodl-tmp/scgpt_models/whole_human"
echo "     source /etc/network_turbo"
echo "     gdown --folder <scGPT_whole_human_drive_url> -O /root/autodl-tmp/scgpt_models/whole_human"
echo "     需文件:best_model.pt / args.json / vocab.json"
echo "     (国内拉 Google Drive 常失败,推荐先传到 AutoDL 网盘再拷入)"

echo "==== 版本汇总 ===="
python - <<'PY'
import importlib
for m in ["scanpy","anndata","scvi","torch","sklearn","xgboost","lightgbm"]:
    try:
        mod=importlib.import_module(m); print(f"ok  {m} {getattr(mod,'__version__','')}")
    except Exception as e:
        print(f"MISS {m} -> {repr(e)[:80]}")
for m in ["geneformer","scgpt"]:
    try:
        mod=importlib.import_module(m); print(f"ok  {m} {getattr(mod,'__version__','')}")
    except Exception as e:
        print(f"MISS {m} -> {repr(e)[:80]}  (登录后手动修)")
import torch
print("CUDA:", torch.cuda.is_available(),
      "| device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
PY
echo "==== onstart_autodl 完成 ===="
echo "提示:跑提取前确认已带卡开机(nvidia-smi 能看到卡);新开终端记得重新 source /etc/network_turbo"
