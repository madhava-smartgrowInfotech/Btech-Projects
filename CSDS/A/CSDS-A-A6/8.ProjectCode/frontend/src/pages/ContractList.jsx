import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Plus } from "lucide-react";
import { contractsApi, getErrorMessage } from "../api.js";
import { LoadingState, ErrorState } from "../components/StatusStates.jsx";
import { GradeBadge } from "../components/Badges.jsx";

export default function ContractList() {
  const [contracts, setContracts] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    setContracts(null);
    contractsApi
      .list()
      .then((res) => setContracts(res.data))
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(load, []);

  return (
    <div className="py-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">My contracts</h1>
        <Link
          to="/upload"
          className="flex items-center gap-1 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <Plus className="h-4 w-4" /> Upload
        </Link>
      </div>

      {error && <div className="mt-6"><ErrorState message={error} onRetry={load} /></div>}
      {!error && contracts === null && <LoadingState label="Loading contracts..." />}

      {contracts && contracts.length === 0 && (
        <p className="mt-8 text-center text-slate-500">No contracts yet. Upload one to get started.</p>
      )}

      {contracts && contracts.length > 0 && (
        <div className="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {contracts.map((c) => (
            <Link
              key={c.id}
              to={`/contracts/${c.id}`}
              className="flex items-center justify-between px-4 py-4 hover:bg-slate-50"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="font-medium text-slate-900">{c.filename}</p>
                  <p className="text-xs text-slate-500">
                    {new Date(c.uploaded_at).toLocaleString()} - {c.flag_count} flag(s)
                  </p>
                </div>
              </div>
              <GradeBadge grade={c.complexity_grade} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
