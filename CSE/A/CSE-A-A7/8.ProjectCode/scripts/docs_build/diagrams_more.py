"""ATHENA UML class diagram, use-case diagram and ER diagram (06, 08, 09) drawn from backend/app/db.py, routes/api.py and services/."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def uml_class_diagram():
    fig, ax = canvas(10.4, 12.2, 100, 122)
    ax.set_ylim(-6, 116)
    ax.text(50, 114, "UML class diagram - ORM models, request schemas, router and services", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    fs = 6.4
    gap = 4.5
    # left column: SQLAlchemy models
    X1, W1 = 5, 29
    y = 110
    user = uml_class(ax, X1, y, W1, "User", ["+id: int (PK)", "+name: str", "+email: str (unique)", "+password_hash: str", "+role: str"], [], hdr=NAVY, fs=fs, stereotype="table users")
    y = user[1] - gap - 2
    pat = uml_class(ax, X1, y, W1, "Patient", ["+id: int (PK)", "+name: str", "+created_at: datetime", "+created_by: int -> users", "+source: live | sample", "+vitals: JSON", "+report: JSON",
                                               "+fused: JSON (36 inputs)", "+model_priority: int", "+priority: int", "+risk_level: str", "+confidence: float", "+probabilities: JSON",
                                               "+shap: JSON", "+ocr_seconds: float", "+model_seconds: float", "+total_seconds: float", "+recorded_outcome: int?"], [], hdr=NAVY, fs=fs, stereotype="table patients")
    y = pat[1] - gap - 2
    ovr = uml_class(ax, X1, y, W1, "Override", ["+id: int (PK)", "+patient_id: int -> patients", "+user_id: int -> users", "+user_name: str", "+old_priority: int", "+new_priority: int",
                                               "+action: accept | change", "+reason: text", "+created_at: datetime"], [], hdr=NAVY, fs=fs, stereotype="table overrides")
    # middle column: Pydantic schemas
    X2, W2 = 40, 24
    y = 110
    login = uml_class(ax, X2, y, W2, "LoginIn", ["+email: str", "+password: str"], [], hdr=TEAL, fs=fs, stereotype="schema")
    y = login[1] - gap - 2
    pin = uml_class(ax, X2, y, W2, "PatientIn", ["+name: str", "+vitals: VitalsIn", "+report: dict?", "+ocr_seconds: float"], [], hdr=TEAL, fs=fs, stereotype="schema")
    y = pin[1] - gap - 4
    vit = uml_class(ax, X2, y, W2, "VitalsIn", ["+age: int 0-120", "+heart_rate: int 20-250", "+sbp: int 40-300", "+dbp: int 20-200", "+spo2: int 50-100", "+temp_c: float 30-44",
                                               "+resp_rate: int 4-70", "+arrival_mode: str"], [], hdr=TEAL, fs=fs, stereotype="schema")
    y = vit[1] - gap - 2
    oin = uml_class(ax, X2, y, W2, "OverrideIn", ["+priority: int 1-5", "+reason: str"], [], hdr=TEAL, fs=fs, stereotype="schema")
    # right column: router and services
    X3, W3 = 69, 28
    y = 110
    api = uml_class(ax, X3, y, W3, "api router (/api)", [], ["login(), me()", "extract_report(file)", "create_patient(body)", "list_patients(), get_patient(id)", "override(id, body)", "summary_pdf(id)",
                                                           "metrics(), health()", "public_stats()", "list_samples(), get_sample(f)"], hdr=ORANGE, fs=fs, stereotype="APIRouter")
    mods = []
    y = api[1] - 2.4
    for name, attrs, meths in [
        ("auth", [], ["hash_password(), verify_password()", "make_token(user)  HS256", "current_user()  bearer JWT"]),
        ("extract", [], ["read_pages(data, name)", "parse(pages) -> flags", "extract_report(data, name)", "_ocr_image(img)  RapidOCR"]),
        ("features", ["FEATURES: 36 names", "REPORT_FLAGS: 28 flags"], ["fuse(vitals, flags)", "risk_level(priority)", "label_for(name)"]),
        ("triage", ["_bundle(): XGBoost, calibrator,", "          SHAP explainer"], ["predict(vitals, flags, top=8)"]),
        ("pdf", [], ["build_summary(patient) -> bytes"]),
    ]:
        c = uml_class(ax, X3, y, W3, name, attrs, meths, hdr=ORANGE, fs=fs, stereotype="module")
        mods.append(c)
        y = c[1] - 2.4

    def ln(p, color=NAVY, lw=1.2, ls="-"):
        ax.plot([q[0] for q in p], [q[1] for q in p], color=color, lw=lw, ls=ls, zorder=4)

    # User 1 - * Patient (created_by)
    cx = X1 + W1 / 2
    ln([(cx, user[1]), (cx, pat[1] + pat[3])])
    ax.text(cx + 1, user[1] - 1.6, "1", fontsize=7, color=INK, fontweight="bold")
    ax.text(cx + 1, pat[1] + pat[3] + 1.2, "*", fontsize=8, color=INK, fontweight="bold")
    ax.text(cx + 3.5, (user[1] + pat[1] + pat[3]) / 2 - 0.3, "created_by", fontsize=6.2, color=GREY)
    # Patient 1 - * Override
    ln([(cx, pat[1]), (cx, ovr[1] + ovr[3])])
    ax.text(cx + 1, pat[1] - 1.6, "1", fontsize=7, color=INK, fontweight="bold")
    ax.text(cx + 1, ovr[1] + ovr[3] + 1.2, "*", fontsize=8, color=INK, fontweight="bold")
    ax.text(cx + 3.5, (pat[1] + ovr[1] + ovr[3]) / 2 - 0.3, "patient_id", fontsize=6.2, color=GREY)
    # User 1 - * Override (user_id) along the left margin
    yu = user[1] + user[3] - 14
    yo = ovr[1] + ovr[3] - 14
    ln([(X1, yu), (1.8, yu), (1.8, yo), (X1, yo)])
    ax.text(2.4, yu + 1.0, "1", fontsize=7, color=INK, fontweight="bold")
    ax.text(2.4, yo + 1.0, "*", fontsize=8, color=INK, fontweight="bold")
    ax.text(0.2, (yu + yo) / 2, "user_id", fontsize=6.2, color=GREY, rotation=90, va="center")
    # PatientIn contains VitalsIn
    mx = X2 + W2 / 2
    arrow(ax, (mx, pin[1]), (mx, vit[1] + vit[3]), "", color=TEAL, lw=1.2)
    ax.text(mx + 1.5, (pin[1] + vit[1] + vit[3]) / 2, "contains", fontsize=6.2, color=INK, va="center")
    # router uses schemas (dashed bus at x=66.5)
    bx = 66.6
    ln([(X3, api[1] + api[3] - 2), (bx, api[1] + api[3] - 2), (bx, oin[1] + oin[3] - 6)], color=GREY, ls="--", lw=1.1)
    for c, dy in ((login, 6), (pin, 6), (oin, 6)):
        yy = c[1] + c[3] - dy
        arrow(ax, (bx, yy), (X2 + W2, yy), "", color=GREY, ls="--", lw=1.1)
    ax.text(bx + 0.4, api[1] + api[3] + 0.9, "uses", fontsize=6.2, color=INK, ha="center")
    # router uses services (dashed bus on the right margin)
    rx = 98.8
    ln([(X3 + W3, api[1] + 4), (rx, api[1] + 4), (rx, mods[-1][1] + mods[-1][3] - 4)], color=GREY, ls="--", lw=1.1)
    for c in mods:
        yy = c[1] + c[3] - 5
        arrow(ax, (rx, yy), (X3 + W3, yy), "", color=GREY, ls="--", lw=1.1)
    ax.text(X2, ovr[1] + 6, "The router reads and writes User, Patient and\nOverride through a SQLAlchemy session (get_db).\nThe triage and pdf modules only read Patient\nobjects and the saved model file.\nRegistered with the app in main.py; users and a\n12-case sample queue are seeded at start-up.",
            fontsize=6.4, color=INK, va="top", linespacing=1.5)
    save(fig, OUT / "06_uml_class.png")


def stick(ax, x, y, label):
    ax.add_patch(Circle((x, y + 8), 2.2, fc=WHITE, ec=NAVY, lw=1.5, zorder=3))
    ax.plot([x, x], [y + 5.8, y], color=NAVY, lw=1.5, zorder=3)
    ax.plot([x - 3, x + 3], [y + 4, y + 4], color=NAVY, lw=1.5, zorder=3)
    ax.plot([x, x - 2.8], [y, y - 4.5], color=NAVY, lw=1.5, zorder=3)
    ax.plot([x, x + 2.8], [y, y - 4.5], color=NAVY, lw=1.5, zorder=3)
    ax.text(x, y - 7, label, ha="center", va="top", fontsize=7.4, color=INK, fontweight="bold")


def use_case_diagram():
    fig, ax = canvas(10, 7.8, 100, 78)
    ax.text(50, 75.5, "Use-case diagram", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.add_patch(FancyBboxPatch((24, 2), 52, 70, boxstyle="round,pad=0,rounding_size=1.2", fc="#F7F9FC", ec=NAVY, lw=1.4, zorder=1))
    ax.text(50, 69, "ATHENA triage system", ha="center", fontsize=8.6, color=NAVY, fontweight="bold")
    rows = [("signin", "Sign in", "both"), ("upload", "Upload and read report", "n"), ("sample", "Try a sample report", "n"), ("vitals", "Enter vitals", "n"),
            ("assess", "Assess priority and view reasons (SHAP)", "n"), ("decide", "Accept or change priority with a reason", "n"), ("pdf", "Download summary PDF", "n"),
            ("queue", "View triage queue", "both"), ("perf", "View model performance", "both"), ("retrain", "Retrain model (ml/train.py)", "d")]
    pitch, y0, cx = 6.0, 62.0, 50
    pos = {}
    for i, (k, t, who) in enumerate(rows):
        y = y0 - i * pitch
        ellipse(ax, cx, y, 40, 4.6, t, fs=6.9)
        pos[k] = y
    stick(ax, 10, 38, "Triage nurse /\nclinician")
    stick(ax, 90, 38, "Administrator")
    stick(ax, 90, 10, "Developer\n(offline)")
    for k, _, who in rows:
        if who in ("n", "both"):
            ax.plot([13.5, cx - 20], [42, pos[k]], color=GREY, lw=0.9, zorder=2)
        if who in ("both",):
            ax.plot([86.5, cx + 20], [42, pos[k]], color=GREY, lw=0.9, zorder=2)
        if who == "d":
            ax.plot([86.5, cx + 20], [14, pos[k]], color=GREY, lw=0.9, zorder=2)
    # extend: sample report extends upload
    arrow(ax, (cx + 14, pos["sample"] + 2.3), (cx + 14, pos["upload"] - 2.3), "", color=ORANGE, ls="--", lw=1.2)
    ax.text(cx + 15.5, (pos["sample"] + pos["upload"]) / 2, "<<extend>>", fontsize=6.4, color=ORANGE, style="italic", va="center")
    ax.text(50, 0.2, "Sign in is required before any other use case; the sign-in guard is a route guard in the React app and a bearer token on the API.",
            ha="center", fontsize=6.4, color=GREY)
    save(fig, OUT / "08_use_case.png")


def table(ax, x, y, w, name, cols, hdr=NAVY, rh=3.1):
    h = 4.2 + rh * len(cols) + 0.8
    ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((x, y - 4.2), w, 4.2, fc=hdr, ec=NAVY, lw=1.3, zorder=3))
    ax.text(x + w / 2, y - 2.1, name, ha="center", va="center", color=WHITE, fontsize=9, fontweight="bold", zorder=4)
    for i, (key, col, typ) in enumerate(cols):
        yy = y - 4.2 - 0.4 - rh * (i + 0.5)
        if key:
            ax.add_patch(Rectangle((x + 0.3, yy - rh / 2 + 0.2), w - 0.6, rh - 0.4, fc=PALE_ORANGE if key == "PK" else PALE_BLUE, ec="none", zorder=3))
        ax.text(x + 1.0, yy, key, ha="left", va="center", fontsize=6.6, color=ORANGE if key == "PK" else BLUE, fontweight="bold", zorder=4)
        ax.text(x + 4.6, yy, col, ha="left", va="center", fontsize=7.0, color=INK, zorder=4, family="DejaVu Sans Mono")
        ax.text(x + w - 0.9, yy, typ, ha="right", va="center", fontsize=6.4, color=GREY, zorder=4)
    return x, y, w, h


def er_diagram():
    fig, ax = canvas(10.4, 8.2, 100, 79)
    ax.text(50, 76.5, "Entity-relationship diagram (SQLite, SQLAlchemy models in backend/app/db.py)", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    table(ax, 2, 68, 26, "users", [("PK", "id", "INTEGER"), ("", "name", "VARCHAR(80)"), ("UQ", "email", "VARCHAR(120)"), ("", "password_hash", "VARCHAR(120)"), ("", "role", "VARCHAR(20)")])
    table(ax, 36, 68, 34, "patients", [("PK", "id", "INTEGER"), ("", "name", "VARCHAR(80)"), ("", "created_at", "DATETIME"), ("FK", "created_by", "INTEGER null"), ("", "source", "live | sample"),
                                       ("", "vitals", "JSON"), ("", "report", "JSON null"), ("", "fused", "JSON"), ("", "model_priority", "INTEGER"), ("", "priority", "INTEGER, index"),
                                       ("", "risk_level", "VARCHAR(12)"), ("", "confidence", "FLOAT"), ("", "probabilities", "JSON"), ("", "shap", "JSON"), ("", "ocr_seconds", "FLOAT"),
                                       ("", "model_seconds", "FLOAT"), ("", "total_seconds", "FLOAT"), ("", "recorded_outcome", "INTEGER null")], hdr=TEAL)
    table(ax, 76, 68, 22, "overrides", [("PK", "id", "INTEGER"), ("FK", "patient_id", "INTEGER"), ("FK", "user_id", "INTEGER null"), ("", "user_name", "VARCHAR(80)"), ("", "old_priority", "INTEGER"),
                                        ("", "new_priority", "INTEGER"), ("", "action", "accept|change"), ("", "reason", "TEXT"), ("", "created_at", "DATETIME")], hdr=ORANGE)
    rowy = lambda i: 68 - 4.2 - 0.4 - 3.1 * (i + 0.5)
    # users.id (row 0) 1 -- N patients.created_by (row 3)
    ax.plot([28, 32, 32, 36], [rowy(0), rowy(0), rowy(3), rowy(3)], color=NAVY, lw=1.4, zorder=4)
    ax.text(28.6, rowy(0) + 1.2, "1", fontsize=8, color=INK, fontweight="bold")
    ax.text(32.6, rowy(3) + 1.2, "N", fontsize=8, color=INK, fontweight="bold")
    # patients.id (row 0) 1 -- N overrides.patient_id (row 1)
    ax.plot([70, 76], [rowy(0), rowy(1)], color=NAVY, lw=1.4, zorder=4)
    ax.text(70.6, rowy(0) + 1.2, "1", fontsize=8, color=INK, fontweight="bold")
    ax.text(73.4, rowy(1) - 2.6, "N", fontsize=8, color=INK, fontweight="bold")
    # users 1 -- N overrides.user_id, routed above the tables
    ax.plot([15, 15, 87, 87], [68, 72.4, 72.4, 68], color=NAVY, lw=1.4, zorder=4)
    ax.text(15.8, 69.0, "1", fontsize=8, color=INK, fontweight="bold")
    ax.text(86.0, 69.0, "N", fontsize=8, color=INK, fontweight="bold")
    ax.text(51, 73.2, "overrides.user_id -> users.id (who reviewed)", fontsize=6.6, color=GREY, ha="center")
    ax.text(2, 41.5, "Relationships\n- users 1:N patients  (patients.created_by)\n- patients 1:N overrides  (overrides.patient_id)\n- users 1:N overrides  (overrides.user_id)\n\nNotes\n- source is 'sample' for the 12 seeded queue cases\n  (they carry recorded_outcome) and 'live' for entered\n  patients.\n- priority is the current priority; model_priority keeps\n  the model's first suggestion.\n- An override with action 'change' needs a reason;\n  'accept' keeps the priority.\n- fused, probabilities and shap store the model input\n  and output of the case as JSON.",
            fontsize=6.8, color=INK, va="top", linespacing=1.45)
    save(fig, OUT / "09_er_diagram.png")


def main():
    uml_class_diagram()
    use_case_diagram()
    er_diagram()


if __name__ == "__main__":
    main()
