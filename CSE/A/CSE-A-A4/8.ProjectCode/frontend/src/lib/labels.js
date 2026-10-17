// Display names for the three training modes the API calls classical / sa / qa.
export const MODES = ['classical', 'sa', 'qa']
export const MODE_LABEL = { classical: 'Classical', sa: 'Simulated annealing', qa: 'Quantum-inspired' }
export const MODE_CODE = { classical: 'PCD', sa: 'SAS', qa: 'QS' }
export const MODE_TONE = { classical: 'sky', sa: 'peach', qa: 'lavender' }
export const MODE_COLOR = { classical: '#A9D6FF', sa: '#FFC9A3', qa: '#C7B9FF' }

export const MERCHANTS = ['Grocery', 'Fuel', 'Restaurant', 'Travel', 'Electronics', 'Health', 'Online']
export const CHANNELS = ['Chip', 'Contactless', 'Online', 'Swipe']

export const RISK_TONE = { LOW: 'mint', MEDIUM: 'peach', HIGH: 'rose' }
export const RISK_ACTION = {
  LOW: 'Approve instantly',
  MEDIUM: 'Challenge with 3-D Secure',
  HIGH: 'Decline and alert the fraud team',
}
