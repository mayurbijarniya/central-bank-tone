"use client"

import { Check, ChevronsUpDown } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { count, flag } from "@/lib/format"
import type { Bank, Region } from "@/lib/types"
import { cn } from "@/lib/utils"

const REGIONS: Region[] = ["Americas", "Europe", "Asia-Pacific", "Middle East and Africa", "Other"]

export function BankPicker({ banks, current }: { banks: Bank[]; current: string }) {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const selected = banks.find((b) => b.code === current)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" aria-expanded={open} className="w-full justify-between sm:w-80">
          <span className="flex min-w-0 items-center gap-2">
            <span aria-hidden>{selected ? flag(selected.code) : "🏦"}</span>
            <span className="truncate">{selected?.name ?? "Choose a central bank"}</span>
          </span>
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-(--radix-popover-trigger-width) p-0 sm:w-80" align="start">
        <Command>
          <CommandInput placeholder="Search central banks…" />
          <CommandList>
            <CommandEmpty>No central bank found.</CommandEmpty>
            {REGIONS.map((region) => {
              const inRegion = banks.filter((b) => b.region === region)
              if (!inRegion.length) return null
              return (
                <CommandGroup key={region} heading={region}>
                  {inRegion.map((bank) => (
                    <CommandItem
                      key={bank.code}
                      value={`${bank.name} ${bank.code}`}
                      onSelect={() => {
                        setOpen(false)
                        router.push(`/banks/${bank.code}`)
                      }}
                    >
                      <span aria-hidden>{flag(bank.code)}</span>
                      <span className="flex-1 truncate">{bank.name}</span>
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {count(bank.speeches)}
                      </span>
                      <Check className={cn(bank.code === current ? "opacity-100" : "opacity-0")} />
                    </CommandItem>
                  ))}
                </CommandGroup>
              )
            })}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
