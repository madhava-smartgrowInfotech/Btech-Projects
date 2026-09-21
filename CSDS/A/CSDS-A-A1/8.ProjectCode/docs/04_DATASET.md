# Data and datasets

PolicyLens needs no training data: it works on whatever policy wording a user uploads. The repository ships two kinds of data - **sample policy wordings** that make the product usable immediately, and an **evaluation set** written from them to measure quality. Everything is small (about 4.7 MB), so the **complete data is committed**; there is nothing to download and no Kaggle dataset is used.

---

## 1. Sample policy wordings - `data/policies/`

Four publicly published health-insurance policy wordings from Indian insurers, downloaded from each insurer's official website and stored unmodified.

| File | Product | Insurer | UIN | Pages | Size | Official source |
|---|---|---|---|---|---|---|
| `star-health-family-health-optima.pdf` | Family Health Optima Insurance Plan | Star Health and Allied Insurance Co. Ltd | SHAHLIP26046V092526 | 44 | 1.2 MB | [starhealth.in (policy wording PDF)](https://d28c6jni2fmamz.cloudfront.net/Policy_Family_Health_Optima_Insurance_Plan_V_21_bbe089bd74.pdf) |
| `hdfc-ergo-optima-secure.pdf` | my: Optima Secure | HDFC ERGO General Insurance Co. Ltd | HDFHLIP25041V062425 | 53 | 0.6 MB | [hdfcergo.com (policy wording PDF)](https://www.hdfcergo.com/docs/default-source/downloads/policy-wordings/health/optima-secure-revision-pw.pdf) |
| `niva-bupa-reassure-2.pdf` | ReAssure 2.0 | Niva Bupa Health Insurance Co. Ltd | NBHHLIP23169V012223 | 24 | 0.3 MB | [nivabupa.com (policy wording PDF)](https://www.nivabupa.com/content/dam/nivabupa/PDF/reassure-2-0/ReAssure%202.0%20-%20Policy%20Wording.pdf) |
| `care-health-care-supreme.pdf` | Care Supreme | Care Health Insurance Ltd | CHIHLIP23128V012223 | 45 | 1.7 MB | [careinsurance.com (terms and conditions PDF)](https://cms.careinsurance.com/cms/public/uploads/download_center/care-supreme---policy-terms-and-conditions.pdf) |

**Licence and use.** Policy wordings are public documents that Indian insurers must publish for prospective customers. The copyright belongs to the respective insurers. They are included unchanged, only as sample input for demonstrating and testing the product; PolicyLens is not affiliated with these insurers, and the files carry no endorsement. Remove them (and `data/processed/`) if your use requires it - the app works with any uploaded wording.

**Why these four.** They cover the layouts a real product meets: a two-column A4 layout with letter-spaced headings (Star Health), a small-page two-column layout with separately printed clause numbers (Care Supreme), a single-column layout with `Def. N` numbering and ruled tables (HDFC ERGO) and a single-column layout with multi-level numbering (Niva Bupa). All four cover the demo topics - cataract, joint replacement, waiting periods, co-payment and room rent.

### How to add more sample policies

1. Open the insurer's website and search for the plan name; policy wordings are usually under **Downloads -> Policy Wordings** or on the product page ("Policy wording", "Terms and conditions").
2. Download the PDF - it must contain selectable text (try selecting a sentence in your PDF viewer; scanned images are rejected).
3. Save it in `data/policies/` with a short lower-case name, e.g. `insurer-product.pdf`.
4. With the app stopped, run `venv\Scripts\python scripts\process_samples.py` - it parses, indexes and extracts the Policy Card (one Gemini request) and writes `data/processed/<name>/`.
5. Start the app; the new sample appears for the demo account and under **My policies -> Sample policies**.

---

## 2. Processed samples - `data/processed/<name>/`

Produced by `scripts/process_samples.py` with the product's own pipeline, and committed so that a fresh install shows complete sample policies **without any AI requests**.

| File | Contents |
|---|---|
| `document.json` | File name and path, SHA-256, size, pages, insurer, product, UIN, parse statistics (pages, words, clauses, two-column, headers removed, page sizes, parse time) |
| `clauses.jsonl` | One clause per line: `ordinal`, `clause_ref` (e.g. `Excl02`, `4.2.1`, `Def. 5`), `heading`, `section_path`, `text`, `page_start`, `page_end`, `bboxes` (highlight rectangles in PDF points), `word_count` |
| `card.json` | Policy Card (`data`), summary, the Gemini model that produced it, prompt version, share of values verified in the text, and the risk highlights |

Totals: 790 clauses across 166 pages; 772 KB.

`setup.bat` (through `scripts/init_app.py`) loads these into the database and builds the vector index locally.

---

## 3. Evaluation set - `data/eval/`

Written by hand from the four sample wordings. Every expected answer was checked against the PDF; evidence snippets are copied verbatim from the policy text.

### `qa.jsonl` - 57 questions (51 answerable, 6 not answerable)

| Field | Meaning |
|---|---|
| `id` | e.g. `star-02` |
| `policy` | sample name (folder in `data/processed/`) |
| `category` | `waiting_period`, `benefit`, `sub_limit`, `room_rent`, `claim_process`, `exclusion`, `policy_terms`, `out_of_scope` |
| `question` | as a policyholder would ask it |
| `answerable` | `false` for questions the policy does not address (e.g. "Does this policy insure my house against fire?") |
| `evidence` | verbatim snippets from the supporting clause(s) - used to judge retrieval and citations independently of how the parser splits chunks |
| `pages` | page numbers of the supporting text |
| `key_facts` | facts the answer must contain, each a list of accepted variants, e.g. `[["24 months", "2 years"]]` |
| `expected_answer` | reference answer in plain English |

Questions per policy: Star Health 14, HDFC ERGO 13, Niva Bupa 12, Care Supreme 12, plus 6 out-of-scope questions.

### `qa_multilingual.jsonl` - 5 questions

The same format plus `language` (`hi` or `te`): questions asked in Hindi or Telugu (and one English question answered in Hindi). Used to check that answers come back in the requested script and still contain the key facts.

### `claims.jsonl` - 14 Claim Copilot scenarios

`treatment`, `inputs` (admission type, claim mode, `policy_start_date_months_ago`, age, pre-existing condition, estimated cost) and `expected_verdict` (`covered` 5, `partly_covered` 1, `not_covered` 7, `needs_info` 1) with the reason, e.g. knee replacement with 6 months of cover -> not covered (24-month waiting period).

### `cards.json` - 52 hand-checked Policy Card values

For each sample: UIN, insurer, waiting periods (initial, pre-existing, specific diseases), pre/post-hospitalisation days, free-look period, room rent, cumulative bonus, claim deadlines and whether cataract is on the specific-disease list. Check types: `exact`, `text` (contains), `months` / `days` / `hours` (numeric after unit conversion) and `list`.

**Split.** There is no training, so the whole set is a held-out test set used only for evaluation. See [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md).

---

## 4. Generated data

`backend/tests/fixtures.py` generates a small **synthetic** two-page policy wording ("Test Health Insurance Ltd") used by the automated tests. It is deterministic - the same code always produces the same PDF - so tests are repeatable. It is never shown in the product.

## 5. What is not committed

User uploads (`data/uploads/`), the database (`data/app.db`), the vector index (`data/chroma/`), rendered page images (`data/pages/`) and the AI response cache (`data/cache/`) are created at run time on each machine and are listed in `.gitignore`.
