import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export function Section({
  eyebrow,
  title,
  description,
  action,
  children,
  className,
}: {
  eyebrow?: string
  title: string
  description?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn("reveal space-y-6", className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-3xl space-y-2">
          {eyebrow && (
            <p className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
              {eyebrow}
            </p>
          )}
          <h2 className="text-2xl font-semibold tracking-tight text-balance">{title}</h2>
          {description && <div className="text-muted-foreground text-pretty">{description}</div>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}
