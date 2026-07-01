# AutoDL 租用 GPU 跑 Embedding 提取 — 完整流程(国内版)

> **定位**:本机(Mac, MPS, 无 CUDA)与 MX450 2GB 都跑不动 Geneformer/scGPT。
> 阶段 2 的「数据集 → embedding」放到云端 GPU 一次性批处理;产物 `.h5ad` 下载回本地,
> 后续 split / leakage / BGI 全在本机 CPU 跑(轻量 sklearn,不需要 GPU)。
> 本文档是 Vast.ai 版的**国内 AutoDL 等价流程**——`extract_embeddings.py` 脚本本身平台无关、**不需改动**,
> 只是把「在哪租、怎么连、怎么装、目录在哪」换成 AutoDL 的做法。

---

## 与 Vast.ai 版的三个关键差异(先记住)

| 维度 | Vast.ai | **AutoDL** |
|---|---|---|
| 数据/工作目录 | `/workspace` | **`/root/autodl-tmp`**(数据盘,大且持久;系统盘 `/root` 小,别往里塞数据) |
| 外网访问 | 直连 | **需学术加速**:`source /etc/network_turbo`;HuggingFace 用镜像 `hf-mirror.com` |
| 省钱机制 | Stop 仍收存储费 | **「无卡模式开机」**:不要 GPU、只传数据/装环境时用,几毛/小时;**关机后只收数据盘存储费** |

> 因此本流程所有路径用 `/root/autodl-tmp`,装环境脚本换成 `onstart_autodl.sh`(同目录),
> 它在 onstart.sh 基础上加了学术加速 + HF 镜像 + 国内 pip 源。

---

## 0. 选卡建议(AutoDL 在售卡)

| GPU | 显存 | 适用 | AutoDL 约价 |
|---|---|---|---|
| RTX 4090 | 24 GB | 最稳,Geneformer+scGPT 全量从容 | ¥2–3/h |
| RTX 3090 | 24 GB | 同上 | ¥1.3–2/h |
| RTX A5000 | 24 GB | 同上 | ¥1.5–2.5/h |
| RTX 4080 / 3080Ti | 12–16 GB | 够用,scGPT 控制 batch | ¥1–1.8/h |
| RTX 2080Ti / T4 | 11–16 GB | 能跑但慢,适合先验证 | ¥0.5–1/h |

**推荐:24GB 卡(4090/3090)**。embedding 提取是一次性任务,几小时过完所有数据集,GPU 段总花费通常 **< ¥20**。

---

## 1. 注册与充值
1. 注册 `https://www.autodl.com/`,实名认证(国内平台需实名)
2. **控制台 → 费用 → 充值**:先充 ¥20–50 足够
3. AutoDL 用 **网页 JupyterLab + SSH** 登录,SSH 默认用**密码**(实例页给);也可在「容器实例 → SSH」里加公钥免密

---

## 2. 创建实例(算力市场 → 选机)
1. **地区/主机**:挑有现卡、价格合适的;优先和数据盘同区
2. **GPU**:选 RTX 4090 / 3090(24GB),数量 1
3. **镜像**:选基础镜像 **`PyTorch 2.x / Python 3.10 / CUDA 12.1`**(AutoDL「社区镜像/基础镜像」里有官方 PyTorch;选 2.1~2.3 + cu121 一档)
4. **数据盘扩容**:默认数据盘可能不够,**扩到 ≥ 50 GB**(数据集 + 模型 checkpoint + 输出)
5. 点 **立即创建**。几十秒后实例在 **控制台 → 容器实例** 出现

> 省钱:若想先只传数据/装环境,创建后用 **「无卡模式开机」**(实例右侧下拉),装完再关机、改成带卡开机跑提取。

---

## 3. 连接实例
**方式 A(推荐,简单):** 实例卡片点 **JupyterLab**,网页里直接开 Terminal,所有命令在里面跑。

**方式 B(SSH):** 实例卡片有「登录指令」与「密码」,形如:
```bash
ssh -p <PORT> root@<REGION>.autodl.com
# 首次粘贴密码;或先把本机公钥加到实例 → 免密
```
> 连不上 → 确认实例为「运行中」;密码从实例页复制(每次重建会变)。

---

## 4. 装环境(关键:先开学术加速)
把本目录 `onstart_autodl.sh` 传上去(见第 5 节),或在 JupyterLab Terminal 里:
```bash
cd /root/autodl-tmp
source /etc/network_turbo      # ★ AutoDL 学术加速,装包/拉 HF 前必须先开
bash onstart_autodl.sh         # 装 scanpy/scvi-tools/geneformer/scgpt + GPU 自检
```
脚本末尾打印各包版本与 `nvidia-smi`,确认 GPU 可见、关键包 `ok`。

> `network_turbo` 只对当前 shell 生效;新开终端要重新 `source`。

---

## 5. 传数据与脚本(本机 → 实例)

AutoDL 推荐用 **JupyterLab 直接拖拽上传**(小文件最省事),或用 scp:

```bash
# 在本机 bioguard-scfm/ 目录;PORT/REGION 换成实例页的值
export ADL_PORT=<PORT>
export ADL_HOST=<REGION>.autodl.com

# 实例上先建目录(JupyterLab Terminal):mkdir -p /root/autodl-tmp/{data,embeddings}
scp -P $ADL_PORT cloud/extract_embeddings.py       root@$ADL_HOST:/root/autodl-tmp/
scp -P $ADL_PORT cloud/autodl/onstart_autodl.sh    root@$ADL_HOST:/root/autodl-tmp/
scp -P $ADL_PORT data/processed/<dataset>.h5ad     root@$ADL_HOST:/root/autodl-tmp/data/
```

> 大文件(>几 GB)建议用 AutoDL 的**阿里云盘/公网网盘中转**或 JupyterLab 上传,scp 跨境可能慢。
> 传数据这一步可在 **无卡模式** 下做,省 GPU 钱。

---

## 6. 跑提取(实例 `/root/autodl-tmp` 下)
```bash
cd /root/autodl-tmp
source /etc/network_turbo      # 若 scGPT/Geneformer 运行时还要联网拉东西

# scVI(验证流水线,最快)—— 这条已确认可跑通
python extract_embeddings.py --input data/<ds>.h5ad --model scvi       --dataset <ds> --out embeddings

# Geneformer(需 var['ensembl_id'];见下方「Geneformer 两处必改」)
python extract_embeddings.py --input data/<ds>.h5ad --model geneformer --dataset <ds> --out embeddings

# scGPT(需先下 whole-human checkpoint,见 onstart_autodl.sh 第 5 节)
python extract_embeddings.py --input data/<ds>.h5ad --model scgpt      --dataset <ds> --out embeddings \
    --scgpt-model-dir /root/autodl-tmp/scgpt_models/whole_human
```
产出:`embeddings/<ds>/<model>/embedding.h5ad`(`obsm["X_embedding"]`)+ `run_metadata.json`。

**首次跑 Geneformer 务必核对**:打印 `emb_df.columns` 和 `emb.shape`,确认没有 metadata 列混进 embedding、行数与输入一致(对应 code review 的 #3/#4)。

---

## Geneformer 说明(脚本已修复,无需再手改代码)

之前 code review 的 Geneformer 三处问题(#2 权重目录、#3 取列、#4 行对齐)**已全部修进 `extract_embeddings.py`**,跑之前不用再改源码,只需注意两个命令行参数:

**(1) 权重目录(原 #2,已自动探测)**
脚本现在会在 geneformer 包内自动找含 `config.json` + 权重文件的子目录。多数情况下直接跑即可。
若自动探测失败(会报错并列出包目录内容),用 `--gf-model-dir` 显式指定:
```bash
# 先看包目录里有哪些权重子目录
python -c "import geneformer,os;print(os.path.dirname(geneformer.__file__))"
# 然后指定,例如:
python extract_embeddings.py --input data/<ds>.h5ad --model geneformer --dataset <ds> --out embeddings \
    --gf-model-dir <上面目录>/Geneformer-V2-104M
```

**(2) 取第几层(原注释里的 emb_layer,已参数化)**
默认 `--gf-emb-layer -1`(倒数第二层,新版常用)。若你的权重适配 `0`,加 `--gf-emb-layer 0` 即可,无需改代码。

> 行对齐(原 #4)与取列(原 #3)已在脚本内用 `emb_label=[bgi_cell_id]` + 列名筛选自动处理;
> 首次跑时留意日志里是否出现 `[warn] emb_df 未带 bgi_cell_id 列` —— 若出现说明该版本 EmbExtractor 行为不同,需人工核对行序。

---

## 7. 下载产物回本地
```bash
# 在本机 bioguard-scfm/ 目录
scp -P $ADL_PORT -r root@$ADL_HOST:/root/autodl-tmp/embeddings/<ds> embeddings/
```
确认每个 `embedding.h5ad` 的 `obsm["X_embedding"]` 维度正确、`run_metadata.json` 齐全。
> 也可在 JupyterLab 里右键文件「Download」。

---

## 8. ⚠️ 跑完务必关机
AutoDL 按 **GPU 运行时长** 计费,跑完务必 **关机**(控制台 → 容器实例 → 关机):
- **关机**:停止 GPU 计费,数据盘保留(仍收少量存储费,通常几毛/天)——下次可直接开机复用环境
- **彻底不用了**:确认第 7 步产物下载完整后,**释放实例 + 删数据盘**,停止一切计费
- 销毁/释放前务必确认产物已下回本地

---

## 成本预估
24GB 卡 ~¥2/h ×(装环境 0.5h + 跑完所有数据集模型 2–4h)≈ **¥5–10/次**。
无卡模式传数据/装环境段几乎不花钱。建议一次性把所有数据集 × 所有模型跑完再关机,避免反复装环境。

---

## 复现性(宪法约束 4)
- 每次提取产出的 `run_metadata.json` 含:模型版本/checkpoint、输入维度、耗时、显存峰值、随机种子、`pip freeze`
- AutoDL 镜像名 + CUDA 版本(如 `PyTorch 2.3 / CUDA 12.1`)记进对应数据集的提取记录
- 数据集固定 DOI/版本(见 data_survey/candidates.csv)

---

## 一页速查(TL;DR)
```bash
# 1) 网页创建 4090 实例,镜像 PyTorch2.x+cu121,数据盘≥50G →(可无卡模式)开机
# 2) JupyterLab Terminal:
cd /root/autodl-tmp && source /etc/network_turbo && bash onstart_autodl.sh
# 3) 上传 data/processed/<ds>.h5ad 到 /root/autodl-tmp/data/
# 4) 跑:
python extract_embeddings.py --input data/<ds>.h5ad --model scvi --dataset <ds> --out embeddings
# 5) 下载 embeddings/<ds>/ 回本地 → 关机/释放实例
```
