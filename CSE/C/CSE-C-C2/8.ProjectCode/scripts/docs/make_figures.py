"""Result figures for the StoryVox documents (matplotlib, 150 dpi) -> docs/figures/.

    python -m scripts.docs.make_figures            # all
    python -m scripts.docs.make_figures f01 f05    # selected

Reads only experiments/**/metrics.json (written by scripts/run_experiments.py, measure_api.py and run_tests.py).
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import facts as F
from .dgm_lib import BLUE, GREY, INK, NAVY, ORANGE, PURPLE, TEAL

RED = "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelsize": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8895A7", "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.grid": True, "grid.color": "#E3E8EF", "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "legend.frameon": False, "legend.fontsize": 8.5})

LANG_NAMES = {"en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
              "ar": "Arabic", "tr": "Turkish", "nl": "Dutch", "pl": "Polish", "zh": "Chinese", "ja": "Japanese", "ko": "Korean"}
COND_LABEL = {"A_app_raw_prompt": "A: shipped (raw prompt)", "B_chat_template": "B: chat template", "C_local_composer": "C: offline composer"}
COND_COLOR = {"A_app_raw_prompt": ORANGE, "B_chat_template": BLUE, "C_local_composer": GREY}


def out(name):
    os.makedirs(F.FIGS, exist_ok=True)
    return os.path.join(F.FIGS, name)


def finish(fig, name):
    fig.tight_layout()
    fig.savefig(out(name), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", name)


def label_bars(ax, bars, fmt="{:.2f}", pad=0.01, horizontal=False, fs=8):
    for b in bars:
        if horizontal:
            w = b.get_width()
            ax.text(w + pad, b.get_y() + b.get_height() / 2, fmt.format(w), va="center", ha="left", fontsize=fs, color=INK)
        else:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + pad, fmt.format(h), ha="center", va="bottom", fontsize=fs, color=INK)


def _langs():
    return F.TTS["languages"]


def _is_fallback(entry):
    return "facebook/mms" not in " ".join(entry.get("models_used", [])) and bool(entry.get("models_used"))


# ------------------------------------------------------------------------------------------------ f01 RTF
def f01():
    langs = [c for c, e in _langs().items() if e.get("mean_rtf") is not None]
    cap = 1.3
    vals = [_langs()[c]["mean_rtf"] for c in langs]
    cols = [ORANGE if _is_fallback(_langs()[c]) else BLUE for c in langs]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bars = ax.bar([LANG_NAMES[c] for c in langs], [min(v, cap) for v in vals], color=cols)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, min(v, cap) + 0.02, f"{v:.2f}" + (" ▲" if v > cap else ""), ha="center", va="bottom", fontsize=7.5)
    ax.axhline(1.0, color=RED, lw=1, ls="--")
    ax.text(-0.45, 1.03, "real time (RTF = 1)", color=RED, ha="left", va="bottom", fontsize=8)
    ax.set_ylim(0, cap + 0.25)
    ax.set_ylabel("Real-time factor (synthesis time / audio duration)")
    ax.set_title("Narration speed per language on CPU (lower is faster; bars above 1.3 are cut)")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="MMS-TTS (VITS)"), Patch(color=ORANGE, label="OS fallback voice")], loc="upper center", ncol=2)
    finish(fig, "f01_rtf_by_language.png")


# ------------------------------------------------------------------------------------------------ f02 WER / CER
def f02():
    langs = [c for c, e in _langs().items() if e.get("cer_norm_corpus") is not None]
    x = np.arange(len(langs))
    w = 0.38
    wer = [_langs()[c].get("wer_norm_corpus") for c in langs]
    cer = [_langs()[c]["cer_norm_corpus"] for c in langs]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    b1 = ax.bar(x - w / 2, [v if v is not None else 0 for v in wer], w, color=NAVY, label="WER (normalised)")
    b2 = ax.bar(x + w / 2, cer, w, color=TEAL, label="CER (normalised)")
    for bars in (b1, b2):
        for b, c in zip(bars, langs):
            if _is_fallback(_langs()[c]):
                b.set_hatch("///")
                b.set_edgecolor("white")
    for xi, v in zip(x, wer):
        if v is None:
            ax.text(xi - w / 2, 0.005, "n/a", ha="center", va="bottom", fontsize=7, color=GREY)
    label_bars(ax, [b for b, v in zip(b1, wer) if v is not None], "{:.2f}", 0.006, fs=6.5)
    label_bars(ax, b2, "{:.2f}", 0.006, fs=6.5)
    def tick(c):
        e = _langs()[c]
        return LANG_NAMES[c] + (f" ({e['narrated']}/{e['n']} spoken)" if e.get("narrated") is not None and e["narrated"] < e["n"] else "")

    ax.set_xticks(x)
    ax.set_xticklabels([tick(c) for c in langs], rotation=35, ha="right")
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Error rate (Whisper-small vs. source text)")
    ax.set_title("Round-trip intelligibility (hatched = OS fallback voice, not MMS)")
    ax.legend(loc="upper left")
    finish(fig, "f02_wer_cer_by_language.png")


# ------------------------------------------------------------------------------------------------ f03 story conditions
def f03():
    summ = F.STORY["summary"]
    keys = list(summ)
    panels = [("mean_latency_s", "Mean latency (s)", "{:.1f}"), ("mean_words", "Mean words", "{:.0f}"),
              ("language_match_rate", "Target-language match rate", "{:.2f}"), ("mean_distinct_2", "Distinct-2 (variety)", "{:.2f}")]
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 3.0))
    for ax, (k, title, fmt) in zip(axes, panels):
        vals = [summ[c][k] or 0 for c in keys]
        bars = ax.bar(range(len(keys)), vals, color=[COND_COLOR[c] for c in keys])
        label_bars(ax, bars, fmt, max(vals) * 0.02, fs=7.5)
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(["A", "B", "C"])
        ax.set_title(title, fontsize=8.5)
        ax.set_ylim(0, max(vals) * 1.18 if max(vals) else 1)
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COND_COLOR[c]) for c in keys], labels=[COND_LABEL[c] for c in keys], loc="lower center", ncol=3, fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out("f03_story_conditions.png"), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved f03_story_conditions.png")


# ------------------------------------------------------------------------------------------------ f04 length scaling
def f04():
    rows = F.STORY["length_scaling"]
    x = np.arange(len(rows))
    gen = [r["gen_s"] for r in rows]
    tts = [r["tts_s"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    b1 = ax.bar(x, gen, 0.5, color=BLUE, label="Story generation (Qwen3-0.6B)")
    b2 = ax.bar(x, tts, 0.5, bottom=gen, color=ORANGE, label="Narration (MMS English)")
    for i, r in enumerate(rows):
        ax.text(i, gen[i] + tts[i] + 2, f"{r['total_s']:.0f} s\n{r['words']} words, {r['audio_s']:.0f} s audio", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['length']}\n({r['max_new_tokens']} tokens)" for r in rows])
    ax.set_ylabel("Seconds (CPU)")
    ax.set_ylim(0, (max(g + t for g, t in zip(gen, tts))) * 1.3)
    ax.set_title("End-to-end time by story length")
    ax.legend(loc="upper left")
    finish(fig, "f04_length_scaling.png")


# ------------------------------------------------------------------------------------------------ f05 API latency
def f05():
    ep = F.API["endpoints"]
    names = [n for n in ep if "median_ms" in ep[n]]
    med = [ep[n]["median_ms"] for n in names]
    p95 = [ep[n]["p95_ms"] for n in names]
    y = np.arange(len(names))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.barh(y + 0.2, med, 0.38, color=BLUE, label="median")
    ax.barh(y - 0.2, p95, 0.38, color=ORANGE, label="95th percentile")
    for yi, m, p in zip(y, med, p95):
        ax.text(m + 0.4, yi + 0.2, f"{m:.1f}", va="center", fontsize=7)
        ax.text(p + 0.4, yi - 0.2, f"{p:.1f}", va="center", fontsize=7)
    ax.set_yticks(y)
    ax.set_yticklabels([n.replace(" (empty prompt, 422)", " (422)") for n in names], fontsize=7.5)
    ax.set_xlim(0, max(p95) * 1.15)
    ax.set_xlabel("Latency in ms")
    ax.set_title("API latency of the non-model endpoints (ms)")
    ax.legend(loc="center right")
    finish(fig, "f05_api_latency.png")


# ------------------------------------------------------------------------------------------------ f06 prompt-story similarity
def f06():
    conds = F.STORY["conditions"]
    n = len(conds["A_app_raw_prompt"])
    x = np.arange(n)
    w = 0.27
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    for i, (c, rows) in enumerate(conds.items()):
        ax.bar(x + (i - 1) * w, [r["prompt_story_similarity"] for r in rows], w, color=COND_COLOR[c], label=COND_LABEL[c])
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['language']}\n{r['style'][:4]}" if r["language"] == "en" else r["language"] for r in conds["A_app_raw_prompt"]], fontsize=7)
    ax.set_ylabel("MiniLM cosine: idea vs. story")
    ax.set_title("Prompt-story similarity rewards quoting the idea (offline composer is usually highest)")
    ax.legend(loc="upper right", ncol=3)
    ax.set_ylim(0, 1.0)
    finish(fig, "f06_prompt_similarity.png")


# ------------------------------------------------------------------------------------------------ f07 language match
def f07():
    conds = F.STORY["conditions"]
    keys = list(conds)
    langs = [r["language"] + (":" + r["style"][:3] if r["language"] == "en" else "") for r in conds[keys[0]]]
    mat = np.array([[1.0 if r["language_match"] else (0.0 if r["language_match"] is not None else 0.5) for r in conds[c]] for c in keys])
    fig, ax = plt.subplots(figsize=(7.4, 2.4))
    ax.imshow(mat, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(langs)))
    ax.set_xticklabels(langs, fontsize=7, rotation=45, ha="right")
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([COND_LABEL[c] for c in keys], fontsize=8)
    ax.grid(False)
    ax.set_title("Did the story come out in the requested language? (green = yes, red = no)")
    finish(fig, "f07_language_match.png")


def f08():
    """Where the end-to-end time goes for the 7 measured API generate calls."""
    rows = [r for r in F.API["generate"] if r.get("story_gen_s") is not None]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.bar(x, [r["story_gen_s"] for r in rows], 0.55, color=BLUE, label="story generation")
    ax.bar(x, [r["tts_s"] for r in rows], 0.55, bottom=[r["story_gen_s"] for r in rows], color=ORANGE, label="narration")
    ax.set_xticks(x)
    ax.set_xticklabels([f"#{r['order']} {r['language']}\n{r['style'][:5]}\n{r['length'][:3]}" + ("\ncold" if r.get("cold") else "") for r in rows], fontsize=7)
    ax.set_ylabel("Seconds")
    ax.set_title("Measured POST /api/stories/generate calls (with narration)")
    ax.legend(loc="upper left")
    finish(fig, "f08_generate_calls.png")


def main():
    wanted = set(a.lower() for a in sys.argv[1:])
    for name, fn in [("f01", f01), ("f02", f02), ("f03", f03), ("f04", f04), ("f05", f05), ("f06", f06), ("f07", f07), ("f08", f08)]:
        if wanted and name not in wanted:
            continue
        try:
            fn()
        except Exception as exc:  # report and continue so one missing metric file does not hide the others
            print("FAILED", name, type(exc).__name__, exc)


if __name__ == "__main__":
    main()
