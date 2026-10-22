import * as THREE from 'three'
import { useEffect, useRef } from 'react'
import { useTheme } from '../../lib/theme'

// Wireframe terrain: a flat grid whose vertices ride a slow wave, tilted like a control-room floor.
// Colours come from the theme tokens, so it re-tints on light/dark switch.
export default function GridScene({ intensity = 1, onFail }) {
  const host = useRef(null)
  const { tokens } = useTheme()
  const colorRef = useRef(tokens.ok)
  colorRef.current = tokens.ok
  const matRef = useRef(null)

  useEffect(() => {
    if (matRef.current && tokens.ok) matRef.current.color.set(tokens.ok)
  }, [tokens.ok])

  useEffect(() => {
    const el = host.current
    if (!el) return
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
    } catch {
      onFail?.()
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75))
    el.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
    camera.position.set(0, 3.2, 6)
    camera.lookAt(0, 0, -2)

    const geo = new THREE.PlaneGeometry(26, 20, 52, 40)
    geo.rotateX(-Math.PI / 2)
    const base = geo.attributes.position.array.slice()
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(colorRef.current || '#4ade80'), wireframe: true, transparent: true, opacity: 0.2 * intensity })
    matRef.current = mat
    const mesh = new THREE.Mesh(geo, mat)
    mesh.position.set(0, -1.2, -4)
    scene.add(mesh)

    function resize() {
      const w = el.clientWidth || 1
      const h = el.clientHeight || 1
      renderer.setSize(w, h, false)
      renderer.domElement.style.width = '100%'
      renderer.domElement.style.height = '100%'
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(el)

    let mx = 0
    let my = 0
    const onMove = (e) => {
      mx = (e.clientX / window.innerWidth - 0.5) * 2
      my = (e.clientY / window.innerHeight - 0.5) * 2
    }
    window.addEventListener('pointermove', onMove, { passive: true })

    let raf = 0
    let visible = true
    const io = new IntersectionObserver(([en]) => { visible = en.isIntersecting })
    io.observe(el)
    const t0 = performance.now()
    const pos = geo.attributes.position
    function frame() {
      raf = requestAnimationFrame(frame)
      if (!visible || document.hidden) return
      const t = (performance.now() - t0) / 1000
      for (let i = 0; i < pos.count; i++) {
        const x = base[i * 3]
        const z = base[i * 3 + 2]
        pos.array[i * 3 + 1] = Math.sin(x * 0.55 + t * 0.7) * 0.28 + Math.cos(z * 0.45 + t * 0.5) * 0.28
      }
      pos.needsUpdate = true
      camera.position.x += (mx * 0.9 - camera.position.x) * 0.04
      camera.position.y += (3.2 - my * 0.5 - camera.position.y) * 0.04
      camera.lookAt(0, 0, -2)
      renderer.render(scene, camera)
    }
    frame()

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      io.disconnect()
      window.removeEventListener('pointermove', onMove)
      geo.dispose()
      mat.dispose()
      renderer.dispose()
      renderer.domElement.remove()
      matRef.current = null
    }
  }, [intensity, onFail])

  return <div ref={host} className="wiregrid absolute inset-0" aria-hidden="true" />
}
