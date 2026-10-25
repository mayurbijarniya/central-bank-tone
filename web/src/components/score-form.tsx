"use client"

import { LoaderCircle, Sparkles } from "lucide-react"
import { useState } from "react"

import { ToneBadge } from "@/components/tone-badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { percent, signed, stance } from "@/lib/format"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const EXAMPLES = [
  {
    label: "Hawkish",
    text: "Inflation has proved more persistent than we expected, and wage growth remains well above levels consistent with our target. The labour market is still tight. We stand ready to raise interest rates further if price pressures do not ease.",
  },
  {
    label: "Dovish",
    text: "Growth has slowed markedly over recent quarters and unemployment has started to rise. Inflation is now below our target and expected to fall further. With downside risks increasing, there is scope to lower interest rates to support the economy.",
  },
  {
    label: "Mixed",
    text: "Headline inflation has come down, but core inflation remains elevated. At the same time, economic activity has softened and job creation has slowed. We will keep policy restrictive for as long as needed, while watching closely for signs of weakness.",
  },
]

interface Scored {
  sentence: string
  tone: number
  label: "hawkish" | "dovish" | "neutral"
  hawkish: number
  dovish: number
  neutral: number
}

interface Result {
  tone: number | null
  policy_sentences: number
  sentences: Scored[]
}

const ROW = {
  hawkish: "border-l-hawk bg-hawk/6",
  dovish: "border-l-dove bg-dove/6",
  balanced: "border-l-border",
}

export function ScoreForm() {
  const [text, setText] = useState(EXAMPLES[2].text)
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function score() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      })
      if (!response.ok) throw new Error(`The scoring service answered ${response.status}.`)
      setResult((await response.json()) as Result)
    } catch (err) {
      setResult(null)
      setError(
        err instanceof TypeError
          ? "The scoring service is not reachable. Start it with `uvicorn cbtone.api:app`."
          : (err as Error).message,
      )
    } finally {
      setLoading(false)
    }
  }

  const position = result?.tone == null ? 50 : ((result.tone + 1) / 2) * 100

  return (
    <div className="grid gap-12 lg:grid-cols-5 lg:gap-10">
      <div className="space-y-4 lg:col-span-2">
        <div className="space-y-1">
          <p className="font-medium">Speech text</p>
          <p className="text-sm text-muted-foreground">Paste a passage, or start from an example.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <Button key={example.label} variant="outline" size="sm" onClick={() => setText(example.text)}>
              {example.label}
            </Button>
          ))}
        </div>
        <Textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          className="min-h-64 resize-y"
          placeholder="Paste a central banker's speech…"
          aria-label="Speech text"
        />
        <Button onClick={score} disabled={loading || !text.trim()} size="lg" className="w-full">
          {loading ? <LoaderCircle className="animate-spin" /> : <Sparkles />}
          {loading ? "Scoring…" : "Score tone"}
        </Button>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      <div className="space-y-6 lg:col-span-3">
        <div className="space-y-1">
          <p className="font-medium">Result</p>
          <p className="text-sm text-muted-foreground">
            Each sentence about policy, prices, rates or the economy, scored by the local model.
          </p>
        </div>
        {result === null ? (
          <p className="rounded-lg bg-muted/50 p-10 text-center text-sm text-muted-foreground">
            Scores appear here.
          </p>
        ) : result.tone === null ? (
          <p className="text-sm text-muted-foreground">
            No sentence about policy, prices, rates or the economy was found. Sentences need at
            least eight words.
          </p>
        ) : (
          <>
            <div className="space-y-2">
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-4xl font-semibold tabular-nums">{signed(result.tone)}</span>
                <span className="text-sm text-muted-foreground capitalize">
                  {stance(result.tone)} · {result.policy_sentences} policy{" "}
                  {result.policy_sentences === 1 ? "sentence" : "sentences"}
                </span>
              </div>
              <div className="relative h-2 rounded-full bg-linear-to-r from-dove via-muted to-hawk">
                <span
                  className="absolute top-1/2 size-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-foreground shadow"
                  style={{ left: `${position}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Dovish −1</span>
                <span>Hawkish +1</span>
              </div>
            </div>
            <ul className="space-y-2">
              {result.sentences.map((s, i) => (
                <li
                  key={i}
                  className={cn("rounded-r-md border-l-4 px-3 py-2 text-sm", ROW[stance(s.tone) ?? "balanced"])}
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="leading-relaxed">{s.sentence}</p>
                    <ToneBadge tone={s.tone} className="shrink-0" />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    hawkish {percent(s.hawkish, 0)} · dovish {percent(s.dovish, 0)} · neutral{" "}
                    {percent(s.neutral, 0)}
                  </p>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  )
}
