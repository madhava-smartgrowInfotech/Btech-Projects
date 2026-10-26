"""DFD level 1 (diagram 04) - kept apart so the layout can be tuned on its own."""

from .dgm_lib import BLUE, GREY, INK, NAVY, PALE_BLUE, PALE_PURPLE, PURPLE, TEAL, W, arrow, box, canvas, ellipse, out, save_min as save, store, txt


def d_dfd1():
    fig, ax = canvas(W, 7.0, 100)          # height 63.6
    pw, ph = 18, 11
    # external entities
    box(ax, 6, 28, 9, 46, "User", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=10.5, bold=True, r=0.6)
    box(ax, 60, 60.2, 40, 5, "Hugging Face model cache (local)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=9, r=0.6)
    box(ax, 92, 46, 14, 8, "OS speech\nengine", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.5, r=0.6, ls="--")
    # processes
    ellipse(ax, 30, 44, pw, ph, "1.0\nValidate\nrequest", fc=PALE_BLUE, ec=BLUE, fs=8.6)
    ellipse(ax, 51, 44, pw, ph, "2.0\nGenerate\nstory text", fc=PALE_BLUE, ec=BLUE, fs=8.6)
    ellipse(ax, 72, 44, pw, ph, "3.0\nSynthesize\nnarration", fc=PALE_BLUE, ec=BLUE, fs=8.6)
    ellipse(ax, 36, 12, 22, 11.5, "4.0\nManage history\nand playback", fc=PALE_BLUE, ec=BLUE, fs=8.6)
    ellipse(ax, 74, 12, 20, 11.5, "5.0\nRun evaluation", fc=PALE_BLUE, ec=BLUE, fs=8.6)
    # data stores
    store(ax, 42, 30, 16, 4.6, "D1  stories", fs=8.6)
    store(ax, 63, 30, 20, 4.6, "D2  audio_outputs", fs=8.6)
    store(ax, 86, 30, 20, 4.6, "D3  data/audio/*.wav", fs=8.6)
    store(ax, 93.5, 11, 11, 8, "D4\nevaluations\n+ files", fs=8.2)
    # user in
    arrow(ax, (10.5, 44), (21, 44), "story idea, language,\nstyle, length, flag", color=NAVY, lo=(2, 5.2), fs=8)
    # P1 -> P2 -> P3
    arrow(ax, (39, 44), (42, 44), color=GREY)
    arrow(ax, (60, 44), (63, 44), color=GREY)
    txt(ax, 40.5, 50.5, "valid\nrequest", 8, GREY)
    txt(ax, 61.5, 50.5, "story text,\nlanguage", 8, GREY)
    # model cache
    arrow(ax, (50, 57.7), (50, 49.6), color=NAVY, lw=1.2)
    txt(ax, 51.5, 54, "LM weights", 8, NAVY, ha="left")
    arrow(ax, (72, 57.7), (72, 49.6), color=NAVY, lw=1.2)
    txt(ax, 73.5, 54, "speech weights", 8, NAVY, ha="left")
    # OS speech engine
    arrow(ax, (80.5, 45), (85, 45.5), color=PURPLE, ls="--", lw=1.2, style="<|-|>")
    txt(ax, 92, 39.6, "text out,\naudio back", 8, PURPLE)
    # writes
    arrow(ax, (47, 38.7), (43.5, 32.4), "title, body,\nword count", color=TEAL, lo=(-9.5, 0.5), fs=8)
    arrow(ax, (68, 38.7), (64, 32.4), "duration, model id,\nsynthesis time, RTF", color=TEAL, lo=(-10, 1.2), fs=8)
    arrow(ax, (78, 38.7), (84, 32.4), "WAV", color=TEAL, lo=(4.5, 0), fs=8)
    # reads for process 4
    arrow(ax, (40, 27.6), (35, 17.8), "", color=TEAL)
    arrow(ax, (58, 27.6), (44.5, 16.5), "", color=TEAL)
    arrow(ax, (88, 27.6), (46, 13.6), "", color=TEAL, lw=1.1)
    txt(ax, 44, 22.6, "story, audio rows,\nWAV to stream", 8, TEAL)
    # user <-> 4.0
    arrow(ax, (10.5, 15), (25.5, 15), "list, open, delete,\nregenerate narration", color=NAVY, lo=(-1, 4.6), fs=8)
    arrow(ax, (25.6, 9.5), (10.5, 9.5), "stories, audio stream", color=TEAL, lo=(-1, -2.6), fs=8)
    # 5.0
    arrow(ax, (10.5, 3.6), (64.5, 8.4), "run request  /  metrics", color=NAVY, lo=(-4, -2.3), fs=8, style="<|-|>")
    arrow(ax, (74.5, 17.7), (74.5, 38.9), color=GREY, ls="--", lw=1.1)
    txt(ax, 76, 21.5, "calls 2.0 and 3.0", 8, GREY, ha="left")
    arrow(ax, (84, 11), (88, 11), color=TEAL)
    save(fig, out("04_dfd_level1.png"))


DRAWERS = {"dfd1": d_dfd1}
