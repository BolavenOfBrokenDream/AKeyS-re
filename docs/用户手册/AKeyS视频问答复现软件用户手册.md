# AKeyS 视频问答复现软件用户手册

（Software User Manual，SUM）

适用软件：AKeyS × DeepSeek 视频问答复现程序

文档标识：AKEYS-SUM-001　　软件版本：1.0　　文档版本：1.0　　编制日期：2026 年 11 月 12 日

# 文档修订记录

| 版本 | 日期 | 修订内容 | 修订人 |
|---|---|---|---|
| 1.0 | 2026-11-12 | 首次编制 AKeyS × DeepSeek 复现程序说明 | 项目组 |

本手册按照 GB/T 8567—2006 第 7.23 条“软件用户手册（SUM）”进行剪裁编制。对本项目不适用的图形交互界面、账户访问控制和联机消息等内容不单独设置章节。

# 目录

在 Word 中右键单击此处并选择“更新域”，以生成目录。

# 1 引言

## 1.1 标识

| 项目 | 标识内容 |
|---|---|
| 系统/软件名称 | AKeyS 视频问答复现程序（DeepSeek 后端） |
| 软件标识 | AKEYS-CSCI-001 |
| 软件版本 | 1.0 |
| 文档名称 | AKeyS 视频问答复现软件用户手册 |
| 文档标识 | AKEYS-SUM-001 |
| 文档版本 | 1.0 |
| 代码仓库 | https://github.com/BolavenOfBrokenDream/AKeyS-re |
| 源仓库 | https://github.com/fansunqi/AKeyS |
| 保密性 | 公开，无保密要求；API 密钥和原始响应日志不得公开 |

## 1.2 系统概述

本软件用于复现 AKeyS（Agentic Keyframe Search）在 EgoSchema Subset 上的问题引导关键帧搜索与视频问答过程。复现版将原 GPT-4o 后端替换为 DeepSeek，使用仓库附带的 500 个问答标注和每视频 180 条 LaViLa 字幕，提供 AKeyS-A*、均匀采样 18 帧和均匀采样 24 帧三种运行方式。

软件为命令行程序，无需 GPU，不执行模型训练。主要工作包括动态视频段搜索、时序摘要、问题回答、置信度评估、后处理投票、缓存、准确率与帧数统计、API token 用量和费用汇总。随仓库保存的完整结果为：AKeyS 准确率 70.0%、平均 22.508 帧；均匀 18 帧和 24 帧准确率分别为 65.8% 和 66.6%。

软件面向具备 Python 和命令行基础的研究人员或课程复现人员。运行完整实验需要有效的 DeepSeek API 密钥并会产生网络服务费用；只检查已有结果不需要密钥。

## 1.3 文档概述

本手册说明软件清单、运行环境、代码组织、数据准备、安装设置、快速预检、三组完整实验、单组运行、结果汇总、输出解释、缓存恢复和常见故障处理。算法分析与实验结果详见 `docs/复现报告/main.pdf`。

文档和项目代码无额外保密限制；数据、字幕、第三方源码及 API 服务的使用须遵守各自许可和服务条款。API 密钥应仅保存在用户自己的环境变量或仓库外的安全位置。

# 2 引用文件

| 编号 | 文件名称 | 版本/日期 | 来源 |
|---|---|---|---|
| GB/T 8567—2006 | 计算机软件文档编制规范 | 2006-03-14 发布 | 国家标准 |
| PAPER-001 | Agentic Keyframe Search for Video Question Answering | arXiv:2503.16032，2025 | https://arxiv.org/abs/2503.16032 |
| SRC-001 | fansunqi/AKeyS（源仓库） | 复现基准版本 | https://github.com/fansunqi/AKeyS |
| DATA-001 | EgoSchema Subset 标注与 LaViLa 字幕 | 源仓库附带子集，500 样本 | https://egoschema.github.io/ |
| SRC-002 | LLoVi（字幕来源相关项目） | 源仓库引用版本 | https://github.com/CeeZh/LLoVi |
| API-001 | DeepSeek API Documentation | 以运行时在线文档为准 | https://api-docs.deepseek.com/ |

# 3 软件综述

## 3.1 软件应用

软件通过命令行参数选择数据、模型、缓存和输出目录。AKeyS 主程序先读取少量初始字幕，再由语言模型执行摘要问答、反思问答、置信度评估和候选时间段扩展；满足双路径答案一致与置信度条件时提前终止，否则在最大搜索步数后进入后处理投票和直接作答兜底。

均匀采样基线从 180 条字幕中固定抽取 18 或 24 条，一次请求直接作答。离线汇总程序从预测 JSON 和用量 JSONL 计算准确率、平均帧数、解析失败率、搜索状态、API 调用、token 和可选费用。

## 3.2 软件清单

| 软件/文件 | 用途 | 必要性 |
|---|---|---|
| `main.py` | AKeyS 搜索、作答与评价主入口 | 运行 AKeyS 必需 |
| `uniform_baseline.py` | 均匀采样 18/24 帧基线 | 运行基线必需 |
| `model.py` | OpenAI 兼容 API、DeepSeek 参数、重试、缓存与用量日志 | 必需 |
| `summarizer.py` | 时序摘要与基于摘要的问答 | AKeyS 必需 |
| `video_seg.py` | 视频段树及节点拆分、合并 | AKeyS 必需 |
| `arg_parser.py` | 全部命令行参数 | 必需 |
| `util.py` | JSON/答案解析、缓存锁、日志和字幕读取 | 必需 |
| `eval.py` | 准确率、已回答数和平均帧数输出 | 必需 |
| `summarize_run.py` | 单次运行离线汇总及费用估算 | 推荐 |
| `analyze_results.py` | 按答案产生阶段统计并生成 PNG | 可选 |
| `scripts/deepseek_smoke.sh` | 5 样本 AKeyS 预检 | 推荐 |
| `scripts/deepseek_full.sh` | 顺序执行三组 500 样本实验 | 完整复现推荐 |
| `data/egoschema/` | 子集标注、字幕和上下文示例 | 必需 |
| `requirements.txt` | Python 依赖清单 | 必需 |
| `results/` | 预测、汇总和已有实验结果 | 自动生成或已提供 |
| `cache/` | LLM 响应缓存 | 自动生成，不纳入版本控制 |
| `docs/` | 复现报告和用户手册 | 文档交付物 |

## 3.3 软件环境

| 资源 | 要求或实测设置 |
|---|---|
| 操作系统 | 提供的 DeepSeek 脚本面向 Windows Git Bash；Python 主程序也可在其他系统运行 |
| Python | 支持依赖文件所列版本；已在 Python 3.14 环境配置兼容依赖 |
| Python 环境 | 推荐使用项目内 `.venv` 虚拟环境 |
| 主要依赖 | openai 1.63.2、NumPy、tqdm；分析图表另用 Matplotlib |
| GPU/CUDA | 不需要 |
| 网络 | 必须能够访问 `https://api.deepseek.com`；原始 GPT-4o 流程需相应 OpenAI 服务 |
| API 账户 | DeepSeek 密钥及可用余额；完整 AKeyS 会产生多轮调用费用 |
| 磁盘空间 | 代码与随附子集数据较小；缓存和原始响应用量日志随运行增长，建议预留数百 MB |
| 文档工具（可选） | XeLaTeX 用于重编译复现报告；Word 用于更新手册目录 |

## 3.4 软件组织与操作概述

所有命令均在仓库根目录执行。输入数据默认位于 `data/egoschema/`，输出由 `--output_base_path` 和 `--logger_base_path` 指定。预测文件以启动时间戳命名；用量日志按 JSONL 追加，记录运行 ID、样本 ID、调用类型、状态和 token。每次启动都会生成新的运行 ID，结果汇总时按该 ID 过滤日志。

`cache/` 保存语言模型响应。缓存命中时不调用 API，但仍写一条 `cache_hit` 用量记录。缓存不是预测级断点续跑：重新执行命令仍会遍历所选样本并生成一份新预测文件，只是相同模型和消息的响应可直接从缓存取得。

# 4 软件访问

## 4.1 首次用户

### 4.1.1 获取软件

```bash
git clone https://github.com/BolavenOfBrokenDream/AKeyS-re.git
cd AKeyS-re
```

### 4.1.2 访问控制

本软件本身无登录、账户或网络服务访问控制。访问 DeepSeek 时由 API 密钥鉴权。用户应限制密钥、缓存和原始响应日志的访问权限，不得把真实密钥写入脚本、命令截图、JSON 结果或 Git 提交。

### 4.1.3 安装与设置

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
```

Windows Git Bash：

```bash
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux 或 macOS 的激活命令为：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

检查依赖：

```bash
python -c "import openai, numpy, matplotlib, pandas, cv2, PIL, tqdm; print('dependencies ok')"
python main.py --help
```

在 Git Bash 中设置 DeepSeek 密钥和服务地址：

```bash
export OPENAI_API_KEY='替换为你的密钥'
export OPENAI_BASE_URL='https://api.deepseek.com'
export PYTHONUTF8=1
```

PowerShell 可使用 `$env:OPENAI_API_KEY='替换为你的密钥'`。环境变量仅对当前终端及其子进程有效；关闭终端后需重新设置。也支持 `--api_key_file` 从文件读取，但推荐使用环境变量，密钥文件必须放在仓库外并限制访问。

## 4.2 数据准备

### 4.2.1 EgoSchema Subset

完整复现所需子集已经随仓库提供，无需另下载原始视频：

```text
data/egoschema/
├─ subset_anno.json          # 500 个问题、选项和标签
├─ lavila_subset.json        # 500 个视频，每个 180 条字幕
├─ example_summary.txt       # 时序摘要上下文示例
└─ example_qa_by_summary.txt # 摘要问答上下文示例
```

标注和字幕按视频 ID 对应，答案编号为 0 至 4。不要改变样本键名、选项字段 `option 0` 至 `option 4`、`truth` 字段或字幕顺序。默认命令只处理标注顺序中的前 `--process_num` 个样本。

### 4.2.2 EgoSchema 全集和演示数据

全集实验需按源仓库说明另行下载 `fullset_anno.json` 与 `lavila_fullset.json`，放入 `data/egoschema/` 后运行 `scripts/egoschema_fullset.sh`。该全集脚本保留原始 GPT-4o 默认参数，不是本次 DeepSeek 完整复现脚本。

`data/demo/` 提供演示标注、字幕和视频，`scripts/demo.sh` 同样使用原始模型默认值。若只想验证 DeepSeek 复现链路，应优先使用 5.2 节的 5 样本预检，不必运行演示脚本。

# 5 软件使用指南

## 5.1 通用操作约定

正式实验建议按“安装检查—5 样本预检—三组完整实验—离线汇总—抽查预测”的顺序执行。下列参数最常用；完整列表以 `python main.py --help` 或 `arg_parser.py` 为准。

| 参数 | 含义 |
|---|---|
| `--model_name NAME` | 模型名；复现使用 `deepseek-flash`，原始默认为 GPT-4o |
| `--temperature X` | 采样温度；复现固定为 0.2 |
| `--max_tokens N` | DeepSeek 最大输出 token；复现为 1024 |
| `--process_num N` | 从标注开头处理 N 个样本；预检 5，完整 500 |
| `--max_workers N` | 并发样本数；复现脚本为 1，提高并发会增加限流风险 |
| `--cache_path PATH` | 响应缓存路径；不同模型或参数实验应使用不同文件 |
| `--use_cache` | 沿用原仓库的反向开关：传入此参数会禁用缓存，默认启用缓存 |
| `--usage_log_path PATH` | 用量 JSONL；不传则不记录详细 token 和原始响应 |
| `--output_base_path DIR` | 预测 JSON 输出目录 |
| `--logger_base_path DIR` | 运行日志输出目录 |
| `--num_frames N` | 均匀基线帧数，复现取 18 或 24 |
| `--search_strategy NAME` | `a_star`、`bfs`、`gbfs` 或 `dijkstra` |
| `--beam_size N` | 每轮节点选择次数，复现为 5 |
| `--final_step N` | 最大搜索步数，复现为 5 |
| `--init_interval N` | 初始字幕间隔，复现为 10 |
| `--ans_mode MODE` | 主流程答案模式，复现为 `vote_conf_and` |
| `--post_ans_mode MODE` | 后处理答案模式，复现为 `vote` |
| `--specific_id ID` | 只运行一个指定视频 ID |
| `--specific_id_path PATH` | 从 JSON 字符串列表读取要处理的视频 ID |
| `--post_resume_samples` | 反向开关：传入后后处理使用累计帧，而非恢复初始帧 |

缓存键由模型名和消息组成，不包含 temperature、最大 token 或 base URL。更改这些设置、提示词或服务商时，应更换 `--cache_path`，避免混用旧响应。原始 `usage*.jsonl` 和缓存已被 `.gitignore` 排除。

## 5.2 5 样本预检

在 Windows Git Bash、仓库根目录执行：

```bash
export OPENAI_API_KEY='替换为你的密钥'
bash scripts/deepseek_smoke.sh
```

脚本自动设置 DeepSeek base URL，使用 `.venv/Scripts/python`，处理前 5 个样本，输出到：

- `results/deepseek_akeys/TIMESTAMP.json`：5 条预测；
- `results/deepseek_akeys/TIMESTAMP.log`：运行日志；
- `results/deepseek_akeys/usage.jsonl`：API 与缓存用量；
- `cache/deepseek_flash.pkl`：DeepSeek 独立缓存。

正常结束时终端显示 `Total: 5`、准确率、平均帧数和时间戳。预检只验证链路，不用 5 样本准确率推断完整结果。Linux/macOS 用户可将脚本中的 `.venv/Scripts/python` 改为 `.venv/bin/python`，或按 5.4 节直接使用当前虚拟环境的 `python`。

## 5.3 三组完整实验

确认预检成功并了解 API 费用后执行：

```bash
bash scripts/deepseek_full.sh
```

脚本依次运行：

1. 均匀采样 18 帧，500 个样本；
2. 均匀采样 24 帧，500 个样本；
3. AKeyS-A*，500 个样本。

三组实验均使用 temperature 0.2、最大输出 1024 token 和独立缓存。每组结束后自动调用 `summarize_run.py`，输出 `TIMESTAMP_summary.json`。AKeyS 使用单工作线程，完整运行包含大量多轮请求，耗时可较长；不要同时启动多个写同一缓存或同一用量文件的完整脚本。

脚本中的价格参数为非缓存输入 0.3、缓存输入 0.006、输出 1.2 美元/百万 token，仅用于本次记录。若需按其他价格估算，可在离线汇总时覆盖，不应把估算值当作实时报价。

## 5.4 单组运行与自定义实验

### 5.4.1 单独运行 AKeyS

以下命令不依赖脚本内的解释器路径，可在已激活虚拟环境中运行：

```bash
python main.py \
  --dataset egoschema_subset \
  --cap_path data/egoschema/lavila_subset.json \
  --anno_path data/egoschema/subset_anno.json \
  --example_summary_path data/egoschema/example_summary.txt \
  --example_qa_by_summary_path data/egoschema/example_qa_by_summary.txt \
  --model_name deepseek-flash \
  --cache_path cache/deepseek_flash.pkl \
  --temperature 0.2 \
  --max_tokens 1024 \
  --process_num 500 \
  --max_workers 1 \
  --output_base_path results/deepseek_akeys/ \
  --logger_base_path results/deepseek_akeys/ \
  --usage_log_path results/deepseek_akeys/usage.jsonl
```

快速单样本检查可增加 `--specific_id 视频ID --process_num 1`。`--specific_id` 优先于默认样本列表；指定 ID 必须存在于标注和字幕中。

### 5.4.2 单独运行均匀基线

均匀 24 帧示例：

```bash
python uniform_baseline.py \
  --dataset egoschema_subset \
  --cap_path data/egoschema/lavila_subset.json \
  --anno_path data/egoschema/subset_anno.json \
  --model_name deepseek-flash \
  --cache_path cache/deepseek_uniform_24.pkl \
  --temperature 0.2 \
  --max_tokens 1024 \
  --num_frames 24 \
  --process_num 500 \
  --output_base_path results/deepseek_uniform/ \
  --logger_base_path results/deepseek_uniform/ \
  --usage_log_path results/deepseek_uniform/usage_24.jsonl
```

均匀 18 帧需同时把 `--num_frames` 改为 18，并更换缓存、用量日志路径，避免结果混淆。基线输出中的 `get_ans_step` 固定为 `uniform`。

## 5.5 评价、汇总与图表

主程序和基线结束时自动调用 `eval.py`。也可对已有预测重新评价：

```bash
python eval.py results/deepseek_akeys/TIMESTAMP.json
```

离线汇总需要预测文件和对应用量日志。预测文件名的时间戳应与用量记录中的 `run_id` 一致：

```bash
python summarize_run.py \
  results/deepseek_akeys/TIMESTAMP.json \
  results/deepseek_akeys/usage.jsonl \
  --input_price 0.3 \
  --cached_input_price 0.006 \
  --output_price 1.2 \
  --output results/deepseek_akeys/TIMESTAMP_summary.json
```

不需要费用时省略三个价格参数，`total_cost_usd` 将为 `null`。若预测文件名不是运行 ID，可显式传 `--run_id`。汇总只统计该运行 ID 的记录，同一 JSONL 中可保留多次运行。

生成答案阶段统计图：

```bash
python analyze_results.py --filepath results/deepseek_akeys_final/predictions.json
```

程序在预测文件旁生成同名 PNG。该分析适用于包含有效 `get_ans_step` 的 AKeyS 结果；含执行错误且该字段为 `null` 的结果应先检查错误记录。

## 5.6 输出及解释

| 输出位置 | 内容 |
|---|---|
| `results/deepseek_akeys/TIMESTAMP.json` | 新运行 AKeyS 的逐样本预测 |
| `results/deepseek_akeys_final/predictions.json` | 随仓库保存的 500 样本最终 AKeyS 预测 |
| `results/deepseek_akeys_final/summary.json` | 最终 AKeyS 汇总：70.0%、22.508 帧等 |
| `results/deepseek_uniform/TIMESTAMP.json` | 均匀基线逐样本预测 |
| `results/deepseek_uniform/*_summary.json` | 均匀基线汇总和费用 |
| `results/<实验>/TIMESTAMP.log` | 截断后的提示、响应、异常等运行日志 |
| `results/<实验>/usage*.jsonl` | 原始响应、调用状态、运行 ID 和 token；默认不入库 |
| `cache/*.pkl` | LLM 响应缓存；默认不入库 |
| `docs/复现报告/` | LaTeX 报告、PDF 和结果图 |
| `docs/用户手册/` | Markdown 与 Word 用户手册 |

预测 JSON 以视频 ID 为键，主要字段如下：

| 字段 | 含义 |
|---|---|
| `answer` | 预测选项编号 0—4；-1 表示无有效答案 |
| `label` | 正确选项编号 |
| `corr` | 答案与标签一致为 1，否则为 0 |
| `count_frame` | 本样本累计读取的不同字幕帧数；异常样本可能为 0 |
| `get_ans_step` | 答案产生阶段，如 `1_s_r`、`post_s_r`、`final_direct_qa` 或 `uniform` |
| `answer_parse_failed` | 是否发生答案解析失败或异常导致的无答案 |
| `search_status` | `completed`、`max_steps` 或 `error` |
| `error` | 单样本异常类型和消息；仅异常时存在 |

汇总 JSON 中，`api_calls` 只计成功网络调用，`cache_hits` 另计缓存命中，`api_errors` 计 API 错误；`prompt_tokens`、`completion_tokens` 和 `cached_tokens` 仅来自网络成功记录。`eval.py` 的平均帧数只统计有答案样本，`summarize_run.py` 统计全部预测样本；存在无答案时两者可能不同，本次三组完整结果解析失败均为 0，因此一致。

## 5.7 中断后的恢复与重跑

程序没有预测级断点文件。中断后重新执行相同命令会开始一个新运行 ID 并重新遍历样本，但已缓存的模型请求会命中缓存，通常可减少重复 API 调用。恢复步骤：

1. 保留原缓存、预测和用量日志，不删除旧结果；
2. 使用相同模型、提示词、生成参数和 `--cache_path`；
3. 重新执行命令，并确认新输出文件名使用新的时间戳；
4. 用新时间戳汇总新运行，不要误把旧日志中的另一运行 ID 混入；
5. 若只需补跑指定样本，把视频 ID 写成 JSON 字符串列表并传 `--specific_id_path`，随后人工核对合并口径。

若需完全无缓存重跑，传入 `--use_cache` 或指定新的缓存路径。禁用缓存会显著增加完整 AKeyS 实验的 API 调用和费用。

# 6 错误、诊断与恢复

| 现象 | 可能原因 | 处理方法 |
|---|---|---|
| 脚本提示 `Set OPENAI_API_KEY...` | 当前 Git Bash 未设置密钥 | 按 4.1.3 设置环境变量，不要在脚本中硬编码 |
| OpenAI 鉴权错误 | 密钥无效、过期或服务地址错误 | 核对密钥和 `OPENAI_BASE_URL`，检查账户状态 |
| `RateLimitError` 或请求超时 | 并发过高、网络不稳定或限流 | 程序会有限重试；降低 `--max_workers`，稍后利用缓存重跑 |
| 余额不足或费用异常 | 多轮 AKeyS 调用量较大 | 停止完整运行，先用 5 样本预检；检查用量日志和服务商账单 |
| 找不到 `.venv/Scripts/python` | 在非 Windows 系统直接运行所附脚本 | 激活虚拟环境后按 5.4 使用 `python`，或改为本机解释器路径 |
| `ModuleNotFoundError` | 未安装依赖或使用了错误解释器 | 激活 `.venv`，重新执行 `pip install -r requirements.txt` |
| 找不到数据或视频 ID | 路径错误、未在根目录执行或 ID 不在子集 | 核对 4.2 的目录与参数；从仓库根目录执行 |
| JSON/答案解析失败 | 模型输出不符合预期或 API 返回空内容 | 查看对应日志和原始响应；失败计为答错，不用随机答案替代 |
| 结果文件样本数少于预期 | 运行中断、样本列表被限制或 ID 筛选 | 检查 `process_num`、ID 列表和日志；按 5.7 缓存重跑或补跑 |
| 汇总费用或 token 为 0 | 运行 ID 不匹配、未启用用量日志或全部命中缓存 | 核对 `run_id` 和 JSONL；缓存命中本身不产生新的网络 token |
| 汇总结果混入旧记录 | 多次运行共用日志且未按 ID 区分 | 使用新预测的时间戳作为 `run_id`，必要时传 `--run_id` |
| 改参数后仍得到旧回答 | 缓存键不含 temperature、max token 或 base URL | 为新配置指定独立缓存路径 |
| 缓存写入失败 | 目录无权限、磁盘不足或并发运行冲突 | 检查磁盘和权限；避免多个完整脚本写同一缓存 |
| `analyze_results.py` 在 `None` 阶段出错 | 预测中含执行错误，`get_ans_step` 为空 | 先查看 `search_status=error` 的样本并补跑，再分析完整结果 |

注意：原始用量日志包含模型响应，运行日志包含截断提示和响应，均可能含敏感或不宜公开的信息。提交代码前使用 `git status --ignored` 检查，不要强制添加 `cache/`、`usage*.jsonl`、密钥文件或本地环境目录。

# 附录A 复现检查表

- □ 已从目标仓库获取完整代码，并在仓库根目录执行命令。
- □ `.venv` 已创建，依赖检查和 `python main.py --help` 通过。
- □ 500 条标注与 500 组、每组 180 条 LaViLa 字幕存在且 ID 对应。
- □ DeepSeek 密钥通过环境变量提供，未写入仓库文件。
- □ 5 样本预检完成，预测、日志、缓存和用量文件均可生成。
- □ 已了解完整 AKeyS 的多轮 API 成本，三组实验使用独立缓存。
- □ 三组完整预测均为 500 条，解析失败、API 错误和样本异常已核查。
- □ 汇总时预测时间戳与用量 `run_id` 一致，费用价格假设已记录。
- □ 已核对最终参考结果：65.8%、66.6%、70.0%，平均帧数 18、24、22.508。
- □ 重跑使用缓存时没有把它误称为预测级断点续跑；新旧结果未混合。

# 附录B 缩略语

| 缩略语 | 英文全称 | 中文含义 |
|---|---|---|
| SUM | Software User Manual | 软件用户手册 |
| CSCI | Computer Software Configuration Item | 计算机软件配置项 |
| AKeyS | Agentic Keyframe Search | 智能体式关键帧搜索 |
| VideoQA | Video Question Answering | 视频问答 |
| API | Application Programming Interface | 应用程序编程接口 |
| JSON | JavaScript Object Notation | JavaScript 对象表示法 |
| JSONL | JSON Lines | 每行一个 JSON 记录的文本格式 |
| LLM | Large Language Model | 大语言模型 |
| LaViLa | Large Language and Vision Assistant | 用于生成视频叙述的语言视觉模型 |
| A* | A-star Search | 结合代价与启发信息的一类搜索策略 |
