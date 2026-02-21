"use client"

import { useMemo } from "react"
import type { Step } from "../playground"

type Props = {
  steps: Step[]
  index: number
}

export default function VisualizationPanel({ steps, index }: Props) {
  const current = steps[index] || {}
  const arr = (current.array || []) as number[]
  const max = useMemo(() => Math.max(1, ...arr, 1), [arr])

  return (
    <div>
      <div className="mb-3 text-sm opacity-80">{current.note || "Steps will appear here…"}</div>
      <div className="grid grid-cols-12 gap-2">
        {arr.map((value, i) => {
          const isActive = (current.highlight || []).includes(i)
          const h = Math.max(10, Math.round((value / max) * 120))
          return (
            <div key={i} className="col-span-1 flex items-end">
              <div
                className={`w-full rounded-sm transition-all duration-300 ${isActive ? "bg-primary" : "bg-muted-foreground/30"}`}
                style={{ height: `${h}px` }}
                aria-label={`Index ${i} value ${value}${isActive ? " active" : ""}`}
              />
            </div>
          )
        })}
      </div>

      {current.vars && (
        <div className="mt-4 rounded-md border p-3 text-xs">
          <div className="opacity-80 mb-1">Variables</div>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(current.vars).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between">
                <span className="opacity-70">{k}</span>
                <span className="font-mono">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
