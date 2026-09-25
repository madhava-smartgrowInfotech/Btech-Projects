import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Loader2, MapPin, ShoppingCart } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { Dialog } from "@/components/ui/Dialog";
import { GradeBadge } from "@/components/ui/Badge";
import { QualityRadarChart } from "@/components/charts/QualityRadarChart";
import { PriceForecastChart } from "@/components/charts/PriceForecastChart";
import { toast } from "@/components/ui/Toast";
import { formatCurrency } from "@/lib/format";
import type { CropListing, PricePrediction } from "@/types";

export function ListingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState<CropListing | null>(null);
  const [price, setPrice] = useState<PricePrediction | null>(null);
  const [open, setOpen] = useState(false);
  const [quantity, setQuantity] = useState("");
  const [agreedPrice, setAgreedPrice] = useState("");
  const [placing, setPlacing] = useState(false);

  useEffect(() => {
    api.get<CropListing>(`/marketplace/listings/${id}`).then(({ data }) => {
      setListing(data);
      setQuantity(String(data.quantity_kg));
      setAgreedPrice(String(data.asking_price));
    });
  }, [id]);

  useEffect(() => {
    if (!listing) return;
    api
      .post<PricePrediction>("/prices/predict", { crop_type: listing.crop_type, region: listing.region, listing_id: listing.id })
      .then(({ data }) => setPrice(data));
  }, [listing]);

  async function placeOrder() {
    setPlacing(true);
    try {
      await api.post("/marketplace/orders", {
        listing_id: Number(id),
        quantity_kg: Number(quantity),
        agreed_price: Number(agreedPrice),
      });
      toast.success("Order placed");
      setOpen(false);
      navigate("/buyer/orders");
    } catch (err) {
      toast.error("Couldn't place order", apiErrorMessage(err));
    } finally {
      setPlacing(false);
    }
  }

  if (!listing) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading listing…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900">{listing.crop_type}</h1>
          <p className="text-sm text-ink-500 mt-1 flex items-center gap-1">
            <MapPin size={13} /> {listing.region} · {listing.quantity_kg} kg available
          </p>
        </div>
        <div className="text-right">
          {listing.quality_grade && <GradeBadge grade={listing.quality_grade.grade} />}
          <p className="text-xl font-semibold text-ink-900 mt-2">{formatCurrency(listing.asking_price)}</p>
        </div>
      </div>

      {listing.image_path && (
        <img src={listing.image_path} className="w-full max-h-72 object-cover rounded-2xl border border-ink-100" alt={listing.crop_type} />
      )}

      {listing.quality_grade && (
        <Card>
          <CardHeader>
            <CardTitle>Quality breakdown</CardTitle>
            <CardDescription>Confidence {(listing.quality_grade.confidence * 100).toFixed(0)}%</CardDescription>
          </CardHeader>
          <CardContent>
            <QualityRadarChart features={listing.quality_grade.features} />
          </CardContent>
        </Card>
      )}

      {price && (
        <Card>
          <CardHeader>
            <CardTitle>Market price trend</CardTitle>
            <CardDescription>Reference price for this crop, grade and region.</CardDescription>
          </CardHeader>
          <CardContent>
            <PriceForecastChart
              forecast={price.forecast}
              confidenceLow={price.confidence_low}
              confidenceHigh={price.confidence_high}
              bestSellDay={price.best_sell_day}
            />
          </CardContent>
        </Card>
      )}

      <Button onClick={() => setOpen(true)} disabled={listing.status !== "listed"}>
        <ShoppingCart size={16} /> {listing.status === "listed" ? "Place order" : "Not available"}
      </Button>

      <Dialog open={open} onClose={() => setOpen(false)} title="Place order">
        <div className="space-y-4">
          <div>
            <Label htmlFor="q">Quantity (kg)</Label>
            <Input id="q" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="p">Agreed price (₹/quintal)</Label>
            <Input id="p" type="number" value={agreedPrice} onChange={(e) => setAgreedPrice(e.target.value)} />
          </div>
          <Button className="w-full" onClick={placeOrder} disabled={placing}>
            {placing ? <Loader2 size={14} className="animate-spin" /> : "Confirm order"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
