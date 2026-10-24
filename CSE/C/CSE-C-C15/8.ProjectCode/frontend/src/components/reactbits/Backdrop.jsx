import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'

function webglOk() {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

// three.js wireframe terrain grid. Lazy-loads three, falls back to the CSS grid when motion is reduced
// or WebGL is missing, pauses when off-screen / tab hidden, and follows the light/dark theme.
export default function Backdrop({ intensity = 1, className = '' }) {
  const host = useRef(null)
  const reduced = useReducedMotion()
  const [fallback, setFallback] = useState(false)

  useEffect(() => {
    const el = host.current
    if (!el) return undefined
    if (reduced || !webglOk()) { setFallback(true); return undefined }
    setFallback(false)

    let disposed = false
    let raf = 0
    let cleanup = () => {}

    import('three').then((THREE) => {
      if (disposed) return
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
      renderer.setPixelRatio(1)
      el.appendChild(renderer.domElement)
      renderer.domElement.setAttribute('aria-hidden', 'true')

      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
      camera.position.set(0, 5.2, 9)
      camera.lookAt(0, 0, -4)

      const SEG = 40
      const geo = new THREE.PlaneGeometry(60, 40, SEG, SEG / 1.4 | 0)
      geo.rotateX(-Math.PI / 2)
      const base = geo.attributes.position.array.slice()
      const mat = new THREE.MeshBasicMaterial({ wireframe: true, transparent: true, opacity: 0.4 * intensity, color: 0x4ade80 })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.position.z = -6
      scene.add(mesh)

      const paint = () => {
        const cs = getComputedStyle(document.documentElement)
        mat.color.set(cs.getPropertyValue('--ok').trim() || '#4ade80')
        mat.opacity = (document.documentElement.dataset.theme === 'light' ? 0.28 : 0.4) * intensity
      }
      paint()
      const mo = new MutationObserver(paint)
      mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })

      const resize = () => {
        const w = el.clientWidth || 1
        const h = el.clientHeight || 1
        renderer.setSize(w, h, false)
        camera.aspect = w / h
        camera.updateProjectionMatrix()
      }
      resize()
      const ro = new ResizeObserver(resize)
      ro.observe(el)

      let visible = true
      const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
      io.observe(el)

      const pos = geo.attributes.position
      const t0 = performance.now()
      let last = 0
      const frame = (now) => {
        raf = requestAnimationFrame(frame)
        if (!visible || document.hidden || now - last < 33) return // ~30 fps is plenty for a slow wave
        last = now
        const t = (performance.now() - t0) / 1000
        for (let i = 0; i < pos.count; i += 1) {
          const x = base[i * 3]
          const z = base[i * 3 + 2]
          pos.array[i * 3 + 1] = Math.sin(x * 0.35 + t * 0.9) * 0.45 + Math.cos(z * 0.45 + t * 0.7) * 0.4
        }
        pos.needsUpdate = true
        renderer.render(scene, camera)
      }
      raf = requestAnimationFrame(frame)

      cleanup = () => {
        cancelAnimationFrame(raf)
        mo.disconnect(); ro.disconnect(); io.disconnect()
        geo.dispose(); mat.dispose(); renderer.dispose()
        renderer.domElement.remove()
      }
    }).catch(() => setFallback(true))

    return () => { disposed = true; cleanup() }
  }, [reduced, intensity])

  return (
    <div ref={host} className={`wiregrid pointer-events-none ${fallback ? 'grid-bg fade-mask' : ''} ${className}`} aria-hidden="true" />
  )
}
