import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useTheme } from '../../lib/theme'

const SPAN = 40 // world units across the grid
const CELLS = 36 // grid cells per side

// Slow wireframe floor (three.js). Colour follows the theme's --ok token; the canvas is styled by .wiregrid in index.css.
export default function WireGrid({ intensity = 0.5 }) {
  const host = useRef(null)
  const material = useRef(null)
  const theme = useTheme()
  const color = theme?.tokens?.ok || '#4ade80'

  useEffect(() => {
    if (material.current) material.current.color.set(color)
  }, [color])

  useEffect(() => {
    const el = host.current
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    } catch {
      el.classList.add('grid-bg') // no WebGL: fall back to the CSS grid
      return undefined
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 200)
    camera.position.set(0, 7, 14)
    camera.lookAt(0, 0, -4)

    const pts = []
    for (let i = 0; i <= CELLS; i++) {
      const p = -SPAN / 2 + (i * SPAN) / CELLS
      pts.push(-SPAN / 2, 0, p, SPAN / 2, 0, p, p, 0, -SPAN / 2, p, 0, SPAN / 2)
    }
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3))
    material.current = new THREE.LineBasicMaterial({
      color, transparent: true, opacity: 0.14 + 0.4 * intensity,
    })
    const grid = new THREE.LineSegments(geometry, material.current)
    scene.add(grid)

    const step = SPAN / CELLS
    const start = performance.now()
    let raf = 0
    const frame = (now) => {
      grid.position.z = (((now - start) / 1000) * 0.8) % step // scrolls one cell in a loop
      renderer.render(scene, camera)
      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)

    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      if (!width || !height) return
      renderer.setSize(width, height, false)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    })
    ro.observe(el)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      geometry.dispose()
      material.current.dispose()
      material.current = null
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [intensity]) // eslint-disable-line react-hooks/exhaustive-deps -- colour is applied by the effect above

  return <div ref={host} className="wiregrid h-full w-full" />
}
