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

// Double helix: two backbone strands joined by base-pair rungs, wrapped in a faint wireframe shell.
const TURNS = 3.2
const STEPS = 96
const HEIGHT = 5.2
const RADIUS = 0.95

function helixGeometry() {
  const strandA = []
  const strandB = []
  const rungs = []
  for (let i = 0; i < STEPS; i++) {
    const t = i / (STEPS - 1)
    const ang = t * TURNS * Math.PI * 2
    const y = (t - 0.5) * HEIGHT
    const a = [Math.cos(ang) * RADIUS, y, Math.sin(ang) * RADIUS]
    const b = [Math.cos(ang + Math.PI) * RADIUS, y, Math.sin(ang + Math.PI) * RADIUS]
    strandA.push(...a)
    strandB.push(...b)
    if (i % 3 === 0) rungs.push(...a, ...b)
  }
  return { a: new Float32Array(strandA), b: new Float32Array(strandB), rungs: new Float32Array(rungs) }
}

function Helix({ pointer, colors }) {
  const group = useRef()
  const geo = useMemo(() => helixGeometry(), [])
  const shell = useMemo(() => new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(2.55, 1)), [])
  const rungGeo = useMemo(() => {
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(geo.rungs, 3))
    return g
  }, [geo])

  useFrame((state, delta) => {
    const d = Math.min(delta, 0.05)
    const g = group.current
    if (!g) return
    g.rotation.y += d * 0.22
    // ease toward the pointer
    g.rotation.x = THREE.MathUtils.lerp(g.rotation.x, pointer.current.y * 0.3, 0.05)
    g.rotation.z = THREE.MathUtils.lerp(g.rotation.z, 0.32 - pointer.current.x * 0.15, 0.05)
    g.position.x = THREE.MathUtils.lerp(g.position.x, pointer.current.x * 0.25, 0.04)
  })

  return (
    <group ref={group}>
      <Float speed={1.1} rotationIntensity={0.15} floatIntensity={0.5}>
        <lineSegments geometry={rungGeo}>
          <lineBasicMaterial color={colors.accent2} transparent opacity={0.55} />
        </lineSegments>
        <Points positions={geo.a} stride={3}>
          <PointMaterial transparent color={colors.accent} size={0.09} sizeAttenuation depthWrite={false} opacity={0.95} />
        </Points>
        <Points positions={geo.b} stride={3}>
          <PointMaterial transparent color={colors.accent2} size={0.09} sizeAttenuation depthWrite={false} opacity={0.95} />
        </Points>
        <lineSegments geometry={shell}>
          <lineBasicMaterial color={colors.accent} transparent opacity={0.14} />
        </lineSegments>
      </Float>
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
        <Helix pointer={pointer} colors={colors} />
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
