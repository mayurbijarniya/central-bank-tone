"use client"

import { ArrowUpRight, Radio, Search } from "lucide-react"
import Link from "next/link"
import { useMemo, useState } from "react"

import { ToneBadge } from "@/components/tone-badge"
import { Input } from "@/components/ui/input"
import { count, flag } from "@/lib/format"
import type { Bank, Region } from "@/lib/types"

const REGIONS: Region[] = ["Americas", "Europe", "Asia-Pacific", "Middle East and Africa", "Other"]

export function BankDirectory({ banks }: { banks: Bank[] }) {
  const [query, setQuery] = useState("")
  const shown = useMemo(() => {
    const q = query.trim().toLowerCase()
    return q ? banks.filter((b) => `${b.name} ${b.code} ${b.region}`.toLowerCase().includes(q)) : banks
  }, [banks, query])

  return (
    <div className="space-y-10">
      <div className="relative max-w-md">
        <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by bank, country code or region"
          className="h-10 pl-9"
          aria-label="Search central banks"
        />
      </div>
      {REGIONS.map((region) => {
        const inRegion = shown.filter((b) => b.region === region)
        if (!inRegion.length) return null
        return (
          <section key={region} className="space-y-2">
            <h2 className="text-lg font-semibold tracking-tight">
              {region} <span className="font-normal text-muted-foreground">{inRegion.length}</span>
            </h2>
            <ul className="grid border-t sm:grid-cols-2 sm:gap-x-10">
              {inRegion.map((bank) => (
                <li key={bank.code} className="border-b">
                  <Link
                    href={`/banks/${bank.code}`}
                    transitionTypes={["nav-forward"]}
                    className="group flex items-center gap-3 px-1 py-3 transition-colors hover:bg-muted/60"
                  >
                    <span className="text-2xl leading-none" aria-hidden>
                      {flag(bank.code)}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5 font-medium">
                        <span className="truncate">{bank.name}</span>
                        {bank.live && <Radio className="size-3 shrink-0 text-muted-foreground" />}
                      </span>
                      <span className="block text-xs text-muted-foreground">
                        {count(bank.speeches)} speeches · {bank.first.slice(0, 4)}–{bank.last.slice(0, 4)}
                        {bank.tested && " · rate test"}
                      </span>
                    </span>
                    <ToneBadge tone={bank.recentTone} />
                    <ArrowUpRight className="size-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )
      })}
      {!shown.length && <p className="text-muted-foreground">No central bank matches “{query}”.</p>}
    </div>
  )
}
