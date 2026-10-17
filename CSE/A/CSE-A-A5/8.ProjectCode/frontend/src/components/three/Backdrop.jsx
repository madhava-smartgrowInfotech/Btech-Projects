import * as THREE from 'three'
import { useEffect, useRef } from 'react'
import { useTheme } from '../../lib/theme'

// Kinetic wire-grid: a perspective plane whose vertices ripple slowly. Pauses off-screen / in background tabs.
export default function Backdrop({ intensity = 1, className = '' }) {
  const host = useRef(null)
  const { tokens } = useTheme()
  const colors = useRef(tokens)
  colors.current = tokens
  const live = useRef({})

  useEffect(() => {
    const el = host.current
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
    } catch {
      return // no WebGL: the CSS .grid-bg fallback on the wrapper stays visible
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75))
    el.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
    camera.position.set(0, 3.2, 7)
    camera.lookAt(0, 0, -2)

    const SEG = 56
    const geo = new THREE.PlaneGeometry(40, 28, SEG, SEG)
    geo.rotateX(-Math.PI / 2)
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(colors.current.ok), wireframe: true, transparent: true, opacity: 0.32 })
    const mesh = new THREE.Mesh(geo, mat)
    mesh.position.set(0, -1.2, -6)
    scene.add(mesh)
    live.current = { mat }

    const pos = geo.attributes.position
    const base = Float32Array.from(pos.array)

    function size() {
      const w = el.clientWidth || 1
      const h = el.clientHeight || 1
      renderer.setSize(w, h, false)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    size()
    const ro = new ResizeObserver(size)
    ro.observe(el)

    let visible = true
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(el)

    const t0 = performance.now()
    let raf
    const mouse = { x: 0, y: 0 }
    const onMove = (e) => { mouse.x = (e.clientX / window.innerWidth - 0.5) * 2; mouse.y = (e.clientY / window.innerHeight - 0.5) * 2 }
    window.addEventListener('pointermove', onMove, { passive: true })

    function frame() {
      raf = requestAnimationFrame(frame)
      if (!visible || document.hidden) return
      const t = (performance.now() - t0) / 1000
      for (let i = 0; i < pos.count; i++) {
        const x = base[i * 3]
        const z = base[i * 3 + 2]
        pos.array[i * 3 + 1] = (Math.sin(x * 0.45 + t * 0.7) + Math.cos(z * 0.5 + t * 0.55)) * 0.32 * intensity
      }
      pos.needsUpdate = true
      camera.position.x += (mouse.x * 0.9 - camera.position.x) * 0.03
      camera.position.y += (3.2 - mouse.y * 0.4 - camera.position.y) * 0.03
      camera.lookAt(0, 0, -2)
      renderer.render(scene, camera)
    }
    frame()

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('pointermove', onMove)
      ro.disconnect()
      io.disconnect()
      geo.dispose()
      mat.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [intensity])

  // follow the theme without rebuilding the scene
  useEffect(() => {
    live.current.mat?.color.set(tokens.ok)
    if (live.current.mat) live.current.mat.opacity = tokens.bg && tokens.bg.toLowerCase() === '#f2f3ef' ? 0.4 : 0.32
  }, [tokens])

  return <div ref={host} className={`wiregrid pointer-events-none ${className}`} aria-hidden="true" />
}
