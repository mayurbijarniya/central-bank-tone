import { Radio } from "lucide-react"
import Link from "next/link"

import { Section } from "@/components/section"
import { dateLabel, flag, signed } from "@/lib/format"
import type { Bank } from "@/lib/types"
import { cn } from "@/lib/utils"

/** Each bank's recent tone as a bar running left (dovish) or right (hawkish) of zero. */
export function ToneLeaderboard({ banks, asOf }: { banks: Bank[]; asOf: string }) {
  const ranked = banks
    .filter((b) => b.recentTone !== null)
    .sort((a, b) => (b.recentTone ?? 0) - (a.recentTone ?? 0))
  const scale = Math.max(...ranked.map((b) => Math.abs(b.recentTone ?? 0)), 0.05)

  return (
    <Section
      eyebrow="Right now"
      title="Who sounds most hawkish"
      description={
        <>
          Mean tone of each central bank&apos;s speeches in the six months to {dateLabel(asOf)}, for
          banks with at least three. Banks marked <Radio className="inline size-3.5" /> publish
          live feeds; the rest are as current as the BIS archive.
        </>
      }
    >
      <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_3.5rem] gap-x-4 border-b pb-2 text-xs text-muted-foreground">
        <span>Central bank</span>
        <span className="flex justify-between">
          <span>← dovish</span>
          <span>hawkish →</span>
        </span>
        <span className="text-right">Tone</span>
      </div>
      <ul className="-mt-4">
        {ranked.map((bank) => {
          const tone = bank.recentTone ?? 0
          return (
            <li key={bank.code}>
              <Link
                href={`/banks/${bank.code}`}
                transitionTypes={["nav-forward"]}
                className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_3.5rem] items-center gap-x-4 rounded-md py-2 text-sm transition-colors hover:bg-muted/60"
              >
                <span className="flex min-w-0 items-center gap-2 pl-1">
                  <span aria-hidden>{flag(bank.code)}</span>
                  <span className="truncate">{bank.name}</span>
                  {bank.live && <Radio className="size-3 shrink-0 text-muted-foreground" />}
                </span>
                <span className="relative h-2 rounded-full bg-muted">
                  <span className="absolute inset-y-[-3px] left-1/2 w-px bg-muted-foreground/40" />
                  <span
                    className={cn(
                      "absolute inset-y-0 rounded-full",
                      tone >= 0 ? "left-1/2 bg-hawk" : "right-1/2 bg-dove",
                    )}
                    style={{ width: `${(Math.abs(tone) / scale) * 50}%` }}
                  />
                </span>
                <span className="pr-1 text-right font-mono tabular-nums">{signed(tone)}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </Section>
  )
}
