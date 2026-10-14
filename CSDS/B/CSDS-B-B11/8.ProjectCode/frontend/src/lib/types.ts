// Response shapes returned by the NutriSense API (see docs/FRONTEND_PLAN.md, section 1).

export type Meal = "breakfast" | "lunch" | "snack" | "dinner";

export const MEALS: { value: Meal; label: string }[] = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "snack", label: "Snack" },
  { value: "dinner", label: "Dinner" },
];

export interface Nutrients {
  kcal: number;
  protein: number;
  carbs: number;
  fat: number;
  fibre: number;
  sugar: number;
  sodium: number;
  gl?: number;
}

export interface UserSummary {
  id: number;
  name: string;
  email: string;
  has_profile: boolean;
}

export interface AuthResponse {
  token: string;
  user: UserSummary;
}

export interface ProfileOptions {
  activity: string[];
  allergies: string[];
  conditions: string[];
  diet_type: string[];
  cuisine: string[];
  goal: string[];
}

export interface Profile {
  age: number;
  gender: "male" | "female" | "other";
  height_cm: number;
  weight_kg: number;
  activity: string;
  diet_type: string;
  cuisine: string;
  allergies: string[];
  conditions: string[];
  goal: string;
  adaptive_adjust: number;
}

export interface Targets {
  bmi: number;
  bmi_category: string;
  bmr: number;
  tdee: number;
  goal_adjust: number;
  adaptive_adjust: number;
  kcal: number;
  calorie_floor: number;
  floor_applied: boolean;
  macros_pct: { protein: number; carbs: number; fat: number };
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fibre_g: number;
  sodium_max_mg: number;
  sugar_max_g: number;
  gl_max: number | null;
  exclude_fried_rich: boolean;
  goal_rate_kg_week: number;
  notes: string[];
  disclaimer: string;
}

export interface ProfileResponse {
  profile: Profile | null;
}

export interface SaveProfileResponse {
  profile: Profile;
  targets: Targets;
}

export interface PlanDish {
  food_id: number;
  name: string;
  role: string;
  cuisine: string;
  servings: number;
  grams: number;
  kcal: number;
  protein: number;
  carbs: number;
  fat: number;
  fibre: number;
  sugar: number;
  sodium: number;
  gl: number;
}

export interface PlanDay {
  day: number;
  date: string;
  weekday: string;
  meals: Record<Meal, PlanDish[]>;
}

export interface Plan {
  id: number;
  created_at: string;
  start_date: string;
  target_kcal: number;
  days: PlanDay[];
  targets?: Record<string, number | null>;
}

export interface PlanLatestResponse {
  plan: Plan | null;
}

export interface SwapOption {
  food_id: number;
  name: string;
  role: string;
  cuisine: string;
  grams: number;
  servings: number;
  kcal: number;
  protein: number;
  carbs: number;
  fat: number;
  fibre: number;
  sugar: number;
  sodium: number;
  gl: number;
  same_cluster: boolean;
  similarity: number;
  kcal_diff: number;
}

export interface SwapOptionsResponse {
  original: PlanDish;
  options: SwapOption[];
}

export interface Recipe {
  food_id: number;
  name: string;
  grams: number;
  nutrients: Nutrients;
  ingredients: { item: string; quantity: string }[];
  steps: string[];
  prep_minutes: number | null;
  cook_minutes: number | null;
  health_tips: string[];
  typical_minutes_dataset: number | null;
  warnings: string[];
  model: string | null;
  cached: boolean;
}

export interface FoodResult {
  food_id: number;
  name: string;
  role: string;
  diet: string;
  cuisine: string;
  allergens: string[];
  serving_g: number;
  per_100g: Nutrients;
  grams: number;
  nutrients: Nutrients;
  warnings: string[];
}

export interface UsdaResult {
  fdc_id: number;
  name: string;
  data_type: string | null;
}

export interface LogEntry {
  id: number;
  date: string;
  meal: Meal;
  food_id: number | null;
  name: string;
  grams: number;
  source: "database" | "photo" | "usda";
  kcal: number;
  protein: number;
  carbs: number;
  fat: number;
  fibre: number;
  sugar: number;
  sodium: number;
}

export interface LogDay {
  date: string;
  entries: LogEntry[];
  totals: Nutrients;
  targets: { kcal: number; protein: number; carbs: number; fat: number; fibre: number; sodium: number; sugar: number };
}

export interface PhotoItem {
  detected: string;
  confidence: number | null;
  estimated_grams: number | null;
  description: string;
  matches: FoodResult[];
}

export interface PhotoResponse {
  items: PhotoItem[];
  model: string;
}

export interface Weight {
  id: number;
  date: string;
  weight_kg: number;
}

export interface Recalculation {
  as_of: string;
  latest_weight: number;
  observed_kg_week: number;
  expected_kg_week: number;
  step: number;
  adaptive_adjust: number;
  reason: string;
  old_target_kcal: number;
  new_target_kcal: number;
}

export interface WeightSaveResponse {
  ok: boolean;
  recalculated: Recalculation | null;
  target_kcal: number;
}

export interface ProgressResponse {
  weights: Weight[];
  intake: { date: string; kcal: number; protein: number; carbs: number; fat: number; target: number }[];
  adherence: { score: number; days_logged: number; window_days: number };
  target_history: { date: string; kcal: number; weight_kg: number; reason: string }[];
  current_target: number;
  trend_kg_week: number | null;
  goal_rate_kg_week: number;
}

export interface EvaluationResponse {
  requirements: { profiles: number; bmr_max_abs_error_kcal: number; calorie_floor_respected_pct: number; demo_profile_target_kcal: number };
  meal_plans: {
    profiles: number;
    plans_built: number;
    failures: number;
    days: number;
    days_within_5pct_kcal_pct: number;
    mean_abs_kcal_error_pct: number;
    days_meeting_90pct_fibre_target_pct: number;
    mean_unique_dishes_per_week: number;
    safety: {
      allergen_violations: number;
      diet_or_condition_exclusion_violations: number;
      sodium_cap_violations: number;
      glycaemic_load_cap_violations: number;
    };
  };
  swaps: { items_tested: number; options_returned: number; unsafe_suggestions: number };
  dish_matching: { queries: number; top1_accuracy_pct: number; top3_accuracy_pct: number };
  adaptation: { error_reduction_pct: number; simulated_users: number; weeks: number };
  food_database: { dishes: number; allergens_tracked: string[] };
}
