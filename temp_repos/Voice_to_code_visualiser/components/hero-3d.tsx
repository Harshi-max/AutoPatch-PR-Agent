"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import { useMemo, useRef } from "react"
import type * as THREE from "three"

function Bars() {
  const count = 18
  const group = useRef<THREE.Group>(null)
  const base = useMemo(
    () => Array.from({ length: count }, (_, i) => 0.4 + Math.random() * 3 + (i % 3 === 0 ? 1 : 0)),
    [count],
  )

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()
    if (!group.current) return
    group.current.children.forEach((child, i) => {
      const mesh = child as THREE.Mesh
      const pulse = Math.sin(t * 1.2 + i * 0.35) * 0.5 + 0.5
      const h = base[i] + pulse * 1.5
      const scaleY = Math.max(0.5, h)
      mesh.scale.set(1, scaleY, 1)
      mesh.position.y = scaleY / 2
      const hue = (0.55 + i / (count * 3)) % 1 // blue/teal range
      ;(mesh.material as THREE.MeshStandardMaterial).color.setHSL(hue, 0.55, 0.55)
      ;(mesh.material as THREE.MeshStandardMaterial).emissive.setHSL(hue, 0.25, 0.15)
    })
  })

  return (
    <group ref={group} position={[-(count - 1) * 0.6 * 0.5, 0, 0]}>
      {Array.from({ length: count }).map((_, i) => (
        <mesh key={i} position={[i * 0.6, 0.5, 0]}>
          <boxGeometry args={[0.5, 1, 0.5]} />
          <meshStandardMaterial metalness={0.3} roughness={0.3} />
        </mesh>
      ))}
    </group>
  )
}

function Dolly() {
  const tRef = useRef(0)
  useFrame(({ camera }, delta) => {
    tRef.current += delta
    // gentle circle around origin
    const r = 10
    const speed = 0.12
    const x = Math.cos(tRef.current * speed) * r
    const z = Math.sin(tRef.current * speed) * r
    camera.position.x = x
    camera.position.z = z
    camera.lookAt(0, 0.5, 0)
  })
  return null
}

export function HeroScene3D() {
  return (
    <div className="w-full h-[320px] md:h-[380px] rounded-xl border bg-card">
      <Canvas camera={{ position: [0, 6, 10], fov: 55 }}>
        {/* Lighting */}
        <ambientLight intensity={0.7} />
        <directionalLight position={[5, 10, 5]} intensity={0.9} />
        {/* Floor */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
          <planeGeometry args={[50, 50]} />
          <meshStandardMaterial color="#0b1220" metalness={0.1} roughness={0.9} />
        </mesh>
        {/* Animated bars */}
        <group position={[0, 0, 0]}>
          <Bars />
        </group>
        {/* Subtle camera dolly */}
        <Dolly />
      </Canvas>
    </div>
  )
}
