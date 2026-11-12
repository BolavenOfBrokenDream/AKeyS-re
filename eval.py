import json
import argparse

def main(filepath):
    with open(filepath, encoding="utf-8") as result_file:
        data = json.load(result_file)

    no_ans = []
    accs = []
    answered_accs = []
    frames = []
    for key, item in data.items():
        acc = item["answer"] == item["label"]
        accs.append(acc)
        if item["answer"] == -1:
            no_ans.append(key)
        else:
            answered_accs.append(acc)
            frames.append(item["count_frame"])

    total = len(data)
    print("Total: ", total)
    print("No answer: ", len(no_ans))
    print("Have answer: ", len(answered_accs))
    print("Mean accuracy (included no answer): {:.2f}%".format(sum(accs) / total * 100 if total else 0))
    print("Mean accuracy (excluded no answer): {:.2f}%".format(sum(answered_accs) / len(answered_accs) * 100 if answered_accs else 0))
    print("Mean frame: {:.2f}".format(sum(frames) / len(frames) if frames else 0))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process timestamp for JSON file.")
    parser.add_argument("filepath", default="", type=str)
    args = parser.parse_args()
    main(args.filepath)