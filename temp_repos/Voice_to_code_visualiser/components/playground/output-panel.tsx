"use client"

import Editor from "@monaco-editor/react"

type Props = {
  language: "javascript" | "python"
  code: string
  setCode: (v: string) => void
}

export default function OutputPanel({ language, code, setCode }: Props) {
  return (
    <div className="rounded-md border">
      <Editor
        height="320px"
        defaultLanguage={language === "python" ? "python" : "javascript"}
        language={language === "python" ? "python" : "javascript"}
        theme="vs-dark"
        value={code}
        onChange={(v) => setCode(v || "")}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          scrollBeyondLastLine: false,
          lineNumbers: "on",
        }}
      />
    </div>
  )
}
