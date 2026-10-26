"""UML class diagram (06): routes and schemas, services and TTS providers, evaluation and utilities, ORM models."""

from matplotlib.patches import Polygon

from .dgm_lib import BLUE, GREY, NAVY, ORANGE, PURPLE, TEAL, W, arrow, canvas, out, save_min as save, txt, uml_class

FS = 8.0
LH = 1.75


def _stack(ax, x, y_top, w, specs, gap=2.6):
    """Draw class boxes top to bottom in one column; returns {name: (x, y_bottom, w, h)}."""
    boxes, y = {}, y_top
    for spec in specs:
        name, attrs, meths, hdr, st = spec
        b = uml_class(ax, x, y, w, name, attrs, meths, hdr=hdr, fs=FS, stereotype=st, lh=LH)
        boxes[name] = b
        y = b[1] - gap
    return boxes


def _tri(ax, x, y, up=True, left=False):
    """Hollow generalisation triangle."""
    s = 1.0
    if left:
        pts = [(x, y), (x - 1.6, y + s), (x - 1.6, y - s)]
    else:
        pts = [(x, y), (x - s, y - 1.6), (x + s, y - 1.6)] if up else [(x, y), (x - s, y + 1.6), (x + s, y + 1.6)]
    ax.add_patch(Polygon(pts, fc="white", ec=NAVY, lw=1.2, zorder=6))


def d_uml():
    fig, ax = canvas(W, 11.2, 100)          # height 101.8
    H_ = 100 * 11.2 / W
    top = H_ - 4.6
    X = [0.8, 26.5, 52.2, 77.9]
    CW = 21.0
    c1 = _stack(ax, X[0], top, CW, [
        ("api.routes", ["router = APIRouter('/api')"],
         ["health()", "list_languages()", "meta()", "generate_story(payload)", "synthesize_story(story_id)", "list_stories(limit)",
          "get_story(story_id)", "delete_story(story_id)", "stream_audio(audio_id)", "list_evaluations()", "run_evaluation(payload)"], NAVY, "FastAPI router"),
        ("schemas", ["StoryGenerateRequest", "StoryResponse", "AudioResponse", "StoryListItem", "LanguageInfo", "EvaluationRunRequest", "EvaluationSummary"],
         [], BLUE, "Pydantic models"),
    ], gap=4.2)
    c2 = _stack(ax, X[1], top, CW, [
        ("story_generator", ["STYLE_GUIDANCE (8 styles)", "LOCAL_OPENINGS (15 langs)"],
         ["build_prompt()", "_try_load_pipeline(id)", "generate_story_text()", "_parse_model_output()", "local_fallback_story()", "max_tokens_for_length()"], NAVY, "service"),
        ("tts_service", ["TARGET_SR = 16000"],
         ["synthesize_story_narration()", "resolve_audio_abs_path()", "get_provider()"], NAVY, "service"),
        ("MMSTTSProvider", ["name = 'mms'"], ["_load(checkpoint)", "synthesize(text, lang)"], TEAL, "facebook/mms-tts-*"),
        ("SystemTTSProvider", ["name = 'system-fallback'"], ["synthesize(text, lang)"], TEAL, "pyttsx3 / SAPI5"),
        ("TTSProvider", ["name: str"], ["synthesize(text, lang)*"], GREY, "abstract"),
    ], gap=2.6)
    c3 = _stack(ax, X[2], top, CW, [
        ("evaluation_service", [], ["default_eval_prompts()", "run_evaluation(samples,..)", "_try_semantic_similarity()", "_persist(metrics)", "list_saved_evaluations()"], NAVY, "service"),
        ("asr_service", ["_asr_model_id"], ["_load_asr(model_id)", "transcribe_wav(path, lang)"], NAVY, "Whisper"),
        ("app.utils", [], ["wer()  cer()", "tfidf_cosine()", "rouge_l_f1()", "chunk_text()", "word_count()", "read/write_wav_mono()", "concat_wav_segments()", "is_silent()"], GREY, "helpers"),
    ], gap=3.0)
    c4 = _stack(ax, X[3], top, CW, [
        ("Story", ["id (PK)", "prompt, title", "story_text", "language_code, language_name", "style, length_option", "word_count", "generation_time_seconds", "created_at"], [], ORANGE, "ORM stories"),
        ("AudioOutput", ["id (PK)", "story_id (FK)", "file_path", "duration_seconds, sample_rate", "tts_model", "synthesis_time_seconds", "rtf", "created_at"], [], ORANGE, "ORM audio_outputs"),
        ("Evaluation", ["id (PK)", "evaluation_type", "language_code", "sample_count", "metrics_json (JSON)", "created_at"], [], ORANGE, "ORM evaluations"),
        ("database", ["Base = declarative_base()"], ["get_engine()", "get_session_factory()", "init_db()", "reset_engine()"], GREY, "SQLite"),
    ], gap=3.4)

    def right(b, y=None):
        return (b[0] + b[2], y if y is not None else b[1] + b[3] / 2)

    def left(b, y=None):
        return (b[0], y if y is not None else b[1] + b[3] / 2)

    R, SG, TS, MM, SY, TP = c1["api.routes"], c2["story_generator"], c2["tts_service"], c2["MMSTTSProvider"], c2["SystemTTSProvider"], c2["TTSProvider"]
    EV, AS, UT = c3["evaluation_service"], c3["asr_service"], c3["app.utils"]
    ST, AO, EVm = c4["Story"], c4["AudioOutput"], c4["Evaluation"]
    # routes -> schemas
    arrow(ax, (R[0] + 8, R[1]), (R[0] + 8, c1["schemas"][1] + c1["schemas"][3]), "validates with", color=BLUE, lo=(8.5, 0), fs=8)
    # routes -> services (adjacent column)
    arrow(ax, (R[0] + R[2], SG[1] + SG[3] - 4), (SG[0], SG[1] + SG[3] - 4), "", color=NAVY)
    ya = TS[1] + TS[3] - 3
    arrow(ax, (R[0] + R[2], ya), (TS[0], ya), "", color=NAVY)
    # bus over the top: routes -> evaluation_service and -> ORM models
    yb = H_ - 2.9
    ax.plot([R[0] + 14, R[0] + 14], [R[1] + R[3], yb], color=NAVY, lw=1.4, zorder=3)
    ax.plot([R[0] + 14, ST[0] + 10], [yb, yb], color=NAVY, lw=1.4, zorder=3)
    arrow(ax, (EV[0] + 10, yb), (EV[0] + 10, EV[1] + EV[3] + 0.1), color=NAVY)
    arrow(ax, (ST[0] + 10, yb), (ST[0] + 10, ST[1] + ST[3] + 0.1), color=ORANGE)
    txt(ax, EV[0] + 11, yb + 1.2, "run_evaluation()", 8, NAVY, ha="left")
    txt(ax, ST[0] + 9.5, yb + 1.2, "Session CRUD (SQLAlchemy)", 8, ORANGE, ha="right")
    # evaluation_service uses the story generator, tts_service, asr_service and helpers
    ye = SG[1] + SG[3] - 11
    arrow(ax, (EV[0], ye), (SG[0] + SG[2], ye), "", color=NAVY)
    arrow(ax, (EV[0], EV[1] + 3), (TS[0] + TS[2], TS[1] + TS[3] - 2), "", color=NAVY)
    arrow(ax, (EV[0] + 10, EV[1]), (EV[0] + 10, AS[1] + AS[3]), "", color=NAVY)
    ax.plot([EV[0] + EV[2], EV[0] + EV[2] + 2.0], [EV[1] + 3, EV[1] + 3], color=GREY, lw=1.2, zorder=3)
    ax.plot([EV[0] + EV[2] + 2.0] * 2, [EV[1] + 3, UT[1] + UT[3] - 2.5], color=GREY, lw=1.2, zorder=3)
    arrow(ax, (EV[0] + EV[2] + 2.0, UT[1] + UT[3] - 2.5), (UT[0] + UT[2], UT[1] + UT[3] - 2.5), "", color=GREY)
    # tts_service -> providers, utils
    arrow(ax, (TS[0] + 10, TS[1]), (TS[0] + 10, MM[1] + MM[3]), "tries in order", color=TEAL, lo=(6.5, 0), fs=8)
    arrow(ax, (MM[0] + 10, MM[1]), (MM[0] + 10, SY[1] + SY[3]), "", color=TEAL, lw=1.0, ls="--")
    arrow(ax, (TS[0] + TS[2], TS[1] + 3), (UT[0], UT[1] + UT[3] - 12), "", color=GREY)
    # generalisation: both providers implement TTSProvider (trunk in the left margin)
    xt = X[1] - 2.3
    ym, ys = MM[1] + MM[3] / 2, SY[1] + SY[3] / 2
    ytp = TP[1] + TP[3] / 2
    for yy in (ym, ys):
        ax.plot([X[1], xt], [yy, yy], color=NAVY, lw=1.2, zorder=3)
    ax.plot([xt, xt], [ym, ytp], color=NAVY, lw=1.2, zorder=3)
    ax.plot([xt, X[1] - 1.6], [ytp, ytp], color=NAVY, lw=1.2, zorder=3)
    ax.add_patch(Polygon([(X[1] - 0.05, ytp), (X[1] - 1.7, ytp + 1.0), (X[1] - 1.7, ytp - 1.0)], fc="white", ec=NAVY, lw=1.2, zorder=6))
    txt(ax, xt - 0.4, (ys + ytp) / 2, "implements", 8, NAVY, ha="right")
    # asr_service uses the helpers
    # ORM relations
    arrow(ax, (ST[0] + 10, ST[1]), (ST[0] + 10, AO[1] + AO[3]), "", color=ORANGE, lw=1.3, style="-")
    txt(ax, ST[0] + 9.0, ST[1] - 1.4, "1", 8.5, ORANGE, ha="right", bold=True)
    txt(ax, AO[0] + 11.0, AO[1] + AO[3] + 1.4, "0..*", 8.5, ORANGE, ha="left", bold=True)
    txt(ax, ST[0] + 3.2, (ST[1] + AO[1] + AO[3]) / 2, "has", 8, ORANGE)
    # API routes read/write; evaluation standalone note
    txt(ax, EVm[0] + 10.5, EVm[1] - 0.2, "", 8)
    save(fig, out("06_uml_class.png"))


DRAWERS = {"uml": d_uml}
