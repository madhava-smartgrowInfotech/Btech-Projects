export type Role = "admin" | "invigilator";
export type UserStatus = "active" | "pending" | "disabled";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  status: UserStatus;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
}

export interface Rules {
  adjacency: 4 | 8;
  roll_gap: number;
  department_mix: boolean;
  fill_strategy: "compact" | "balanced";
  accessible_per_hall: number;
}

export interface DemoInfo {
  enabled: boolean;
  password: string | null;
  accounts: { role: Role; email: string; name: string }[];
}
