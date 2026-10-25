import type { Metadata } from "next"

import { NextStep } from "@/components/next-step"
import { ScoreForm } from "@/components/score-form"

export const metadata: Metadata = { title: "Score a speech" }

export default function ScorePage() {
  return (
    <div className="space-y-12">
      <header className="max-w-3xl space-y-3 pt-6">
        <h1 className="text-4xl font-semibold tracking-tight">Score a speech</h1>
        <p className="text-lg text-muted-foreground text-pretty">
          The same local model that scored the archive: sentence embeddings from bge-small and a
          classifier trained on human and language-model labels. It agrees with people about six
          times in ten on single sentences, so read a whole passage rather than one line.
        </p>
      </header>
      <ScoreForm />
      <NextStep
        href="/how-it-works"
        label="How it works"
        text="Where the data comes from, how the model was checked, and what it cannot tell you."
      />
    </div>
  )
}
