export type SeedType =
  | 'Pearl Millet'
  | 'Finger Millet'
  | 'Foxtail Millet'
  | 'Little Millet'
  | 'Kodo Millet'
  | 'Proso Millet'
  | 'Barnyard Millet'

export type PredictionLabel = 'germinate' | 'no_germinate'
export type RiskLevel = 'low' | 'medium' | 'high'
export type FactorImpact = 'positive' | 'negative'

export interface MorphologicalFeatures {
  area: number
  perimeter: number
  aspect_ratio: number
  circularity: number
  mean_color_rgb: [number, number, number]
  color_std: number
}

export interface EmbeddingSummary {
  encoder: string
  embedding_dim: number
  top_activations: number[]
}

export interface KeyFactor {
  factor: string
  impact: FactorImpact
  weight: number
  detail: string
}

export interface Explanation {
  summary: string
  key_factors: KeyFactor[]
  recommendations: string[]
}

export interface PredictionRecord {
  id: string
  prediction: PredictionLabel
  confidence: number
  probability_germinate: number
  risk_level: RiskLevel
  morphological_features: MorphologicalFeatures
  embedding_summary: EmbeddingSummary
  explanation: Explanation
  seed_type: SeedType
  soil_moisture: number
  temperature: number
  humidity: number
  rainfall: number
  soil_ph: number
  created_at: string
  image_url?: string
}

export interface PredictRequest {
  image: File
  soil_moisture: number
  temperature: number
  humidity: number
  rainfall: number
  soil_ph: number
  seed_type: SeedType
}

export interface StatsResponse {
  total_predictions: number
  germination_rate: number
  avg_confidence: number
  seed_type_breakdown: Record<string, number>
  trend: { date: string; count: number; germination_rate: number }[]
  model_metrics: {
    accuracy: number
    precision: number
    recall: number
    f1: number
    confusion_matrix: number[][]
  }
}

export interface ModelInfoResponse {
  architecture: {
    name: string
    encoder: string
    fusion: string
    classifier: string
    explainer: string
  }[]
  pipeline_stages: { stage: string; description: string }[]
  global_feature_importance: { feature: string; importance: number }[]
}

export interface HealthResponse {
  status: string
  model_version: string
  encoder_version: string
}
