"""Compact output-screens section for the full report (used when F.REPORT is True).
The main screens are shown here; the remaining ones (theme variants, registration, search, delete dialog, phone width, 404) are in Appendix C
(appendix.screens_blocks). Chapter document 14 keeps the one-screen-per-figure layout of ch8._screens."""

from . import facts as F
from .blocks import H2, P, PAIR
from .ch8 import S, _cap

# screens placed in Appendix C in the report (every screenshot appears exactly once in the report)
APPENDIX_C = ["02_landing_dark.png", "03_landing_bottom_dark.png", "04_register.png", "10_history_search.png", "12_delete_confirm.png", "14_about_dark.png",
              "15_mobile_assistant.png", "16_mobile_history.png", "17_not_found.png"]


def screens():
    return [
        H2("8.2 Output screens"),
        P("The principal screens captured from the running application are shown here (Chrome, 1440 by 900 pixels, backend on port 8412, React frontend on port 5412, demo account, real queries through the real pipeline); "
          "the other captures (dark theme, registration, search, delete dialog, phone width and the 404 page) are in Appendix C. The application is called CareLens AI on screen. "
          "The answer, evidence, caution, emergency, history and detail screens were captured with the evidence-based fallback generator active, because the default local generator returns its own prompt in this software environment (Section 8.6); "
          "one screen in this section was captured with the default generator and shows that defect."),
        PAIR([_cap("01_landing_light.png", "Landing page, light theme: product pitch and entry buttons."),
              _cap("05_login.png", "Sign-in form; the demo account is created automatically at start-up.")], 2.8),
        PAIR([_cap("06_assistant_empty.png", "Symptom assistant before the first question: example chips and the permanent not-a-diagnosis line."),
              _cap("18_assistant_lay_query.png", "Everyday-language query retrieving Urinary Tract Infection.")], 2.8),
        S("07_assistant_answer.png", "Answer to \"I have high fever, headache and body pain since yesterday\" (fallback generator): top condition Influenza; the guidance sentence repeats because several near-identical records matched.", 5.0, 3.3),
        PAIR([_cap("20_assistant_evidence.png", "Evidence cards of the same answer: symptoms, description, guidance, severity, match bar and red flags; the fifth card is Dengue at 75%."),
              _cap("19_assistant_caution.png", "Caution banner (amber) for a message that mentions pregnancy; top record Gastritis.")], 2.8),
        PAIR([_cap("08_assistant_emergency.png", "Emergency banner (red) for severe chest pain and difficulty breathing; top record Heart Attack."),
              _cap("21_assistant_generator_echo.png", "Failure case: the default Flan-T5 generator returns its prompt as the answer.")], 2.8),
        PAIR([_cap("09_history.png", "Consultation history with safety badges and a displayed relevance of 100% in every row."),
              _cap("11_consultation_detail.png", "Saved consultation: summary table and stored answer.")], 2.8),
        PAIR([_cap("13_about_metrics.png", "About page showing the shipped evaluation figures (100%, 245 ms, 176 records) - an upper bound (Section 8.3).")], 3.2),
    ]
