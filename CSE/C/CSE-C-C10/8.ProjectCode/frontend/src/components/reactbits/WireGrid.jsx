import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Slow, undulating wireframe floor (three.js). Throttled to ~30 fps, paused when the tab is hidden.
// Calls onFail() when WebGL is unavailable so the caller can fall back to the CSS grid.
export default function WireGrid({ color = '#4ade80', opacity = 0.3, speed = 0.12, className = '', onFail }) {
  const ref = useRef(null)
  useEffect(() => {
    const host = ref.current
    if (!host) return
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' })
    } catch {
      onFail?.()
      return
    }
    renderer.setPixelRatio(Math.min(1.5, window.devicePixelRatio || 1))
    host.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 120)
    camera.position.set(0, 4.5, 11)
    camera.lookAt(0, 0, -8)

    const SIZE = 72, SEG = 48, cell = SIZE / SEG
    const geo = new THREE.PlaneGeometry(SIZE, SIZE, SEG, SEG)
    geo.rotateX(-Math.PI / 2)
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color), wireframe: true, transparent: true, opacity })
    const mesh = new THREE.Mesh(geo, mat)
    scene.add(mesh)
    const pos = geo.attributes.position
    const base = Float32Array.from(pos.array)

    const resize = () => {
      const w = host.clientWidth || 1, h = host.clientHeight || 1
      renderer.setSize(w, h, false)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(host)

    let raf, last = 0, visible = document.visibilityState === 'visible'
    const tick = (now) => {
      raf = requestAnimationFrame(tick)
      if (!visible || now - last < 33) return
      last = now
      const t = now / 1000
      const off = (t * speed * 6) % cell
      mesh.position.z = off
      for (let i = 0; i < pos.count; i++) {
        const x = base[i * 3], z = base[i * 3 + 2] + off // world z keeps the wave seamless across the loop
        pos.array[i * 3 + 1] = Math.sin(x * 0.16 + t * 0.5) * 0.45 + Math.cos(z * 0.2 + t * 0.35) * 0.45
      }
      pos.needsUpdate = true
      renderer.render(scene, camera)
    }
    raf = requestAnimationFrame(tick)
    const vis = () => { visible = document.visibilityState === 'visible' }
    document.addEventListener('visibilitychange', vis)
    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      document.removeEventListener('visibilitychange', vis)
      geo.dispose()
      mat.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [color, opacity, speed, onFail])
  return <div ref={ref} className={`wiregrid ${className}`} aria-hidden="true" />
}
