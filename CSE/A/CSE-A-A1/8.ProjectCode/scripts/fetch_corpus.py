"""
Builds the evaluation corpus used by scripts/run_experiments.py.

Six subject files (one per "course") are assembled from English Wikipedia articles (CC BY-SA 4.0), the
exact revision of each article is pinned in experiments/corpus_manifest.json, so a rerun gives the same text.
Each file starts with "Subject: ..." and every article becomes a "Unit n: ..." section, the layout that the
document analyser of the platform recognises.

    python scripts/fetch_corpus.py            # writes experiments/corpus/*.txt (git-ignored) + the manifest
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "experiments", "corpus")
MANIFEST = os.path.join(ROOT, "experiments", "corpus_manifest.json")
API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "ALIP-student-project/1.0 (evaluation corpus builder)"}
MAX_WORDS = 3200

SUBJECTS = {
    "Data Structures": ["Stack (abstract data type)", "Queue (abstract data type)", "Linked list", "Binary search tree",
                        "Hash table", "Heap (data structure)"],
    "Operating Systems": ["Deadlock (computer science)", "Scheduling (computing)", "Paging", "Semaphore (programming)",
                          "Virtual memory", "Thread (computing)"],
    "Database Systems": ["Database normalization", "ACID", "B-tree", "Relational model", "Database index",
                         "Concurrency control"],
    "Computer Networks": ["Transmission Control Protocol", "Domain Name System", "OSI model", "Routing",
                          "Network congestion", "Dynamic Host Configuration Protocol"],
    "Machine Learning": ["Overfitting", "Gradient descent", "Decision tree learning", "Naive Bayes classifier",
                         "K-means clustering", "Support vector machine"],
    "Algorithms": ["Dijkstra's algorithm", "Merge sort", "Quicksort", "Binary search", "Dynamic programming",
                   "Breadth-first search"],
}
TAIL = re.compile(r"^==+\s*(References|See also|External links|Further reading|Notes|Bibliography|Footnotes)\s*==+\s*$", re.I)


def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                data = json.loads(r.read().decode("utf-8"))
            time.sleep(1.5)
            return data
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("Wikipedia kept answering 429")


def strip_math(text):
    """Wikipedia's plain-text extract repeats every formula as a {\displaystyle ...} LaTeX block; drop those blocks."""
    out, i = [], 0
    while True:
        j = text.find("{\displaystyle", i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        depth, k = 0, j
        while k < len(text):
            depth += text[k] == "{"
            depth -= text[k] == "}"
            k += 1
            if depth == 0:
                break
        i = k
    return re.sub(r"[ 	]{2,}", " ", "".join(out))


def clean(extract):
    extract = strip_math(extract)
    lines = []
    for line in extract.splitlines():
        if TAIL.match(line.strip()):
            break
        m = re.match(r"^(=+)\s*(.+?)\s*=+\s*$", line.strip())
        if m:
            lines.append("")
            lines.append(m.group(2))          # section heading as a plain line
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    words = text.split()
    if len(words) > MAX_WORDS:
        cut = " ".join(words[:MAX_WORDS])
        text = cut[: cut.rfind(". ") + 1] if ". " in cut else cut
    return text


def main():
    os.makedirs(OUT, exist_ok=True)
    pinned = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            pinned = {a["title"]: a["revid"] for s in json.load(f)["subjects"] for a in s["articles"]}
    manifest = {"source": "English Wikipedia", "licence": "CC BY-SA 4.0", "max_words_per_article": MAX_WORDS, "subjects": []}
    for si, (subject, titles) in enumerate(SUBJECTS.items(), 1):
        parts, arts = [f"Subject: {subject}", ""], []
        for ui, title in enumerate(titles, 1):
            q = {"action": "query", "prop": "extracts|revisions", "explaintext": 1, "titles": title,
                 "rvprop": "ids", "format": "json", "redirects": 1}
            if title in pinned:
                q = {"action": "query", "prop": "extracts", "explaintext": 1, "revids": pinned[title], "format": "json"}
            page = next(iter(get(q)["query"]["pages"].values()))
            revid = pinned.get(title) or page["revisions"][0]["revid"]
            text = clean(page["extract"])
            parts += [f"Unit {ui}: {page['title']}", "", text, ""]
            arts.append({"title": page["title"], "revid": revid, "words": len(text.split())})
            print(subject, "|", page["title"], revid, len(text.split()))
        fname = f"{si:02d}_{subject.replace(' ', '_')}.txt"
        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        manifest["subjects"].append({"subject": subject, "file": fname, "articles": arts})
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
