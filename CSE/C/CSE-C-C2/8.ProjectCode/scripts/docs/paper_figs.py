"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible).

Architecture and flow are drawn from the real code path (app/services/*); the results chart reads experiments/tts_asr/metrics.json;
the two output screens are crops of the real 1440x900 captures in docs/screenshots/.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, GREEN, RED, GREY = "#1B2A41", "#2F6DB5", "#1E9E8F", "#E08A1E", "#3C9D5D", "#C0392B", "#8A94A6"
PALE = {"blue": "#E4EEF9", "teal": "#DFF3EF", "orange": "#FCEBD3", "green": "#E3F3E8", "grey": "#EEF0F4", "red": "#F9E0DC"}


def _save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def _canvas(w, h, xmax, ymax):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 2.9, 100, 83)
    _box(ax, 1, 70, 98, 12, "Web app - React 19 + Vite (port 5402)\nLanding · Studio · History · Story detail · Evaluation", "blue", fs=5.2, bold=True)
    _box(ax, 1, 51, 98, 15, "FastAPI service (port 8402) - 11 routes + SPA fallback\nvalidation (422) · 404 for unknown ids · audio served as audio/wav", "grey", fs=5.0)
    _arrow(ax, 50, 70, 50, 66.6, style="<|-|>")
    _box(ax, 1, 20, 31, 26, "Story service\nQwen3-0.6B pipeline\n(220 / 420 / 700 tokens,\nT 0.8, top-p 0.9)\n-> offline composer\nif < 20 words", "orange", fs=4.6)
    _box(ax, 34.5, 20, 31, 26, "Speech service\nchunk text (380 chars)\nMMS-TTS VITS, 16 kHz\n-> OS voice\nif no checkpoint\npeak-norm, 0.25 s gaps", "green", fs=4.6)
    _box(ax, 68, 20, 31, 26, "Evaluation service\nWhisper-small ASR\njiwer WER / CER\nMiniLM similarity\nROUGE-L, RTF", "blue", fs=4.6)
    for x in (16.5, 50, 83.5):
        _arrow(ax, x, 52, x, 46.5)
    _box(ax, 1, 2, 62, 12, "SQLite: stories, audio_outputs, evaluations\nWAV files on disk (data/audio)", "grey", fs=4.8)
    _box(ax, 66, 2, 33, 12, "Hugging Face Hub\n(one-time model download)", "orange", fs=4.6)
    _arrow(ax, 25, 20, 25, 14.5, style="-")
    _arrow(ax, 50, 20, 50, 14.5, style="-")
    _arrow(ax, 82, 20, 82, 14.5, style="<|-", color=ORANGE, ls="--")
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 3.1, 100, 88)
    NL = chr(10)
    steps = [("Story idea + language, style, length" + NL + "(idea up to 2000 characters)", "grey"),
             ("Build prompt -> Qwen3-0.6B" + NL + "text-generation pipeline", "orange"),
             ("Parse title and body; under 20 words" + NL + "or pipeline error -> offline composer", "orange"),
             ("Split into chunks of at most 380" + NL + "characters at sentence ends", "green"),
             ("MMS-TTS (VITS) per chunk, peak-normalise 0.9," + NL + "0.25 s pauses; no checkpoint -> OS voice;" + NL + "silent result rejected", "green"),
             ("Save WAV + SQLite rows;" + NL + "browser plays /api/audio/{id}", "teal")]
    y = 79
    for t, c in steps:
        _box(ax, 2, y, 58, 8.4, t, c, fs=4.3)
        y -= 12.4
    for i in range(5):
        _arrow(ax, 31, 79 - i * 12.4, 31, 79 - i * 12.4 - 4.8)
    ax.add_patch(FancyBboxPatch((64, 6), 35, 82, boxstyle="round,pad=0.25,rounding_size=1.2", fc="white", ec=TEAL, lw=0.9, ls="--"))
    ax.text(81.5, 84, "Evaluation", ha="center", fontsize=5.2, fontweight="bold", color=NAVY)
    d = [("Narration WAV\n(>30 s -> chunked)", "grey"), ("Whisper-small\ntranscript", "blue"), ("WER, CER\nvs. story text", "orange"),
         ("MiniLM cosine,\nROUGE-L vs. idea", "orange"), ("RTF = t_synth /\nt_audio; latency", "green")]
    y = 72
    for t, c in d:
        _box(ax, 67, y, 29, 9.6, t, c, fs=4.3)
        y -= 14
    for i in range(4):
        _arrow(ax, 81.5, 72 - i * 14, 81.5, 72 - i * 14 - 4.4)
    _arrow(ax, 60, 22, 64, 22, color=TEAL)
    return _save(fig, "paper_flow.png")


def results():
    L = F.LANGS
    codes = [c for c in L if L[c].get("cer_norm_corpus") is not None and c not in ("zh", "ja")]
    codes.sort(key=lambda c: L[c]["cer_norm_corpus"])
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    y = np.arange(len(codes))
    h = 0.38
    wer = [L[c]["wer_norm_corpus"] for c in codes]
    cer = [L[c]["cer_norm_corpus"] for c in codes]
    bw = ax.barh(y - h / 2, wer, h, color=NAVY, label="WER")
    bc = ax.barh(y + h / 2, cer, h, color=TEAL, label="CER")
    for i, c in enumerate(codes):
        if c in F.FALLBACK_LANGS:
            bw[i].set_hatch("////"); bc[i].set_hatch("////")
            bw[i].set_edgecolor("white"); bc[i].set_edgecolor("white")
    ax.set_yticks(y)
    ax.set_yticklabels([F.LANG_NAMES[c] + ("*" if c in F.FALLBACK_LANGS else "") for c in codes], fontsize=5.6)
    ax.invert_yaxis()
    ax.tick_params(axis="x", labelsize=5.6)
    ax.set_xlabel("Normalised error rate, MMS speech -> Whisper-small (10 FLEURS sentences)", fontsize=5.4)
    for yy, v in zip(y + h / 2, cer):
        ax.text(v + 0.006, yy, f"{v:.2f}", va="center", fontsize=4.6)
    for yy, v in zip(y - h / 2, wer):
        ax.text(v + 0.006, yy, f"{v:.2f}", va="center", fontsize=4.6)
    ax.legend(fontsize=5.5, loc="upper right", frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, 0.56)
    fig.tight_layout(pad=0.3)
    return _save(fig, "paper_errors.png")


def langmatch():
    conds = F.STORY["conditions"]
    keys = ["A_app_raw_prompt", "B_chat_template", "C_local_composer"]
    names = {"A_app_raw_prompt": "A shipped", "B_chat_template": "B chat template", "C_local_composer": "C composer"}
    cols = [r["language"] + ("-" + r["style"][:2] if r["language"] == "en" else "") for r in conds[keys[0]]]
    mat = np.array([[1.0 if r["language_match"] else 0.0 for r in conds[k]] for k in keys])
    fig, ax = plt.subplots(figsize=(3.5, 1.35))
    ax.imshow(mat, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, fontsize=4.6, rotation=90)
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([names[k] for k in keys], fontsize=5.2)
    ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(keys), 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.8)
    ax.tick_params(which="both", length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.tight_layout(pad=0.3)
    return _save(fig, "paper_langmatch.png")


def scaling():
    rows = F.LENGTH_SCALING
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    gen = [r["gen_s"] for r in rows]
    tts = [r["tts_s"] for r in rows]
    ax.bar(x, gen, 0.5, color=BLUE, label="story generation")
    ax.bar(x, tts, 0.5, bottom=gen, color=ORANGE, label="narration (MMS, English)")
    for i, r in enumerate(rows):
        ax.text(i, gen[i] + tts[i] + 1.5, f"{r['total_s']:.0f} s total" + chr(10) + f"{r['words']} words, {r['audio_s']:.0f} s audio", ha="center", fontsize=4.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['length']} ({r['max_new_tokens']} tokens)" for r in rows], fontsize=5.5)
    ax.tick_params(axis="y", labelsize=5.5)
    ax.set_ylabel("Seconds on the CPU", fontsize=5.8)
    ax.set_ylim(0, max(g + t for g, t in zip(gen, tts)) * 1.3)
    ax.legend(fontsize=5.3, loc="upper left", frameon=False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.3)
    return _save(fig, "paper_scaling.png")


def _crop(src, box, out):
    im = Image.open(os.path.join(F.SHOTS, src)).convert("RGB").crop(box)
    p = os.path.join(F.FIGS, out)
    os.makedirs(F.FIGS, exist_ok=True)
    im.save(p, optimize=True)
    return p


def screens():
    # right-hand result panel of the Studio (story text + narration player) and, stitched, the metric cards and the Samples table of the Evaluation page
    studio = _crop("03_studio_result.png", (730, 290, 1410, 720), "paper_shot_studio.png")
    src = Image.open(os.path.join(F.SHOTS, "08_evaluation_samples.png")).convert("RGB")
    top, table = src.crop((270, 70, 1420, 260)), src.crop((270, 455, 1420, 830))
    im = Image.new("RGB", (1150, top.height + table.height + 14), "white")
    im.paste(top, (0, 0))
    im.paste(table, (0, top.height + 14))
    p = os.path.join(F.FIGS, "paper_shot_eval.png")
    im.save(p, optimize=True)
    return {"studio": studio, "eval": p}


def make():
    s = screens()
    return {"arch": arch(), "flow": flow(), "results": results(), "lang": langmatch(), "scale": scaling(), "studio": s["studio"], "eval": s["eval"]}
