"use client"

import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Progress } from "@/components/ui/progress"

export function Controls({
  canPlay,
  playing,
  onPlay,
  onPause,
  onStepForward,
  onStepBack,
  onReset,
  speedMs,
  onSpeedChange,
  current,
  total,
}: {
  canPlay: boolean
  playing: boolean
  onPlay: () => void
  onPause: () => void
  onStepForward: () => void
  onStepBack: () => void
  onReset: () => void
  speedMs: number
  onSpeedChange: (ms: number) => void
  current: number
  total: number
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button onClick={onStepBack} disabled={!canPlay}>
          Step ◀
        </Button>
        {!playing ? (
          <Button onClick={onPlay} disabled={!canPlay}>
            Play ▶
          </Button>
        ) : (
          <Button variant="secondary" onClick={onPause}>
            Pause ⏸
          </Button>
        )}
        <Button onClick={onStepForward} disabled={!canPlay}>
          Step ▶
        </Button>
        <Button variant="outline" onClick={onReset} disabled={!canPlay}>
          Reset ↺
        </Button>
      </div>

      <div className="space-y-2">
        <Label>Speed</Label>
        <Slider
          value={[Math.max(100, Math.min(2000, speedMs))]}
          min={100}
          max={2000}
          step={100}
          onValueChange={(v) => onSpeedChange(v[0])}
        />
        <div className="text-xs text-muted-foreground">{speedMs} ms per step</div>
      </div>

      <div className="space-y-2">
        <Label>Progress</Label>
        <Progress value={total > 0 ? ((current + 1) / total) * 100 : 0} />
        <div className="text-xs text-muted-foreground">
          Step {total === 0 ? 0 : current + 1} / {total}
        </div>
      </div>
    </div>
  )
}
