export interface Stat {
  label: string
  value: string
  detail?: string
}

/** A row of headline figures on a tinted field. */
export function StatStrip({ stats }: { stats: Stat[] }) {
  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-8 bg-muted/60 p-6 sm:p-8 lg:grid-cols-4">
      {stats.map(({ label, value, detail }) => (
        <div key={label} className="space-y-1.5">
          <dt className="text-sm text-muted-foreground">{label}</dt>
          <dd className="text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl">
            {value}
          </dd>
          {detail && <dd className="text-sm text-muted-foreground">{detail}</dd>}
        </div>
      ))}
    </dl>
  )
}
