# 🌲 AKeyS: Agentic Keyframe Search for Video Question Answering

[![GitHub license](https://img.shields.io/badge/License-MIT-green.svg?logo=github)](https://lbesson.mit-license.org/)
[![Arxiv](https://img.shields.io/badge/arXiv-2503.16032-B31B1B.svg?logo=arxiv)](https://arxiv.org/abs/2503.16032)

This repository is the official implementation of [Agentic Keyframe Search for Video Question Answering](https://arxiv.org/abs/2503.16032).

## News and Todo 🗓️

- [x] Release Code for Demo

- [x] Release Code for EgoSchema

- [ ] Release Code for NExT-QA

## Introduction 

​	We present **Agentic Keyframe Search (AKeyS)**, a simple yet powerful algorithm for identifying keyframes in the VideoQA task. It can effectively distinguish key information from redundant, irrelevant content by leveraging modern language agents to direct classical search algorithms. Specifically, we first segment the video and organize it as a tree structure. Then, AKEYS uses a
language agent to estimate heuristics and movement costs while dynamically expanding nodes. Finally, the agent determines if sufficient keyframes have been collected based on termination conditions and provides answers. Extensive experiments on the EgoSchema and NExT-QA datasets show that AKEYS outperforms all previous methods with the highest keyframe searching efficiency, which means it can accurately identify key information and conduct effective visual reasoning with minimal computational overhead. For example, on the EgoSchema subset, it achieves 1.8% higher accuracy while processing only 43.5% of the frames compared to VideoTree.

<img src="assets/teaser.png" style="zoom:200%;" />

## Installation Steps 🛠️

Our AKeyS does not require many computational resources; it can run on a personal computer without GPU.

1. Clone the repository 📦:

   ```python
   git clone git@github.com:fansunqi/AKeyS.git
   cd AKeyS
   ```

2. Create a virtual environment 🧹 and install the dependencies 🧑‍🍳:

   ```python
   python3 -m venv tva_env
   source tva_env/bin/activate
   pip install -r requirements.txt
   ```

3. Set up your API key 🗝️:

   Obtain an OpenAI API key and set  ```OPENAI_API_KEY``` and ```OPENAI_BASE_URL``` as environmental variables in  ```~/.zshrc``` or ```~/.bashrc```. In the ```main.py```, we will use the following codes to obtain the API key and base URL:

   ```
   api_key = os.getenv("OPENAI_API_KEY")
   base_url = os.getenv("OPENAI_BASE_URL")
   ```

## QuickStart 🚀

We present a case demo by running:

```
sh scripts/demo.sh
```

A visualized example:

<img src="assets/viz.png" style="zoom:200%;" />

## EgoSchema Experiments 🔬

We obtained the dataset annotations and extracted captions from the File [LLoVi](https://drive.google.com/file/d/13M10CB5ePPVlycn754_ff3CwnpPtDfJA/view?usp=drive_link) provided. We have already placed subset annotations and captions in ```data/egoschema/```. 

If you don't want to pay for the OpenAI API, we provide our LLM conversation cache [here](https://drive.google.com/file/d/1c_wId28ozyGEQKd5x3Zl8ugmvDVlJSED/view?usp=sharing). You can specify the cache path in ```arg_parser.py```.

For the EgoSchema subset (500 videos), run:

```
sh scripts/egoschema_subset.sh
```

For the EgoSchema fullest, download annotations and captions from [LLoVi](https://drive.google.com/file/d/13M10CB5ePPVlycn754_ff3CwnpPtDfJA/view?usp=drive_link), specify the data path in ```arg_parser.py,``` and run:

```
sh scripts/egoschema_fullset.sh
```

The code will run an automated evaluation script and output accuracy and mean frame number.

## Reproduction documents

The Chinese reproduction report and software user manual are included in this fork:

- [复现报告（PDF）](docs/复现报告/main.pdf) · [LaTeX 源文件](docs/复现报告/main.tex)
- [软件用户手册（Word）](docs/用户手册/AKeyS视频问答复现软件用户手册.docx) · [Markdown 源文件](docs/用户手册/AKeyS视频问答复现软件用户手册.md)

To obtain this reproduction version, clone `https://github.com/BolavenOfBrokenDream/AKeyS-re.git`.

## DeepSeek five-sample smoke validation

Create the virtual environment with `python -m venv .venv` and install `requirements.txt`. On Python 3.14, the requirements file selects compatible package versions automatically. Set your DeepSeek key as the `OPENAI_API_KEY` environment variable (do not store it in any file inside the repository); the scripts read it without printing it, call `deepseek-flash` at `https://api.deepseek.com`, disable thinking, and use `cache/deepseek_flash.pkl` separately from the GPT-4o cache.

Run from the repository root:

```bash
bash scripts/deepseek_smoke.sh
```

This command is capped at five samples. Predictions and logs are written to `results/deepseek_akeys/`; `usage.jsonl` records the run ID, sample ID, call type, raw response, API status, and actual token usage. Answer parsing failures count as incorrect answers. Summarize one run with `python summarize_run.py results/deepseek_akeys/TIMESTAMP.json results/deepseek_akeys/usage.jsonl --output results/deepseek_akeys/TIMESTAMP_summary.json`; optional price arguments are denominated in USD per million tokens.

The independent uniform baseline supports 18 or 24 frames through `--num_frames`. For example, after setting the same API options, run `python uniform_baseline.py --model_name deepseek-flash --num_frames 24 --process_num 5 --cache_path cache/deepseek_uniform_24.pkl`. It is not executed by the AKeyS smoke script.

After checking the 5-sample AKeyS run, `bash scripts/deepseek_full.sh` runs all three 500-sample experiments in order: uniform 18 frames, uniform 24 frames, and AKeyS-A*. Each experiment uses a separate cache and usage log, and the script writes per-run summaries using peak prices.

The final AKeyS results are kept in `results/deepseek_akeys_final/`: `predictions.json` contains the 500 per-sample predictions and `summary.json` the overall metrics (70.0% accuracy, 22.508 mean frames). Uniform-baseline predictions and summaries are in `results/deepseek_uniform/`.

For a step-by-step analysis, run:

```
python3 analyze_results.py --filepath YOUR_RESULT_JSON_FILE_PATH
```

It will output a histogram showing the number of problems solved and the accuracy at each step like this:

<img src="results/egoschema_subset/20250315_162843.png" style="zoom: 50%;" />

## Acknowledgments

We thank the developers of [LLoVi](https://github.com/CeeZh/LLoVi), [VideoTree](https://github.com/Ziyang412/VideoTree), [VideoAgent](https://github.com/wxh1996/VideoAgent) and [HCQA](https://github.com/Hyu-Zhang/HCQA) for their public code release. 

## Citation

If you find our repo useful, please kindly consider citing:

```
@misc{fan2025agentickeyframesearchvideo,
      title={Agentic Keyframe Search for Video Question Answering}, 
      author={Sunqi Fan and Meng-Hao Guo and Shuojin Yang},
      year={2025},
      eprint={2503.16032},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2503.16032}, 
}
```

