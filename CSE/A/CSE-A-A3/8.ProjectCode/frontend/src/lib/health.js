import { api } from './api'
import { useAsync } from './useAsync'

// Backend reachability, re-checked every 30 s so the topbar/sidebar badges stay honest.
export function useHealth() {
  const { data, error } = useAsync(api.health, [], { poll: 30000 })
  return { online: !!data && !error, offline: !!error, checking: !data && !error }
}
