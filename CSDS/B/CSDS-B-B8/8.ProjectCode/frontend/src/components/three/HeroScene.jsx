import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Float, PointMaterial, Points } from '@react-three/drei'
import * as THREE from 'three'

const FRAME_MS = 1000 / 60

// frameloop="demand" + our own rAF: renders at most 60fps and only while `active`.
function FrameLimiter({ active }) {
  const invalidate = useThree((s) => s.invalidate)
  useEffect(() => {
    if (!active) return undefined
    let raf
    let last = 0
    const tick = (t) => {
      raf = requestAnimationFrame(tick)
      if (t - last >= FRAME_MS - 1) {
        last = t
        invalidate()
      }
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [active, invalidate])
  return null
}

function spherePoints(count, radius) {
  const arr = new Float32Array(count * 3)
  // golden-spiral distribution with a little radial jitter, deterministic
  const golden = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2
    const r = Math.sqrt(1 - y * y)
    const theta = golden * i
    const jitter = radius * (1 + (Math.sin(i * 12.9898) * 43758.5453 % 1) * 0.08)
    arr[i * 3] = Math.cos(theta) * r * jitter
    arr[i * 3 + 1] = y * jitter
    arr[i * 3 + 2] = Math.sin(theta) * r * jitter
  }
  return arr
}

function Shield({ pointer, colors }) {
  const group = useRef()
  const inner = useRef()
  const shell = useMemo(() => new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(1.55, 1)), [])
  const core = useMemo(() => new THREE.EdgesGeometry(new THREE.OctahedronGeometry(0.72, 0)), [])
  const positions = useMemo(() => spherePoints(1600, 2.35), [])

  useFrame((state, delta) => {
    const d = Math.min(delta, 0.05)
    const g = group.current
    if (!g) return
    g.rotation.y += d * 0.12
    // ease toward the pointer
    g.rotation.x = THREE.MathUtils.lerp(g.rotation.x, pointer.current.y * 0.35, 0.05)
    g.rotation.z = THREE.MathUtils.lerp(g.rotation.z, -pointer.current.x * 0.18, 0.05)
    g.position.x = THREE.MathUtils.lerp(g.position.x, pointer.current.x * 0.25, 0.04)
    if (inner.current) {
      inner.current.rotation.x -= d * 0.35
      inner.current.rotation.y -= d * 0.22
    }
  })

  return (
    <group ref={group}>
      <Float speed={1.2} rotationIntensity={0.25} floatIntensity={0.6}>
        <lineSegments geometry={shell}>
          <lineBasicMaterial color={colors.accent} transparent opacity={0.75} />
        </lineSegments>
        <lineSegments ref={inner} geometry={core}>
          <lineBasicMaterial color={colors.accent2} transparent opacity={0.9} />
        </lineSegments>
      </Float>
      <Points positions={positions} stride={3}>
        <PointMaterial transparent color={colors.accent2} size={0.022} sizeAttenuation depthWrite={false} opacity={0.75} />
      </Points>
    </group>
  )
}

export default function HeroScene({ colors }) {
  const wrap = useRef(null)
  const pointer = useRef({ x: 0, y: 0 })
  const active = useActive(wrap)

  useEffect(() => {
    const move = (e) => {
      pointer.current.x = (e.clientX / window.innerWidth) * 2 - 1
      pointer.current.y = (e.clientY / window.innerHeight) * 2 - 1
    }
    window.addEventListener('pointermove', move, { passive: true })
    return () => window.removeEventListener('pointermove', move)
  }, [])

  return (
    <div ref={wrap} className="hero-canvas" aria-hidden="true">
      <Canvas
        frameloop="demand"
        dpr={[1, 1.75]}
        camera={{ position: [0, 0, 6], fov: 45 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <FrameLimiter active={active} />
        <Shield pointer={pointer} colors={colors} />
      </Canvas>
    </div>
  )
}

// Active only while the canvas is on screen and the tab is visible.
function useActive(ref) {
  const [onScreen, setOnScreen] = useState(true)
  const [tabVisible, setTabVisible] = useState(() => document.visibilityState === 'visible')
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const io = new IntersectionObserver(([e]) => setOnScreen(e.isIntersecting), { threshold: 0.01 })
    io.observe(el)
    const vis = () => setTabVisible(document.visibilityState === 'visible')
    document.addEventListener('visibilitychange', vis)
    return () => {
      io.disconnect()
      document.removeEventListener('visibilitychange', vis)
    }
  }, [ref])
  return onScreen && tabVisible
}
