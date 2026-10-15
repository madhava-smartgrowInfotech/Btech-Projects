import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'

// three.js wireframe terrain: a slow travelling wave in the product's phosphor colour.
// three is imported lazily; with reduced motion it renders a single still frame, and without
// WebGL (or before it loads) the CSS grid shows instead.
export default function Backdrop({ intensity = 0.6, className = '' }) {
  const host = useRef(null)
  const reduced = useReducedMotion()
  const { theme } = useTheme()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const el = host.current
    if (!el) return
    let disposed = false
    let raf = 0
    let cleanup = () => {}

    import('three').then((THREE) => {
      if (disposed) return
      let renderer
      try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
      } catch {
        return // no WebGL: the CSS grid fallback stays
      }
      const css = getComputedStyle(document.documentElement)
      const color = new THREE.Color(css.getPropertyValue('--ok').trim() || '#4ade80')
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5))
      renderer.setClearColor(0x000000, 0)
      el.appendChild(renderer.domElement)

      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
      camera.position.set(0, 3.2, 6)
      camera.lookAt(0, 0, -2)

      const geo = new THREE.PlaneGeometry(26, 20, 52, 40)
      geo.rotateX(-Math.PI / 2)
      const mat = new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.32 * intensity + 0.1 })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.position.z = -4
      scene.add(mesh)

      const pos = geo.attributes.position
      const base = Float32Array.from(pos.array)
      const wave = (t) => {
        for (let i = 0; i < pos.count; i++) {
          const x = base[i * 3], z = base[i * 3 + 2]
          pos.array[i * 3 + 1] = (Math.sin(x * 0.7 + t) * 0.22 + Math.cos(z * 0.55 + t * 0.8) * 0.26) * intensity * 1.6
        }
        pos.needsUpdate = true
      }

      const resize = () => {
        const w = el.clientWidth || 1, h = el.clientHeight || 1
        renderer.setSize(w, h, false)
        camera.aspect = w / h
        camera.updateProjectionMatrix()
      }
      const ro = new ResizeObserver(resize)
      ro.observe(el)
      resize()

      const t0 = performance.now()
      const frame = () => {
        raf = requestAnimationFrame(frame)
        if (document.hidden) return
        wave(((performance.now() - t0) / 1000) * 0.6)
        renderer.render(scene, camera)
      }
      wave(1.2)
      renderer.render(scene, camera)
      if (!reduced) frame()
      setReady(true)

      cleanup = () => {
        cancelAnimationFrame(raf)
        ro.disconnect()
        geo.dispose()
        mat.dispose()
        renderer.dispose()
        renderer.domElement.remove()
      }
    }).catch(() => {})

    return () => { disposed = true; cleanup(); setReady(false) }
  }, [reduced, intensity, theme])

  return (
    <div aria-hidden="true" className={`pointer-events-none overflow-hidden ${className}`}>
      <div className={`grid-bg fade-mask absolute inset-0 transition-opacity duration-700 ${ready ? 'opacity-0' : 'opacity-100'}`} />
      <div ref={host} className="wiregrid absolute inset-0" />
    </div>
  )
}
