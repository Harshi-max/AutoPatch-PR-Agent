"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

type Props = {
  transcript: string
  onTranscript: (t: string) => void
}

export function VoiceInput({ transcript, onTranscript }: Props) {
  const [lang, setLang] = useState<"en-US" | "hi-IN" | "te-IN">("en-US")
  const [recording, setRecording] = useState(false)
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    // @ts-ignore
    const SpeechRecognition =
      typeof window !== "undefined" && (window.SpeechRecognition || (window as any).webkitSpeechRecognition)
    if (SpeechRecognition) {
      const recog = new SpeechRecognition()
      recog.lang = lang
      recog.interimResults = true
      recog.continuous = true

      recog.onresult = (event: any) => {
        let finalText = ""
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i]
          finalText += res[0].transcript
        }
        onTranscript(finalText)
      }

      recog.onerror = (e: any) => {
        console.log("[v0] speech error", e)
        setRecording(false)
      }
      recognitionRef.current = recog
    } else {
      recognitionRef.current = null
    }
  }, [lang, onTranscript])

  function start() {
    if (!recognitionRef.current) return
    try {
      recognitionRef.current.lang = lang
      recognitionRef.current.start()
      setRecording(true)
    } catch (_) {}
  }

  function stop() {
    if (!recognitionRef.current) return
    try {
      recognitionRef.current.stop()
    } catch (_) {}
    setRecording(false)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Select value={lang} onValueChange={(v) => setLang(v as any)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Language" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="en-US">English (US)</SelectItem>
            <SelectItem value="hi-IN">Hindi (India)</SelectItem>
            <SelectItem value="te-IN">Telugu (India)</SelectItem>
          </SelectContent>
        </Select>
        <Button
          onClick={recording ? stop : start}
          variant={recording ? "destructive" : "default"}
          disabled={!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)}
          aria-pressed={recording}
        >
          {recording ? "Stop" : "Record"}
        </Button>
      </div>

      {!("webkitSpeechRecognition" in window || "SpeechRecognition" in window) && (
        <div className="text-xs text-destructive">
          Browser speech recognition not available. Please type your prompt below.
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="prompt">Prompt</Label>
        <Textarea
          id="prompt"
          value={transcript}
          onChange={(e) => onTranscript(e.target.value)}
          placeholder="Describe the algorithm you want (e.g., 'bubble sort this array [5,2,9,1] and show steps')"
          className="min-h-[120px] font-mono"
        />
      </div>
    </div>
  )
}
