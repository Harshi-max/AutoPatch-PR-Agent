"use client"

import { Canvas } from "@react-three/fiber"
import { OrbitControls } from "@react-three/drei"
import type { AlgoStep } from "@/lib/types"

export function AlgorithmVisualizer3D({ step }: { step: AlgoStep | null }) {
  if (!step || !step.arrays || step.arrays.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">No array data</div>
    )
  }

  const first = step.arrays[0]
  const values = first.values

  return (
    <Canvas camera={{ position: [0, 8, 14], fov: 50 }}>
      <ambientLight intensity={0.8} />
      <pointLight position={[10, 10, 10]} />
      <group position={[-(values.length / 2), 0, 0]}>
        {values.map((v, i) => (
          <mesh key={i} position={[i * 1.2, v / 4, 0]}>
            <boxGeometry args={[1, Math.max(0.5, v / 2), 1]} />
            <meshStandardMaterial color={i === first.highlightIndex ? "#0ea5e9" : "#64748b"} />
          </mesh>
        ))}
      </group>
      <OrbitControls />
    </Canvas>
  )
}
