import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function randRange(min: number, max: number) {
  return Math.random() * (max - min) + min
}

function ParticleField() {
  const groupRef = useRef<THREE.Group>(null)
  const count = 220

  const particles = useMemo(() => {
    return new Array(count).fill(0).map(() => ({
      position: [randRange(-9, 9), randRange(-5, 5), randRange(-6, 2)] as [number, number, number],
      scale: randRange(0.02, 0.09),
      speed: randRange(0.05, 0.18),
      offset: randRange(0, Math.PI * 2),
      color: Math.random() > 0.72 ? '#fbbf24' : Math.random() > 0.4 ? '#34d399' : '#6ee7b7',
    }))
  }, [])

  useFrame((state) => {
    if (!groupRef.current) return
    groupRef.current.rotation.y = state.clock.elapsedTime * 0.03
    groupRef.current.children.forEach((child, i) => {
      const p = particles[i]
      child.position.y = p.position[1] + Math.sin(state.clock.elapsedTime * p.speed + p.offset) * 0.6
      child.position.x = p.position[0] + Math.cos(state.clock.elapsedTime * p.speed * 0.6 + p.offset) * 0.3
    })
  })

  return (
    <group ref={groupRef}>
      {particles.map((p, i) => (
        <mesh key={i} position={p.position} scale={p.scale}>
          <sphereGeometry args={[1, 8, 8]} />
          <meshStandardMaterial
            color={p.color}
            emissive={p.color}
            emissiveIntensity={0.6}
            roughness={0.3}
            transparent
            opacity={0.85}
          />
        </mesh>
      ))}
    </group>
  )
}

function CoreOrb() {
  const meshRef = useRef<THREE.Mesh>(null)
  useFrame((state) => {
    if (!meshRef.current) return
    meshRef.current.rotation.y = state.clock.elapsedTime * 0.15
    meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.2
    const s = 1 + Math.sin(state.clock.elapsedTime * 0.6) * 0.04
    meshRef.current.scale.set(s, s, s)
  })
  return (
    <mesh ref={meshRef} position={[0, 0, -2]}>
      <icosahedronGeometry args={[1.6, 1]} />
      <meshStandardMaterial
        color="#10b981"
        emissive="#059669"
        emissiveIntensity={0.35}
        wireframe
        transparent
        opacity={0.28}
      />
    </mesh>
  )
}

export function SeedField() {
  return (
    <Canvas
      camera={{ position: [0, 0, 7], fov: 50 }}
      dpr={[1, 1.6]}
      gl={{ antialias: true, alpha: true }}
    >
      <ambientLight intensity={0.6} />
      <pointLight position={[5, 5, 5]} intensity={40} color="#34d399" />
      <pointLight position={[-5, -3, 2]} intensity={20} color="#fbbf24" />
      <CoreOrb />
      <ParticleField />
    </Canvas>
  )
}
