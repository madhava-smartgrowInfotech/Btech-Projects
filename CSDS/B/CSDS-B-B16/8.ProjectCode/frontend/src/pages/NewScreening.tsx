import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, UserPlus, Users } from "lucide-react";
import { toast } from "sonner";

import { AlertBox } from "@/components/app/AlertBox";
import { ClinicalForm } from "@/components/app/ClinicalForm";
import { Disclaimer } from "@/components/app/Disclaimer";
import { PageHeader } from "@/components/ui/Layout";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input } from "@/components/ui/Field";
import { FileDrop } from "@/components/ui/FileDrop";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { Segmented } from "@/components/ui/Toggles";
import { Select } from "@/components/ui/Select";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { api, errorMessage } from "@/lib/api";
import { clinicalPayload, EMPTY_CLINICAL, type ClinicalValues } from "@/lib/clinical";
import { keys } from "@/lib/queries";
import type { PatientSummary, Sample, ScreeningFull } from "@/lib/types";
import { cn } from "@/lib/utils";

const MAX_IMAGE_BYTES = 15 * 1024 * 1024;

function validateImage(file: File): string | null {
  const typeOk = file.type === "image/png" || file.type === "image/jpeg" || /\.(png|jpe?g)$/i.test(file.name);
  if (!typeOk) return "Use a PNG or JPG image.";
  if (file.size === 0) return "That file is empty. Choose another image.";
  if (file.size > MAX_IMAGE_BYTES) return "That image is larger than 15 MB. Choose a smaller file.";
  return null;
}

type PatientMode = "existing" | "new";
type NewPatient = { name: string; age: string; sex: string; code: string };

export default function NewScreening() {
  useBreadcrumb(null);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const queryClient = useQueryClient();

  const patientsQuery = useQuery({
    queryKey: keys.patients(""),
    queryFn: async () => (await api.get<PatientSummary[]>("/patients")).data,
  });
  const samplesQuery = useQuery({
    queryKey: keys.samples,
    queryFn: async () => (await api.get<Sample[]>("/samples")).data,
    staleTime: Infinity,
  });

  const [mode, setMode] = useState<PatientMode>("existing");
  const [patientId, setPatientId] = useState(params.get("patient") ?? "");
  const [newPatient, setNewPatient] = useState<NewPatient>({ name: "", age: "", sex: "Male", code: "" });
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [sampleName, setSampleName] = useState<string | null>(null);
  const [sampleBusy, setSampleBusy] = useState<string | null>(null);
  const [eye, setEye] = useState<"Right" | "Left">("Right");
  const [clinical, setClinical] = useState<ClinicalValues>(EMPTY_CLINICAL);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  // No patients yet: start on the "new patient" form.
  useEffect(() => {
    if (patientsQuery.data && patientsQuery.data.length === 0) setMode("new");
  }, [patientsQuery.data]);

  // Age and sex from the chosen patient fill the clinical form (the user can still change them).
  useEffect(() => {
    if (mode === "existing") {
      const p = patientsQuery.data?.find((x) => String(x.id) === patientId);
      if (p) setClinical((c) => ({ ...c, age: p.age, sex: p.sex === "Female" ? 0 : 1 }));
    } else if (newPatient.age) {
      setClinical((c) => ({ ...c, age: Number(newPatient.age), sex: newPatient.sex === "Female" ? 0 : 1 }));
    }
  }, [mode, patientId, patientsQuery.data, newPatient.age, newPatient.sex]);

  // Object URL for the chosen image; revoked when the file changes or the page closes.
  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function pickSample(sample: Sample) {
    setError("");
    setSampleBusy(sample.name);
    try {
      const { data } = await api.get<Blob>(`/samples/${sample.name}`, { responseType: "blob" });
      setFile(new File([data], sample.name, { type: data.type || "image/png" }));
      setSampleName(sample.name);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSampleBusy(null);
    }
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    if (!file) {
      setError("Choose a fundus image first: upload one or pick a sample.");
      return;
    }
    let payload: ReturnType<typeof clinicalPayload>;
    try {
      payload = clinicalPayload(clinical);
    } catch (err) {
      setError(errorMessage(err));
      return;
    }

    let screeningId: number | null = null;
    try {
      let pid = patientId;
      if (mode === "new") {
        setBusy("Registering patient…");
        const { data } = await api.post<PatientSummary>("/patients", {
          name: newPatient.name,
          age: Number(newPatient.age),
          sex: newPatient.sex,
          code: newPatient.code || null,
        });
        pid = String(data.id);
        queryClient.invalidateQueries({ queryKey: ["patients"] });
      }
      if (!pid) {
        setError("Select a patient, or add a new one.");
        return;
      }

      setBusy("Analysing the fundus image…");
      const form = new FormData();
      form.append("patient_id", pid);
      form.append("eye", eye);
      form.append("file", file);
      const { data: screening } = await api.post<ScreeningFull>("/screenings/image", form);
      screeningId = screening.id;

      setBusy("Scoring heart-disease risk…");
      await api.post<ScreeningFull>(`/screenings/${screeningId}/clinical`, payload);
      queryClient.invalidateQueries({ queryKey: ["screenings"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      toast.success(`Screening #${screeningId} saved`);
      navigate(`/screenings/${screeningId}`);
    } catch (err) {
      if (screeningId) {
        // The image is stored; show the result and say what is missing.
        queryClient.invalidateQueries({ queryKey: ["screenings"] });
        navigate(`/screenings/${screeningId}`, { state: { clinicalError: errorMessage(err) } });
      } else {
        setError(errorMessage(err));
      }
    } finally {
      setBusy("");
    }
  }

  if (patientsQuery.isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading patients">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-48 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }
  if (patientsQuery.isError) {
    return (
      <ErrorState
        error={patientsQuery.error}
        title="Couldn't load patients"
        hint="Make sure the RetinaGuard API is running, then try again."
        onRetry={() => patientsQuery.refetch()}
      />
    );
  }

  const patients = patientsQuery.data;
  const samples = samplesQuery.data ?? [];

  return (
    <form onSubmit={submit} className="space-y-6">
      <PageHeader
        title="New screening"
        description="One fundus image and the clinical profile for one patient. The result opens when the analysis finishes."
      />

      <Card className="space-y-5 p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-lg font-semibold">1. Patient</h2>
          <Segmented<PatientMode>
            label="Patient"
            value={mode}
            onChange={setMode}
            options={[
              { value: "existing", label: "Existing patient", icon: <Users /> },
              { value: "new", label: "New patient", icon: <UserPlus /> },
            ]}
          />
        </div>

        {mode === "existing" ? (
          patients.length === 0 ? (
            <p className="text-sm text-muted-foreground">No patients yet. Switch to “New patient” to register one.</p>
          ) : (
            <FormField label="Choose a patient" id="patient-select">
              {({ id, ...aria }) => (
                <Select
                  id={id}
                  aria-label="Choose a patient"
                  aria-describedby={aria["aria-describedby"]}
                  value={patientId}
                  onValueChange={setPatientId}
                  placeholder="Select a patient…"
                  options={patients.map((p) => ({
                    value: String(p.id),
                    label: `${p.name} · ${p.code}`,
                    description: `${p.age} years, ${p.sex}`,
                  }))}
                />
              )}
            </FormField>
          )
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <FormField label="Full name" id="new-name" className="sm:col-span-2">
              {({ id, ...aria }) => (
                <Input
                  id={id}
                  {...aria}
                  autoComplete="off"
                  required
                  maxLength={120}
                  value={newPatient.name}
                  onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })}
                />
              )}
            </FormField>
            <FormField label="Age" id="new-age">
              {({ id, ...aria }) => (
                <Input
                  id={id}
                  {...aria}
                  type="number"
                  min={1}
                  max={120}
                  required
                  inputMode="numeric"
                  value={newPatient.age}
                  onChange={(e) => setNewPatient({ ...newPatient, age: e.target.value })}
                />
              )}
            </FormField>
            <FormField label="Sex" id="new-sex">
              {({ id, ...aria }) => (
                <Select
                  id={id}
                  aria-label="Sex"
                  aria-describedby={aria["aria-describedby"]}
                  value={newPatient.sex}
                  onValueChange={(v) => setNewPatient({ ...newPatient, sex: v })}
                  options={["Male", "Female", "Other"].map((s) => ({ value: s, label: s }))}
                />
              )}
            </FormField>
            <FormField label="Patient code (optional)" id="new-code" hint="Generated automatically if empty." className="sm:col-span-2">
              {({ id, ...aria }) => (
                <Input id={id} {...aria} autoComplete="off" value={newPatient.code} onChange={(e) => setNewPatient({ ...newPatient, code: e.target.value })} />
              )}
            </FormField>
            <p className="flex items-end gap-2 text-xs text-muted-foreground sm:col-span-2 lg:col-span-4">
              <UserPlus className="size-4 shrink-0" aria-hidden /> The patient is saved when the screening runs.
            </p>
          </div>
        )}
      </Card>

      <Card className="space-y-5 p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-lg font-semibold">2. Fundus image</h2>
          <Segmented<"Right" | "Left">
            label="Eye"
            value={eye}
            onChange={setEye}
            options={[
              { value: "Right", label: "Right eye" },
              { value: "Left", label: "Left eye" },
            ]}
          />
        </div>

        <FileDrop
          file={file}
          onFile={(f) => {
            setFile(f);
            setSampleName(null);
            setError("");
          }}
          accept="image/png,image/jpeg,.png,.jpg,.jpeg"
          validate={validateImage}
          onPick={() => setError("")}
          title="Drop a fundus image here, or click to browse"
          hint="PNG or JPG, up to 15 MB"
          disabled={!!busy}
        >
          {preview && (
            <img src={preview} alt="Selected fundus image preview" className="max-h-56 w-auto rounded-xl bg-black object-contain" />
          )}
        </FileDrop>

        {samplesQuery.isError ? (
          <p className="text-xs text-muted-foreground">Sample images are unavailable right now. You can still upload your own image.</p>
        ) : samples.length > 0 ? (
          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold">Or use a labelled sample</h3>
              <p className="text-xs text-muted-foreground">
                Sample images from the held-out test split. The badge shows the ground-truth label.
              </p>
            </div>
            <ul className="grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-8">
              {samples.map((s) => {
                const selected = sampleName === s.name;
                const loading = sampleBusy === s.name;
                return (
                  <li key={s.name}>
                    <button
                      type="button"
                      onClick={() => pickSample(s)}
                      disabled={!!busy || sampleBusy !== null}
                      aria-pressed={selected}
                      aria-label={`Sample ${s.name}, ${s.label ? "retinopathy" : "no retinopathy"} (ground truth)`}
                      title={`${s.name}: ${s.label ? "retinopathy" : "no retinopathy"} (ground truth)`}
                      className={cn(
                        "relative block w-full overflow-hidden rounded-lg ring-2 transition-[box-shadow,transform] duration-200 hover:scale-[1.03] disabled:opacity-60",
                        selected ? "ring-violet" : "ring-transparent",
                      )}
                    >
                      <img src={s.url} alt="" loading="lazy" className="aspect-square w-full bg-black object-cover" />
                      <span
                        className={cn(
                          "absolute inset-x-0 bottom-0 bg-black/40 py-0.5 text-center text-[10px] font-semibold text-white",
                          s.label ? "bg-danger/85" : "bg-success/85",
                        )}
                      >
                        {s.label ? "HR" : "Normal"}
                      </span>
                      {loading && (
                        <span className="absolute inset-0 grid place-items-center bg-black/40">
                          <Loader2 className="size-5 animate-spin text-white" aria-hidden />
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}
      </Card>

      <Card className="space-y-5 p-5 sm:p-6">
        <div>
          <h2 className="font-display text-lg font-semibold">3. Clinical parameters</h2>
          <p className="text-sm text-muted-foreground">Used for the heart-disease risk. Age and sex are filled from the patient.</p>
        </div>
        <ClinicalForm value={clinical} onChange={setClinical} disabled={!!busy} idPrefix="new-clinical" />
      </Card>

      {error && <AlertBox>{error}</AlertBox>}

      <div className="flex flex-wrap items-center gap-4">
        <Button type="submit" size="lg" loading={!!busy} disabled={!!busy}>
          Run screening
        </Button>
        <span role="status" aria-live="polite" className="text-sm text-muted-foreground">
          {busy}
        </span>
        {!patients.length && mode === "existing" && (
          <Link to="/patients" className="text-sm text-violet-ink underline-offset-4 hover:underline">
            View patients
          </Link>
        )}
      </div>

      <Disclaimer />
    </form>
  );
}
