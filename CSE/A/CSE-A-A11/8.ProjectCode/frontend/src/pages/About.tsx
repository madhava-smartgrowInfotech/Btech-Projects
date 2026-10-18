import { AlertTriangle, BookMarked, Terminal } from "lucide-react";

import { CodeBlock } from "@/components/app/CodeBlock";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/Layout";
import { Table, type Column } from "@/components/ui/Table";

const PAPER_TO_PRODUCT = [
  ["Predict vulnerability from source-code metrics", "ML Risk Agent scores every changed function inside the PR (paper's gap: it was offline only)"],
  ["14 metrics from a code property graph", "14 metric families computed from the Python AST/CFG (same numbering for the top metrics M1, M5, M6, M7, M9, M11)"],
  ["7 feature-selection methods + consensus", "Implemented (Pearson, SVM, Lasso, Chi², RFE-LR, RFE-RF, Variance); k validated on held-out data"],
  ["SmoteTomek + Min-Max", "Own SMOTE + Tomek-link implementation, no external imbalance library"],
  ["9 models, Random Forest best", "RF, DT, LR, SVM, KNN, NB, GB, XGBoost, soft-voting ensemble"],
  ["Vulnerability-type classification", "Random-forest type classifier over 8 types; static rules give exact CWE"],
  ["(extension) explain + fix", "Security Reasoner and Remediation agents explain flow/impact and generate re-scan-verified patches"],
  ["(extension) codebase intelligence", "Graph-based retrieval assistant with route, auth and UI discovery"],
].map(([paper, product]) => ({ paper, product }));

const LIMITS = [
  <>The ML model is trained on a <strong>generated</strong> Python corpus, not the paper&apos;s C datasets (which are not distributable here); treat its scores as a <em>prioritisation signal</em>, not proof.</>,
  <>Deep taint analysis covers <strong>Python</strong> (intra-function). JavaScript/PHP/Java use pattern rules only.</>,
  <>Without an API key the “reasoning” agents are deterministic knowledge-base agents; with a key, explanations for the top findings are written by Claude.</>,
  <>Auto-fixes cover a curated set (SQL parameterisation, shell → argv list, <code className="font-mono text-xs">yaml.safe_load</code>, hash upgrade, TLS verify, debug flag, <code className="font-mono text-xs">is None</code>).</>,
];

const cols: Column<(typeof PAPER_TO_PRODUCT)[number]>[] = [
  { key: "paper", header: "Paper contribution", cell: (r) => <span className="font-medium">{r.paper}</span> },
  { key: "product", header: "Where it lives in AutoSecAI", cell: (r) => <span className="text-muted-foreground">{r.product}</span> },
];

export default function About() {
  return (
    <div className="space-y-8">
      <PageHeader eyebrow="About" title="About AutoSecAI" />

      <Card>
        <CardBody className="space-y-4 text-sm leading-relaxed">
          <p>
            <strong>Project:</strong> AutoSecAI - Autonomous Pull Request Analysis for Security, Vulnerability Detection and Code Quality using Multi-Agent LLMs · CSE-A · Batch 11
          </p>
          <p>
            <strong>Abstract (implemented).</strong> Modern teams merge pull requests too fast for manual security review, and new developers struggle to find their way
            around large codebases. AutoSecAI extracts the files changed by a PR, runs static analysis, reasons over the findings with cooperating agents to produce explanations,
            impact and safe remediation - and offers a natural-language codebase assistant.
          </p>
          <p>
            <strong>Base paper.</strong> <em>Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With Machine Learning</em>, Abbasi &amp; Shameli-Sendi, IEEE Access
            2026, DOI 10.1109/ACCESS.2026.3679930.
          </p>
        </CardBody>
      </Card>

      <section className="space-y-3">
        <h2 className="flex items-center gap-2 font-display text-xl font-semibold"><BookMarked className="size-5 text-violet-ink" /> From paper to product</h2>
        <Table columns={cols} rows={PAPER_TO_PRODUCT} rowKey={(r) => r.paper} pageSize={8} caption="From paper to product" />
      </section>

      <Card>
        <CardHeader title="Known limitations" icon={<AlertTriangle />} />
        <CardBody>
          <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed">
            {LIMITS.map((l, i) => <li key={i}>{l}</li>)}
          </ul>
        </CardBody>
      </Card>

      <section className="space-y-3">
        <h2 className="flex items-center gap-2 font-display text-xl font-semibold"><Terminal className="size-5 text-violet-ink" /> Run locally</h2>
        <CodeBlock code={"run.bat                    # API on 8311 + this app on 5311\npython -m pytest tests -q   # engine tests\npython scripts/smoke_test.py  # API smoke test (API running)"} language="bash" label="Windows" />
      </section>
    </div>
  );
}
