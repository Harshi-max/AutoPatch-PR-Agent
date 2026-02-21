"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type Step = {
  index: number
  vars: Record<string, number | string>
  array?: number[]
  desc?: string
}

type GenerateResponse = {
  source: "offline" | "ai"
  language: "js" | "python"
  title: string
  explanation: string
  code: string
  steps: Step[]
}

function useSpeechRecognition() {
  const [supported, setSupported] = useState(false)
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState("")
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    const SR: any =
      typeof window !== "undefined" && ((window as any).webkitSpeechRecognition || (window as any).SpeechRecognition)
    if (SR) {
      setSupported(true)
      recognitionRef.current = new SR()
      recognitionRef.current.continuous = false
      recognitionRef.current.lang = "en-US"
      recognitionRef.current.onresult = (e: any) => {
        const t = Array.from(e.results)
          .map((r: any) => r[0].transcript)
          .join(" ")
        setTranscript((prev) => (prev ? prev + " " + t : t))
      }
      recognitionRef.current.onend = () => setListening(false)
    }
  }, [])

  const start = (lang: string) => {
    if (!recognitionRef.current) return
    recognitionRef.current.lang = lang
    setTranscript("")
    setListening(true)
    recognitionRef.current.start()
  }

  const stop = () => {
    if (!recognitionRef.current) return
    recognitionRef.current.stop()
  }

  return { supported, listening, transcript, start, stop }
}

export function Playground() {
  const [inputLang, setInputLang] = useState<"en-US" | "hi-IN" | "te-IN">("en-US")
  const [codeLang, setCodeLang] = useState<"js" | "python">("js")
  const [vizMode, setVizMode] = useState<"2d" | "3d">("2d")
  const [speed, setSpeed] = useState(600)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [current, setCurrent] = useState(0)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const { supported, listening, transcript, start, stop } = useSpeechRecognition()

  const currentStep = useMemo(() => {
    if (!result) return null
    return result.steps[current] ?? null
  }, [result, current])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const onPlay = () => {
    if (!result) return
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(
      () => {
        setCurrent((c) => {
          if (!result) return c
          if (c >= result.steps.length - 1) {
            if (timerRef.current) clearInterval(timerRef.current)
            return c
          }
          return c + 1
        })
      },
      Math.max(100, speed),
    )
  }

  const onPause = () => {
    if (timerRef.current) clearInterval(timerRef.current)
  }

  const onStep = (dir: 1 | -1) => {
    if (!result) return
    setCurrent((c) => {
      const next = c + dir
      if (next < 0) return 0
      if (next >= result.steps.length) return result.steps.length - 1
      return next
    })
  }

  const onReset = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    setCurrent(0)
  }

  async function generate() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch("/api/generate-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript: transcript || "Create a bubble sort visualization for [5,3,8,4,2]",
          language: codeLang,
        }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Request failed: ${res.status} ${text}`)
      }
      const data: GenerateResponse = await res.json()
      setResult(data)
      setCurrent(0)
    } catch (e: any) {
      setError(e?.message || "Failed to generate")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div id="playground" className="grid gap-6">
      <Card className="p-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <Select value={inputLang} onValueChange={(v: any) => setInputLang(v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Input language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en-US">English</SelectItem>
                <SelectItem value="hi-IN">Hindi</SelectItem>
                <SelectItem value="te-IN">Telugu</SelectItem>
              </SelectContent>
            </Select>

            <Select value={codeLang} onValueChange={(v: any) => setCodeLang(v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Code language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="js">JavaScript</SelectItem>
                <SelectItem value="python">Python</SelectItem>
              </SelectContent>
            </Select>

            <Tabs value={vizMode} onValueChange={(v: any) => setVizMode(v)}>
              <TabsList>
                <TabsTrigger value="2d">2D</TabsTrigger>
                <TabsTrigger value="3d">3D</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Speed</span>
              <div className="w-40">
                <Slider value={[speed]} min={100} max={1200} step={50} onValueChange={(v) => setSpeed(v[0])} />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={listening ? "secondary" : "default"}
              onClick={() => (listening ? stop() : start(inputLang))}
              disabled={!supported}
            >
              {supported ? (listening ? "Stop Mic" : "Start Mic") : "Mic Not Supported"}
            </Button>
            <Button onClick={generate} disabled={loading}>
              {loading ? "Generating..." : "Generate"}
            </Button>
          </div>
        </div>

        <p className="mt-3 text-sm text-muted-foreground">
          {transcript
            ? `Transcript: ${transcript}`
            : "Tip: Try “Sort the array [5,3,8,4,2] using bubble sort and show steps.”"}
        </p>
      </Card>

      {result && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold">{result.title}</h3>
                <Badge variant="outline">{result.language.toUpperCase()}</Badge>
                <Badge variant={result.source === "offline" ? "secondary" : "default"}>
                  {result.source === "offline" ? "Offline mode" : "AI"}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">{result.steps.length} steps</div>
            </div>
            <pre className="mt-2 overflow-auto rounded-lg border bg-muted/40 p-3 text-sm">
              <code>{result.code}</code>
            </pre>
            <p className="mt-3 text-sm text-muted-foreground">{result.explanation}</p>
          </Card>

          <Card className="p-4">
            <div className="mb-3 flex items-center gap-2">
              <Button size="sm" onClick={onPlay}>
                Play
              </Button>
              <Button size="sm" variant="secondary" onClick={onPause}>
                Pause
              </Button>
              <Button size="sm" variant="outline" onClick={() => onStep(-1)}>
                Step ←
              </Button>
              <Button size="sm" variant="outline" onClick={() => onStep(1)}>
                Step →
              </Button>
              <Button size="sm" variant="ghost" onClick={onReset}>
                Reset
              </Button>
              <div className="ml-auto text-xs text-muted-foreground">
                Step {current + 1}/{result.steps.length}
              </div>
            </div>

            {/* Visualization */}
            <div className="rounded-xl border bg-card p-4">
              {currentStep?.array ? (
                <Bars
                  data={currentStep.array}
                  mode={vizMode}
                  highlightKeys={Object.entries(currentStep.vars || {})
                    .filter(([k]) => k === "i" || k === "j")
                    .map(([, v]) => Number(v))}
                />
              ) : (
                <div className="text-sm text-muted-foreground">
                  {currentStep?.desc || "No array state in this step."}
                </div>
              )}
              {currentStep && (
                <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
                  {Object.entries(currentStep.vars || {}).map(([k, v]) => (
                    <div key={k} className="rounded-md border bg-muted/40 p-2 text-center">
                      <div className="text-xs text-muted-foreground">{k}</div>
                      <div className="font-medium">{String(v)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {error && (
        <Card className="border-destructive p-4">
          <div className="text-sm text-destructive">Error: {error}</div>
        </Card>
      )}
    </div>
  )
}

function Bars({
  data,
  mode,
  highlightKeys = [],
}: {
  data: number[]
  mode: "2d" | "3d"
  highlightKeys?: number[]
}) {
  const max = Math.max(1, ...data)
  return (
    <div
      className={cn(
        "grid h-56 grid-cols-12 items-end gap-2 rounded-lg border bg-muted/30 p-3",
        mode === "3d" && "perspective-1000",
      )}
    >
      {data.map((v, idx) => {
        const h = Math.round((v / max) * 100)
        const highlight = highlightKeys.includes(idx)
        return (
          <div key={idx} className="flex h-full items-end">
            <div
              className={cn("w-full rounded-md bg-primary/80 transition-all", highlight && "bg-primary")}
              style={{
                height: `${h}%`,
                transform: mode === "3d" ? "translateZ(0) rotateX(8deg) translateY(2px)" : "none",
              }}
              aria-label={`index ${idx} value ${v}`}
            />
          </div>
        )
      })}
    </div>
  )
}
