import { Canvas, useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import * as THREE from 'three'

function ParticleGrid() {
  const pointsRef = useRef<THREE.Points>(null)
  const materialRef = useRef<THREE.PointsMaterial>(null)

  const { positions, count } = useMemo(() => {
    const cols = 64
    const rows = 36
    const spacingX = 0.34
    const spacingY = 0.34
    const arr = new Float32Array(cols * rows * 3)
    let i = 0
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        arr[i * 3] = (x - cols / 2) * spacingX
        arr[i * 3 + 1] = (y - rows / 2) * spacingY
        arr[i * 3 + 2] = 0
        i++
      }
    }
    return { positions: arr, count: cols * rows }
  }, [])

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    return geo
  }, [positions])

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    const pos = geometry.attributes.position as THREE.BufferAttribute
    for (let i = 0; i < count; i++) {
      const x = pos.getX(i)
      const y = pos.getY(i)
      const dist = Math.sqrt(x * x + y * y)
      const z = Math.sin(dist * 0.9 - t * 1.2) * 0.55 * Math.exp(-dist * 0.06)
      pos.setZ(i, z)
    }
    pos.needsUpdate = true

    if (pointsRef.current) {
      pointsRef.current.rotation.z = Math.sin(t * 0.05) * 0.05
    }
  })

  return (
    <points ref={pointsRef} geometry={geometry} rotation={[-0.55, 0, 0]}>
      <pointsMaterial
        ref={materialRef}
        size={0.028}
        color="#22d3ee"
        transparent
        opacity={0.75}
        sizeAttenuation
      />
    </points>
  )
}

export function ScanField() {
  return (
    <Canvas
      camera={{ position: [0, 2.2, 9], fov: 50 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true }}
    >
      <ambientLight intensity={0.6} />
      <ParticleGrid />
    </Canvas>
  )
}
