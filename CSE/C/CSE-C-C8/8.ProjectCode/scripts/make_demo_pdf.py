"""PeerScope demo-paper fixture generator (reportlab; clearly demo data)."""
from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "data" / "demo" / "demo_paper.pdf"

TITLE = "Efficient Retrieval-Grounded Text Classification with Lightweight Transformers"
BODY = [
    ("Summary", "This paper studies efficient text classification with lightweight transformer models augmented by retrieval grounding. "
     "We describe a compact architecture, training procedure, and evaluation on two public benchmarks. "
     "Results show accuracy gains over a non-retrieval baseline with modest latency overhead. Limitations and future work are discussed."),
    ("1 Introduction", "Text classification remains a core task in language processing. Large models are accurate but costly to deploy. "
     "This work investigates whether a small transformer combined with a retrieval component can close the gap. "
     "Our contribution is a lightweight architecture, a training recipe, and an empirical comparison against baselines."),
    ("2 Related Work", "Prior work explores efficient transformers, distillation, and retrieval augmentation for knowledge tasks. "
     "We build on these directions and compare directly with strong baselines on shared benchmarks."),
    ("3 Method", "Our model uses a 6-layer transformer encoder with hidden size 384. A retriever selects top-3 passages from a fixed index; "
     "embeddings are concatenated with the input representation before classification. Training uses cross-entropy loss, AdamW, "
     "learning rate 3e-5, batch size 64, 5 epochs, seeds 1-3. Data splits are fixed and documented."),
    ("4 Experiments", "We evaluate on two public text-classification benchmarks with accuracy and macro-F1. Baselines include a linear model, "
     "a small transformer without retrieval, and a larger reference model. Each experiment is repeated with three seeds; we report means and standard deviations."),
    ("5 Results", "The retrieval-grounded small model improves accuracy by 2.1 points and macro-F1 by 1.8 points over the non-retrieval baseline. "
     "Latency increases by 12% on CPU. Ablations show retrieval depth and encoder size both matter. Error analysis highlights long-tail classes."),
    ("6 Discussion", "Gains are consistent but modest; retrieval quality bounds performance. Failure cases involve ambiguous labels and stale index entries. "
     "We discuss threats to validity including benchmark choice and hardware differences."),
    ("7 Conclusion", "Lightweight transformers with retrieval grounding offer a practical accuracy-efficiency trade-off. "
     "Future work includes index refresh strategies and broader language coverage."),
    ("References", "[1] Benchmark Author. Public text benchmark, 2023.\n[2] Efficient Models Author. Compact transformers, 2022.\n"
     "[3] Retrieval Methods Author. Retrieval for language tasks, 2023.\n[4] Evaluation Practice Author. Reliable evaluation, 2021.\n"
     "[5] Optimization Author. AdamW optimizer, 2019.\n[6] Statistics Author. Reporting with standard deviations, 2020.\n"
     "[7] Distillation Author. Knowledge distillation, 2021.\n[8] Indexing Author. Passage indexing, 2022."),
]


def main() -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    story = [Paragraph(TITLE, styles["Title"]), Spacer(1, 12),
             Paragraph("Demo fixture — generated locally for PeerScope workflow demonstration only.", styles["Normal"]),
             Spacer(1, 12)]
    for head, text in BODY:
        story += [Paragraph(head, styles["Heading2"]), Paragraph(text, styles["BodyText"]), Spacer(1, 8)]
    story.append(PageBreak())
    story += [Paragraph("Appendix: Reproducibility Notes", styles["Heading2"]),
              Paragraph("Code and data splits are described in Section 3-4. Hyperparameters, seeds, and compute environment "
                        "(single CPU workstation) are documented. Results tables report means with standard deviations.", styles["BodyText"])]
    SimpleDocTemplate(str(OUT), pagesize=A4).build(story)
    print(f"Demo paper written -> {OUT}")


if __name__ == "__main__":
    main()
