import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

const VERT = /* glsl */ `
  uniform float uTime;
  uniform float uSize;
  uniform vec2 uPointer;
  attribute float aPhase;
  attribute float aScale;
  varying float vGlow;

  void main() {
    vec3 pos = position;

    // slow organic breathing along the shell normal
    float wave = sin(uTime * 0.55 + aPhase * 6.2831) * 0.055
               + sin(uTime * 0.23 + pos.y * 2.4) * 0.035;
    pos *= 1.0 + wave;

    // parallax lean toward the pointer
    pos.x += uPointer.x * 0.16 * (0.4 + aScale);
    pos.y += uPointer.y * 0.16 * (0.4 + aScale);

    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = uSize * aScale * (1.0 / -mv.z) * 60.0;

    vGlow = 0.35 + 0.65 * smoothstep(-1.4, 1.6, pos.z) * (0.55 + 0.45 * sin(uTime * 0.9 + aPhase * 9.0));
  }
`

const FRAG = /* glsl */ `
  precision mediump float;
  uniform vec3 uColorA;
  uniform vec3 uColorB;
  varying float vGlow;

  void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    if (d > 0.5) discard;
    float alpha = smoothstep(0.5, 0.06, d) * vGlow;
    vec3 color = mix(uColorB, uColorA, clamp(vGlow, 0.0, 1.0));
    gl_FragColor = vec4(color, alpha * 0.9);
  }
`

function fibonacciSphere(count: number, radius: number) {
  const positions = new Float32Array(count * 3)
  const phases = new Float32Array(count)
  const scales = new Float32Array(count)
  const golden = Math.PI * (3 - Math.sqrt(5))

  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2
    const r = Math.sqrt(Math.max(0, 1 - y * y))
    const theta = golden * i
    // slight shell thickness so it reads as volume, not a hollow skin
    const jitter = 0.86 + Math.random() * 0.2
    positions[i * 3] = Math.cos(theta) * r * radius * jitter
    positions[i * 3 + 1] = y * radius * jitter
    positions[i * 3 + 2] = Math.sin(theta) * r * radius * jitter
    phases[i] = Math.random()
    scales[i] = 0.45 + Math.random() * 0.85
  }
  return { positions, phases, scales }
}

/**
 * The intelligence layer, visualised: a slowly rotating volumetric point field with
 * an orbiting filament ring. Pointer parallax, DPR clamping, and it parks itself
 * whenever the tab or section is out of view.
 */
export function HeroScene({ className }: { className?: string }) {
  const mountRef = useRef<HTMLDivElement>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
    } catch {
      setFailed(true)
      return
    }

    const width = mount.clientWidth || 1
    const height = mount.clientHeight || 1

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8))
    renderer.setSize(width, height)
    renderer.setClearColor(0x000000, 0)
    mount.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100)
    camera.position.set(0, 0, 5.4)

    const group = new THREE.Group()
    scene.add(group)

    /* ---- particle shell ---- */
    const COUNT = window.innerWidth < 720 ? 2600 : 5200
    const { positions, phases, scales } = fibonacciSphere(COUNT, 1.65)
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1))
    geometry.setAttribute('aScale', new THREE.BufferAttribute(scales, 1))

    const uniforms = {
      uTime: { value: 0 },
      uSize: { value: 2.05 },
      uPointer: { value: new THREE.Vector2(0, 0) },
      uColorA: { value: new THREE.Color('#F3D194') },
      uColorB: { value: new THREE.Color('#3F5F9E') },
    }

    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: VERT,
      fragmentShader: FRAG,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })

    const points = new THREE.Points(geometry, material)
    group.add(points)

    /* ---- orbiting filament ring ---- */
    const ringPts: THREE.Vector3[] = []
    for (let i = 0; i <= 220; i++) {
      const a = (i / 220) * Math.PI * 2
      ringPts.push(new THREE.Vector3(Math.cos(a) * 2.35, Math.sin(a * 3) * 0.16, Math.sin(a) * 2.35))
    }
    const ringGeo = new THREE.BufferGeometry().setFromPoints(ringPts)
    const ringMat = new THREE.LineBasicMaterial({
      color: new THREE.Color('#E5A54B'),
      transparent: true,
      opacity: 0.28,
    })
    const ring = new THREE.Line(ringGeo, ringMat)
    ring.rotation.x = 1.12
    group.add(ring)

    const ring2Mat = new THREE.LineBasicMaterial({
      color: new THREE.Color('#6B93FF'),
      transparent: true,
      opacity: 0.18,
    })
    const ring2 = new THREE.Line(ringGeo, ring2Mat)
    ring2.rotation.set(0.5, 0.9, -0.6)
    group.add(ring2)

    /* ---- core glow ---- */
    const core = new THREE.Mesh(
      new THREE.SphereGeometry(0.62, 48, 48),
      new THREE.MeshBasicMaterial({ color: new THREE.Color('#1A1C22'), transparent: true, opacity: 0.85 }),
    )
    group.add(core)

    /* ---- interaction ---- */
    const pointer = { x: 0, y: 0 }
    const target = { x: 0, y: 0 }
    const onPointerMove = (event: PointerEvent) => {
      const rect = mount.getBoundingClientRect()
      target.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      target.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1)
    }
    window.addEventListener('pointermove', onPointerMove, { passive: true })

    /* ---- visibility gating ---- */
    let visible = true
    const observer = new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting
      },
      { threshold: 0.02 },
    )
    observer.observe(mount)

    /* ---- resize ---- */
    const resize = () => {
      const w = mount.clientWidth || 1
      const h = mount.clientHeight || 1
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    }
    const ro = new ResizeObserver(resize)
    ro.observe(mount)

    /* ---- loop ---- */
    const clock = new THREE.Clock()
    let frame = 0
    const render = () => {
      frame = requestAnimationFrame(render)
      // off-screen or backgrounded: keep the loop alive but skip the heavy work
      if (!visible || document.hidden) return
      const t = clock.getElapsedTime()
      pointer.x += (target.x - pointer.x) * 0.045
      pointer.y += (target.y - pointer.y) * 0.045

      uniforms.uTime.value = reduced ? 0 : t
      uniforms.uPointer.value.set(pointer.x, pointer.y)

      const spin = reduced ? 0.0 : 1
      group.rotation.y = t * 0.075 * spin + pointer.x * 0.28
      group.rotation.x = Math.sin(t * 0.14) * 0.09 * spin - pointer.y * 0.2
      ring.rotation.z = t * 0.11 * spin
      ring2.rotation.z = -t * 0.08 * spin

      renderer.render(scene, camera)
    }
    render()

    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      ro.disconnect()
      window.removeEventListener('pointermove', onPointerMove)
      geometry.dispose()
      material.dispose()
      ringGeo.dispose()
      ringMat.dispose()
      ring2Mat.dispose()
      core.geometry.dispose()
      ;(core.material as THREE.Material).dispose()
      renderer.dispose()
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div className={className} ref={mountRef} aria-hidden>
      {failed && (
        <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_45%,rgba(229,165,75,0.22),transparent_70%)]" />
      )}
    </div>
  )
}
