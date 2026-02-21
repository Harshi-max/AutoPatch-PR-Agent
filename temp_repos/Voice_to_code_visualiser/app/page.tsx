"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { AlgorithmVisualizer2D } from "@/components/visualizer-2d"
import { AlgorithmVisualizer3D } from "@/components/visualizer-3d"
import { Controls } from "@/components/controls"
import { VoiceInput } from "@/components/voice-input"
import { CodePanel } from "@/components/code-panel"
import { LandingHero } from "@/components/landing-hero"
import type { AlgoResponse, AlgoStep } from "@/lib/types"

export default function HomePage() {
  const [transcript, setTranscript] = useState("")
  const [targetLang, setTargetLang] = useState<"javascript" | "python">("javascript")
  const [result, setResult] = useState<AlgoResponse | null>(null)
  const [steps, setSteps] = useState<AlgoStep[]>([])
  const [current, setCurrent] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speedMs, setSpeedMs] = useState(800)
  const [use3D, setUse3D] = useState(false)
  const [generating, setGenerating] = useState(false)

  // playback timer
  const timerRef = useRef<number | null>(null)
  useEffect(() => {
    if (playing && steps.length > 0) {
      timerRef.current = window.setInterval(() => {
        setCurrent((prev) => {
          const next = prev + 1
          if (next >= steps.length) {
            setPlaying(false)
            return prev
          }
          return next
        })
      }, speedMs) as unknown as number
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [playing, steps.length, speedMs])

  const currentStep = useMemo(() => steps[current] ?? null, [steps, current])

  async function handleGenerate() {
    if (!transcript.trim()) return
    setGenerating(true)
    setResult(null)
    setSteps([])
    setCurrent(0)
    setPlaying(false)

    try {
      const res = await fetch("/api/generate-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript,
          targetLanguage: targetLang,
        }),
      })
      if (!res.ok) throw new Error("Failed to generate")
      const data: AlgoResponse = await res.json()
      setResult(data)
      setSteps(data.steps || [])
      setCurrent(0)
    } catch (e) {
      console.error("[v0] generation error", e)
    } finally {
      setGenerating(false)
    }
  }

  function resetPlayback() {
    setPlaying(false)
    setCurrent(0)
  }

  return (
    <>
      <LandingHero />

      <main id="playground" className="mx-auto max-w-6xl p-6 md:p-10 space-y-6">
        <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-balance">Voice-to-Code Algorithm Visualizer</h1>
            <p className="text-muted-foreground">
              Speak commands in English, Hindi, or Telugu. Generate Python or JavaScript code and visualize it
              step-by-step.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Select value={targetLang} onValueChange={(v) => setTargetLang(v as any)}>
              <SelectTrigger className="w-[170px]">
                <SelectValue placeholder="Target language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="javascript">JavaScript</SelectItem>
                <SelectItem value="python">Python</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={handleGenerate} disabled={!transcript.trim() || generating}>
              {generating ? "Generating…" : "Run & Visualize"}
            </Button>
          </div>
        </header>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Voice Input</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <VoiceInput transcript={transcript} onTranscript={setTranscript} />
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Generated Code</CardTitle>
            </CardHeader>
            <CardContent>
              <CodePanel
                language={result?.language ?? targetLang}
                code={result?.code ?? ""}
                explanation={result?.explanation ?? ""}
              />
            </CardContent>
          </Card>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Visualization</CardTitle>
              <div className="flex items-center gap-2">
                <Button variant={use3D ? "default" : "secondary"} onClick={() => setUse3D(false)} aria-pressed={!use3D}>
                  2D
                </Button>
                <Button variant={use3D ? "secondary" : "outline"} onClick={() => setUse3D(true)} aria-pressed={use3D}>
                  3D (beta)
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {steps.length === 0 ? (
                <div className="text-muted-foreground">No steps yet. Generate code to see the visualization.</div>
              ) : (
                <div className="w-full">
                  {!use3D ? (
                    <AlgorithmVisualizer2D step={currentStep} />
                  ) : (
                    <div className="w-full h-[360px] rounded border">
                      <AlgorithmVisualizer3D step={currentStep} />
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Controls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Controls
                canPlay={steps.length > 0}
                playing={playing}
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                onStepForward={() => setCurrent((s) => Math.min(s + 1, Math.max(0, steps.length - 1)))}
                onStepBack={() => setCurrent((s) => Math.max(0, s - 1))}
                onReset={resetPlayback}
                speedMs={speedMs}
                onSpeedChange={setSpeedMs}
                current={current}
                total={steps.length}
              />
              <div className="space-y-2">
                <div className="text-sm font-medium">Step Description</div>
                <div className="text-sm text-muted-foreground min-h-12">{currentStep?.description || "—"}</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Trace Timeline</div>
                <ol className="text-xs max-h-[200px] overflow-auto pr-2 space-y-1">
                  {steps.map((s, i) => (
                    <li
                      key={i}
                      className={cn(
                        "rounded px-2 py-1 border",
                        i === current ? "bg-primary text-primary-foreground" : "bg-card",
                      )}
                    >
                      {i + 1}. {s.description}
                    </li>
                  ))}
                </ol>
              </div>
            </CardContent>
          </Card>
        </section>

        <footer className="text-xs text-muted-foreground">
          Tip: Try commands like “Sort this array [5,2,9,1] using bubble sort and show steps” in English, Hindi, or
          Telugu.
        </footer>
      </main>
    </>
  )
}
