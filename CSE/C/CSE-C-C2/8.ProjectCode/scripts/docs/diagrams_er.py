"""ER diagram (09): the three SQLite tables of app/models/__init__.py plus the files they point to."""

from matplotlib.patches import Rectangle

from .dgm_lib import GREY, INK, NAVY, ORANGE, PALE_ORANGE, PALE_TEAL, PURPLE, TEAL, W, arrow, box, canvas, out, save_min as save, txt

ROW = 3.15


def _table(ax, x, y_top, w, name, cols, hdr=NAVY):
    """cols: [(name, type, key)] -> returns dict col name -> y centre."""
    h_head = 4.6
    h = h_head + ROW * len(cols) + 0.8
    ax.add_patch(Rectangle((x, y_top - h), w, h, fc="white", ec=NAVY, lw=1.4, zorder=2))
    ax.add_patch(Rectangle((x, y_top - h_head), w, h_head, fc=hdr, ec=NAVY, lw=1.4, zorder=3))
    ax.text(x + w / 2, y_top - h_head / 2, name, ha="center", va="center", color="white", fontsize=10, fontweight="bold", zorder=4)
    ys = {}
    for i, (cn, ct, key) in enumerate(cols):
        y = y_top - h_head - ROW * (i + 0.5) - 0.4
        ys[cn] = y
        if key:
            ax.text(x + 0.9, y, key, ha="left", va="center", fontsize=8, color=ORANGE if key == "PK" else PURPLE, fontweight="bold", zorder=4)
        ax.text(x + 4.6, y, cn, ha="left", va="center", fontsize=8.2, color=INK, zorder=4, family="DejaVu Sans Mono")
        ax.text(x + w - 0.8, y, ct, ha="right", va="center", fontsize=7.8, color=GREY, zorder=4)
        if i:
            ax.plot([x, x + w], [y + ROW / 2, y + ROW / 2], color="#DDE3EC", lw=0.7, zorder=3)
    return ys, (x, y_top - h, w, h)


def d_er():
    fig, ax = canvas(W, 6.4, 100)          # height 58.2
    top = 55.5
    sy, sb = _table(ax, 1, top, 30, "stories", [
        ("id", "INTEGER", "PK"), ("prompt", "TEXT", ""), ("title", "VARCHAR(300)", ""), ("story_text", "TEXT", ""), ("language_code", "VARCHAR(16)", ""),
        ("language_name", "VARCHAR(64)", ""), ("style", "VARCHAR(64)", ""), ("length_option", "VARCHAR(16)", ""), ("word_count", "INTEGER", ""),
        ("created_at", "DATETIME", ""), ("generation_time_seconds", "FLOAT", "")])
    ay, ab = _table(ax, 38, top, 30, "audio_outputs", [
        ("id", "INTEGER", "PK"), ("story_id", "INTEGER, NOT NULL", "FK"), ("file_path", "VARCHAR(512)", ""), ("duration_seconds", "FLOAT", ""),
        ("sample_rate", "INTEGER", ""), ("tts_model", "VARCHAR(256)", ""), ("synthesis_time_seconds", "FLOAT", ""), ("rtf", "FLOAT", ""), ("created_at", "DATETIME", "")])
    ey, eb = _table(ax, 72, top, 27, "evaluations", [("id", "INTEGER", "PK"), ("evaluation_type", "VARCHAR(64)", ""), ("language_code", "VARCHAR(16)", ""), ("sample_count", "INTEGER", ""), ("metrics_json", "JSON", ""), ("created_at", "DATETIME", "")], hdr=TEAL)
    # relationship
    y = sy["id"]
    arrow(ax, (31.0, y), (38.0, ay["story_id"]), color=ORANGE, lw=1.6, style="-")
    txt(ax, 32.4, y + 1.9, "1", 9.5, ORANGE, bold=True)
    txt(ax, 36.4, ay["story_id"] + 1.9, "0..*", 9, ORANGE, bold=True)
    box(ax, 34.5, (y + ay["story_id"]) / 2 - 3.8, 5.6, 3.6, "has", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8.4, r=0.5)
    # file pointers
    box(ax, 53, 6.2, 31, 5.4, "data/audio/storyvox_story0_<ms>_<id>.wav\n(file_path points here; deleted with the story)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8, r=0.6)
    arrow(ax, (53, 8.9), (53, ab[1] - 0.1), color=TEAL, ls="--", lw=1.2)
    box(ax, 85.5, 24, 16, 5.8, "data/evaluations/\n*.json  *.csv", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8, r=0.6)
    arrow(ax, (85.5, 27), (85.5, eb[1] - 0.1), color=TEAL, ls="--", lw=1.2)
    txt(ax, 14, 8.0, "Deleting a story removes its\naudio_outputs rows through the\nORM cascade (all, delete-orphan);\nSQLite foreign-key enforcement\nis not switched on.", 8.2, INK, style="italic")
    txt(ax, 85.5, 14, "no relation:\nwritten only by\nPOST /api/\nevaluations/run", 8, GREY)
    save(fig, out("09_er_diagram.png"))


DRAWERS = {"er": d_er}
