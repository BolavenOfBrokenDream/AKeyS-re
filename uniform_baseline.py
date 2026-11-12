import json
import os
from datetime import datetime

import numpy as np
from tqdm import tqdm

from arg_parser import parse_args
from eval import main as evaluate_results
from model import GPT
from util import parse_text_find_number, read_caption, set_logger


def generate_answer(model, question, caption, num_frames, args, logger, video_id):
    answer_format = {"final_answer": "xxx"}
    prompt = f"""
    Given a video that has {num_frames} frames, the frames are decoded at 1 fps. Given the following descriptions of the sampled frames in the video:
    {caption}
    #C to denote the sentence is an action done by the camera wearer (the person who recorded the video while wearing a camera on their head).
    #O to denote that the sentence is an action done by someone other than the camera wearer.
    Please answer the following question:
    ```
    {question}
    ```
    Please think carefully and write the best answer index in Json format {answer_format}. Note that only one answer is returned for the question, and you must select one answer index from the candidates.
    """
    system_prompt = "You are a helpful assistant designed to output JSON."
    response, _ = model.forward(
        head=system_prompt,
        prompt=prompt,
        logger=logger,
        use_cache=args.use_cache,
        use_json_format=True,
        sample_id=video_id,
        call_type=f"uniform_{args.num_frames}",
    )
    return response


def main(args):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = set_logger(timestamp, args.logger_base_path)
    api_key = os.getenv("OPENAI_API_KEY")
    if args.api_key_file:
        with open(args.api_key_file, encoding="utf-8") as key_file:
            api_key = key_file.read().strip()
    model = GPT(
        api_key=api_key,
        model_name=args.model_name,
        temperature=args.temperature,
        base_url=os.getenv("OPENAI_BASE_URL"),
        max_tokens=args.max_tokens,
        usage_log_path=args.usage_log_path,
        run_id=timestamp,
    )

    with open(args.anno_path, encoding="utf-8") as anno_file:
        anns = json.load(anno_file)
    with open(args.cap_path, encoding="utf-8") as cap_file:
        all_caps = json.load(cap_file)

    logs = {}
    process_video_ids = list(anns.keys())[:args.process_num]
    for video_id in tqdm(process_video_ids):
        ann = anns[video_id]
        caps = all_caps[video_id]
        try:
            question = ann["question"]
            answers = [ann[f"option {i}"] for i in range(5)]
            formatted_question = (
                f"Here is the question: {question}\n"
                + "Here are the choices: "
                + " ".join(f"{i}. {answer}" for i, answer in enumerate(answers))
            )
            sample_idx = np.linspace(
                1, len(caps), args.num_frames, dtype=int
            ).tolist()
            sampled_caps = read_caption(caps, sample_idx)
            response = generate_answer(
                model, formatted_question, sampled_caps, len(caps), args,
                logger, video_id
            )
            answer = parse_text_find_number(response, logger)
            label = int(ann["truth"])
            logs[video_id] = {
                "answer": answer,
                "label": label,
                "corr": int(label == answer),
                "count_frame": len(set(sample_idx)),
                "get_ans_step": "uniform",
                "answer_parse_failed": answer == -1,
            }
        except Exception as exc:
            logger.exception(f"Error processing {video_id}")
            logs[video_id] = {
                "answer": -1,
                "label": int(ann["truth"]),
                "corr": 0,
                "count_frame": args.num_frames,
                "get_ans_step": "uniform",
                "answer_parse_failed": True,
                "error": f"{type(exc).__name__}: {exc}",
            }

    output_result_file = os.path.join(args.output_base_path, f"{timestamp}.json")
    with open(output_result_file, "w", encoding="utf-8") as result_file:
        json.dump(logs, result_file, ensure_ascii=False, indent=2)
    print(f"timestamp: {timestamp}")
    evaluate_results(output_result_file)


if __name__ == "__main__":
    main(parse_args())
