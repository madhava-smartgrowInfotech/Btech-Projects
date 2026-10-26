"""Diagrams 07, 08 and 12: sequence diagram, use-case diagram and model architecture (see make_diagrams.py)."""

from matplotlib.patches import Rectangle

from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W,
                      actor, arrow, box, canvas, ellipse, out, panel, pline, save_min as save, txt)


# ------------------------------------------------------------------------------------------------ 07 sequence
def d_seq():
    fig, ax = canvas(W, 9.6, 100)          # height 87.3
    H_ = 100 * 9.6 / W
    xs = {"B": 8, "R": 25, "D": 42, "G": 59.5, "T": 76, "A": 91}
    heads = {"B": ("Browser\n(React UI)", NAVY), "R": ("API routes\n(FastAPI)", NAVY), "D": ("SQLite\nstoryvox.db", ORANGE),
             "G": ("story_generator", BLUE), "T": ("tts_service", BLUE), "A": ("data/audio\n(WAV files)", ORANGE)}
    top = H_ - 5
    for k, (t, c) in heads.items():
        box(ax, xs[k], top, 14.5 if k != "G" else 16, 6.4, t, fc=c, fs=8.4, bold=True, r=0.8)
        ax.plot([xs[k], xs[k]], [top - 3.2, 1.5], color=GREY, lw=1.0, ls=(0, (4, 3)), zorder=1)

    def msg(y, a, b, text, color=NAVY, dashed=False, dy=1.4):
        arrow(ax, (xs[a] + (0.3 if xs[b] > xs[a] else -0.3), y), (xs[b] - (0.3 if xs[b] > xs[a] else -0.3), y), color=color, lw=1.4, ls="--" if dashed else "-")
        ax.text((xs[a] + xs[b]) / 2, y + dy, text, ha="center", va="bottom", fontsize=8, color=INK, zorder=6, linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.92))

    def note(y, k, text, fc=PALE_ORANGE, ec=ORANGE, w=21):
        box(ax, xs[k], y, w, 4.6, text, fc=fc, tc=INK, ec=ec, fs=8, r=0.6)

    y0, step = top - 7.4, 5.1
    ys = [y0 - i * step for i in range(15)]
    msg(ys[0], "B", "R", "POST /api/stories/generate\n{prompt, language_code, style, length, synthesize}", dy=0.7)
    note(ys[1] + 1.3, "R", "validate: non-empty, <= 2000 chars,\nknown language, style, length", w=26)
    msg(ys[2] + 0.4, "R", "G", "generate_story_text(prompt, language,\nstyle, length)", dy=0.5)
    note(ys[3] + 0.6, "G", "Qwen3-0.6B sampling,\nelse offline composer", w=20)
    msg(ys[4] + 0.4, "G", "R", "title, body, model id, seconds", dashed=True, color=TEAL)
    msg(ys[5], "R", "D", "INSERT stories; commit")
    # optional block
    ax.add_patch(Rectangle((3, ys[11] - 2.3), 94, ys[6] - ys[11] + 4.3, fc="none", ec=PURPLE, lw=1.2, ls="--", zorder=2))
    ax.text(3.8, ys[6] + 2.0, "opt  synthesize = true", ha="left", va="center", fontsize=8, color=PURPLE, fontweight="bold", zorder=6, bbox=dict(fc="white", ec="none", pad=0.5))
    msg(ys[7] - 0.2, "R", "T", "synthesize_story_narration(body, language_code)", dy=0.6)
    note(ys[8] - 0.2, "T", "MMS VITS per chunk,\nelse OS fallback voice", w=22)
    msg(ys[9] - 0.4, "T", "A", "write_wav_mono(*.wav)", dy=0.5)
    msg(ys[10] - 0.4, "T", "R", "path, duration, model id, synthesis time, RTF", dashed=True, color=TEAL)
    msg(ys[11] - 0.4, "R", "D", "INSERT audio_outputs; commit")
    msg(ys[12] - 0.9, "R", "B", "200 StoryResponse (audio URL /api/audio/{id})", dashed=True, color=TEAL)
    msg(ys[13] - 0.6, "B", "R", "GET /api/audio/{id}")
    msg(ys[14] - 1.4, "R", "B", "FileResponse audio/wav (reads the stored WAV path)", dashed=True, color=TEAL)
    save(fig, out("07_sequence_flow.png"))


# ------------------------------------------------------------------------------------------------ 08 use case
def d_usecase():
    fig, ax = canvas(W, 7.4, 100)          # height 67.3
    ax.add_patch(Rectangle((19.5, 0.8), 61, 61.7, fc="#FAFBFD", ec=NAVY, lw=1.5, zorder=1))
    ax.text(50, 60.0, "StoryVox system boundary", ha="center", va="center", fontsize=9.5, color=NAVY, fontweight="bold", zorder=3)
    ys = [52, 42.6, 33.2, 23.8, 14.4, 5.0]
    left = ["Generate story", "Enter story idea", "Choose language,\nstyle and length", "Narrate story\n(auto or on demand)", "Play narration", "Download WAV"]
    right = ["Run evaluation", "View evaluation\nmetrics", "Browse history", "Regenerate\nnarration", "Open a story", "Delete story\nand its audio"]
    EW, EH = 19.5, 6.4
    for y, t in zip(ys, left):
        ellipse(ax, 33, y, EW, EH, t, fc=PALE_BLUE, ec=BLUE, fs=8.2)
    for y, t in zip(ys, right):
        ellipse(ax, 67, y, EW, EH, t, fc=PALE_TEAL, ec=TEAL, fs=8.2)
    # actors and their buses
    actor(ax, 7, 27, "Story creator\nand listener\n(Studio page)")
    actor(ax, 93, 27, "Library and\nevaluation user\n(History and\nEvaluation pages)")
    ax.plot([15, 15], [5.0, 52], color=NAVY, lw=1.3, zorder=2)
    ax.plot([85, 85], [5.0, 52], color=NAVY, lw=1.3, zorder=2)
    ax.plot([9.0, 15], [31.6, 31.6], color=NAVY, lw=1.3, zorder=2)
    ax.plot([85, 91.0], [31.6, 31.6], color=NAVY, lw=1.3, zorder=2)
    for y in ys:
        arrow(ax, (15, y), (23.2, y), color=NAVY, lw=1.1, style="-")
        arrow(ax, (85, y), (76.8, y), color=NAVY, lw=1.1, style="-")
    # include relations
    arrow(ax, (33, 48.8), (33, 45.8), color=GREY, ls="--", lw=1.1)
    ax.text(34.4, 47.3, "<<include>>", fontsize=8, color=GREY, ha="left", va="center", zorder=6, style="italic")
    pline(ax, [(25.9, 50.3), (21.6, 50.3), (21.6, 33.2), (23.3, 33.2)], color=GREY, ls="--", lw=1.1)
    ax.text(21.0, 41.6, "<<include>>", fontsize=8, color=GREY, ha="right", va="center", zorder=6, style="italic", rotation=90)
    # supporting systems between the columns, level with the rows that use them
    box(ax, 50, 52, 9.6, 6.4, "Hugging Face\nmodel cache", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.6, ls="--")
    box(ax, 50, 23.8, 9.6, 6.4, "OS speech\nengine", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.6, ls="--")
    for y in (52, 23.8):
        arrow(ax, (45.2, y), (42.8, y), color=PURPLE, ls="--", lw=1.1)
        arrow(ax, (54.8, y), (57.2, y), color=PURPLE, ls="--", lw=1.1)
    txt(ax, 50, 57.2, "<<uses>>", 8, PURPLE, style="italic")
    txt(ax, 50, 28.9, "<<uses>>", 8, PURPLE, style="italic")
    txt(ax, 50, 65.2, "No translation, rating, voice or speed use case exists in this build", 8.2, GREY, style="italic")
    save(fig, out("08_use_case.png"))


# ------------------------------------------------------------------------------------------------ 12 model architecture
def d_model():
    fig, ax = canvas(W, 7.6, 100)          # height 69.1
    H_ = 100 * 7.6 / W
    rows = [
        ("Story model", "Qwen/Qwen3-0.6B\ndecoder-only LM", NAVY, 58.5,
         ["Prompt text\nidea, language, style,\nlength, 'Title:' rule", "Tokenizer\n(byte-level BPE)\n+ embeddings", "Stack of decoder\nblocks: self-attention\n+ feed-forward",
          "Language-model\nhead: next-token\nprobabilities", "Sampling loop\nT 0.8, top-p 0.9,\n220 / 420 / 700\nnew tokens", "Story text\n'Title:' line + body\n(word count)"]),
        ("Narration model", "facebook/mms-tts-<lang>\nVITS, 16 kHz", TEAL, 42.5,
         ["Text chunk\n<= 380 chars at\nsentence boundary", "Tokenizer\n(per-language\ncharacter vocabulary)", "Text encoder\n(Transformer)", "Stochastic\nduration predictor\n+ alignment",
          "Normalising flow\n(run in reverse)", "HiFi-GAN decoder\n-> mono waveform\n16 kHz"]),
        ("Speech recognition", "openai/whisper-small\nevaluation only", BLUE, 26.5,
         ["Narration WAV\n(read as 16 kHz\nmono)", "Log-Mel\nspectrogram\n(30 s window)", "Transformer\nencoder", "Transformer\ndecoder, language\nand task tokens",
          "Transcript\ntext", "WER and CER\nagainst the story\ntext (jiwer)"]),
        ("Similarity model", "paraphrase-multilingual-\nMiniLM-L12-v2\nevaluation only", PURPLE, 10.5,
         ["Prompt and\nstory text", "Sentence-piece\ntokenizer", "12-layer Transformer\nencoder (MiniLM)", "Mean pooling +\nL2 normalise",
          "Cosine\nsimilarity", "Topic score\n(TF-IDF proxy if\nmodel unavailable)"]),
    ]
    for label, sub, col, y, blocks in rows:
        panel(ax, 0.8, y - 7.6, 98.4, 15.2, "", fc=LIGHT)
        box(ax, 9.2, y, 16, 12.6, f"{label}"+chr(10)+chr(10)+f"{sub}", fc=col, fs=8, bold=False, r=0.9)
        for i, t in enumerate(blocks):
            x = 24.4 + i * 13.6
            box(ax, x, y, 12, 11.6, t, fc="#FFFFFF", tc=INK, ec=col, fs=8, r=0.8, lw=1.5)
            if i:
                arrow(ax, (x - 7.5, y), (x - 6.0, y), color=col, lw=1.4)
    save(fig, out("12_model_architecture.png"))


DRAWERS = {"seq": d_seq, "usecase": d_usecase, "model": d_model}
