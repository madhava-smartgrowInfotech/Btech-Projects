"""Does the same contract give the same flags as DOCX and as PDF? (no API needed)

    venv\\Scripts\\python.exe scripts\\exp_format_parity.py

PDF text keeps the visual line breaks, and several rules use `.{0,N}` (which does not cross a newline) between
two key phrases. This script parses the sample contracts the way the upload route does, and again after
collapsing whitespace, and reports which rule ids are found in each case. It also compares the typeset CUAD
PDF with the original CUAD text. Writes experiments/parity/metrics.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services import parsing  # noqa: E402
from app.services.graph import detect_risky_combinations  # noqa: E402
from app.services.rules import detect_flags  # noqa: E402

S = ROOT / "docs" / "sample_inputs"


def analyse(pages, collapse=False):
    clauses = parsing.split_into_clauses(pages)
    found, per_clause = set(), []
    for c in clauses:
        text = " ".join(c["text"].split()) if collapse else c["text"]
        ids = [r.id for r in detect_flags(text)]
        found.update(ids)
        per_clause.append({"flags": ids})
    for i, pc in enumerate(per_clause):
        pc["id"] = i
    combos = [h["combo_id"] for h in detect_risky_combinations(per_clause)]
    return {"clauses": len(clauses), "rules": sorted(found), "n_rules": len(found), "combos": combos,
            "flagged_clauses": sum(1 for p in per_clause if p["flags"])}


def main():
    out = {}
    for name in ("freelance_services_agreement.docx", "freelance_services_agreement.pdf", "balanced_consulting_agreement.docx"):
        pages = parsing.extract_pages(str(S / name), "")
        out[name] = {"as_uploaded": analyse(pages), "whitespace_collapsed": analyse(pages, collapse=True)}

    data = json.loads((ROOT / "data/cuad/CUADv1.json").read_text(encoding="utf-8"))["data"]
    doc = next(x for x in data if x["title"].startswith("FUSIONPHARMACEUTICALSINC_06_05_2020-EX-10.17"))
    orig = [parsing.ParsedPage(doc["paragraphs"][0]["context"], 1)]
    pages = parsing.extract_pages(str(S / "supply_agreement_cuad.pdf"), "")
    out["supply_agreement: original CUAD text"] = {"as_uploaded": analyse(orig), "whitespace_collapsed": analyse(orig, collapse=True)}
    out["supply_agreement_cuad.pdf"] = {"as_uploaded": analyse(pages), "whitespace_collapsed": analyse(pages, collapse=True)}

    # a clause that runs across a page break is cut in two by the per-page splitter
    pdf_pages = parsing.extract_pages(str(S / "freelance_services_agreement.pdf"), "")
    out["page_break"] = {"pages": len(pdf_pages), "clauses_from_pdf": len(parsing.split_into_clauses(pdf_pages)),
                         "clauses_from_docx": len(parsing.split_into_clauses(parsing.extract_pages(str(S / "freelance_services_agreement.docx"), "")))}
    (ROOT / "experiments" / "parity").mkdir(parents=True, exist_ok=True)
    (ROOT / "experiments" / "parity" / "metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k, v in out.items():
        print(k, json.dumps(v)[:400])


if __name__ == "__main__":
    main()
