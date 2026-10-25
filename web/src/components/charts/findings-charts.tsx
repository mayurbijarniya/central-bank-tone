"use client"

import { Bar, BarChart, CartesianGrid, Cell, ErrorBar, LabelList, ReferenceLine, XAxis, YAxis } from "recharts"
import type { LabelProps } from "recharts"

import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart"
import { DOVE, HAWK, signed } from "@/lib/format"
import type { Summary } from "@/lib/types"

function Tip({ lines }: { lines: [string, string][] }) {
  return (
    <div className="grid min-w-40 gap-1 rounded-lg border bg-background px-3 py-2 text-xs shadow-lg">
      {lines.map(([label, value], i) =>
        i === 0 ? (
          <p key={label} className="font-medium">{label}</p>
        ) : (
          <div key={label} className="flex justify-between gap-6">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-mono tabular-nums">{value}</span>
          </div>
        ),
      )}
    </div>
  )
}

const rhoConfig = { rho: { label: "Rank correlation" } } satisfies ChartConfig
type BankRho = Summary["policy"]["banks"][number]

/** A value label just past the end of a horizontal bar: right of positive bars, left of negative. */
function EndLabel({ x, y, width, height, value }: LabelProps) {
  const v = Number(value)
  const [bx, by, bw, bh] = [x, y, width, height].map(Number)
  const end = bx + bw
  const positive = v >= 0
  return (
    <text
      x={positive ? end + 6 : end - 6}
      y={by + bh / 2}
      dominantBaseline="central"
      textAnchor={positive ? "start" : "end"}
      className="fill-muted-foreground font-mono text-[11px] tabular-nums"
    >
      {signed(v)}
    </text>
  )
}

/** Each bank's rank correlation between its tone and its coming rate change. */
export function BankCorrelationChart({ banks }: { banks: BankRho[] }) {
  const extent = Math.max(...banks.map((b) => Math.abs(b.rho))) + 0.12
  return (
    <ChartContainer
      config={rhoConfig}
      className="aspect-auto w-full"
      style={{ height: banks.length * 28 + 40 }}
    >
      <BarChart data={banks} layout="vertical" margin={{ left: 0, right: 16, top: 0, bottom: 0 }}>
        <CartesianGrid horizontal={false} strokeDasharray="3 3" />
        <XAxis
          type="number"
          domain={[-Math.min(extent, 0.35), extent]}
          tickLine={false}
          axisLine={false}
          tickCount={6}
          tickFormatter={(v: number) => v.toFixed(1)}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={200}
          tickLine={false}
          axisLine={false}
          interval={0}
          tick={{ fontSize: 12 }}
        />
        <ReferenceLine x={0} stroke="var(--muted-foreground)" strokeOpacity={0.6} />
        <ChartTooltip
          cursor={{ fill: "var(--muted)", opacity: 0.5 }}
          content={({ active, payload }) => {
            const bank = payload?.[0]?.payload as BankRho | undefined
            if (!active || !bank) return null
            return (
              <Tip
                lines={[
                  [bank.name, ""],
                  ["Correlation", signed(bank.rho)],
                  ["Bank-months", bank.months.toLocaleString()],
                ]}
              />
            )
          }}
        />
        <Bar dataKey="rho" radius={3} barSize={16} animationDuration={700} animationEasing="ease-out">
          {banks.map((bank) => (
            <Cell key={bank.area} fill={bank.rho >= 0 ? HAWK : DOVE} />
          ))}
          <LabelList dataKey="rho" content={<EndLabel />} />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}

const decisionConfig = { mean_tone: { label: "Mean tone" } } satisfies ChartConfig
const DECISION_COLOR = { cut: DOVE, hold: "var(--muted-foreground)", hike: HAWK }
type DecisionRow = Summary["beforeDecisions"][number] & { label: string; error: [number, number] }

/** Mean tone in the three months before each kind of decision, with 95% intervals. */
export function DecisionToneChart({ rows }: { rows: Summary["beforeDecisions"] }) {
  const data: DecisionRow[] = rows.map((r) => ({
    ...r,
    label: `Before a ${r.decision}`,
    error: [r.mean_tone - r.low, r.high - r.mean_tone],
  }))
  const top = Math.max(...rows.map((r) => r.high), 0)
  const bottom = Math.min(...rows.map((r) => r.low), 0)
  const pad = (top - bottom) * 0.25

  return (
    <ChartContainer config={decisionConfig} className="aspect-auto h-72 w-full">
      <BarChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis
          domain={[bottom - pad, top + pad]}
          tickLine={false}
          axisLine={false}
          width={52}
          tickCount={5}
          tickFormatter={(v: number) => (v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2))}
        />
        <ReferenceLine y={0} stroke="var(--muted-foreground)" strokeOpacity={0.6} />
        <ChartTooltip
          cursor={{ fill: "var(--muted)", opacity: 0.5 }}
          content={({ active, payload }) => {
            const row = payload?.[0]?.payload as DecisionRow | undefined
            if (!active || !row) return null
            return (
              <Tip
                lines={[
                  [row.label, ""],
                  ["Mean tone", signed(row.mean_tone, 3)],
                  ["95% interval", `${signed(row.low, 3)} to ${signed(row.high, 3)}`],
                  ["Bank-months", row.months.toLocaleString()],
                ]}
              />
            )
          }}
        />
        <Bar dataKey="mean_tone" radius={4} maxBarSize={64} animationDuration={700} animationEasing="ease-out">
          {data.map((row) => (
            <Cell key={row.decision} fill={DECISION_COLOR[row.decision]} />
          ))}
          <ErrorBar dataKey="error" width={8} stroke="var(--foreground)" strokeWidth={1.25} />
          <LabelList
            dataKey="mean_tone"
            content={({ x, y, width, height, value, index }) => {
              const row = data[Number(index)]
              const v = Number(value)
              const [bx, by, bw, bh] = [x, y, width, height].map(Number)
              const barTop = Math.min(by, by + bh)
              const barBottom = Math.max(by, by + bh)
              // Beyond the 95% interval; a bar a few pixels tall gives no usable scale.
              const pixelsPerUnit = Math.abs(bh) / Math.max(Math.abs(v), 1e-9)
              const reach = (units: number) => (Math.abs(bh) >= 6 ? units * pixelsPerUnit : 10)
              const labelY =
                v >= 0 ? barTop - reach(row.error[1]) - 8 : barBottom + reach(row.error[0]) + 8
              return (
                <text
                  x={bx + bw / 2}
                  y={labelY}
                  textAnchor="middle"
                  dominantBaseline={v >= 0 ? "auto" : "hanging"}
                  className="fill-foreground font-mono text-xs font-medium tabular-nums"
                >
                  {signed(v, 3)}
                </text>
              )
            }}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}

const placeboConfig = { runs: { label: "Shuffles" } } satisfies ChartConfig

/** How much shuffled tone improved test log loss, against what real tone did. */
export function PlaceboChart({ placebo }: { placebo: Summary["placebo"] }) {
  const gains = placebo.shuffled_gains
  const min = Math.min(...gains, placebo.actual_gain)
  const max = Math.max(...gains, placebo.actual_gain)
  const bins = 16
  const width = (max - min) / bins
  const data = Array.from({ length: bins }, (_, i) => {
    const start = min + i * width
    const end = i === bins - 1 ? Infinity : start + width
    return { start, mid: start + width / 2, runs: gains.filter((g) => g >= start && g < end).length }
  })
  const actual = data.findIndex((d, i) => placebo.actual_gain < d.start + width || i === bins - 1)

  return (
    <ChartContainer config={placeboConfig} className="aspect-auto h-72 w-full">
      <BarChart data={data} margin={{ left: 0, right: 8, top: 24, bottom: 0 }} barCategoryGap={2}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis
          dataKey="mid"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          interval={3}
          tickFormatter={(v: number) => (v > 0 ? `+${v.toFixed(3)}` : v.toFixed(3))}
        />
        <YAxis tickLine={false} axisLine={false} width={32} allowDecimals={false} />
        <ChartTooltip
          cursor={{ fill: "var(--muted)", opacity: 0.5 }}
          content={({ active, payload }) => {
            const bin = payload?.[0]?.payload as (typeof data)[number] | undefined
            if (!active || !bin) return null
            return (
              <Tip
                lines={[
                  [`Change in log loss near ${signed(bin.mid, 3)}`, ""],
                  ["Shuffles", String(bin.runs)],
                ]}
              />
            )
          }}
        />
        <Bar dataKey="runs" radius={[3, 3, 0, 0]} animationDuration={700} animationEasing="ease-out">
          {data.map((bin, i) => (
            <Cell key={bin.start} fill={i === actual ? HAWK : DOVE} fillOpacity={i === actual ? 0.9 : 0.4} />
          ))}
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}
