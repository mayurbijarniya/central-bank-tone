"use client"

import { useMemo, useState } from "react"
import { Area, AreaChart, CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts"

import { inRange, RangeToggle, type Range } from "@/components/charts/range-toggle"
import { SplitGradient, zeroOffset } from "@/components/charts/split-gradient"
import { RateTooltip, ToneTooltip } from "@/components/charts/tooltips"
import { Section } from "@/components/section"
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart"
import { RATE } from "@/lib/format"
import type { RatePoint, TonePoint } from "@/lib/types"

const toneConfig = { tone: { label: "Tone" } } satisfies ChartConfig
const rateConfig = { rate: { label: "Policy rate", color: RATE } } satisfies ChartConfig

interface Row {
  m: string
  tone?: number
  n?: number
  rate?: number
  decision?: RatePoint["decision"]
}

const X_AXIS = {
  dataKey: "m",
  tickLine: false,
  axisLine: false,
  minTickGap: 56,
  tickMargin: 8,
  tickFormatter: (m: string) => m.slice(0, 4),
}

export function ToneRateChart({ tone, rates }: { tone: TonePoint[]; rates: RatePoint[] }) {
  const [range, setRange] = useState<Range>("all")

  // One row per month holding both series, so the two charts share an x-axis exactly.
  const rows = useMemo(() => {
    const byMonth = new Map<string, Row>()
    for (const p of tone) byMonth.set(p.m, { m: p.m, tone: p.tone, n: p.n })
    for (const p of rates) {
      byMonth.set(p.m, { ...(byMonth.get(p.m) ?? { m: p.m }), rate: p.rate, decision: p.decision })
    }
    const all = [...byMonth.values()].sort((a, b) => a.m.localeCompare(b.m))
    return inRange(all, range, all.at(-1)?.m ?? "")
  }, [tone, rates, range])

  const offset = zeroOffset(rows.flatMap((r) => (r.tone === undefined ? [] : [r.tone])))
  const hasRates = rows.some((r) => r.rate !== undefined)

  return (
    <Section
      title="Does the tone run ahead of the rate?"
      description="Speech tone over the previous three months, and the policy rate at the end of each month, on the same timeline. Hover over either chart to read the same month in both."
      action={<RangeToggle value={range} onChange={setRange} />}
    >
      <div className="space-y-1">
        <p className="text-sm font-medium">Speech tone</p>
        <ChartContainer config={toneConfig} className="aspect-auto h-56 w-full">
          <AreaChart data={rows} syncId="bank" margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
            <SplitGradient id="bank-tone" offset={offset} />
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis {...X_AXIS} hide />
            <YAxis
              tickLine={false}
              axisLine={false}
              width={48}
              tickCount={5}
              tickFormatter={(v: number) => (v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2))}
            />
            <ReferenceLine y={0} stroke="var(--muted-foreground)" strokeOpacity={0.6} />
            <ChartTooltip cursor={{ stroke: "var(--border)" }} content={<ToneTooltip countKey="n" countLabel="speeches" />} />
            <Area
              dataKey="tone"
              type="monotone"
              stroke="url(#bank-tone-stroke)"
              strokeWidth={1.75}
              fill="url(#bank-tone-fill)"
              baseValue={0}
              animationDuration={700}
              animationEasing="ease-out"
            />
          </AreaChart>
        </ChartContainer>
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium">Policy rate</p>
        {hasRates ? (
          <ChartContainer config={rateConfig} className="aspect-auto h-44 w-full">
            <LineChart data={rows} syncId="bank" margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis {...X_AXIS} />
              <YAxis tickLine={false} axisLine={false} width={48} tickCount={4} tickFormatter={(v: number) => `${v}%`} />
              <ChartTooltip cursor={{ stroke: "var(--border)" }} content={<RateTooltip />} />
              <Line
                dataKey="rate"
                type="stepAfter"
                connectNulls
                stroke="var(--color-rate)"
                strokeWidth={2}
                dot={false}
                animationDuration={700}
                animationEasing="ease-out"
              />
            </LineChart>
          </ChartContainer>
        ) : (
          <p className="rounded-lg bg-muted/50 p-6 text-center text-sm text-muted-foreground">
            The BIS does not publish a policy rate for this central bank, so only its tone is
            shown.
          </p>
        )}
      </div>
    </Section>
  )
}
