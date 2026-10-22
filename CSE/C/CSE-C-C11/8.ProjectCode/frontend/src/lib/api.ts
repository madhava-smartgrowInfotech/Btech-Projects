import axios from "axios";

const TOKEN_KEY = "finjarvis-token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable - the session lasts until the page is closed */
  }
}

/** All calls go through the Vite proxy (/api -> backend), so no CORS and no hard-coded port. */
export const api = axios.create({ baseURL: "/api", timeout: 60_000 });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    // An expired or invalid session anywhere except the login form sends the user back to sign in.
    if (axios.isAxiosError(error) && error.response?.status === 401 && !error.config?.url?.startsWith("/auth/login")) {
      setToken(null);
      window.dispatchEvent(new Event("finjarvis:signed-out"));
    }
    return Promise.reject(error);
  },
);

/** Turns any thrown value into a sentence for the user (API detail first, then a network hint). */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail) return detail;
    if (Array.isArray(detail) && detail.length) return detail.map((d) => d?.msg ?? String(d)).join("; ");
    // no response at all, or the dev proxy answering for a backend that is down
    if (!error.response || [502, 503, 504].includes(error.response.status))
      return "Can't reach the FINJARVIS server. Start the backend (run.bat) and try again.";
    return `The server answered ${error.response.status}.`;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}

/* ------------------------------------------------------------------ types */
export interface User {
  id: number;
  name: string;
  email: string;
  username: string;
  currency: string;
  monthly_income: number;
  risk_profile: string;
  savings_target: number;
  created_at: string | null;
}

export interface Meta {
  categories: string[];
  default_categories: string[];
  payment_methods: string[];
  asset_types: string[];
  currencies: string[];
  risk_profiles: string[];
  goal_presets: string[];
}

export interface Transaction {
  id: number;
  date: string;
  description: string;
  category: string;
  amount: number;
  transaction_type: "income" | "expense";
  payment_method: string;
  notes: string;
}

export interface TransactionList {
  items: Transaction[];
  total: number;
  income: number;
  expense: number;
}

export interface BudgetStatus {
  id: number;
  category: string;
  budget_amount: number;
  actual_spent: number;
  remaining: number;
  percent_used: number;
}

export interface Goal {
  id: number;
  goal_name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  status: string;
  percent_complete: number;
  required_monthly_savings: number;
}

export interface Holding {
  id: number;
  asset_name: string;
  symbol: string;
  asset_type: string;
  quantity: number;
  purchase_price: number;
  current_price: number;
  purchase_date: string;
  invested_amount: number;
  current_value: number;
  profit_loss: number;
  return_percent: number;
}

export interface Portfolio {
  total_invested: number;
  total_current_value: number;
  total_profit_loss: number;
  total_return_percent: number;
  holdings: Holding[];
}

export interface Health {
  score: number;
  rating: string;
  explanation: string;
  components: Record<string, number>;
  weakest_area: string;
  weakest_area_reason: string;
}

export interface Dashboard {
  month: number;
  year: number;
  month_name: string;
  metrics: {
    monthly_income: number;
    monthly_expenses: number;
    monthly_savings: number;
    savings_rate: number;
    investment_value: number;
    net_worth: number;
    total_balance: number;
    avg_budget_usage: number;
  };
  health: Health;
  alerts: BudgetStatus[];
  charts: {
    category_spend: { category: string; amount: number }[];
    trend: { month: string; income: number; expense: number }[];
    allocation: { name: string; value: number }[];
    budget_vs_actual: { category: string; budget: number; actual: number }[];
    goals: { name: string; percent: number }[];
  };
  counts: { budgets: number; goals: number; holdings: number };
}

export interface Analytics {
  range: { start: string; end: string };
  type: string;
  overview: {
    total_income: number;
    total_expenses: number;
    avg_daily_spending: number;
    largest_expense: { description: string; amount: number; category: string } | null;
    top_category: string | null;
    savings_rate: number;
  };
  category_distribution: { category: string; amount: number }[];
  income_expense_split: { transaction_type: string; amount: number }[];
  trend: { month: string; income: number; expense: number }[];
  prediction:
    | { available: false; message: string }
    | {
        available: true;
        predicted_next_month_expense: number;
        recent_average: number;
        trend: "increasing" | "decreasing" | "stable";
        months_used: number;
      };
  category_prediction: { available: boolean; message?: string; predictions?: Record<string, number>; months_used?: number };
  overrun_risks: { category: string; predicted_spend: number; budget: number; overrun_amount: number }[];
}

export interface Notice {
  id: number;
  message: string;
  type: "info" | "warning" | "danger" | "success" | string;
  created_at: string | null;
  is_read: boolean;
}

export interface ImportPreview {
  rows: { date: string; description: string; amount: number; category: string; transaction_type: string }[];
  valid: number;
  warnings: string[];
}

export interface Showcase extends Dashboard {
  assistant: { question: string; answer: string; disclaimer: string; source?: string };
}
