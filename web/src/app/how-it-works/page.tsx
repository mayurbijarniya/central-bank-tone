import { ArrowUpRight } from "lucide-react"
import type { Metadata } from "next"
import type { ReactNode } from "react"

import { GitHubMark } from "@/components/logo"
import { NextStep } from "@/components/next-step"
import { Button } from "@/components/ui/button"
import { getSummary } from "@/lib/data"
import { count, dateLabel, percent } from "@/lib/format"
import { AUTHOR, REPOSITORY } from "@/lib/site"

export const metadata: Metadata = { title: "How it works" }

function Part({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="reveal grid gap-4 border-t pt-8 md:grid-cols-[14rem_1fr] md:gap-10">
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      <div className="max-w-3xl space-y-4 text-muted-foreground [&_strong]:font-medium [&_strong]:text-foreground">
        {children}
      </div>
    </section>
  )
}

const STACK = [
  ["Data pipeline", "Python, polars, DuckDB, Parquet"],
  ["Language models", "DeepSeek V4.1 Flash and GLM 5.3 through an OpenAI-compatible API"],
  ["Local model", "fastembed (ONNX Runtime), BAAI/bge-small-en-v1.5, scikit-learn"],
  ["Statistics", "SciPy, scikit-learn: grouped cross-validation, gradient boosting, placebo tests"],
  ["API", "FastAPI, Uvicorn, Pydantic"],
  ["Website", "Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, Recharts"],
  ["Quality", "pytest with synthetic data of known answers, ruff, ESLint"],
]

export default async function HowItWorksPage() {
  const s = await getSummary()
  const { data, labeling } = s

  return (
    <div className="space-y-12">
      <header className="max-w-3xl space-y-4 pt-6">
        <h1 className="text-4xl font-semibold tracking-tight">How it was built</h1>
        <p className="text-lg text-muted-foreground text-pretty">
          From thirty years of raw speeches to a tested answer, and what the numbers can and
          cannot tell you.
        </p>
        <Button asChild variant="outline">
          <a href={REPOSITORY} target="_blank" rel="noreferrer">
            <GitHubMark className="size-4" /> Source code, data pipeline and tests
            <ArrowUpRight data-icon="inline-end" />
          </a>
        </Button>
      </header>

      <Part title="Why">
        <p>
          Interest rates move every price in finance: bonds, stocks, currencies and mortgages.
          Central bankers signal where rates are going in their speeches, and fund managers and
          analysts read them for that signal. There are hundreds a month from dozens of central
          banks. Tools that score that language exist for the US Federal Reserve; this project
          covers <strong>every central bank in the BIS archive</strong>, measures how well the
          scoring agrees with people, and tests whether it tells you anything about the next
          decision.
        </p>
      </Part>

      <Part title="Data">
        <p>
          <strong>{count(data.archive_speeches)} speeches</strong> from the Bank for International
          Settlements&apos; archive of central bankers&apos; speeches, {data.first_speech.slice(0, 4)}{" "}
          to {dateLabel(data.archive_last_speech)}, and{" "}
          <strong>{data.feed_speeches} newer speeches</strong> from the live feeds of the Federal
          Reserve, ECB, Bank of England, Bank of Canada and Reserve Bank of Australia. The archive
          has no institution column, so each speech is matched to its central bank from the
          speaker&apos;s title.
        </p>
        <p>
          Daily <strong>policy rates</strong> and monthly <strong>consumer prices</strong> come from
          the BIS as well. A month&apos;s decision is a move of at least 0.10 percentage points in the
          end-of-month rate.
        </p>
      </Part>

      <Part title="Reading tone">
        <p>
          Only sentences about policy, prices, rates or the real economy can lean one way, so the{" "}
          {count(data.policy_sentences)} such sentences are scored and the rest left out.
        </p>
        <ol className="list-decimal space-y-2 pl-5">
          <li>
            <strong>An answer key from people.</strong> The Trillion Dollar Words study labeled
            2,480 Federal Reserve sentences by hand. Its test file is used once, for the final
            score.
          </li>
          <li>
            <strong>A language model labels a sample.</strong> 8,001 sentences, spread across
            banks, labeled hawkish, dovish or neutral. Three models were compared on the training
            file; the fastest of the equally accurate ones was kept.
          </li>
          <li>
            <strong>A small model learns from both.</strong> Sentence embeddings and logistic
            regression, chosen over a word-count baseline by cross-validation grouped by speech.
            It runs on a laptop CPU, so the whole archive was scored once for free.
          </li>
          <li>
            <strong>A check outside the Fed.</strong> A second model from a different family
            labeled 150 sentences from 20 other banks; the two agreed{" "}
            {percent(labeling.crosscheck.agreement)} of the time.
          </li>
        </ol>
      </Part>

      <Part title="Testing it">
        <p>
          Every bank-month holds only what was known by the end of that month: tone from speeches
          already given, and inflation lagged a month because prices are published a month late.
          Models predict the next month&apos;s decision from past rates and inflation, then again
          with tone added. They are trained on 1999–2016, chosen on 2017–2019 and tested once on
          2020 onward.
        </p>
        <p>
          Any extra column lets a model fit a little noise, so a <strong>placebo test</strong>{" "}
          shuffles each bank&apos;s tone across months a hundred times. Tone counts only if it beats
          nearly all of the shuffles.
        </p>
      </Part>

      <Part title="Limits">
        <ul className="list-disc space-y-2 pl-5">
          <li>A model reads the tone, not people; single sentences are often misread.</li>
          <li>The human answer key is the Fed&apos;s; elsewhere there is only agreement between models.</li>
          <li>Every speaker counts the same; the archive does not say who votes.</li>
          <li>Not causal and not a trading signal: markets price expected decisions in advance.</li>
          <li>Only the five banks with live feeds are current; the rest follow the BIS archive.</li>
        </ul>
      </Part>

      <Part title="Built with">
        <dl className="divide-y border-y">
          {STACK.map(([layer, tools]) => (
            <div key={layer} className="grid gap-1 py-2.5 sm:grid-cols-[10rem_1fr]">
              <dt className="font-medium text-foreground">{layer}</dt>
              <dd>{tools}</dd>
            </div>
          ))}
        </dl>
      </Part>

      <Part title="About">
        <p>
          Built by <strong>{AUTHOR}</strong>. The code, the labels and every result are in the{" "}
          <a href={REPOSITORY} className="font-medium text-foreground underline-offset-4 hover:underline">
            repository
          </a>
          , so the analysis can be rerun from the raw data. The BIS data is for non-commercial use.
        </p>
      </Part>
      <NextStep
        href="/banks"
        label="Start with a central bank"
        text="Pick any of the 72 and see its tone against its own policy rate."
      />
    </div>
  )
}
