import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, MapPin, SlidersHorizontal } from "lucide-react";
import { api } from "@/lib/api";
import { Select } from "@/components/ui/Input";
import { GradeBadge } from "@/components/ui/Badge";
import { CROPS, REGIONS, GRADES } from "@/lib/staticOptions";
import { formatCurrency } from "@/lib/format";
import type { CropListing } from "@/types";

export function Marketplace() {
  const navigate = useNavigate();
  const [listings, setListings] = useState<CropListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [crop, setCrop] = useState("");
  const [region, setRegion] = useState("");
  const [grade, setGrade] = useState("");

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (crop) params.crop_type = crop;
    if (region) params.region = region;
    if (grade) params.grade = grade;
    api
      .get<CropListing[]>("/marketplace/listings", { params })
      .then(({ data }) => setListings(data))
      .finally(() => setLoading(false));
  }, [crop, region, grade]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">Marketplace</h1>
        <p className="text-sm text-ink-500 mt-1">Graded, price-forecast crops ready to buy.</p>
      </div>

      <div className="flex flex-wrap items-center gap-3 bg-white border border-ink-100 rounded-xl p-3">
        <SlidersHorizontal size={16} className="text-ink-400" />
        <Select value={crop} onChange={(e) => setCrop(e.target.value)} className="w-auto">
          <option value="">All crops</option>
          {CROPS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </Select>
        <Select value={region} onChange={(e) => setRegion(e.target.value)} className="w-auto">
          <option value="">All regions</option>
          {REGIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </Select>
        <Select value={grade} onChange={(e) => setGrade(e.target.value)} className="w-auto">
          <option value="">All grades</option>
          {GRADES.map((g) => (
            <option key={g} value={g}>
              Grade {g}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <p className="text-sm text-ink-500 flex items-center gap-2">
          <Loader2 size={15} className="animate-spin" /> Loading listings…
        </p>
      ) : listings.length === 0 ? (
        <p className="text-sm text-ink-500">No listings match these filters yet.</p>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {listings.map((l, i) => (
            <motion.button
              key={l.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              onClick={() => navigate(`/buyer/listings/${l.id}`)}
              className="text-left rounded-2xl border border-ink-100 bg-white overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="h-32 bg-sand-100 flex items-center justify-center overflow-hidden">
                {l.image_path ? (
                  <img src={l.image_path} className="w-full h-full object-cover" alt={l.crop_type} />
                ) : (
                  <span className="text-ink-300 text-xs">No image</span>
                )}
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-ink-900">{l.crop_type}</p>
                    <p className="text-xs text-ink-500 flex items-center gap-1 mt-0.5">
                      <MapPin size={12} /> {l.region}
                    </p>
                  </div>
                  {l.quality_grade && <GradeBadge grade={l.quality_grade.grade} />}
                </div>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-ink-500">{l.quantity_kg} kg available</span>
                  <span className="text-sm font-semibold text-ink-900">{formatCurrency(l.asking_price)}</span>
                </div>
              </div>
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
}
