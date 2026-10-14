import { useState } from 'react'
import { Crosshair, MapPin, PenLine } from 'lucide-react'
import { Alert, Button, Input, Tabs } from './ui'

/**
 * Browser GPS + (when the backend allows it) manual coordinates — the same two tabs as
 * ui/common.location_picker. Value: {lat, lon, accuracy|null}.
 */
export function LocationPicker({ value, onChange, allowManual, defaultLat = 17.385, defaultLon = 78.4867 }) {
  const [tab, setTab] = useState('gps')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [lat, setLat] = useState(String(defaultLat))
  const [lon, setLon] = useState(String(defaultLon))
  const [manualErr, setManualErr] = useState('')

  const locate = () => {
    setError('')
    if (!navigator.geolocation) {
      setError('This browser has no geolocation support.')
      return
    }
    setBusy(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setBusy(false)
        onChange({ lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy ?? 0 })
      },
      (e) => {
        setBusy(false)
        setError(
          e.code === 1
            ? 'Location permission was denied. Allow location for this site in the address bar and retry.'
            : e.code === 3
              ? 'Timed out waiting for a GPS fix. Move near a window or outdoors and retry.'
              : 'Your position is unavailable right now. Retry in a moment.',
        )
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 },
    )
  }

  const useManual = () => {
    const a = Number(lat)
    const b = Number(lon)
    if (!Number.isFinite(a) || a < -90 || a > 90 || !Number.isFinite(b) || b < -180 || b > 180) {
      setManualErr('Enter a latitude between −90 and 90 and a longitude between −180 and 180.')
      return
    }
    setManualErr('')
    onChange({ lat: a, lon: b, accuracy: null })
  }

  const tabs = [{ id: 'gps', label: 'Browser GPS', icon: Crosshair }]
  if (allowManual) tabs.push({ id: 'manual', label: 'Manual (testing)', icon: PenLine })

  return (
    <div className="stack" style={{ '--gap': '12px' }}>
      <Tabs label="Location source" tabs={tabs} value={tab} onChange={setTab} />
      {tab === 'gps' ? (
        <div className="stack" style={{ '--gap': '10px' }}>
          <p className="small muted">Allow the location permission when your browser asks.</p>
          <div>
            <Button icon={Crosshair} onClick={locate} loading={busy}>
              {busy ? 'Waiting for GPS fix…' : 'Get my location'}
            </Button>
          </div>
          {error && <Alert tone="error">{error}</Alert>}
        </div>
      ) : (
        <div className="stack" style={{ '--gap': '10px' }}>
          <div className="grid grid-2" style={{ '--gap': '12px' }}>
            <Input label="Latitude" type="number" step="0.000001" value={lat} onChange={(e) => setLat(e.target.value)} />
            <Input label="Longitude" type="number" step="0.000001" value={lon} onChange={(e) => setLon(e.target.value)} />
          </div>
          {manualErr && <Alert tone="error">{manualErr}</Alert>}
          <div>
            <Button icon={MapPin} onClick={useManual}>
              Use these coordinates
            </Button>
          </div>
        </div>
      )}
      {value && (
        <Alert tone="success">
          Location: <span className="mono">{value.lat.toFixed(6)}, {value.lon.toFixed(6)}</span>
          {value.accuracy !== null && value.accuracy !== undefined ? ` (±${Math.round(value.accuracy)} m)` : ' (manual)'}
        </Alert>
      )}
    </div>
  )
}
