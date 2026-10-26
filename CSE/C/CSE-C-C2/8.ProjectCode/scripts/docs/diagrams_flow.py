"""Flowcharts 10 and 11: story generation algorithm; narration provider chain and evaluation loop."""

from .dgm_lib import (BLUE, GREY, INK, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W,
                      arrow, box, canvas, diamond, out, panel, pline, save_min as save, txt)


def _yes(ax, x, y, t="yes", c=TEAL):
    txt(ax, x, y, t, 8.2, c, bold=True)


def _no(ax, x, y, t="no", c=ORANGE):
    txt(ax, x, y, t, 8.2, c, bold=True)


# ------------------------------------------------------------------------------------------------ 10 algorithm
def d_algo():
    fig, ax = canvas(W, 8.6, 100)          # height 78.2
    x = 27
    ys = [74.2, 65.4, 56.6, 47.8, 39.0, 30.2, 21.4, 12.6, 3.8]
    box(ax, x, ys[0], 40, 5.4, "generate_story_text(prompt, language_code, style, length)", fc=NAVY, fs=8.2, bold=True, r=2.5)
    diamond(ax, x, ys[1], 34, 7.4, "inputs valid?", fs=8.6)
    box(ax, x, ys[2], 44, 5.6, "build_prompt(): style guidance, paragraph target,\n'Title:' first-line rule, story idea", fc=BLUE, fs=8)
    box(ax, x, ys[3], 44, 5.6, "_try_load_pipeline(Qwen3-0.6B): lock + cache,\nCUDA fp16 if present, else CPU fp32", fc=BLUE, fs=8)
    diamond(ax, x, ys[4], 34, 7.4, "pipeline loaded?", fs=8.6)
    box(ax, x, ys[5], 44, 5.6, "generator(prompt): max_new_tokens 220/420/700,\ntemperature 0.8, top_p 0.9, sampling on", fc=BLUE, fs=8)
    box(ax, x, ys[6], 44, 5.6, "_parse_model_output(): 'Title:' line (or short\nfirst line) = title; rest = body", fc=BLUE, fs=8)
    diamond(ax, x, ys[7], 38, 7.4, "body >= 20 words,\nno exception?", fs=8.2)
    box(ax, x, ys[8], 44, 5.0, "return title, body, model id, seconds", fc=TEAL, fs=8.2, bold=True, r=2.5)
    # main arrows
    for a, b, ha, hb in [(0, 1, 2.7, 3.7), (1, 2, 3.7, 2.8), (2, 3, 2.8, 2.8), (3, 4, 2.8, 3.7), (4, 5, 3.7, 2.8), (5, 6, 2.8, 2.8), (6, 7, 2.8, 3.7), (7, 8, 3.7, 2.5)]:
        arrow(ax, (x, ys[a] - ha), (x, ys[b] + hb), color=GREY)
    _yes(ax, x + 3, ys[1] - 5.0)
    _yes(ax, x + 3, ys[4] - 5.0)
    _yes(ax, x + 3, ys[7] - 5.0)
    # right column
    box(ax, 77, ys[1], 38, 7.8, "ValueError -> HTTP 422:\nunknown language, style or length,\nempty or over-long prompt", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.7)
    arrow(ax, (x + 17, ys[1]), (58, ys[1]), color=ORANGE)
    _no(ax, x + 20.5, ys[1] + 1.8)
    box(ax, 77, 23, 38, 11, "local_fallback_story(): prompt-conditioned offline\ncomposer - language opening, the idea quoted,\n3 / 5 / 8 paragraphs by length (always works)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.7)
    pline(ax, [(x + 17, ys[4]), (77, ys[4]), (77, 28.7)], color=ORANGE)
    _no(ax, x + 20.5, ys[4] + 1.8)
    pline(ax, [(x + 19, ys[7]), (56, ys[7]), (56, 23), (58, 23)], color=ORANGE)
    _no(ax, x + 22.5, ys[7] + 1.8)
    box(ax, 77, 3.8, 38, 5.0, "return title, body,\n'storyvox-local-fallback-v1', seconds", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=2.5)
    arrow(ax, (77, 17.5), (77, 6.4), color=PURPLE)
    txt(ax, 77, 9.6, "model id records the fallback", 8, PURPLE, style="italic")
    save(fig, out("10_flowchart_algorithm.png"))


# ------------------------------------------------------------------------------------------------ 11 narration + evaluation
def d_tts_eval():
    fig, ax = canvas(W, 8.4, 100)          # height 76.4
    panel(ax, 0.8, 1, 47.4, 74.4, "Narration: tts_service.synthesize_story_narration", fc="#F7F9FC", fs=8.8)
    panel(ax, 51.6, 1, 47.6, 74.4, "Evaluation: evaluation_service.run_evaluation", fc="#F7F9FC", fs=8.8)
    mx, sx, mw = 14.5, 40.2, 25.0
    box(ax, mx, 67.3, mw, 5.2, "text, language_code", fc=NAVY, fs=8.2, bold=True, r=2.5)
    diamond(ax, mx, 58.8, mw, 7.6, "text and language\nvalid?", fs=8.2)
    box(ax, sx, 58.8, 14.6, 6.2, "ValueError\n-> HTTP 422", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.7)
    box(ax, mx, 49.2, mw, 6.2, "MMSTTSProvider: chunk_text\n<= 380 chars, VITS per chunk", fc=BLUE, fs=8)
    box(ax, mx, 40.6, mw, 6.2, "peak-normalise to 0.9, join\nchunks with 0.25 s pauses", fc=BLUE, fs=8)
    diamond(ax, mx, 31.2, mw, 7.6, "non-empty and\nnot silent?", fs=8.2)
    box(ax, sx, 31.2, 14.6, 6.2, "SystemTTS-\nProvider\n(pyttsx3)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.7)
    box(ax, mx, 19.5, mw, 6.2, "duration = samples / rate\nRTF = synthesis time / duration", fc=BLUE, fs=8)
    box(ax, mx, 9.0, mw, 7.0, "write_wav_mono -> data/audio\nreturn path, duration, model id,\nsynthesis time, RTF", fc=TEAL, fs=8, r=1.0)
    for a, b in [(64.7, 62.6), (55.0, 52.3), (46.1, 43.7), (37.5, 35.0), (27.4, 22.6), (16.4, 12.5)]:
        arrow(ax, (mx, a), (mx, b), color=GREY)
    arrow(ax, (mx + mw / 2, 58.8), (sx - 7.3, 58.8), color=ORANGE)
    _no(ax, mx + mw / 2 + 1.9, 60.5)
    _yes(ax, mx + 2.5, 54.0)
    _yes(ax, mx + 2.5, 25.6)
    arrow(ax, (mx + mw / 2, 31.2), (sx - 7.3, 31.2), color=ORANGE)
    _no(ax, mx + mw / 2 + 1.9, 32.9)
    pline(ax, [(mx + mw / 2, 49.2), (sx, 49.2), (sx, 34.4)], color=ORANGE, ls="--", lw=1.1)
    txt(ax, sx + 0.2, 44.4, "load or\ninference\nerror", 8, ORANGE)
    pline(ax, [(sx, 28.1), (sx, 19.5), (mx + mw / 2, 19.5)], color=PURPLE)
    txt(ax, sx, 23.9, "voice audio,\n16 kHz", 8, PURPLE)
    txt(ax, sx - 1.5, 13.6, "provider also silent:\nRuntimeError -> HTTP 500", 8, ORANGE)
    # evaluation panel
    ex, ew = 68.5, 26.5
    sbx = 91.8
    box(ax, ex, 67.3, ew, 5.2, "run_evaluation(samples, ...)", fc=NAVY, fs=8, bold=True, r=2.5)
    box(ax, ex, 59.3, ew, 6.2, "5 built-in prompts (en x2,\nfr, de, es); filter, first n", fc=BLUE, fs=8)
    box(ax, ex, 50.7, ew, 6.2, "generate_story_text() ->\nstory, latency (unless skipped)", fc=BLUE, fs=8)
    box(ax, ex, 42.1, ew, 6.2, "similarity (MiniLM cosine,\nelse TF-IDF) and ROUGE-L F1", fc=BLUE, fs=8)
    box(ax, ex, 33.5, ew, 6.2, "synthesize_story_narration()\n-> TTS time, duration, RTF", fc=BLUE, fs=8)
    diamond(ax, ex, 24.0, ew, 7.8, "Whisper loaded?", fs=8.2)
    box(ax, sbx, 24.0, 13.6, 7.0, "asr_error kept;\nWER, CER null", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.7)
    box(ax, ex, 14.3, ew, 6.2, "transcribe_wav() -> WER,\nCER (jiwer) vs story text", fc=BLUE, fs=8)
    box(ax, ex, 5.4, ew, 6.2, "means -> averages; JSON + CSV;\nroute INSERTs evaluations row", fc=TEAL, fs=8, r=1.0)
    for a, b in [(64.7, 62.4), (56.2, 53.8), (47.6, 45.2), (39.0, 36.6), (30.4, 27.9), (20.1, 17.4), (11.2, 8.5)]:
        arrow(ax, (ex, a), (ex, b), color=GREY)
    arrow(ax, (ex + ew / 2, 24.0), (sbx - 6.8, 24.0), color=ORANGE)
    _no(ax, ex + ew / 2 + 1.8, 25.7)
    _yes(ax, ex + 2.5, 19.2)
    pline(ax, [(sbx, 20.5), (sbx, 5.4), (ex + ew / 2, 5.4)], color=ORANGE, ls="--", lw=1.1)
    pline(ax, [(ex - ew / 2, 14.3), (54.4, 14.3), (54.4, 50.7), (ex - ew / 2, 50.7)], color=PURPLE, lw=1.2)
    ax.text(53.0, 32.5, "next prompt", rotation=90, ha="center", va="center", fontsize=8, color=PURPLE, zorder=5)
    save(fig, out("11_flowchart_tts_evaluation.png"))


DRAWERS = {"algo": d_algo, "tts_eval": d_tts_eval}
