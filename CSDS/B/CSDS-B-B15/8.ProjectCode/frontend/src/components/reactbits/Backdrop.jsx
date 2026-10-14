import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { useReducedMotion } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'

// Can this browser make a WebGL context? Checked once, without creating a renderer.
function hasWebGL() {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

/**
 * Slow wireframe grid drawn with three.js, scrolling towards the viewer.
 * Renders a plain CSS grid instead when the user prefers reduced motion or WebGL is unavailable.
 */
export default function Backdrop({ className = '' }) {
  const ref = useRef(null)
  const reduced = useReducedMotion()
  const { theme } = useTheme()
  const [webgl] = useState(hasWebGL)

  useEffect(() => {
    const host = ref.current
    if (!host || reduced || !webgl) return

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    renderer.domElement.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block'
    host.appendChild(renderer.domElement)

    // colours follow the active theme tokens
    const styles = getComputedStyle(document.documentElement)
    const accent = styles.getPropertyValue('--ok').trim() || '#4ade80'
    const muted = styles.getPropertyValue('--muted').trim() || '#9a9fa8'

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
    camera.position.set(0, 2.4, 7)
    camera.lookAt(0, 0, -2)

    const grid = new THREE.GridHelper(60, 60, accent, muted) // 1-unit cells
    grid.material.transparent = true
    grid.material.opacity = 0.35
    grid.material.depthWrite = false
    scene.add(grid)

    const resize = () => {
      const w = host.clientWidth
      const h = Math.max(host.clientHeight, 1)
      renderer.setSize(w, h, false)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(host)

    const clock = new THREE.Clock()
    let raf
    const frame = () => {
      // one cell per cycle keeps the loop seamless
      grid.position.z = -((clock.getElapsedTime() * 0.6) % 1)
      renderer.render(scene, camera)
      raf = requestAnimationFrame(frame)
    }
    frame()

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      grid.geometry.dispose()
      grid.material.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [reduced, webgl, theme])

  if (reduced || !webgl) return <div aria-hidden="true" className={`grid-bg absolute inset-0 ${className}`} />
  return <div ref={ref} aria-hidden="true" className={`absolute inset-0 overflow-hidden ${className}`} />
}
