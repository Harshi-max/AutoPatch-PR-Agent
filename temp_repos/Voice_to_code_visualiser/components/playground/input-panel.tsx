"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Mic, Square } from "lucide-react"

type Props = {
  prompt: string
  setPrompt: (v: string) => void
  language: "javascript" | "python"
  setLanguage: (v: "javascript" | "python") => void
}

export default function InputPanel({ prompt, setPrompt, language, setLanguage }: Props) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    if (typeof window === "undefined") return
    // @ts-ignore
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const r = new SR()
    r.continuous = true
    r.interimResults = true
    r.onresult = (event: any) => {
      let final = ""
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const tr = event.results[i][0].transcript
        if (event.results[i].isFinal) final += tr
      }
      if (final) setPrompt((p) => (p ? p + " " + final : final))
    }
    recognitionRef.current = r
  }, [setPrompt])

  const toggleMic = () => {
    const r = recognitionRef.current
    if (!r) return
    if (!listening) {
      r.lang = language === "python" ? "en-US" : "en-US" // language detection can be extended
      try {
        r.start()
        setListening(true)
      } catch {}
    } else {
      try {
        r.stop()
      } catch {}
      setListening(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Button variant={listening ? "destructive" : "default"} onClick={toggleMic}>
          {listening ? (
            <>
              <Square className="mr-2 h-4 w-4" /> Stop
            </>
          ) : (
            <>
              <Mic className="mr-2 h-4 w-4" /> Mic
            </>
          )}
        </Button>

        <Select value={language} onValueChange={(v: "javascript" | "python") => setLanguage(v)}>
          <SelectTrigger className="w-[170px]">
            <SelectValue placeholder="Language" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="javascript">JavaScript</SelectItem>
            <SelectItem value="python">Python</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={5}
        placeholder="Describe your algorithm in English, Hindi, or Telugu… e.g., “Bubble sort this array: [5,3,8,4,2]”"
      />
    </div>
  )
}
