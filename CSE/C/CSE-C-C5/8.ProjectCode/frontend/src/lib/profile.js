// Student-profile fields shared by the Eligibility and Recommendation forms (ranges mirror backend validation).
export const FIELDS = {
  cgpa: { label: 'CGPA', min: 0, max: 10, step: 0.01, hint: '0 - 10' },
  tenth: { label: '10th %', min: 0, max: 100, step: 0.1 },
  twelfth: { label: '12th %', min: 0, max: 100, step: 0.1 },
  aptitude: { label: 'Aptitude', min: 0, max: 100, step: 1, hint: '0 - 100' },
  technical: { label: 'Technical', min: 0, max: 100, step: 1, hint: '0 - 100' },
  communication: { label: 'Communication', min: 0, max: 100, step: 1 },
  dsa: { label: 'DSA', min: 0, max: 100, step: 1 },
  projects: { label: 'Projects', min: 0, max: 20, step: 1, int: true },
  internships: { label: 'Internships', min: 0, max: 20, step: 1, int: true },
  certifications: { label: 'Certifications', min: 0, max: 20, step: 1, int: true },
  backlogs: { label: 'Backlogs', min: 0, max: 20, step: 1, int: true },
}

// Defaults are the ones the original Flask forms used.
export const PREDICT_DEFAULTS = {
  cgpa: '8.0', tenth: '85', twelfth: '85', aptitude: '70', technical: '70', communication: '70', dsa: '70',
  projects: '1', internships: '0', certifications: '1', backlogs: '0', branch: 'CSE', degree: 'BTech',
}
export const RECOMMEND_DEFAULTS = {
  cgpa: '7.2', aptitude: '65', technical: '65', communication: '65', dsa: '65',
  projects: '1', internships: '0', certifications: '1', backlogs: '0', branch: 'CSE',
}

export function validate(values, keys) {
  const errors = {}
  for (const k of keys) {
    const f = FIELDS[k]
    const raw = String(values[k] ?? '').trim()
    const n = Number(raw)
    if (raw === '' || Number.isNaN(n)) errors[k] = 'Enter a number'
    else if (n < f.min || n > f.max) errors[k] = `Must be ${f.min} - ${f.max}`
    else if (f.int && !Number.isInteger(n)) errors[k] = 'Whole number'
  }
  return errors
}

export function numeric(values, keys) {
  return Object.fromEntries(keys.map((k) => [k, Number(values[k])]))
}
