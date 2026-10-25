import { ArrowRight } from "lucide-react"
import Link from "next/link"

import { GlobalToneChart } from "@/components/charts/global-tone-chart"
import { MethodSteps } from "@/components/method-steps"
import { NextStep } from "@/components/next-step"
import { Section } from "@/components/section"
import { StatStrip } from "@/components/stat-strip"
import { ToneLeaderboard } from "@/components/tone-leaderboard"
import { ToneScale } from "@/components/tone-scale"
import { Button } from "@/components/ui/button"
import { getBanks, getGlobalTone, getSummary } from "@/lib/data"
import { count, dateLabel, percent } from "@/lib/format"

export default async function OverviewPage() {
  const [summary, points, banks] = await Promise.all([getSummary(), getGlobalTone(), getBanks()])
  const { data, labeling, policy, placebo } = summary

  return (
    <div className="space-y-20">
      <section className="space-y-8 pt-6">
        <div className="space-y-5">
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
            What are central banks really saying?
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground text-pretty">
            Central bankers hint at where interest rates are going in their speeches. This project
            reads thirty years of them from every central bank, scores each sentence as hawkish or
            dovish, and tests whether the tone tells you what the bank will do next.
          </p>
          <p className="text-sm text-muted-foreground">
            {count(data.speeches)} speeches · {data.central_banks} central banks ·{" "}
            {data.first_speech.slice(0, 4)} to {dateLabel(data.last_speech)}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/banks" transitionTypes={["nav-forward"]}>
              Explore a central bank <ArrowRight data-icon="inline-end" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/findings" transitionTypes={["nav-forward"]}>
              See the findings
            </Link>
          </Button>
        </div>
        <StatStrip
          stats={[
            {
              label: "Sentences scored",
              value: count(data.policy_sentences),
              detail: "about policy, prices, rates or the economy",
            },
            {
              label: "Agrees with people",
              value: percent(labeling.llm_fomc_test.accuracy),
              detail: `on ${labeling.llm_fomc_test.n} human-labeled Fed sentences`,
            },
            {
              label: "Tone moves with rates",
              value: `${policy.banks_positive} of ${policy.banks_total}`,
              detail: "central banks tested",
            },
            {
              label: "Predicts the next move",
              value: "No",
              detail: `no better than shuffled tone (p = ${placebo.p_value.toFixed(2)})`,
            },
          ]}
        />
      </section>

      <GlobalToneChart points={points} />

      <ToneScale />

      <ToneLeaderboard banks={banks} asOf={summary.lastSpeech} />

      <MethodSteps summary={summary} />

      <Section
        title="Tone follows the policy cycle; it does not call the next move"
        description={`Speech tone rises before hikes and falls before cuts at ${policy.banks_positive} of ${policy.banks_total} central banks. But it echoes the moves already made and the latest inflation figure as much as it anticipates the next, so once those are known it adds nothing to predicting next month's decision.`}
      >
        <Button asChild variant="outline">
          <Link href="/findings" transitionTypes={["nav-forward"]}>
            Read the three questions <ArrowRight data-icon="inline-end" />
          </Link>
        </Button>
      </Section>

      <NextStep
        href="/banks"
        label="Explore a central bank"
        text="Search the 72 monetary areas and see how each one's tone tracked its rates."
      />
    </div>
  )
}
