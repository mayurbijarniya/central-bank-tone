"use client"

import type { TooltipContentProps } from "recharts"

import { monthLabel, signed, stance } from "@/lib/format"

type Props = Partial<TooltipContentProps<number, string>>

function Frame({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="grid min-w-40 gap-1.5 rounded-lg border bg-background px-3 py-2 text-xs shadow-lg">
      <p className="font-medium">{title}</p>
      {children}
    </div>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-6">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono tabular-nums">{value}</span>
    </div>
  )
}

/** Tone for a month, with how many speeches or banks the average covers. */
export function ToneTooltip({
  active,
  payload,
  countKey,
  countLabel,
}: Props & { countKey: string; countLabel: string }) {
  const row = payload?.[0]?.payload
  if (!active || !row || row.tone === undefined) return null
  return (
    <Frame title={monthLabel(row.m)}>
      <Row label="Tone" value={signed(row.tone, 3)} />
      <Row label="Reads as" value={<span className="capitalize">{stance(row.tone)}</span>} />
      <Row label={countLabel[0].toUpperCase() + countLabel.slice(1)} value={row[countKey]} />
    </Frame>
  )
}

/** Policy rate for a month and the decision that month. */
export function RateTooltip({ active, payload }: Props) {
  const row = payload?.[0]?.payload
  if (!active || !row || row.rate === undefined) return null
  return (
    <Frame title={monthLabel(row.m)}>
      <Row label="Policy rate" value={`${row.rate.toFixed(2)}%`} />
      {row.decision && row.decision !== "hold" && (
        <Row label="Decision" value={<span className="capitalize">{row.decision}</span>} />
      )}
    </Frame>
  )
}
