// Clinical inputs for the heart-disease model. Codes follow the training data
// (docs/02_HOW_IT_WORKS.md maps them to the UCI source). Do not renumber these.

export const CLINICAL_KEYS = [
  "age",
  "sex",
  "trestbps",
  "chol",
  "cp",
  "fbs",
  "restecg",
  "thalach",
  "exang",
  "oldpeak",
  "slope",
  "ca",
  "thal",
] as const;

export type ClinicalKey = (typeof CLINICAL_KEYS)[number];

/** Form state: numeric inputs hold strings while the user types. */
export type ClinicalValues = Record<ClinicalKey, number | string>;

export interface ClinicalField {
  key: ClinicalKey;
  label: string;
  min?: number;
  max?: number;
  step?: number;
  options?: [number, string][];
}

export const CLINICAL_FIELDS: ClinicalField[] = [
  { key: "age", label: "Age (years)", min: 18, max: 100 },
  {
    key: "sex",
    label: "Sex",
    options: [
      [1, "Male"],
      [0, "Female"],
    ],
  },
  { key: "trestbps", label: "Resting blood pressure (mmHg)", min: 80, max: 220 },
  { key: "chol", label: "Serum cholesterol (mg/dl)", min: 100, max: 600 },
  {
    key: "cp",
    label: "Chest pain type",
    options: [
      [3, "Typical angina"],
      [1, "Atypical angina"],
      [2, "Non-anginal pain"],
      [0, "Asymptomatic"],
    ],
  },
  {
    key: "fbs",
    label: "Fasting blood sugar > 120 mg/dl",
    options: [
      [0, "No (<= 120 mg/dl)"],
      [1, "Yes (> 120 mg/dl)"],
    ],
  },
  {
    key: "restecg",
    label: "Resting ECG",
    options: [
      [1, "Normal"],
      [2, "ST-T wave abnormality"],
      [0, "Left ventricular hypertrophy"],
    ],
  },
  { key: "thalach", label: "Max heart rate achieved (bpm)", min: 60, max: 220 },
  {
    key: "exang",
    label: "Exercise-induced angina",
    options: [
      [0, "No"],
      [1, "Yes"],
    ],
  },
  { key: "oldpeak", label: "ST depression by exercise (mm)", min: 0, max: 7, step: 0.1 },
  {
    key: "slope",
    label: "Slope of peak exercise ST segment",
    options: [
      [2, "Upsloping"],
      [1, "Flat"],
      [0, "Downsloping"],
    ],
  },
  {
    key: "ca",
    label: "Major vessels coloured by fluoroscopy",
    options: [
      [0, "0"],
      [1, "1"],
      [2, "2"],
      [3, "3"],
    ],
  },
  {
    key: "thal",
    label: "Thallium stress test",
    options: [
      [2, "Normal"],
      [1, "Fixed defect"],
      [3, "Reversible defect"],
    ],
  },
];

export const EMPTY_CLINICAL: ClinicalValues = {
  age: "",
  sex: 1,
  trestbps: "",
  chol: "",
  cp: 0,
  fbs: 0,
  restecg: 1,
  thalach: "",
  exang: 0,
  oldpeak: "0",
  slope: 2,
  ca: 0,
  thal: 2,
};

/** Stored screening values (numbers) back into form state. */
export function clinicalFromStored(stored: Record<string, number>): ClinicalValues {
  return { ...EMPTY_CLINICAL, ...stored } as ClinicalValues;
}

/** Form state into the request body. Throws a readable message if a numeric field is empty. */
export function clinicalPayload(values: ClinicalValues): Record<ClinicalKey, number> {
  const out = {} as Record<ClinicalKey, number>;
  for (const field of CLINICAL_FIELDS) {
    const raw = values[field.key];
    if (raw === "" || raw === null || raw === undefined) throw new Error(`Missing value: ${field.label}`);
    out[field.key] = Number(raw);
  }
  return out;
}
