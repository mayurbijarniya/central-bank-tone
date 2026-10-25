import type { Metadata } from "next"
import type { ReactNode } from "react"

import { BankCorrelationChart, DecisionToneChart, PlaceboChart } from "@/components/charts/findings-charts"
import { NextStep } from "@/components/next-step"
import { StatStrip } from "@/components/stat-strip"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { getSummary } from "@/lib/data"
import { count, percent, signed } from "@/lib/format"

export const metadata: Metadata = { title: "Findings" }

function modelName(id: string): string {
  return id.split("/").at(-1)?.replace(/-marathon$/, "") ?? id
}

function Question({
  n,
  title,
  verdict,
  children,
}: {
  n: number
  title: string
  verdict: ReactNode
  children: ReactNode
}) {
  return (
    <section className="reveal space-y-8 border-t pt-12">
      <div className="max-w-3xl space-y-3">
        <p className="font-mono text-xs text-muted-foreground">QUESTION {n}</p>
        <h2 className="text-3xl font-semibold tracking-tight text-balance">{title}</h2>
        <div className="text-lg text-muted-foreground text-pretty">{verdict}</div>
      </div>
      {children}
    </section>
  )
}

function ChartBlock({ title, note, children }: { title: string; note: string; children: ReactNode }) {
  return (
    <figure className="space-y-3">
      <figcaption className="space-y-1">
        <p className="font-medium">{title}</p>
        <p className="text-sm text-muted-foreground">{note}</p>
      </figcaption>
      {children}
    </figure>
  )
}

export default async function FindingsPage() {
  const s = await getSummary()
  const { llm_fomc_test: llm, scorer_fomc_test: local, crosscheck } = s.labeling
  const chosen = s.prediction.models[s.prediction.chosen]
  const lead = s.leadsOrFollows

  return (
    <div className="space-y-12">
      <header className="max-w-3xl space-y-3 pt-6">
        <h1 className="text-4xl font-semibold tracking-tight">Findings</h1>
        <p className="text-lg text-muted-foreground text-pretty">
          Three questions, written down before any model was built. Every number on this page
          comes straight from the pipeline&apos;s results file.
        </p>
      </header>

      <Question
        n={1}
        title="Can a cheap model read central bank tone?"
        verdict={
          <>
            About as well as published systems. Against {llm.n} Federal Reserve sentences labeled
            by people, the language model agreed {percent(llm.accuracy)} of the time and the free
            local model {percent(local.accuracy)}. A published benchmark puts zero-shot
            ChatGPT-3.5 at an F1 of 0.58 and a fine-tuned RoBERTa-large at 0.70.
          </>
        }
      >
        <StatStrip
          stats={[
            {
              label: "Language model vs people",
              value: percent(llm.accuracy),
              detail: `${modelName(crosscheck.models[0])}, zero-shot · weighted F1 ${llm.weighted_f1.toFixed(2)}`,
            },
            {
              label: "Local model vs people",
              value: percent(local.accuracy),
              detail: `bge-small + logistic regression · weighted F1 ${local.weighted_f1.toFixed(2)}`,
            },
            {
              label: "Two models agree, outside the Fed",
              value: percent(crosscheck.agreement),
              detail: `${crosscheck.sentences} sentences, ${crosscheck.banks} banks · Cohen's κ ${crosscheck.kappa.toFixed(2)}`,
            },
            {
              label: "Local model matches both",
              value: percent(crosscheck.scorer_on_consensus),
              detail: `on the ${crosscheck.consensus_sentences} sentences where they agree`,
            },
          ]}
        />
        <p className="max-w-3xl text-sm text-muted-foreground">
          No people have labeled other central banks&apos; speeches, so outside the Fed a second
          model from a different family ({modelName(crosscheck.models[1])}) labeled the same
          sentences. That shows the labels are consistent across models, not that they are right.
        </p>
      </Question>

      <Question
        n={2}
        title="Does tone move with policy?"
        verdict={
          <>
            Yes. A bank&apos;s tone over three months lines up with its rate change over the next
            three at {s.policy.banks_positive} of {s.policy.banks_total} central banks (sign test p
            = {s.policy.sign_test_p.toFixed(4)}). But it echoes the moves already made and the
            latest inflation figure as much as it anticipates the next ones.
          </>
        }
      >
        <div className="grid gap-12 lg:grid-cols-5 lg:gap-10">
          <div className="lg:col-span-3">
            <ChartBlock
              title="Tone against the coming rate change, by central bank"
              note={`Rank correlation over ${count(s.policy.months)} bank-months. Above zero: a more hawkish tone came before rate rises.`}
            >
              <BankCorrelationChart banks={s.policy.banks} />
            </ChartBlock>
          </div>
          <div className="space-y-12 lg:col-span-2">
            <ChartBlock
              title="Tone before each kind of decision"
              note="Mean tone over the three months before, with 95% intervals."
            >
              <DecisionToneChart rows={s.beforeDecisions} />
            </ChartBlock>
            <ChartBlock
              title="Leads, or follows?"
              note="Rank correlation of tone with each, across all bank-months."
            >
              <dl className="divide-y border-y text-sm">
                {[
                  ["Rate change in the past three months", lead.with_past_3m_change],
                  ["Latest inflation", lead.with_inflation],
                  ["Rate change in the next three months", lead.with_next_3m_change],
                  ["Next change, once the past change is known", lead.next_given_past],
                ].map(([label, value]) => (
                  <div key={label as string} className="flex justify-between gap-4 py-2.5">
                    <dt className="text-muted-foreground">{label}</dt>
                    <dd className="font-mono tabular-nums">{signed(value as number)}</dd>
                  </div>
                ))}
              </dl>
            </ChartBlock>
          </div>
        </div>
      </Question>

      <Question
        n={3}
        title="Does tone predict the next decision?"
        verdict={
          <>
            No, not once past rates and inflation are known. Adding tone moved the chosen
            model&apos;s test log loss from {chosen.baseline.test.log_loss.toFixed(3)} to{" "}
            {chosen.with_tone.test.log_loss.toFixed(3)}, slightly worse, and shuffled tone did as
            well as the real thing (placebo p = {s.placebo.p_value.toFixed(2)}).
          </>
        }
      >
        <div className="grid gap-12 lg:grid-cols-2 lg:gap-10">
          <ChartBlock
            title={`Test results, ${count(s.prediction.rows.test)} bank-months from 2020`}
            note="Trained on 1999–2016, chosen on 2017–2019, tested once. Lower log loss is better."
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Features</TableHead>
                  <TableHead className="text-right">Log loss</TableHead>
                  <TableHead className="text-right">Moves called</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(s.prediction.models).flatMap(([name, model]) =>
                  (["baseline", "with_tone"] as const).map((key) => (
                    <TableRow key={`${name}-${key}`}>
                      <TableCell className="capitalize">
                        {key === "baseline" ? name.replace("_", " ") : ""}
                        {name === s.prediction.chosen && key === "baseline" && (
                          <Badge variant="secondary" className="ml-2">chosen</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {key === "baseline" ? "Past rates and inflation" : "plus speech tone"}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {model[key].test.log_loss.toFixed(3)}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {percent(model[key].test.move_accuracy)}
                      </TableCell>
                    </TableRow>
                  )),
                )}
              </TableBody>
            </Table>
          </ChartBlock>
          <ChartBlock
            title={`Placebo test, ${s.placebo.runs} shuffles`}
            note="Each bank's tone shuffled across months: same values, no timing. Bars count how much each shuffle improved test log loss; the orange bar marks where real tone falls: among the shuffles, on the worse side, not beyond them."
          >
            <PlaceboChart placebo={s.placebo} />
          </ChartBlock>
        </div>
      </Question>
      <NextStep
        href="/score"
        label="Try the model yourself"
        text="Paste any central banker's words and see how each sentence is scored."
      />
    </div>
  )
}
