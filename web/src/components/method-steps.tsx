import Link from "next/link"

import { Section } from "@/components/section"
import { count } from "@/lib/format"
import type { Summary } from "@/lib/types"

export function MethodSteps({ summary }: { summary: Summary }) {
  const { data, labeling } = summary
  const steps = [
    {
      title: "Collect",
      text: `${count(data.speeches)} speeches from the BIS archive and five central banks' live feeds, matched to each speaker's central bank, split into ${count(data.policy_sentences)} sentences about policy.`,
    },
    {
      title: "Label",
      text: `A language model labels 8,001 sampled sentences hawkish, dovish or neutral. Checked against people, it agrees ${(labeling.llm_fomc_test.accuracy * 100).toFixed(0)}% of the time on Federal Reserve sentences.`,
    },
    {
      title: "Score",
      text: "A small model that runs on a laptop learns from those labels and scores every sentence, so the archive is scored once for free and new speeches in seconds.",
    },
    {
      title: "Test",
      text: `Tone is tested against every rate decision of ${data.tested_banks} central banks, with a placebo test so that chance improvements are not mistaken for a signal.`,
    },
  ]

  return (
    <Section
      title="From raw speeches to a tested answer"
      description={
        <>
          Four steps, each checked before the next.{" "}
          <Link
            href="/how-it-works"
            transitionTypes={["nav-forward"]}
            className="font-medium text-foreground underline-offset-4 hover:underline"
          >
            See each step in detail
          </Link>
          .
        </>
      }
    >
      <ol className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((step) => (
          <li key={step.title} className="space-y-2">
            <h3 className="text-lg font-semibold tracking-tight">{step.title}</h3>
            <p className="text-sm text-muted-foreground">{step.text}</p>
          </li>
        ))}
      </ol>
    </Section>
  )
}
