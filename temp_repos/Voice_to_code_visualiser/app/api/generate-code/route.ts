import { generateObject } from "ai"
import { z } from "zod"
import type { AlgoResponse } from "@/lib/types"

const AI_ENABLED = process.env.AI_ENABLED === "1"

const algoSchema = z.object({
  language: z.enum(["javascript", "python"]),
  code: z.string().describe("Complete, minimal runnable function or script"),
  explanation: z.string().describe("Beginner-friendly explanation of the logic"),
  steps: z
    .array(
      z.object({
        line: z.number().optional().describe("Approximate line number referenced"),
        description: z.string(),
        variables: z.record(z.union([z.string(), z.number(), z.boolean(), z.array(z.number()), z.array(z.string())])),
        arrays: z
          .array(
            z.object({
              name: z.string(),
              values: z.array(z.number()),
              highlightIndex: z.number().nullable().optional(),
            }),
          )
          .optional(),
      }),
    )
    .min(1),
})

function parseArrayFromTranscript(text: string): number[] {
  // Extract [1,2,3] style arrays or loose numbers in the text
  const bracketMatch = text.match(/\[([^\]]+)\]/)
  if (bracketMatch) {
    const nums = bracketMatch[1]
      .split(/[,\s]+/)
      .map((n) => Number(n))
      .filter((n) => Number.isFinite(n))
    if (nums.length) return nums
  }
  const loose = (text.match(/-?\d+(\.\d+)?/g) || []).map((n) => Number(n)).filter((n) => Number.isFinite(n))
  if (loose.length >= 2) return loose
  return [5, 2, 9, 1]
}

function makeBubbleSortTrace(arrInput: number[], lang: "javascript" | "python") {
  const steps: any[] = []
  const arr = [...arrInput]
  const n = arr.length
  steps.push({
    line: 1,
    description: "Initialize bubble sort",
    variables: { n, swaps: 0, i: 0, j: 0 },
    arrays: [{ name: "arr", values: [...arr], highlightIndex: null }],
  })
  let swaps = 0
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      steps.push({
        line: 2,
        description: `Compare arr[${j}] and arr[${j + 1}]`,
        variables: { i, j, n, swaps },
        arrays: [{ name: "arr", values: [...arr], highlightIndex: j }],
      })
      if (arr[j] > arr[j + 1]) {
        const tmp = arr[j]
        arr[j] = arr[j + 1]
        arr[j + 1] = tmp
        swaps++
        steps.push({
          line: 3,
          description: `Swap arr[${j}] and arr[${j + 1}]`,
          variables: { i, j, n, swaps },
          arrays: [{ name: "arr", values: [...arr], highlightIndex: j + 1 }],
        })
      }
    }
  }

  const jsCode = `function bubbleSort(arr){
  const a = arr.slice();
  const n = a.length;
  let swaps = 0;
  for (let i = 0; i < n - 1; i++){
    for (let j = 0; j < n - i - 1; j++){
      if (a[j] > a[j+1]){
        const t = a[j]; a[j] = a[j+1]; a[j+1] = t;
        swaps++;
      }
    }
  }
  return { sorted: a, swaps };
}
// Example:
console.log(bubbleSort([${arrInput.join(", ")}]));`

  const pyCode = `def bubble_sort(arr):
    a = list(arr)
    n = len(a)
    swaps = 0
    for i in range(n-1):
        for j in range(n-i-1):
            if a[j] > a[j+1]:
                a[j], a[j+1] = a[j+1], a[j]
                swaps += 1
    return {"sorted": a, "swaps": swaps}

# Example:
print(bubble_sort([${arrInput.join(", ")}]))`

  const explanation =
    "This is bubble sort. We repeatedly compare adjacent elements and swap them if they are out of order. " +
    "After each outer loop, the largest remaining element bubbles to the end. Steps highlight comparisons and swaps."

  return {
    code: lang === "javascript" ? jsCode : pyCode,
    steps,
    explanation,
  }
}

function localFallbackGenerate(transcript: string, targetLanguage: "javascript" | "python") {
  const t = (transcript || "").toLowerCase()
  const arr = parseArrayFromTranscript(t)
  // Simple keyword routing
  if (t.includes("bubble")) {
    const { code, steps, explanation } = makeBubbleSortTrace(arr, targetLanguage)
    const data = {
      language: targetLanguage,
      code,
      explanation,
      steps,
    }
    return data
  }

  // Generic loop demo fallback
  const steps = []
  let sum = 0
  steps.push({
    line: 1,
    description: "Initialize sum to 0",
    variables: { sum, i: 0 },
    arrays: [{ name: "arr", values: [...arr], highlightIndex: null }],
  })
  for (let i = 0; i < arr.length; i++) {
    steps.push({
      line: 2,
      description: `Add arr[${i}] to sum`,
      variables: { sum, i },
      arrays: [{ name: "arr", values: [...arr], highlightIndex: i }],
    })
    sum += arr[i]
    steps.push({
      line: 3,
      description: `sum is now ${sum}`,
      variables: { sum, i },
      arrays: [{ name: "arr", values: [...arr], highlightIndex: i }],
    })
  }

  const jsCode = `function sumArray(arr){
  let sum = 0;
  for (let i = 0; i < arr.length; i++){
    sum += arr[i];
  }
  return sum;
}
// Example:
console.log(sumArray([${arr.join(", ")}]));`

  const pyCode = `def sum_array(arr):
    s = 0
    for x in arr:
        s += x
    return s

# Example:
print(sum_array([${arr.join(", ")}]))`

  const explanation =
    "This program iterates through the array and accumulates the total. The visualization shows each index being highlighted as its value is added to sum."

  return {
    language: targetLanguage,
    code: targetLanguage === "javascript" ? jsCode : pyCode,
    explanation,
    steps,
  }
}

export async function POST(req: Request) {
  const { transcript, targetLanguage } = await req.json()

  const prompt = [
    "You are an assistant that converts natural language algorithm requests into code and a step-by-step execution trace suitable for visualization.",
    "- Return very clear, beginner-friendly steps. Keep each step small.",
    "- If the request includes an input array, include it in arrays[].values and update per step.",
    "- Use highlightIndex for the current index being compared or swapped.",
    "- Provide variables snapshot every step (like i, j, n, swaps).",
    "- Keep code small and readable.",
    `Target language: ${targetLanguage}.`,
    "Only return the structured object.",
    "",
    `User request: """${transcript}"""`,
  ].join("\n")

  if (!AI_ENABLED) {
    const lang = targetLanguage === "python" ? "python" : "javascript"
    const fallback = localFallbackGenerate(String(transcript || ""), lang as "javascript" | "python")
    return Response.json(fallback)
  }

  try {
    const { object } = await generateObject({
      model: "openai/gpt-5", // Will use Vercel AI Gateway if available
      schema: algoSchema,
      prompt,
      maxOutputTokens: 1500,
      temperature: 0.2,
    })

    // Type guard for runtime
    const data = algoSchema.parse(object) as AlgoResponse
    return Response.json(data)
  } catch (err: any) {
    console.log("[v0] AI call failed, using local fallback:", err?.message || err)
    // Fallback: produce deterministic visualization so UI keeps working
    const lang = targetLanguage === "python" ? "python" : "javascript"
    const fallback = localFallbackGenerate(String(transcript || ""), lang as "javascript" | "python")
    // Always return 200 with fallback data to avoid client failures
    return Response.json(fallback)
  }
}
