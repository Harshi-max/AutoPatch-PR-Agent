"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Editor from "@monaco-editor/react"

export function CodePanel({
  language,
  code,
  explanation,
}: {
  language: "javascript" | "python"
  code: string
  explanation?: string
}) {
  if (!code) {
    return <div className="text-muted-foreground">No code yet. Generate to see results.</div>
  }
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Badge variant="secondary" className="uppercase tracking-wide">
          {language}
        </Badge>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="h-[360px] overflow-hidden rounded-md">
            <Editor
              height="100%"
              theme="vs-dark"
              language={language === "python" ? "python" : "javascript"}
              value={code}
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 13,
                scrollBeyondLastLine: false,
                lineNumbers: "on",
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>
        </CardContent>
      </Card>

      {explanation ? <div className="text-sm text-muted-foreground whitespace-pre-wrap">{explanation}</div> : null}
    </div>
  )
}
