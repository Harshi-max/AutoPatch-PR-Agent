"use client"

import type { AlgoStep } from "@/lib/types"
import { cn } from "@/lib/utils"

export function AlgorithmVisualizer2D({ step }: { step: AlgoStep | null }) {
  if (!step) return <div className="text-muted-foreground">No step</div>

  const arrays = step.arrays ?? []

  return (
    <div className="space-y-6">
      {/* Variables */}
      <section>
        <div className="text-sm font-medium mb-2">Variables</div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {Object.entries(step.variables || {}).map(([key, value]) => (
            <div key={key} className="rounded border p-2 text-sm">
              <div className="text-muted-foreground">{key}</div>
              <div className="font-mono">{formatValue(value)}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Arrays */}
      {arrays.length > 0 && (
        <section className="space-y-4">
          <div className="text-sm font-medium">Arrays</div>
          {arrays.map((arr, idx) => (
            <div key={idx} className="space-y-2">
              <div className="text-xs text-muted-foreground">{arr.name}</div>
              <div className="flex items-end gap-2">
                {arr.values.map((v, i) => (
                  <div
                    key={i}
                    className={cn(
                      "rounded-md border px-3 py-2 font-mono text-sm",
                      arr.highlightIndex === i ? "bg-primary text-primary-foreground" : "bg-card",
                    )}
                    aria-label={`Index ${i} value ${v}`}
                  >
                    {v}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}

function formatValue(v: any) {
  if (Array.isArray(v)) return `[${v.join(", ")}]`
  if (typeof v === "object") return JSON.stringify(v)
  return String(v)
}
