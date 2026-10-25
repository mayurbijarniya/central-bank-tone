import { ArrowLeft, Radio } from "lucide-react"
import type { Metadata } from "next"
import Link from "next/link"

import { BankPicker } from "@/components/bank-picker"
import { ToneRateChart } from "@/components/charts/tone-rate-chart"
import { NextStep } from "@/components/next-step"
import { SpeechesTable } from "@/components/speeches-table"
import { StatStrip } from "@/components/stat-strip"
import { ToneBadge } from "@/components/tone-badge"
import { Badge } from "@/components/ui/badge"
import { getBank, getBanks } from "@/lib/data"
import { count, dateLabel, flag, signed, stance } from "@/lib/format"

export async function generateStaticParams() {
  return (await getBanks()).map((bank) => ({ code: bank.code }))
}

export async function generateMetadata({ params }: PageProps<"/banks/[code]">): Promise<Metadata> {
  const { code } = await params
  return { title: (await getBank(code)).name }
}

export default async function BankPage({ params }: PageProps<"/banks/[code]">) {
  const { code } = await params
  const [bank, banks] = await Promise.all([getBank(code), getBanks()])
  const listed = banks.find((b) => b.code === code)
  const recent = listed?.recentTone ?? null

  return (
    <div className="space-y-14">
      <div className="space-y-6">
        <Link
          href="/banks"
          transitionTypes={["nav-back"]}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" /> All central banks
        </Link>
        <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{bank.region}</p>
            <h1 className="flex items-center gap-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              <span aria-hidden>{flag(bank.code)}</span>
              {bank.name}
            </h1>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              {recent === null ? (
                "Too few recent speeches for a current tone."
              ) : (
                <>
                  Sounds <span className="font-medium text-foreground">{stance(recent)}</span>{" "}
                  lately <ToneBadge tone={recent} />
                </>
              )}
              {listed?.live && (
                <Badge variant="outline">
                  <Radio data-icon="inline-start" /> Live feed
                </Badge>
              )}
            </div>
          </div>
          <BankPicker banks={banks} current={bank.code} />
        </header>
        <StatStrip
          stats={[
            { label: "Speeches", value: count(listed?.speeches ?? bank.speeches.length) },
            { label: "First speech", value: listed ? dateLabel(listed.first) : "–" },
            { label: "Latest speech", value: listed ? dateLabel(listed.last) : "–" },
            {
              label: "Tone vs coming rate moves",
              value: listed?.rho == null ? "Not tested" : signed(listed.rho),
              detail: listed?.rho == null ? "too few speeches or no published rate" : "rank correlation",
            },
          ]}
        />
      </div>

      <ToneRateChart tone={bank.tone} rates={bank.rates} />
      <SpeechesTable speeches={bank.speeches} />
      <NextStep
        href="/findings"
        label="Across all central banks"
        text="How tone lines up with rate moves at every bank tested, and whether it predicts them."
      />
    </div>
  )
}
