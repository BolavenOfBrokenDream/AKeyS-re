#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY to your DeepSeek API key}"
export OPENAI_BASE_URL="https://api.deepseek.com"
export PYTHONUTF8=1

.venv/Scripts/python main.py \
    --dataset egoschema_subset \
    --cap_path data/egoschema/lavila_subset.json \
    --anno_path data/egoschema/subset_anno.json \
    --example_summary_path data/egoschema/example_summary.txt \
    --example_qa_by_summary_path data/egoschema/example_qa_by_summary.txt \
    --model_name deepseek-flash \
    --cache_path cache/deepseek_flash.pkl \
    --temperature 0.2 \
    --max_tokens 1024 \
    --process_num 5 \
    --max_workers 1 \
    --output_base_path results/deepseek_akeys/ \
    --logger_base_path results/deepseek_akeys/ \
    --usage_log_path results/deepseek_akeys/usage.jsonl
