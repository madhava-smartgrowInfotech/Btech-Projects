# User guide

A screen-by-screen walkthrough of PolicyLens. Start it with `run.bat` and open http://localhost:5101.

---

## 1. Landing page

The public home page explains what PolicyLens does, shows an example answer taken from a sample policy, walks through **How it works** as you scroll, and lists the features.

- **Get started** - create an account.
- **Try the demo** / **Sign in** - log in (demo: `demo@policylens.app` / `Demo@12345`).

## 2. Sign in and create an account

- **Create account:** your name, email and a password with at least 8 characters including a letter and a number. You are taken to **My policies**.
- **Sign in:** email and password. **Fill demo login** fills in the demo account.
- Sessions last 24 hours. Use the menu at the top right (your initials) to open **Settings** or **Sign out**.

## 3. Dashboard

Your activity at a glance:

- **KPI tiles:** policies (and how many are ready), questions asked, average faithfulness of answers, median answer time, claim checks and comparisons, and high-severity risks across your policies.
- **Charts:** activity over the last 14 days, how answers are distributed across faithfulness bands, risk highlights per policy by severity, response time of recent answers, and Claim Copilot verdicts. Every chart has a **table** button (grid icon) that shows the same numbers as a table.
- **Recent activity:** your latest uploads, conversations and claim checks - click to open.
- New accounts see a **Get started in three steps** card.

## 4. My policies

- **Upload policy:** drag a PDF onto the box or click to browse (text PDFs up to 25 MB). Give it a name and click **Upload and analyse**.
- Each policy tile shows live processing - *Read PDF -> Build search index -> Policy Card & risk highlights -> Ready* - usually under two minutes.
- When ready, the tile shows the sum insured, waiting periods, co-payment, risk counts and the number of clauses.
- **Sample policies** adds four real Indian policy wordings to your library (labelled *Sample*).
- **⋮ -> Remove** deletes a policy with its conversations and claim checks (you are asked to confirm).

## 5. Policy view

Open a policy from **My policies**. The header shows the UIN, pages and clause count, with buttons to open the **Original PDF**, **Check a claim** and **Ask this policy**.

### Policy Card tab
- **Summary:** what the policy is, who it suits, what to watch out for and recommended next steps.
- **Waiting periods:** initial, pre-existing diseases, specific diseases/procedures and maternity, plus the conditions named on the specific-disease list.
- **Cover and limits:** sum insured, deductible, co-payment, room rent, ICU, pre/post-hospitalisation, day care, ambulance, restoration, no-claim bonus, AYUSH, modern treatments, maternity, free-look, grace and moratorium periods.
- **Lists:** conditional co-payments, sub-limits, key exclusions and claim deadlines.
- Every value has a source chip such as **Clause Excl02 · p. 28**. A green tick means the value's quote was found word-for-word in the policy; an amber warning means it could not be matched - check the page. Click the chip to open the page with the clause highlighted.
- **Display language:** choose हिन्दी or తెలుగు to read the card in that language (quotes stay in English).
- **Re-run AI extraction** reads the policy again (one AI request).

### Risks tab
Gotchas sorted by severity - **High**, **Medium**, **Low** - with filter buttons. Each shows whether it came from a **Rule check** (calculated from the extracted numbers) or an **AI finding**, why it matters, the quote and the page.

### Document tab
The PDF page as an image with the selected clause highlighted in amber.
- Navigate with the arrows or type a page number; zoom with − / +.
- **Click any paragraph** to see which clause it belongs to; the side panel shows the full clause text and lists every clause on the page (hover to preview its highlight).
- **Original PDF** opens the untouched file in your browser's PDF viewer.

### Clause search tab
Search the policy the same way answers are grounded. Choose the method - **Hybrid + re-rank** (default), **Hybrid (RRF)**, **Keyword (BM25)** or **Semantic (embeddings)** - to see how each ranks clauses. Every result shows its keyword rank, semantic rank and re-rank relevance.

## 6. Ask your policy (chat)

1. **New conversation** -> choose a ready policy.
2. Type a question (Enter to send, Shift+Enter for a new line) or pick a suggestion.
3. While it works you see the steps: searching clauses, reading them, writing a cited answer, checking faithfulness.

Each answer shows:
- **Numbered citation chips** in the text - click one to open a side panel with the page image, the clause highlighted and the quoted sentence; **Open in document viewer** jumps to the full viewer.
- **Sources** - the clauses used, with pages.
- A **Faithfulness** badge (0-100) - click it for the support score of each statement. *Well supported* ≥ 80, *partly* 50-79, *weakly* < 50.
- A **"Not covered in this policy document"** label when the policy does not address the question.
- Answer time, the model that answered, and follow-up suggestions.
- For Hindi/Telugu answers, **Show in English** toggles the English version.

The **language menu** at the top right sets the answer language for your next questions. Conversations are listed on the left (a drawer on phones); hover to delete one.

## 7. Claim Copilot

A four-step wizard:
1. **Policy** - which policy you will claim under.
2. **Treatment** - e.g. "Knee replacement" (quick picks available) and the type of admission.
3. **Details** (all optional but they make the result more precise) - cashless or reimbursement, first policy start date, patient age, estimated bill, room type, whether the condition existed before the policy, notes.
4. **Review** - check the details, choose the answer language, **Check my claim**.

The result shows:
- **Verdict** - *Covered*, *Partly covered*, *Not covered* or *Needs more information* - with a short explanation and faithfulness score.
- **Why** - reasons, each linked to its clause.
- **Eligibility pre-checks** - *Calculated* checks from the Policy Card (months of cover versus each waiting period, which co-payment applies at this age) and checks from the policy text. ✓ pass, ✗ fails, ⚠ check, ? unknown.
- **Cost picture** - with an estimated bill: what the insurer may pay and what you may pay after deductible, co-payment and sub-limits, plus cost notes.
- **Document checklist** - tick items as you collect them; progress is saved.
- **Claim steps** - numbered steps with timelines and clause links.

Previous checks are listed on the right.

## 8. Compare plans

Choose **Policy A** and **Policy B** (both need a Policy Card), optionally swap them or pick the language, and click **Compare**.

- **Overview** with *Choose A if…* / *Choose B if…* and each policy's risk counts.
- **Side by side** table of cover, limits and waiting periods; a green tick marks the better value where the direction is clear (for example the shorter waiting period). Source chips open the page.
- **Trade-offs** - the most important differences, each with which policy is better and why, and the clauses from both policies.
- **Recommended next steps.** Saved comparisons are listed on the right.

## 9. Model performance

Measured quality of PolicyLens on the evaluation set built from the sample policies: retrieval accuracy of each search method, answer and citation accuracy, faithfulness, abstention, response time by stage, Policy Card extraction accuracy by field, the Claim Copilot confusion matrix, the models used and the saved plots. See [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md).

## 10. Settings

- **Answer language:** English, हिन्दी or తెలుగు - used for chat, Claim Copilot, comparisons and translated Policy Cards.
- **Appearance:** Light, Dark or System.
- **Account:** change your name or password.

---

## Tips

- Ask one thing at a time; name the treatment or benefit ("Is cataract covered?", "What is the room rent limit?").
- For waiting-period questions in Claim Copilot, enter the start date of your **first** policy with the insurer - continuous renewals count.
- The policy **schedule** (your personal sum insured and options) is a separate document; answers mention when the schedule decides.
- PolicyLens explains your policy wording; the insurer makes the final claim decision.
