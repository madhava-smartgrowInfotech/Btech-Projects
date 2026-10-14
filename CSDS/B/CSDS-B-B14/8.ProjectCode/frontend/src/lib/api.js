import http from '../api'

// Calls the kit's layout makes (health ping for the status pill in the top bar).
export const api = {
  health: () => http.get('/health').then((r) => r.data),
}
