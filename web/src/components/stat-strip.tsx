import type { LucideIcon } from "lucide-react"

export interface Stat {
  label: string
  value: string
  detail?: string
  icon?: LucideIcon
}

/** A row of headline figures separated by thin rules. */
export function StatStrip({ stats }: { stats: Stat[] }) {
  return (
    <dl className="grid grid-cols-2 gap-y-6 border-y py-6 lg:grid-cols-4 lg:divide-x">
      {stats.map(({ label, value, detail, icon: Icon }) => (
        <div key={label} className="space-y-1.5 px-1 lg:px-6 lg:first:pl-0">
          <dt className="flex items-center gap-1.5 text-sm text-muted-foreground">
            {Icon && <Icon className="size-3.5" />}
            {label}
          </dt>
          <dd className="font-mono text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl">
            {value}
          </dd>
          {detail && <dd className="text-sm text-muted-foreground">{detail}</dd>}
        </div>
      ))}
    </dl>
  )
}
