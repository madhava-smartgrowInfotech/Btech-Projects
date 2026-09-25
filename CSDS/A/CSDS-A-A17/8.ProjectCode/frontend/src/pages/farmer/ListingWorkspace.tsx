import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, MapPin, ShieldCheck, Sparkles, Star, TrendingUp } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { GradeBadge, Badge } from "@/components/ui/Badge";
import { QualityRadarChart } from "@/components/charts/QualityRadarChart";
import { ShapBarChart } from "@/components/charts/ShapBarChart";
import { PriceForecastChart } from "@/components/charts/PriceForecastChart";
import { toast } from "@/components/ui/Toast";
import { formatCurrency, dayLabel } from "@/lib/format";
import type { CropListing, PricePrediction, DeliveryRecommendation } from "@/types";

export function ListingWorkspace() {
  const { id } = useParams();
  const [listing, setListing] = useState<CropListing | null>(null);
  const [price, setPrice] = useState<PricePrediction | null>(null);
  const [delivery, setDelivery] = useState<DeliveryRecommendation | null>(null);
  const [loadingPrice, setLoadingPrice] = useState(false);
  const [loadingDelivery, setLoadingDelivery] = useState(false);
  const [askingPrice, setAskingPrice] = useState("");
  const [publishing, setPublishing] = useState(false);

  useEffect(() => {
    api.get<CropListing>(`/crops/${id}`).then(({ data }) => setListing(data));
  }, [id]);

  async function fetchPrice() {
    if (!listing) return;
    setLoadingPrice(true);
    try {
      const { data } = await api.post<PricePrediction>("/prices/predict", {
        crop_type: listing.crop_type,
        region: listing.region,
        listing_id: listing.id,
      });
      setPrice(data);
      setAskingPrice(String(Math.round(data.current_price)));
    } catch (err) {
      toast.error("Couldn't forecast price", apiErrorMessage(err));
    } finally {
      setLoadingPrice(false);
    }
  }

  async function fetchDelivery() {
    setLoadingDelivery(true);
    try {
      const { data } = await api.get<DeliveryRecommendation>(`/delivery/${id}/recommend`);
      setDelivery(data);
    } catch (err) {
      toast.error("Couldn't plan delivery", apiErrorMessage(err));
    } finally {
      setLoadingDelivery(false);
    }
  }

  async function publish() {
    setPublishing(true);
    try {
      const { data } = await api.post<CropListing>(`/crops/${id}/list?asking_price=${askingPrice}`);
      setListing(data);
      toast.success("Listed on the marketplace", `${data.crop_type} · ${formatCurrency(Number(askingPrice))}`);
    } catch (err) {
      toast.error("Couldn't publish listing", apiErrorMessage(err));
    } finally {
      setPublishing(false);
    }
  }

  if (!listing) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading listing…
      </div>
    );
  }

  const grade = listing.quality_grade;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900">
            {listing.crop_type} <span className="text-ink-400 font-normal text-lg">· {listing.quantity_kg} kg</span>
          </h1>
          <p className="text-sm text-ink-500 mt-1 flex items-center gap-1">
            <MapPin size={13} /> {listing.region}
          </p>
        </div>
        <Badge tone={listing.status === "listed" ? "brand" : listing.status === "sold" ? "sky" : "slate"}>{listing.status}</Badge>
      </div>

      {/* QUALITY */}
      {grade && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles size={16} className="text-brand-600" /> Quality grade
                </CardTitle>
                <CardDescription>Computed from real color, texture, edge and size features of your photo.</CardDescription>
              </div>
              <GradeBadge grade={grade.grade} />
            </CardHeader>
            <CardContent className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-ink-500 mb-2">Confidence: {(grade.confidence * 100).toFixed(1)}%</p>
                <QualityRadarChart features={grade.features} />
              </div>
              <div>
                <p className="text-sm text-ink-500 mb-2">What drove this grade</p>
                <ShapBarChart items={grade.shap_explanation.top_features} />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* PRICE */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp size={16} className="text-brand-600" /> Price forecast
            </CardTitle>
            <CardDescription>30-day predicted price with a confidence band.</CardDescription>
          </div>
          {!price && (
            <Button size="sm" onClick={fetchPrice} disabled={loadingPrice}>
              {loadingPrice ? <Loader2 size={14} className="animate-spin" /> : "Forecast price"}
            </Button>
          )}
        </CardHeader>
        {price && (
          <CardContent className="grid lg:grid-cols-[1fr_260px] gap-6">
            <div>
              <div className="flex items-baseline gap-3 mb-2">
                <span className="text-2xl font-semibold text-ink-900">{formatCurrency(price.current_price)}</span>
                <span className="text-xs text-ink-500">
                  range {formatCurrency(price.confidence_low)}–{formatCurrency(price.confidence_high)} / quintal
                </span>
              </div>
              <PriceForecastChart
                forecast={price.forecast}
                confidenceLow={price.confidence_low}
                confidenceHigh={price.confidence_high}
                bestSellDay={price.best_sell_day}
              />
              <p className="text-xs text-ink-500 mt-2">
                Best day to sell within a safe window: <span className="font-semibold text-brand-700">{dayLabel(price.best_sell_day)}</span>
              </p>
            </div>
            <div>
              <p className="text-sm text-ink-500 mb-2">What's driving this price</p>
              <ShapBarChart items={price.shap_explanation.top_features} />
            </div>
          </CardContent>
        )}
      </Card>

      {/* DELIVERY */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Star size={16} className="text-brand-600" /> Delivery planner
            </CardTitle>
            <CardDescription>Ranked buyers by price, distance, reliability and spoilage risk.</CardDescription>
          </div>
          {!delivery && (
            <Button size="sm" onClick={fetchDelivery} disabled={loadingDelivery}>
              {loadingDelivery ? <Loader2 size={14} className="animate-spin" /> : "Plan delivery"}
            </Button>
          )}
        </CardHeader>
        {delivery && (
          <CardContent className="space-y-3">
            {delivery.ranked_buyers.buyers.map((b, i) => (
              <div key={b.buyer_id} className="flex items-center justify-between rounded-xl border border-ink-100 p-3.5">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-brand-700 text-xs font-bold">
                    #{i + 1}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-ink-900">{b.buyer_name}</p>
                    <p className="text-xs text-ink-500">
                      {b.region} · {b.distance_km} km · {b.transit_days}d transit
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-ink-900">{formatCurrency(b.offered_price)}</p>
                  <p className="text-xs text-brand-700">{b.match_score}% match</p>
                </div>
              </div>
            ))}
            <p className="text-xs text-ink-500 pt-1">
              Suggested route: {delivery.best_route.origin} → {delivery.best_route.destination} (
              {delivery.best_route.distance_km} km, ~{delivery.best_route.estimated_transit_days} days)
            </p>
          </CardContent>
        )}
      </Card>

      {/* PUBLISH */}
      {listing.status === "draft" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-brand-600" /> List on the marketplace
            </CardTitle>
            <CardDescription>Buyers will see this listing with its grade and price once published.</CardDescription>
          </CardHeader>
          <CardContent className="flex items-end gap-3">
            <div className="w-48">
              <Label htmlFor="ask">Asking price (₹/quintal)</Label>
              <Input id="ask" type="number" value={askingPrice} onChange={(e) => setAskingPrice(e.target.value)} />
            </div>
            <Button onClick={publish} disabled={publishing || !askingPrice}>
              {publishing ? <Loader2 size={14} className="animate-spin" /> : "Publish listing"}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
