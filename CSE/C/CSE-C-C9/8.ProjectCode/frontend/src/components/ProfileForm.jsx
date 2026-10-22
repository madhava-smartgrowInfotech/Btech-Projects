import { Input, Select } from './ui'

export const EMPTY_PROFILE = {
  age: '',
  workclass: '',
  education: '',
  'marital-status': '',
  occupation: '',
  relationship: '',
  race: '',
  sex: '',
  'native-country': '',
  'capital-gain': '0',
  'capital-loss': '0',
  'hours-per-week': '40',
}

// Same values the project's own test-suite uses as a valid example.
export const SAMPLE_PROFILE = {
  age: '39',
  workclass: 'State-gov',
  education: 'Bachelors',
  'marital-status': 'Never-married',
  occupation: 'Adm-clerical',
  relationship: 'Not-in-family',
  race: 'White',
  sex: 'Male',
  'native-country': 'United-States',
  'capital-gain': '2174',
  'capital-loss': '0',
  'hours-per-week': '40',
}

const SELECTS = [
  ['workclass', 'Employment type'],
  ['education', 'Education'],
  ['marital-status', 'Marital status'],
  ['occupation', 'Occupation'],
  ['relationship', 'Household relationship'],
  ['race', 'Race'],
  ['sex', 'Sex'],
  ['native-country', 'Country'],
]

const NUMBERS = [
  ['age', 'Age', 'age', 'Years, 16 to 100'],
  ['capital-gain', 'Investment gains (annual $)', 'capital-gain', '0 to 1,000,000'],
  ['capital-loss', 'Investment losses (annual $)', 'capital-loss', '0 to 1,000,000'],
  ['hours-per-week', 'Hours worked per week', 'hours-per-week', '1 to 99'],
]

/** Client-side check mirroring app/utils/validation.py. Returns {field: message}. */
export function validateProfile(v, options) {
  const errs = {}
  const lim = options.limits
  NUMBERS.forEach(([key, label]) => {
    const raw = String(v[key] ?? '').trim()
    const [lo, hi] = lim[key]
    if (raw === '') errs[key] = `${label.replace(/ \(.*\)/, '')} is required.`
    else if (Number.isNaN(Number(raw))) errs[key] = 'Enter a number.'
    else if ((key === 'age' || key === 'hours-per-week') && !Number.isInteger(Number(raw))) errs[key] = 'Enter a whole number.'
    else if (Number(raw) < lo || Number(raw) > hi) errs[key] = `Must be between ${lo.toLocaleString('en-US')} and ${hi.toLocaleString('en-US')}.`
  })
  SELECTS.forEach(([key, label]) => {
    if (!v[key]) errs[key] = `${label} is required.`
  })
  return errs
}

/** The 12 assessment inputs. `prefix` keeps element ids unique when two forms share a page. */
export default function ProfileForm({ values, onChange, errors = {}, options, prefix = 'f' }) {
  const set = (k) => (e) => onChange({ ...values, [k]: e.target.value })
  return (
    <div className="form-grid">
      <Input
        id={`${prefix}-age`}
        label="Age *"
        type="number"
        inputMode="numeric"
        min={16}
        max={100}
        hint="Years, 16 to 100"
        value={values.age}
        onChange={set('age')}
        error={errors.age}
        required
      />
      {SELECTS.map(([key, label]) => (
        <Select
          key={key}
          id={`${prefix}-${key}`}
          label={`${label} *`}
          value={values[key]}
          onChange={set(key)}
          options={[{ value: '', label: 'Select…' }, ...options[key]]}
          aria-invalid={errors[key] ? 'true' : undefined}
          hint={undefined}
          error={errors[key]}
          required
        />
      ))}
      {NUMBERS.slice(1).map(([key, label, , hint]) => (
        <Input
          key={key}
          id={`${prefix}-${key}`}
          label={`${label} *`}
          type="number"
          inputMode="numeric"
          min={options.limits[key][0]}
          max={options.limits[key][1]}
          step={1}
          hint={hint}
          value={values[key]}
          onChange={set(key)}
          error={errors[key]}
          required
        />
      ))}
    </div>
  )
}
