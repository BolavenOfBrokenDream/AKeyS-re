#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY to your DeepSeek API key}"
export OPENAI_BASE_URL="https://api.deepseek.com"
export PYTHONUTF8=1

mkdir -p results/deepseek_uniform results/deepseek_akeys

.venv/Scripts/python uniform_baseline.py \
    --dataset egoschema_subset \
    --cap_path data/egoschema/lavila_subset.json \
    --anno_path data/egoschema/subset_anno.json \
    --model_name deepseek-flash \
    --cache_path cache/deepseek_uniform_18.pkl \
    --temperature 0.2 \
    --max_tokens 1024 \
    --num_frames 18 \
    --process_num 500 \
    --output_base_path results/deepseek_uniform/ \
    --logger_base_path results/deepseek_uniform/ \
    --usage_log_path results/deepseek_uniform/usage_18.jsonl

RESULT_18=$(ls -t results/deepseek_uniform/*.json | head -n 1)
.venv/Scripts/python summarize_run.py "$RESULT_18" results/deepseek_uniform/usage_18.jsonl \
    --input_price 0.3 --cached_input_price 0.006 --output_price 1.2 \
    --output "${RESULT_18%.json}_summary.json"

.venv/Scripts/python uniform_baseline.py \
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

RESULT_24=$(ls -t results/deepseek_uniform/*.json | head -n 1)
.venv/Scripts/python summarize_run.py "$RESULT_24" results/deepseek_uniform/usage_24.jsonl \
    --input_price 0.3 --cached_input_price 0.006 --output_price 1.2 \
    --output "${RESULT_24%.json}_summary.json"

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
    --process_num 500 \
    --max_workers 1 \
    --output_base_path results/deepseek_akeys/ \
    --logger_base_path results/deepseek_akeys/ \
    --usage_log_path results/deepseek_akeys/usage.jsonl

RESULT_AKEYS=$(ls -t results/deepseek_akeys/*.json | head -n 1)
.venv/Scripts/python summarize_run.py "$RESULT_AKEYS" results/deepseek_akeys/usage.jsonl \
    --input_price 0.3 --cached_input_price 0.006 --output_price 1.2 \
    --output "${RESULT_AKEYS%.json}_summary.json"

printf 'Uniform-18 result: %s\n' "$RESULT_18"
printf 'Uniform-24 result: %s\n' "$RESULT_24"
printf 'AKeyS result: %s\n' "$RESULT_AKEYS"
