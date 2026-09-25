import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileText } from "lucide-react";
import { contractsApi, getErrorMessage } from "../api.js";
import { ErrorState } from "../components/StatusStates.jsx";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const navigate = useNavigate();

  function handleFileChange(e) {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  }

  function handleDrop(e) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  async function handleUpload() {
    if (!file) return;
    setError("");
    setUploading(true);
    setProgress(0);
    try {
      const res = await contractsApi.upload(file, (evt) => {
        if (evt.total) setProgress(Math.round((evt.loaded / evt.total) * 100));
      });
      navigate(`/contracts/${res.data.id}`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl py-8">
      <h1 className="text-2xl font-semibold text-slate-900">Upload a contract</h1>
      <p className="mt-1 text-sm text-slate-600">PDF or DOCX. ClauseGuard will split it into clauses, classify each one, flag predatory terms, and score its complexity.</p>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-white px-6 py-14 text-center hover:border-brand-400"
      >
        <UploadCloud className="h-10 w-10 text-slate-400" />
        {file ? (
          <div className="mt-3 flex items-center gap-2 text-slate-700">
            <FileText className="h-4 w-4" /> {file.name}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">Drag and drop a file here, or click to browse.</p>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {error && <div className="mt-4"><ErrorState message={error} /></div>}

      {uploading && (
        <div className="mt-4">
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div className="h-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-2 text-center text-sm text-slate-500">
            Uploading and analyzing - this calls the real Gemini pipeline and can take a minute for longer contracts.
          </p>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-6 w-full rounded-md bg-brand-600 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
      >
        {uploading ? "Analyzing..." : "Analyze contract"}
      </button>
    </div>
  );
}
