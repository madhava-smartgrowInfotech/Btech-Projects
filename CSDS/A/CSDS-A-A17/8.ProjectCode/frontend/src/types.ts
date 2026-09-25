export type Role = "farmer" | "buyer" | "distributor" | "admin";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  region: string;
  phone: string;
  reliability_score: number;
}

export interface QualityGrade {
  grade: "A" | "B" | "C" | "Reject";
  confidence: number;
  probabilities: Record<string, number>;
  features: Record<string, number>;
  shap_explanation: { top_features: { feature: string; contribution: number; value?: number }[] };
}

export interface CropListing {
  id: number;
  farmer_id: number;
  crop_type: string;
  region: string;
  quantity_kg: number;
  image_path: string;
  status: "draft" | "listed" | "sold";
  asking_price: number;
  created_at: string;
  quality_grade: QualityGrade | null;
}

export interface PricePrediction {
  crop_type: string;
  region: string;
  grade: string;
  current_price: number;
  confidence_low: number;
  confidence_high: number;
  forecast: Record<string, number>;
  shap_explanation: { top_features: { feature: string; contribution: number }[] };
  best_sell_day: number;
}

export interface RankedBuyer {
  buyer_id: number;
  buyer_name: string;
  region: string;
  offered_price: number;
  distance_km: number;
  transit_days: number;
  reliability_score: number;
  spoilage_risk: number;
  match_score: number;
}

export interface DeliveryRecommendation {
  listing_id: number;
  ranked_buyers: { buyers: RankedBuyer[] };
  best_route: {
    origin?: string;
    destination?: string;
    distance_km?: number;
    estimated_transit_days?: number;
    buyer_name?: string;
  };
  best_sell_day: number;
}

export interface Order {
  id: number;
  listing_id: number;
  buyer_id: number;
  distributor_id: number | null;
  quantity_kg: number;
  agreed_price: number;
  status: "placed" | "confirmed" | "in_transit" | "delivered" | "cancelled";
  created_at: string;
  updated_at: string;
}

export interface Shipment {
  id: number;
  origin: string;
  destination: string;
  stage: string;
  order_id: number | null;
}

export interface SensorReading {
  temperature_c: number;
  humidity_pct: number;
  shock_g: number;
  is_anomaly: boolean;
  recorded_at: string;
}

export interface AdminOverview {
  users_by_role: Record<string, number>;
  total_listings: number;
  listed: number;
  sold: number;
  orders: number;
  gross_volume: number;
}

export interface ModelInsights {
  quality_model: {
    algorithm: string;
    test_accuracy: number;
    feature_importance: { feature: string; importance: number }[];
    training_data: string;
  };
  price_model: {
    algorithm: string;
    test_mae: number;
    test_r2: number;
    feature_importance: { feature: string; importance: number }[];
    training_data: string;
  };
}
