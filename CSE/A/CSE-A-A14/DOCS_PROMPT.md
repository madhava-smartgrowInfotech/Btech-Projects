# DOCUMENTATION PROMPT - Customer Churn Prediction in Telecom Industry (M

> Open the **batch folder** `D:\abstracts\Madhav\CSE\A\CSE-A-A14` as your workspace (not `8.ProjectCode` - you write files at the batch
> root), start a session and say:
> *"Read DOCS_PROMPT.md completely and follow it exactly."*
> Suggested model: **Sonnet, high effort.**

**Batch:** CSE-A-A14 (CSE-A) · **Product:** Customer Churn Prediction in Telecom Industry (M · **Project:** Customer Churn Prediction in Telecom Industry (Machine Learning Based Customer Retention System)
**Code:** `8.ProjectCode` (backend 8314, frontend 5314)
**Templates:** `D:\abstracts\Templates` - `Review_1_PPT.pptx`, `Review_2_PPT.pptx`, `Final_PPT.pptx`, `Project_Report.pdf`

---

## 0. What you are producing

Eleven submission documents at the batch root, replacing the placeholder files of the same names:

| File | What it is |
|---|---|
| `7.Review_1_PPT.pptx` | 16 slides - problem identification and research |
| `9.METHODOLOGY&NOVELTY&KEY CONTRIBUTIONS.docx` | how the system works, what is new in it |
| `10.SCOPE & LIMITATIONS.docx` | what it covers and what it deliberately does not |
| `11. BLOCK DIAGRAMS ALL.docx` | every diagram, captioned (keep the exact filename, including the space) |
| `12.DESIGN &IMPLEMENTATION.docx` | design decisions and how they were implemented |
| `13.Review_2_PPT.pptx` | 20 slides - design, methodology and progress |
| `14.RESULTS.docx` | real measurements and output screens |
| `15.CONCLUSION&FUTURE SCOPE&REFERENCES.docx` | conclusions, future scope, references |
| `16.Final_PPT.pptx` | 28 slides - the complete story |
| `17.Final Document.docx` | the full report: front matter, 10 chapters, references, 3 appendices (~80-95 pages) |
| `19.IEEE_Paper.docx` | a 6-page, two-column IEEE conference paper on this project |

---

## 1. Four rules that decide whether this is acceptable

1. **These are academic submission documents.** Unlike the product code - where institution and student names
   are banned - these documents **must** carry the student names, roll numbers and guide name. Take them from
   the `1.*_BATCH_DETAILS.docx` file and `Students.txt` in this folder. Where something is genuinely unknown
   (college name, principal, HOD, academic year), leave the template's square-bracket placeholder in place.
2. **The templates are structure and quality bar only.** They describe entirely different projects (a social
   media manipulation detector, a bank fraud system). **Not one sentence of their subject matter may survive
   into your documents.** Match their depth, tone, chapter structure and slide counts - never their content.
3. **Every number must be real.** Accuracy, F1, latency, dataset sizes, test counts, timings - all of it comes
   from this project's own artefacts: `experiments/**/metrics.json`, model evaluation output, test runs, measured
   response times. **Invent nothing.** If an objective was not achieved, or a metric was never measured, write
   that plainly - an honest gap is acceptable, a fabricated number is not.
4. **Screenshots must be real.** Actual captures of this application running with real data in it. No mockups,
   no empty dashboards, no borrowed images.

---

## 2. Step 1 - gather the facts, then one stop

1. Read this batch's existing documents: `2.ABSTRACT.docx`, `3.BASE PAPER.docx`, `4.INTRODUCTION.docx`,
   `5.LITERATURE SURVEY.docx`, `6.OBJECTIVES&PROBLEM STATEMENT.docx`, and `1.*_BATCH_DETAILS.docx` for the
   student and guide details.
2. Read the code in `8.ProjectCode`: README, `docs/`, backend routes, models, `ml/`, tests, and every
   `experiments/**/metrics.json`.
3. **Screenshots** - if `8.ProjectCode/docs/screenshots/` is missing or thin, produce them now:
   - `pip install playwright` then `playwright install chromium` (downloads once per machine).
   - Start the app (`run.bat`), log in, put **real data** into it, and capture every screen at 1440x900 into
     `8.ProjectCode/docs/screenshots/<nn>_<screen>.png`. An empty dashboard is not acceptable - upload the
     sample file, run the analysis, generate the plan, whatever this product actually does.
4. Write `8.ProjectCode/docs/REPORT_FACTS.md`: the real metrics table, architecture summary, endpoint list,
   dataset facts (source, licence, size, split), test results, and the screenshot inventory. Everything you
   write later must agree with this file.
5. Show the user a **10-line summary** - metrics found, screenshots captured, anything missing - and **wait for
   "proceed"**. That is the only stop.

---

## 3. Step 2 - diagrams

Generate real diagrams from the real design into `8.ProjectCode/docs/diagrams/` as PNG (150 dpi, readable at
half width). Use **matplotlib** (no system dependency); use graphviz only if `dot` is already on PATH.

Required: system architecture · high-level workflow · DFD level 0, 1 and 2 · UML class diagram · sequence
diagram for the main flow · use-case diagram · ER diagram of the database · a flowchart of the core algorithm.

Each must reflect what the code actually does - read the models and routes first. A diagram that contradicts
the code is worse than no diagram.

---

## 4. Step 3 - the three decks

Work from the templates so the visual design is inherited:

```python
from pptx import Presentation
prs = Presentation(r"D:\abstracts\Templates\Review_2_PPT.pptx")   # then replace the text of each shape
```

Keep each deck's slide count and running order. Replace every text frame with this project's content, and put
your own diagrams and screenshots into the picture placeholders.

- **`7.Review_1_PPT.pptx`** (16): title · contents · abstract · base paper · literature survey · supporting
  evidence · existing system · limitations · research gap · problem statement · objectives · proposed approach ·
  architecture · expected outcomes · references · thank you.
- **`13.Review_2_PPT.pptx`** (20): recap · architecture · methodology · dataset · preprocessing · model ·
  training configuration · decision logic · data flow · database and UML · technology stack · implementation
  progress · preliminary results · **output screens** · testing · challenges · next steps · thank you.
- **`16.Final_PPT.pptx`** (28): the full story through to results, confusion matrix or equivalent, threshold or
  parameter analysis, performance and testing, comparison with the base paper, **three output-screen slides**,
  conclusion, future scope, references, thank you.

Title slides carry the real student names and roll numbers.

---

## 5. Step 4 - the chapter documents

Build with `python-docx`. Consistent formatting across all six: Times New Roman 12 for body, 14 bold for
headings, 1.5 line spacing, justified, numbered figures and tables with captions, page numbers.

- **9. Methodology, novelty and key contributions** - the full pipeline end to end, the algorithms and why they
  were chosen, what is genuinely new here against the base paper, and the contributions as a numbered list.
- **10. Scope and limitations** - what is in scope, what is out, assumptions, and honest limitations
  (dataset size, hardware, anything not implemented).
- **11. Block diagrams (all)** - every diagram from Step 2, each with a caption and a paragraph explaining it.
- **12. Design and implementation** - architecture, module breakdown, database schema, API design, key code
  walkthroughs, and the implementation decisions with their reasoning.
- **14. Results** - the real metrics with tables and charts, every output screen with a caption describing what
  it shows, success and failure cases, and objectives measured against outcomes.
- **15. Conclusion, future scope and references** - what was achieved, key findings, limitations, concrete future
  work, and a numbered IEEE-style reference list (base paper first, then the literature survey sources).

---

## 6. Step 5 - the full report (`17.Final Document.docx`)

The same 10-chapter structure as `Project_Report.pdf`, **~80-95 pages**:

Front matter: cover page · certificate · declaration · acknowledgement · abstract · table of contents · list of
figures · list of tables · list of abbreviations.

1. **Introduction** - domain, background and motivation, problem statement, need, objectives, scope,
   contributions, limitations and assumptions, organisation of the report
2. **Literature Survey** - overview, base paper analysis, related work (grouped by theme), datasets and
   algorithms used, strengths and limitations, research gap
3. **Feasibility Study** - technical, economic, operational, schedule, advantages and constraints
4. **System Requirements and Analysis** - existing system and its limitations, proposed system and its
   advantages, functional and non-functional requirements, hardware, software, user roles and constraints
5. **System Design** - architecture, high-level workflow, DFDs (0/1/2), UML diagrams, database design, module
   design, UI design
6. **Methodology and Software Implementation** - overall methodology, dataset, preprocessing, algorithm choice
   and justification, mathematical formulation, model architecture and training, application architecture, API
   design, security and error handling, installation and execution
7. **System Testing** - strategy, unit, integration, functional, security, validation and edge cases,
   performance, user acceptance, and the limits of the testing done
8. **Results and Output Screens** - every output screen with a caption, model performance, comparison with the
   base paper (state plainly where datasets differ), sample inputs and outputs, success and failure analysis,
   limitations, objectives versus outcomes
9. **Conclusion** - summary, objectives achieved, key findings, practical applications, known limitations
10. **Future Scope** - improvements, additional features, scalability and deployment, further research

Then **References** (IEEE numbered) and **Appendix A: Important Code**, **Appendix B: Installation and User
Guide**, **Appendix C: Additional Screens**.

Everything here must agree with the six chapter documents - reuse that text rather than writing a second,
slightly different version.

---

## 7. Step 6 - the IEEE paper (`19.IEEE_Paper.docx`)

Write this **after** the ten documents above are finished, and build it from `docs/REPORT_FACTS.md` plus the
figures you already produced - **do not re-read the 90-page report to do it**. It is a condensation, so nothing
in it may disagree with what you have just written.

**Format** (matched to the reference paper the owner supplied):

- US Letter 8.5 x 11 in; margins top 0.75 in, bottom 1.0 in, sides 0.69 in.
- **Two columns** (~3.4 in each, 0.25 in gap). Title and author block span the full width in a single-column
  section, then a continuous break switches the body to two columns:
  ```python
  from docx.oxml.ns import qn
  cols = section._sectPr.xpath('./w:cols')[0]
  cols.set(qn('w:num'), '2'); cols.set(qn('w:space'), '360')   # 360 twips = 0.25 in
  ```
- Times New Roman throughout: title **24 pt** centred; author block **9 pt**; abstract and index terms **9 pt**
  with *Abstract---* and *Index Terms---* in bold italic; body **10 pt** justified, first line indented 0.2 in;
  section headings **10 pt bold, centred, Roman numeral + ALL CAPS**; subsections *10 pt italic* (`A. System
  Hardware`); figure captions **8 pt below** the figure (`Fig. 1. ...`); table captions **8 pt above**
  (`TABLE I`); references **8 pt** with a hanging indent.
- Authors: a borderless table so they sit side by side - the four students, then the guide with their
  designation. Department, college, city and email as placeholders where unknown; **never invent an email**.

**Structure - five sections, as in the reference paper:**

1. **Title**, abstract (120-200 words, no citations), **Index Terms** (5-7, alphabetical).
2. **I. INTRODUCTION** (~0.8 page) - domain, how it is done today and what that costs, the gap, 3-4 numbered
   contributions, and the paper's organisation. With subsections *A. System Hardware* (the machine it was
   measured on) and *B. Software Requirements*.
3. **II. LITERATURE SURVEY** (~1.2 pages) - the base paper first in depth, then 6-10 related works grouped by
   theme, each cited `[n]`, closing on the research gap. Include **TABLE I** (Work / Approach / Data / Reported
   result / Limitation).
4. **III. METHODOLOGY** (~1.8 pages) - the real pipeline, data, algorithm and why it was chosen, the
   formulation this project actually uses, architecture and implementation. **Fig. 1** architecture,
   **Fig. 2** main flow.
5. **IV. RESULTS** (~1.5 pages) - **TABLE II** with the real metrics, **Fig. 3** a results chart, **Fig. 4-5**
   output screens. State the test conditions, compare with the base paper and **say plainly where datasets or
   conditions differ**. Include failure cases or observed limits.
6. **V. CONCLUSION** (~0.5 page) - achieved against objectives, key finding, honest limitations, and 3-4 lines
   of future scope (conclusion and future scope are merged, as in the reference).
7. **REFERENCES** - 15-20 IEEE-style entries, base paper first. Every entry cited, every citation listed.

**Length is a hard requirement: 6 pages** (5.5-6.5 acceptable). Build it, convert to PDF and count pages
(`docx2pdf`, Word COM, or `soffice --headless --convert-to pdf`). Over - tighten the prose; under - deepen
Methodology and Results. **Never change the font or margins to fit.** If no converter exists on this machine,
target **5,200-5,800 words** including captions and references, and say in your summary that you estimated.
Save a PDF alongside as `19.IEEE_Paper.pdf` when conversion is possible.

---

## 8. Step 7 - verify, then commit

Write `8.ProjectCode/scripts/verify_docs.py` and make it pass:

1. All ten files exist at the batch root with the exact names above, and none is under 40 KB (except where a
   deck legitimately is smaller).
2. **No template leftovers** - search every output for `[STUDENT NAME`, `[ROLL NO`, "Fakeddit", "PHEME",
   "Snopes", "MCNN", "bank transaction", "social media manipulation". Any hit is a failure.
3. Deck slide counts are 16 / 20 / 28.
4. `17.Final Document.docx` contains all ten chapter headings, the references section and three appendices.
5. Figures are embedded (count them) and every screenshot referenced actually exists.
6. Student names, roll numbers and the guide name from `1.*_BATCH_DETAILS.docx` appear on the title pages.
7. `19.IEEE_Paper.docx` opens cleanly, is two-column in the body, has five Roman-numbered sections, both
   tables, at least four captioned figures, 15-20 references, and lands at 6 pages (or the word target).
8. No leftovers from the reference paper the format was taken from - search for "skincare", "Dayananda",
   "Sindhu", "recommender system" - any hit is a failure.

Then commit from the batch folder: `git add -A .` and `git commit -m "Add project documentation" -- .`
(3-5 word message, no co-author lines, never a bare `git commit`), then `git push`.

Finish with a short summary: what you produced, the real metrics you used, anything you could not measure and
therefore stated as a gap.
