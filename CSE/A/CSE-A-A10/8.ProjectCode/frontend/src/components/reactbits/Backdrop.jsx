import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'

function webglOK() {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

// three.js wire grid: a perspective floor of lines that drifts toward the viewer with a soft pointer parallax.
// three is imported lazily; with reduced motion or no WebGL it falls back to the CSS grid (.grid-bg).
export default function Backdrop({ intensity = 1, className = '' }) {
  const host = useRef(null)
  const reduced = useReducedMotion()
  const { tokens } = useTheme()
  const [gl] = useState(webglOK)
  const live = gl && !reduced

  useEffect(() => {
    if (!live || !host.current) return undefined
    let stop = false
    let cleanup = () => {}
    import('three').then((THREE) => {
      if (stop || !host.current) return
      const el = host.current
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5))
      el.appendChild(renderer.domElement)
      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 120)
      camera.position.set(0, 4.2, 9)
      camera.lookAt(0, 0, -6)

      const color = new THREE.Color(tokens.ok || '#4ade80')
      const lines = new THREE.Group()
      const N = 36
      const size = 80
      const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.22 * intensity })
      const pts = []
      for (let i = -N; i <= N; i++) {
        const p = (i / N) * (size / 2)
        pts.push(new THREE.Vector3(-size / 2, 0, p), new THREE.Vector3(size / 2, 0, p))
        pts.push(new THREE.Vector3(p, 0, -size / 2), new THREE.Vector3(p, 0, size / 2))
      }
      lines.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), mat))
      scene.add(lines)

      // a few "vehicles" gliding along the grid lines
      const dots = []
      const dotMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(tokens.cyan || '#67e8f9') })
      for (let i = 0; i < 14; i++) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.12, 0.6), dotMat)
        const lane = Math.round((Math.random() * 2 - 1) * N) / N * (size / 2)
        const alongX = Math.random() > 0.5
        m.userData = { lane, alongX, speed: (0.6 + Math.random() * 1.4) * (Math.random() > 0.5 ? 1 : -1), pos: (Math.random() - 0.5) * size }
        m.position.y = 0.08
        dots.push(m)
        scene.add(m)
      }

      let mx = 0
      let w = 1
      let h = 1
      const resize = () => {
        w = el.clientWidth || 1
        h = el.clientHeight || 1
        renderer.setSize(w, h, false)
        renderer.domElement.style.width = '100%'
        renderer.domElement.style.height = '100%'
        camera.aspect = w / h
        camera.updateProjectionMatrix()
      }
      resize()
      const ro = new ResizeObserver(resize)
      ro.observe(el)
      const onMove = (e) => { mx = (e.clientX / window.innerWidth - 0.5) * 2 }
      window.addEventListener('pointermove', onMove, { passive: true })

      const clock = new THREE.Clock()
      let raf = 0
      let visible = true
      const io = new IntersectionObserver(([en]) => { visible = en.isIntersecting })
      io.observe(el)
      const tick = () => {
        raf = requestAnimationFrame(tick)
        if (!visible || document.hidden) return
        const t = clock.getElapsedTime()
        lines.position.z = (t * 0.9) % (size / (2 * N))
        camera.position.x += (mx * 1.6 - camera.position.x) * 0.04
        camera.lookAt(0, 0, -6)
        for (const d of dots) {
          const u = d.userData
          u.pos += u.speed * 0.016
          if (Math.abs(u.pos) > size / 2) u.pos = -Math.sign(u.pos) * size / 2
          if (u.alongX) { d.position.set(u.pos, 0.08, u.lane); d.rotation.y = Math.PI / 2 } else { d.position.set(u.lane, 0.08, u.pos); d.rotation.y = 0 }
        }
        renderer.render(scene, camera)
      }
      tick()
      cleanup = () => {
        cancelAnimationFrame(raf)
        io.disconnect()
        ro.disconnect()
        window.removeEventListener('pointermove', onMove)
        mat.dispose()
        dotMat.dispose()
        scene.traverse((o) => { o.geometry?.dispose?.() })
        renderer.dispose()
        renderer.domElement.remove()
      }
    }).catch(() => {})
    return () => { stop = true; cleanup() }
  }, [live, intensity, tokens.ok, tokens.cyan])

  return (
    <div className={`pointer-events-none overflow-hidden ${className}`} aria-hidden="true">
      {live ? <div ref={host} className="wiregrid absolute inset-0" /> : <div className="grid-bg fade-mask absolute inset-0" />}
    </div>
  )
}
