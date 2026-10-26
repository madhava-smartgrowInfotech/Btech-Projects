"""Draws the StoryVox design diagrams (matplotlib, 150 dpi) into docs/diagrams/.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; all twelve
    python -m scripts.docs.make_diagrams arch dfd1  # selected keys

01-03 are here; 04 in diagrams_dfd.py, 05 in diagrams_dfd2.py, 06 in diagrams_uml.py, 07/08/12 in diagrams_more.py,
09 in diagrams_er.py, 10/11 in diagrams_flow.py. Every box mirrors a real module, route or file of the product
(app/main.py, app/api/routes.py, app/services/*.py, app/models/__init__.py, data/).
"""

import sys

from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W,
                      arrow, box, canvas, circle, out, panel, save_min as save, txt)


# ------------------------------------------------------------------------------------------------ 01 architecture
def d_arch():
    fig, ax = canvas(W, 7.6, 100)          # height = 69.1
    H_ = 100 * 7.6 / W
    # presentation tier
    panel(ax, 1, 54.5, 98, 13.5, "Presentation tier: browser, Vite dev server on port 5402")
    box(ax, 14, 58.3, 24, 7.2, "React 19 single-page app\n5 pages: Home, Studio,\nHistory, Story, Evaluation", fc=NAVY, fs=8, bold=True)
    box(ax, 63, 58.3, 22, 7.2, "HTML5 audio player\nWAV download link", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.5)
    box(ax, 39, 58.3, 22, 7.2, "Vite proxy\n/api -> 127.0.0.1:8402", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8.5)
    arrow(ax, (26.2, 58.3), (27.9, 58.3), color=NAVY)
    box(ax, 86.5, 58.3, 21, 7.2, "frontend/dist\n(npm run build, served\nby FastAPI on 8402)", fc=LIGHT, tc=INK, ec=GREY, fs=8)
    # application tier
    panel(ax, 1, 38.5, 98, 13.5, "Application tier: FastAPI + Uvicorn, 127.0.0.1:8402")
    box(ax, 39, 42.4, 24, 7.2, "APIRouter  /api\n11 routes (REST, JSON,\nFileResponse for WAV)", fc=NAVY, fs=8, bold=True)
    box(ax, 14, 42.4, 22, 7.2, "Pydantic schemas\nrequest / response\nvalidation", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.5)
    box(ax, 63, 42.4, 22, 7.2, "Settings (config.py)\n15 languages, 8 styles,\n3 lengths, env values", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8.2)
    box(ax, 86.5, 42.4, 21, 7.2, "SPA fallback route\nindex.html for any\nnon-API path", fc=LIGHT, tc=INK, ec=GREY, fs=8.2)
    arrow(ax, (46, 54.6), (46, 46.1), color=TEAL)
    txt(ax, 47.6, 48.4, "JSON over HTTP", 8, TEAL, ha="left")
    # services tier
    panel(ax, 1, 22.5, 98, 13.5, "Service tier: app/services and app/utils (plain Python, lazy model loading)")
    sv = ["story_generator\nprompt -> title + body", "tts_service\nTTSProvider chain", "asr_service\nWhisper transcribe", "evaluation_service\nWER CER sim RTF", "utils: metrics,\naudio, chunk_text"]
    for i, m in enumerate(sv):
        box(ax, 11.5 + i * 19.2, 26.4, 17.2, 7.2, m, fc=BLUE if i < 4 else GREY, fs=8)
    arrow(ax, (36, 38.8), (36, 36.4), color=NAVY)
    # models + storage
    panel(ax, 1, 1, 56, 19, "Pretrained models (Hugging Face, local cache)", fc=LIGHT)
    box(ax, 11, 11, 17, 8.4, "Qwen/Qwen3-\n0.6B\nstory text", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    box(ax, 29.5, 11, 17.5, 8.4, "facebook/\nmms-tts-*\nspeech (VITS)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    box(ax, 48, 11, 17, 8.4, "whisper-small\nand MiniLM\n(evaluation)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    panel(ax, 59, 1, 40, 19, "Local storage (never uploaded)", fc=LIGHT)
    box(ax, 70, 11, 16, 8.4, "SQLite\ndata/storyvox.db\n3 tables", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 88, 11, 17, 8.4, "data/audio/*.wav\ndata/evaluations/\n*.json  *.csv", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    arrow(ax, (11.5, 22.8), (11, 15.4), color=TEAL)
    arrow(ax, (30.7, 22.8), (29.5, 15.4), color=TEAL)
    arrow(ax, (49.9, 22.8), (48, 15.4), color=TEAL)
    arrow(ax, (68.3, 22.8), (70, 15.4), color=ORANGE)
    arrow(ax, (87.5, 22.8), (88, 15.4), color=ORANGE)
    txt(ax, 79, 36.6, "", 8)
    ax.set_ylim(0, H_)
    save(fig, out("01_system_architecture.png"))


# ------------------------------------------------------------------------------------------------ 02 workflow
def d_flow():
    fig, ax = canvas(W, 6.2, 100)          # height 56.4
    top = ["1  Enter story idea\nlanguage, style, length,\nauto-narrate flag", "2  Validate request\nnon-empty, <= 2000\nchars, known options",
           "3  Build prompt\nstyle guidance, paragraph\ntarget, 'Title:' rule", "4  Generate story\nQwen3-0.6B (sampling),\nelse offline composer",
           "5  Parse and measure\ntitle, body, word count,\ngeneration time", "6  Save story\nINSERT stories\n(SQLite)"]
    bot = ["7  Narrate\nchunks <= 380 chars,\nMMS VITS or OS voice", "8  Save audio\nWAV in data/audio +\nINSERT audio_outputs", "9  Listen and download\nGET /api/audio/{id},\nWAV file link",
           "10  History\nlist, open, regenerate\nnarration, delete", "11  Evaluation\nWER, CER, similarity,\nROUGE-L, RTF, files"]
    xs = [9.5 + i * 16.2 for i in range(6)]
    for i, s in enumerate(top):
        box(ax, xs[i], 38, 14.6, 12, s, fc=NAVY, fs=8)
        if i:
            arrow(ax, (xs[i - 1] + 7.4, 38), (xs[i] - 7.4, 38), color=GREY)
    for i, s in enumerate(bot):
        x = xs[5 - i]
        fc = PURPLE if i == 4 else (TEAL if i in (0, 1) else BLUE)
        box(ax, x, 17, 14.6, 12, s, fc=fc, fs=8)
        if i:
            arrow(ax, (xs[5 - i + 1] - 7.4, 17), (x + 7.4, 17), color=GREY)
    arrow(ax, (xs[5], 32), (xs[5], 23), color=GREY)
    txt(ax, 50, 51, "Every failure returns a plain-language message with HTTP 422 or 500; a story whose narration fails is still saved and can be narrated later.", 8.2, GREY, style="italic")
    box(ax, 27, 4.2, 44, 5.6, "No translation step: the language model writes the story directly\nin the chosen language; narration uses that language's checkpoint", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 77, 4.2, 40, 5.6, "Stories, audio and metrics stay on this machine;\nno analytics or external uploads", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    save(fig, out("02_high_level_workflow.png"))


# ------------------------------------------------------------------------------------------------ 03 DFD 0
def d_dfd0():
    fig, ax = canvas(W, 5.4, 100)          # height 49.1
    circle(ax, 50, 22, 11.5, "StoryVox\n0", fc=NAVY, fs=11)
    box(ax, 12, 22, 18, 8, "User\n(creator, listener)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=10, bold=True, r=0.6)
    box(ax, 50, 44, 34, 6.5, "Hugging Face Hub\n(model weights, first run only)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=9.5, r=0.6)
    box(ax, 88, 22, 20, 8, "OS speech engine\n(SAPI via pyttsx3)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=9.5, r=0.6, ls="--")
    arrow(ax, (21, 26), (38.5, 26), "story idea, language,\nstyle, length,\nevaluation request", lo=(0, 6.2), fs=8, color=NAVY)
    arrow(ax, (38.5, 18), (21, 18), "story text, narration WAV,\nhistory, evaluation metrics", lo=(0, -6.2), fs=8, color=TEAL)
    arrow(ax, (50, 40.6), (50, 33.6), "checkpoints and tokenizers", lo=(11, 0), fs=8, color=NAVY)
    arrow(ax, (61.5, 26), (78, 26), "text to speak", lo=(0, 3.6), fs=8, color=PURPLE)
    arrow(ax, (78, 18), (61.5, 18), "fallback audio", lo=(0, -3.6), fs=8, color=PURPLE)
    save(fig, out("03_dfd_level0.png"))


DRAWERS = {"arch": d_arch, "flow": d_flow, "dfd0": d_dfd0}


def main():
    from . import diagrams_dfd as D
    from . import diagrams_dfd2 as D2
    from . import diagrams_er as ER
    from . import diagrams_flow as FL
    from . import diagrams_more as M
    from . import diagrams_uml as U
    all_ = dict(DRAWERS)
    for mod in (D, U, D2, M, ER, FL):
        all_.update(mod.DRAWERS)
    order = ["arch", "flow", "dfd0", "dfd1", "dfd2", "uml", "seq", "usecase", "er", "algo", "tts_eval", "model"]
    keys = sys.argv[1:] or [k for k in order if k in all_]
    for k in keys:
        all_[k]()


if __name__ == "__main__":
    main()
