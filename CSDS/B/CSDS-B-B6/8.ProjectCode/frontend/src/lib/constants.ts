import type { BadgeTone } from "@/components/ui/Badge";
import type { Role } from "@/lib/auth";

export const CATEGORIES = ["encounters", "conditions", "medications", "labs", "allergies"] as const;

export const CATEGORY_LABEL: Record<string, string> = {
  encounters: "Encounters",
  conditions: "Conditions",
  medications: "Medications",
  labs: "Lab results",
  allergies: "Allergies",
  other: "Other",
};

export const CATEGORY_TONE: Record<string, BadgeTone> = {
  encounters: "violet",
  conditions: "danger",
  medications: "success",
  labs: "info",
  allergies: "warning",
  other: "neutral",
};

/** Hospital names as the platform returns them. Keys match the hospital codes in .env. */
export const HOSPITAL_NAMES: Record<string, string> = {
  A: "Northbridge General Hospital",
  B: "Riverside Medical Center",
  C: "Lakeview Clinic",
};

export const HOSPITAL_TONE: Record<string, BadgeTone> = { A: "violet", B: "cyan", C: "magenta" };

export const ROLE_LABEL: Record<Role, string> = {
  patient: "Patient",
  doctor: "Physician",
  staff: "Records staff",
  admin: "Platform administrator",
};

export const LANGUAGES = ["English", "Telugu", "Hindi", "Tamil", "Kannada", "Marathi", "Bengali", "Spanish", "French"];

/** Human label for a reminder kind. */
export const REMINDER_KIND_LABEL: Record<string, string> = {
  medication: "Daily medication",
  "follow-up": "Follow-up",
  custom: "Your reminder",
};

export const DEMO_ACCOUNTS = [
  { label: "Patient", username: "patient", hint: "records at all three hospitals" },
  { label: "Doctor (Riverside)", username: "dr.riverside", hint: "Riverside Medical Center" },
  { label: "Records staff (Lakeview)", username: "staff.lakeview", hint: "hospital console" },
  { label: "Administrator", username: "admin", hint: "hospitals, MPI, audit" },
];
