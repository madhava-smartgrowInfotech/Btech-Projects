import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ImagePlus, Loader2, Sparkles } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";
import { Card, CardContent } from "@/components/ui/Card";
import { GradeBadge, Badge } from "@/components/ui/Badge";
import { toast } from "@/components/ui/Toast";
import { CROPS } from "@/lib/staticOptions";
import { formatCurrency } from "@/lib/format";
import type { CropListing } from "@/types";

export function FarmerDashboard() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const [listings, setListings] = useState<CropListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [cropType, setCropType] = useState(CROPS[0]);
  const [quantity, setQuantity] = useState("250");
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const loadListings = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<CropListing[]>("/crops/mine");
      setListings(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadListings();
  }, [loadListings]);

  function handleFile(f: File | null) {
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : null);
  }

  async function onUpload() {
    if (!file) {
      toast.error("Add a photo first");
      return;
    }
    setUploading(true);
    try {
      const form = new FormData();
      form.append("crop_type", cropType);
      form.append("region", user?.region ?? "");
      form.append("quantity_kg", quantity);
      form.append("image", file);
      const { data } = await api.post<CropListing>("/crops/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Crop graded", `Grade ${data.quality_grade?.grade} · ${Math.round((data.quality_grade?.confidence ?? 0) * 100)}% confidence`);
      navigate(`/farmer/listings/${data.id}`);
    } catch (err) {
      toast.error("Grading failed", apiErrorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">Grade a new crop</h1>
        <p className="text-sm text-ink-500 mt-1">Upload a photo — CropSight grades it, forecasts the price, and plans delivery.</p>
      </div>

      <Card>
        <CardContent className="grid md:grid-cols-[1fr_260px] gap-6">
          <div>
            <div className="grid sm:grid-cols-2 gap-4 mb-4">
              <div>
                <Label htmlFor="crop">Crop type</Label>
                <Select id="crop" value={cropType} onChange={(e) => setCropType(e.target.value)}>
                  {CROPS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label htmlFor="qty">Quantity (kg)</Label>
                <Input id="qty" type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
              </div>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                handleFile(e.dataTransfer.files?.[0] ?? null);
              }}
              onClick={() => fileInput.current?.click()}
              className={`flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed h-48 cursor-pointer transition-colors ${
                dragOver ? "border-brand-500 bg-brand-50" : "border-ink-200 hover:bg-ink-50"
              }`}
            >
              <input
                ref={fileInput}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
              />
              <ImagePlus className="text-ink-400" size={26} />
              <p className="text-sm text-ink-500">{file ? file.name : "Drag a photo here, or click to browse"}</p>
            </div>

            <Button className="mt-4 w-full" onClick={onUpload} disabled={uploading}>
              {uploading ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Analyzing image…
                </>
              ) : (
                <>
                  <Sparkles size={16} /> Grade this crop
                </>
              )}
            </Button>
          </div>

          <div className="rounded-2xl bg-sand-100 border border-ink-100 flex items-center justify-center overflow-hidden">
            {preview ? (
              <img src={preview} alt="preview" className="w-full h-full object-cover" />
            ) : (
              <p className="text-xs text-ink-400 px-6 text-center">Your photo preview will appear here</p>
            )}
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="font-semibold text-ink-900 mb-3">Your listings</h2>
        {loading ? (
          <p className="text-sm text-ink-500">Loading…</p>
        ) : listings.length === 0 ? (
          <p className="text-sm text-ink-500">No crops graded yet — upload your first photo above.</p>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {listings.map((l, i) => (
              <motion.button
                key={l.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => navigate(`/farmer/listings/${l.id}`)}
                className="text-left rounded-2xl border border-ink-100 bg-white p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-ink-900">{l.crop_type}</p>
                    <p className="text-xs text-ink-500">{l.quantity_kg} kg · {l.region}</p>
                  </div>
                  {l.quality_grade && <GradeBadge grade={l.quality_grade.grade} />}
                </div>
                <div className="flex items-center justify-between mt-4">
                  <Badge tone={l.status === "listed" ? "brand" : l.status === "sold" ? "sky" : "slate"}>{l.status}</Badge>
                  {l.asking_price > 0 && <span className="text-sm font-semibold text-ink-800">{formatCurrency(l.asking_price)}</span>}
                </div>
              </motion.button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
