import { Link } from "react-router-dom";
import { FileWarning, GitGraph, Gauge, FileText } from "lucide-react";
import { useAuth } from "../AuthContext.jsx";

const FEATURES = [
  {
    icon: FileText,
    title: "Upload & segment",
    desc: "Upload a PDF or DOCX contract - ClauseGuard splits it into clauses with page numbers and classifies each one.",
  },
  {
    icon: FileWarning,
    title: "Predatory clause detection",
    desc: "Flags restraint of trade, penalty clauses, unilateral termination, unlimited liability, one-sided arbitration, auto-renewal and IP overreach against Indian contract law.",
  },
  {
    icon: GitGraph,
    title: "Risky combinations",
    desc: "A clause graph surfaces combinations that are harmless alone but dangerous together, like unilateral termination plus no-refund plus penalty.",
  },
  {
    icon: Gauge,
    title: "Complexity grade",
    desc: "Readability, legalese density, cross-references and length combine into a plain A-F grade with a summary and safer wording for every flag.",
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div>
      <section className="py-14 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">
          Know what you're signing.
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          ClauseGuard scores contract complexity and flags predatory clauses in plain language,
          built for Indian agreements - freelancers, small businesses and legal-ops teams.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link
            to={isAuthenticated ? "/upload" : "/register"}
            className="rounded-md bg-brand-600 px-6 py-3 font-medium text-white hover:bg-brand-700"
          >
            {isAuthenticated ? "Upload a contract" : "Get started"}
          </Link>
          <Link
            to="/evaluation"
            className="rounded-md border border-slate-300 px-6 py-3 font-medium text-slate-700 hover:bg-slate-100"
          >
            See evaluation results
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 py-8 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-lg border border-slate-200 bg-white p-5">
            <f.icon className="h-8 w-8 text-brand-600" />
            <h3 className="mt-3 font-semibold text-slate-900">{f.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
