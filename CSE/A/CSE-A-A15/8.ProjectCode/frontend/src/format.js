// hh:mm:ss for the activity log
export const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour12: false })

// 0..1 score where higher is worse: green below a third, amber to two thirds, red above
export const riskVar = (v) => (v >= 0.66 ? 'var(--alert)' : v >= 0.33 ? 'var(--warn)' : 'var(--ok)')
