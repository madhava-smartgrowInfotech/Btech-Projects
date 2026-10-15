import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'

// Slow wireframe floor drawn with three.js. three is imported on demand, so it costs nothing until this mounts.
// Reduced motion, a browser without WebGL, or a failed chunk keeps the static CSS grid from index.css.
export default function Backdrop({ intensity = 0.5, className = '' }) {
  const host = useRef(null)
  const reduced = useReducedMotion()
  const theme = useTheme()?.theme ?? 'dark'
  const [live, setLive] = useState(false)

  useEffect(() => {
    const el = host.current
    if (!el || reduced) return undefined
    let cancelled = false
    let frame = 0
    let cleanup = () => {}

    import('three')
      .then((THREE) => {
        if (cancelled) return
        let renderer
        try {
          renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
        } catch {
          return // no WebGL: the CSS grid stays
        }
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
        renderer.setClearColor(0x000000, 0)
        el.appendChild(renderer.domElement)

        const scene = new THREE.Scene()
        const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
        camera.position.set(0, 2.4, 7)
        camera.lookAt(0, 0, 0)

        const color = theme === 'light' ? 0x15803d : 0x4ade80
        const grid = new THREE.GridHelper(40, 40, color, color)
        grid.material.transparent = true
        grid.material.opacity = 0.12 + 0.2 * intensity
        scene.add(grid)

        const size = () => {
          const w = el.clientWidth || 1
          const h = el.clientHeight || 1
          renderer.setSize(w, h, false)
          camera.aspect = w / h
          camera.updateProjectionMatrix()
        }
        size()
        const ro = new ResizeObserver(size)
        ro.observe(el)

        const start = performance.now()
        const tick = (now) => {
          // one grid cell every 1.2 s, so the floor seems to roll towards the viewer
          grid.position.z = ((now - start) / 1200) % 1
          renderer.render(scene, camera)
          frame = requestAnimationFrame(tick)
        }
        frame = requestAnimationFrame(tick)
        setLive(true)

        cleanup = () => {
          ro.disconnect()
          grid.geometry.dispose()
          grid.material.dispose()
          renderer.dispose()
          renderer.domElement.remove()
        }
      })
      .catch(() => {}) // chunk failed to load: keep the CSS grid

    return () => {
      cancelled = true
      cancelAnimationFrame(frame)
      cleanup()
      setLive(false)
    }
  }, [reduced, intensity, theme])

  return (
    <div ref={host} aria-hidden="true" className={`wiregrid pointer-events-none ${live ? '' : 'grid-bg'} ${className}`} />
  )
}
