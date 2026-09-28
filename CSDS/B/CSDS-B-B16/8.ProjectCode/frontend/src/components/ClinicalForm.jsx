// Codes follow the heart-disease training data (see docs/02_HOW_IT_WORKS.md for the mapping to UCI).
const SELECTS = {
  sex: [
    [1, 'Male'],
    [0, 'Female'],
  ],
  cp: [
    [3, 'Typical angina'],
    [1, 'Atypical angina'],
    [2, 'Non-anginal pain'],
    [0, 'Asymptomatic'],
  ],
  fbs: [
    [0, 'No (<= 120 mg/dl)'],
    [1, 'Yes (> 120 mg/dl)'],
  ],
  restecg: [
    [1, 'Normal'],
    [2, 'ST-T wave abnormality'],
    [0, 'Left ventricular hypertrophy'],
  ],
  exang: [
    [0, 'No'],
    [1, 'Yes'],
  ],
  slope: [
    [2, 'Upsloping'],
    [1, 'Flat'],
    [0, 'Downsloping'],
  ],
  ca: [
    [0, '0'],
    [1, '1'],
    [2, '2'],
    [3, '3'],
  ],
  thal: [
    [2, 'Normal'],
    [1, 'Fixed defect'],
    [3, 'Reversible defect'],
  ],
}

const FIELDS = [
  ['age', 'Age (years)', { min: 18, max: 100 }],
  ['sex', 'Sex'],
  ['trestbps', 'Resting blood pressure (mmHg)', { min: 80, max: 220 }],
  ['chol', 'Serum cholesterol (mg/dl)', { min: 100, max: 600 }],
  ['cp', 'Chest pain type'],
  ['fbs', 'Fasting blood sugar > 120 mg/dl'],
  ['restecg', 'Resting ECG'],
  ['thalach', 'Max heart rate achieved (bpm)', { min: 60, max: 220 }],
  ['exang', 'Exercise-induced angina'],
  ['oldpeak', 'ST depression by exercise (mm)', { min: 0, max: 7, step: 0.1 }],
  ['slope', 'Slope of peak exercise ST segment'],
  ['ca', 'Major vessels coloured by fluoroscopy'],
  ['thal', 'Thallium stress test'],
]

export const EMPTY_CLINICAL = {
  age: '', sex: 1, trestbps: '', chol: '', cp: 0, fbs: 0, restecg: 1, thalach: '', exang: 0, oldpeak: '0', slope: 2, ca: 0, thal: 2,
}

export default function ClinicalForm({ value, onChange, disabled }) {
  const set = (k, v) => onChange({ ...value, [k]: v })
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {FIELDS.map(([key, label, num]) => (
        <div key={key}>
          <label className="label" htmlFor={`f-${key}`}>
            {label}
          </label>
          {SELECTS[key] ? (
            <select id={`f-${key}`} className="input" value={value[key]} disabled={disabled} onChange={(e) => set(key, Number(e.target.value))}>
              {SELECTS[key].map(([v, t]) => (
                <option key={v} value={v}>
                  {t}
                </option>
              ))}
            </select>
          ) : (
            <input
              id={`f-${key}`}
              type="number"
              className="input"
              required
              disabled={disabled}
              min={num.min}
              max={num.max}
              step={num.step || 1}
              value={value[key]}
              onChange={(e) => set(key, e.target.value)}
            />
          )}
        </div>
      ))}
    </div>
  )
}
