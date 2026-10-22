"""Download LIAR2 (Apache-2.0, Hugging Face chengxuphd/liar2) into data/liar2/ so that scripts/run_experiments.py can run.

    python scripts/fetch_liar2.py
"""
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "liar2")
BASE = "https://huggingface.co/datasets/chengxuphd/liar2/resolve/main/"


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in ("README.md", "train.csv", "valid.csv", "test.csv"):
        dest = os.path.join(OUT, name)
        if os.path.exists(dest):
            print("have", name)
            continue
        print("downloading", name)
        urllib.request.urlretrieve(BASE + name, dest)
    print("done:", OUT)


if __name__ == "__main__":
    main()
