import { useState } from 'react'
import { Camera, ImageUp } from 'lucide-react'
import { FileDrop, Tabs } from './ui'
import { CameraCapture } from './CameraCapture'

/** Camera capture or file upload for a face photo. Value is a File (or null). */
export function FacePhotoInput({ label, value, onChange, mirrored = true, disabled }) {
  const hasCamera = typeof navigator !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia)
  const [mode, setMode] = useState(hasCamera ? 'camera' : 'upload')
  return (
    <div>
      <Tabs
        label={`${label} source`}
        value={mode}
        onChange={(m) => {
          setMode(m)
          onChange(null)
        }}
        tabs={[
          { id: 'camera', label: 'Camera', icon: Camera },
          { id: 'upload', label: 'Upload photo', icon: ImageUp },
        ]}
      />
      {mode === 'camera' ? (
        <CameraCapture label={label} mirrored={mirrored} value={value} onCapture={onChange} disabled={disabled} />
      ) : (
        <FileDrop label={`Drop ${label.toLowerCase()} here`} file={value} onFile={onChange} />
      )}
    </div>
  )
}
