"""DFD level 2 (diagram 05): process 3.0 Synthesize narration expanded into seven sub-processes."""

from .dgm_lib import BLUE, GREY, NAVY, ORANGE, PALE_BLUE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W, arrow, box, canvas, ellipse, out, save_min as save, store, txt


def d_dfd2():
    fig, ax = canvas(W, 6.8, 100)          # height 61.8
    pw, ph = 20, 11.5
    ellipse(ax, 14, 40, pw, ph, "3.1\nChunk text", fc=PALE_BLUE, ec=BLUE, fs=8.8)
    ellipse(ax, 38, 40, pw, ph, "3.2\nLoad MMS\ncheckpoint", fc=PALE_BLUE, ec=BLUE, fs=8.8)
    ellipse(ax, 62, 40, pw, ph, "3.3\nVITS forward\nper chunk", fc=PALE_BLUE, ec=BLUE, fs=8.8)
    ellipse(ax, 86, 40, pw, ph, "3.4\nNormalise\nand join", fc=PALE_BLUE, ec=BLUE, fs=8.8)
    ellipse(ax, 86, 19, pw, ph, "3.5\nSilence\ncheck", fc=PALE_BLUE, ec=BLUE, fs=8.8)
    ellipse(ax, 62, 6.5, pw, ph, "3.6\nOS fallback\nvoice", fc=PALE_PURPLE, ec=PURPLE, fs=8.8)
    ellipse(ax, 38, 19, pw, ph, "3.7\nWrite WAV,\nrecord metrics", fc=PALE_BLUE, ec=BLUE, fs=8.8)
    # sources and stores
    box(ax, 14, 55, 25, 6.4, "from 2.0 Generate story:\nstory text, language", fc=PALE_BLUE, tc="#14213D", ec=BLUE, fs=8.2, r=0.6)
    box(ax, 50, 56, 36, 5.2, "Hugging Face cache: mms-tts-<lang>", fc=PALE_BLUE, tc="#14213D", ec=BLUE, fs=8.4, r=0.6)
    box(ax, 91, 5.5, 15, 7.4, "OS speech\nengine (SAPI)", fc=PALE_PURPLE, tc="#14213D", ec=PURPLE, fs=8.2, r=0.6, ls="--")
    store(ax, 9, 22, 17, 4.8, "D3  WAV files", fs=8.4)
    store(ax, 10, 8, 19, 6.4, "D2  audio_outputs\nrow", fs=8.4)
    # main chain
    arrow(ax, (14, 51.7), (14, 45.8), color=NAVY)
    arrow(ax, (24, 40), (28, 40), color=GREY)
    txt(ax, 26, 46.3, "chunks\n<= 380 chars", 8, GREY)
    arrow(ax, (48, 40), (52, 40), color=GREY)
    txt(ax, 50, 46.3, "tokenizer,\nmodel", 8, GREY)
    arrow(ax, (72, 40), (76, 40), color=GREY)
    txt(ax, 74, 46.3, "waveform\nper chunk", 8, GREY)
    arrow(ax, (38, 53.4), (38, 45.8), color=NAVY)
    txt(ax, 39.5, 50, "weights (first call)", 8, NAVY, ha="left")
    arrow(ax, (86, 34.2), (86, 24.8), color=GREY)
    txt(ax, 84.5, 29.5, "peak 0.9, 0.25 s\npauses, 16 kHz", 8, GREY, ha="right")
    # silence check outcomes
    arrow(ax, (76, 19), (48, 19), color=TEAL)
    txt(ax, 62, 21.8, "audio is not silent", 8, TEAL)
    arrow(ax, (80, 14.2), (68, 9.8), color=ORANGE)
    txt(ax, 69.5, 14.4, "silent, empty or\nprovider error", 8, ORANGE)
    arrow(ax, (54.5, 10.2), (44, 14.2), color=PURPLE)
    txt(ax, 47.5, 7.8, "fallback audio", 8, PURPLE)
    arrow(ax, (42, 34.6), (58.5, 12.2), color=ORANGE, ls="--", lw=1.1)
    txt(ax, 51, 28, "checkpoint missing\nor load error", 8, ORANGE, ha="left")
    arrow(ax, (72, 6.5), (83.5, 6.0), color=PURPLE, ls="--", lw=1.1, style="<|-|>")
    # outputs
    arrow(ax, (28, 19.5), (17.5, 21.5), "", color=TEAL)
    arrow(ax, (30.5, 14.5), (19.5, 9.5), "", color=TEAL)
    txt(ax, 26, 5.8, "path, duration, model id,\nsynthesis time, RTF", 8, TEAL, ha="left")
    save(fig, out("05_dfd_level2.png"))


DRAWERS = {"dfd2": d_dfd2}
