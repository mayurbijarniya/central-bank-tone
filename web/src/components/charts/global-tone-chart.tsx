"use client"

import { useMemo, useState } from "react"
import { Area, AreaChart, CartesianGrid, ReferenceLine, XAxis, YAxis } from "recharts"

import { inRange, RangeToggle, type Range } from "@/components/charts/range-toggle"
import { SplitGradient, zeroOffset } from "@/components/charts/split-gradient"
import { ToneTooltip } from "@/components/charts/tooltips"
import { Section } from "@/components/section"
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart"
import type { GlobalPoint } from "@/lib/types"

const EVENTS = [
  { m: "2001-09", label: "Dot-com bust" },
  { m: "2008-09", label: "Lehman collapse" },
  { m: "2020-03", label: "Covid" },
  { m: "2022-03", label: "Hiking cycle" },
]

const config = { tone: { label: "Average tone" } } satisfies ChartConfig

export function GlobalToneChart({ points }: { points: GlobalPoint[] }) {
  const [range, setRange] = useState<Range>("all")
  const shown = useMemo(() => inRange(points, range, points.at(-1)?.m ?? ""), [points, range])
  const offset = zeroOffset(shown.map((p) => p.tone))
  const events = EVENTS.filter((e) => shown.some((p) => p.m === e.m))

  return (
    <Section
      title="How hawkish central banks sound, month by month"
      description="The average tone of the tested central banks' speeches over the previous three months. Tone turned sharply dovish in 2008 and 2020 and swung hawkish as inflation rose in 2022."
      action={<RangeToggle value={range} onChange={setRange} />}
    >
      <ChartContainer config={config} className="aspect-auto h-80 w-full sm:h-96">
        <AreaChart data={shown} margin={{ left: 0, right: 8, top: 28, bottom: 0 }}>
          <SplitGradient id="global" offset={offset} />
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="m"
            tickLine={false}
            axisLine={false}
            minTickGap={56}
            tickMargin={8}
            tickFormatter={(m: string) => m.slice(0, 4)}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={48}
            tickCount={5}
            tickFormatter={(v: number) => (v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2))}
          />
          <ReferenceLine y={0} stroke="var(--muted-foreground)" strokeOpacity={0.6} />
          {events.map((e) => (
            <ReferenceLine
              key={e.m}
              x={e.m}
              stroke="var(--muted-foreground)"
              strokeOpacity={0.35}
              strokeDasharray="2 3"
              label={{
                value: e.label,
                position: "top",
                offset: 10,
                fontSize: 11,
                fill: "var(--muted-foreground)",
              }}
            />
          ))}
          <ChartTooltip cursor={{ stroke: "var(--border)" }} content={<ToneTooltip countLabel="banks" countKey="banks" />} />
          <Area
            dataKey="tone"
            type="monotone"
            stroke="url(#global-stroke)"
            strokeWidth={2}
            fill="url(#global-fill)"
            baseValue={0}
            animationDuration={700}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ChartContainer>
    </Section>
  )
}
