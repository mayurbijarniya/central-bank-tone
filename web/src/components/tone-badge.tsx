import { Minus, TrendingDown, TrendingUp } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { signed, stance } from "@/lib/format"
import { cn } from "@/lib/utils"

const STYLES = {
  hawkish: "bg-hawk/12 text-hawk",
  dovish: "bg-dove/12 text-dove",
  balanced: "bg-muted text-muted-foreground",
}

const ICONS = { hawkish: TrendingUp, dovish: TrendingDown, balanced: Minus }

export function ToneBadge({ tone, className }: { tone: number | null; className?: string }) {
  const kind = stance(tone)
  if (kind === null) return <span className="text-muted-foreground">–</span>
  const Icon = ICONS[kind]
  return (
    <Badge variant="secondary" className={cn("tabular-nums", STYLES[kind], className)}>
      <Icon data-icon="inline-start" />
      {signed(tone)}
    </Badge>
  )
}
