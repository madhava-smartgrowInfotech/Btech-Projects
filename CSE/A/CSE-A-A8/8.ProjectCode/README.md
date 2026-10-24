# AI-Powered Medical Lab Report Analysis & Health Insights Platform

A Streamlit application that lets users upload medical laboratory reports
(PDF, JPG, JPEG, PNG), automatically extracts test names/values/units/
reference ranges via OCR + NLP, classifies each result as **Low / Normal /
High**, stores report history in a database, generates plain-language
educational explanations for abnormal results, and visualizes health
trends over time.

> ⚕️ **This is an educational tool, not a diagnostic device.** It never
> diagnoses disease and always recommends consulting a healthcare
> professional for medical advice.

---

## 1. Project Structure

```
medical_lab_ai/
│
├── app.py                # Streamlit UI (all pages + navigation)
├── database.py            # SQLAlchemy engine, session, CRUD helpers
├── models.py               # SQLAlchemy ORM models (Report, TestResult, HealthInsight)
├── ocr_processor.py        # PDF/image text extraction (PyMuPDF, OpenCV, Tesseract)
├── ner_processor.py        # Regex + TF-IDF structured extraction of test rows
├── result_analyzer.py      # Low/Normal/High classification logic
├── ai_insights.py          # Rule-based (+ optional LLM) health explanations
├── report_processor.py     # Orchestrates the full pipeline end-to-end
├── requirements.txt
├── .env.example            # Copy to .env to enable optional LLM insights
├── data/                   # SQLite database file lives here (auto-created)
├── uploads/                # Scratch space for uploaded files (auto-created)
└── README.md
```

---

## 2. Prerequisites

- **Python 3.11+**
- **Tesseract OCR engine** (system package, required by `pytesseract`):
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS (Homebrew): `brew install tesseract`
  - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
    and ensure `tesseract.exe` is on your `PATH`.

---

## 3. Installation

```bash
# 1. Clone / unzip the project, then move into it
cd medical_lab_ai

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download the spaCy English model (used for optional patient-name NER)
python -m spacy download en_core_web_sm

# 5. (Optional) enable LLM-enriched explanations
cp .env.example .env
# then edit .env and paste your ANTHROPIC_API_KEY
```

If step 4 is skipped, the app still works fully — spaCy is only used for
an optional, non-essential patient-name lookup.

---

## 4. Running the App

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

### New web interface (React + FastAPI)

A redesigned interface ("Depth Studio" kit V3) now sits next to the Streamlit app and uses the same pipeline and database.
Double-click `run.bat` (or see `docs/03_HOW_TO_RUN.md`), then open http://localhost:5308 and sign in with
`demo@lablens.com` / `Demo@1234`. The API lives in `backend/`, the UI in `frontend/`.

---

## 5. Using the App

1. **Upload Report** — upload a PDF/JPG/PNG lab report.
2. Click **Process Report** — watch the status move through
   Uploading → Processing → Extracting text → Analyzing results → Completed.
3. **Report Analysis** — see the structured results table and AI
   explanations for anything flagged Low/High.
4. **Dashboard** — overall counts across all reports.
5. **Health Trends** — pick a test (e.g. Hemoglobin) to see a line chart
   of that value across all your uploaded reports.
6. **Compare Reports** — pick any two reports to see a side-by-side table
   and bar chart of shared tests.
7. **My Reports** — full upload history, with delete option.
8. **Health Insights** — every abnormal result across all reports, in one place.

---

## 6. How Extraction Works (short version)

1. **OCR (`ocr_processor.py`)** — PDFs use PyMuPDF's embedded text layer
   when available; pages/images without a usable text layer are rendered
   and OCR'd via Tesseract after an OpenCV preprocessing pipeline
   (grayscale → denoise → adaptive threshold → deskew).
2. **NER (`ner_processor.py`)** — each line of extracted text is parsed
   with regular expressions to find `<name> <value> <unit> <range>`. A
   scikit-learn TF-IDF character-n-gram matcher normalizes noisy OCR test
   names (e.g. `Haemogl0bin`) against a dictionary of ~50 common lab
   tests. spaCy is used only as an optional add-on for patient-name
   extraction.
3. **Classification (`result_analyzer.py`)** — compares each numeric
   result against its reference range using simple, transparent rules
   (see module docstring).
4. **Insights (`ai_insights.py`)** — abnormal results get a plain-language,
   non-diagnostic explanation from a curated knowledge base. If
   `ANTHROPIC_API_KEY` is configured and the "Use LLM" toggle is on, the
   explanation is rewritten in warmer language by an LLM call — with an
   automatic fallback to the rule-based text if that call fails for any
   reason.

---

## 7. Known Limitations

- OCR accuracy depends heavily on scan/photo quality and lab report layout.
- The regex-based parser is tuned for common tabular lab report formats;
  highly unusual layouts may not extract every row.
- This tool performs **no medical diagnosis** and should not be used as a
  substitute for professional medical advice.

---

## 8. Disclaimer

This application provides educational information only and does not
provide medical diagnosis or treatment. Please consult a qualified
healthcare professional for medical advice.
