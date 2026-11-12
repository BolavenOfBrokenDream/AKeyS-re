import argparse
import json
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_path")
    parser.add_argument("usage_path")
    parser.add_argument("--run_id", default=None)
    parser.add_argument("--input_price", type=float, default=None,
                        help="USD per million non-cached input tokens")
    parser.add_argument("--cached_input_price", type=float, default=None,
                        help="USD per million cached input tokens")
    parser.add_argument("--output_price", type=float, default=None,
                        help="USD per million output tokens")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result_path = Path(args.result_path)
    run_id = args.run_id or result_path.stem
    with result_path.open(encoding="utf-8") as result_file:
        predictions = json.load(result_file)
    with open(args.usage_path, encoding="utf-8") as usage_file:
        usage_records = [json.loads(line) for line in usage_file if line.strip()]
    records = [record for record in usage_records
               if record.get("run_id") == run_id]
    successful = [record for record in records
                  if record.get("status") == "success"]

    prompt_tokens = sum(record.get("prompt_tokens") or 0
                        for record in successful)
    completion_tokens = sum(record.get("completion_tokens") or 0
                            for record in successful)
    cached_tokens = sum(
        record.get("cached_tokens")
        or (record.get("usage") or {}).get("prompt_cache_hit_tokens")
        or 0
        for record in successful
    )
    sample_count = len(predictions)
    correct = sum(item["answer"] == item["label"]
                  for item in predictions.values())
    parse_failures = sum(item.get("answer_parse_failed", item["answer"] == -1)
                         for item in predictions.values())
    status_counts = Counter(record.get("status") for record in records)

    summary = {
        "run_id": run_id,
        "samples": sample_count,
        "correct": correct,
        "accuracy": correct / sample_count if sample_count else 0,
        "mean_frames": (sum(item["count_frame"] for item in predictions.values())
                        / sample_count if sample_count else 0),
        "answer_parse_failure_rate": (parse_failures / sample_count
                                      if sample_count else 0),
        "search_status": dict(Counter(
            item.get("search_status", "completed")
            for item in predictions.values()
        )),
        "api_calls": len(successful),
        "cache_hits": status_counts.get("cache_hit", 0),
        "api_errors": status_counts.get("api_error", 0),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_tokens": cached_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "total_cost_usd": None,
    }

    if args.input_price is not None and args.output_price is not None:
        cached_price = (args.cached_input_price
                        if args.cached_input_price is not None
                        else args.input_price)
        input_cost = ((prompt_tokens - cached_tokens) * args.input_price
                      + cached_tokens * cached_price) / 1_000_000
        output_cost = completion_tokens * args.output_price / 1_000_000
        summary["total_cost_usd"] = input_cost + output_cost
        summary["cost_per_correct_usd"] = (
            summary["total_cost_usd"] / correct if correct else None
        )

    serialized = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write(serialized + "\n")
    print(serialized)


if __name__ == "__main__":
    main()
