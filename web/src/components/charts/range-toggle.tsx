"use client"

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"

export type Range = "all" | "10y" | "5y"

const OPTIONS: { value: Range; label: string }[] = [
  { value: "all", label: "All" },
  { value: "10y", label: "10 years" },
  { value: "5y", label: "5 years" },
]

export function RangeToggle({ value, onChange }: { value: Range; onChange: (r: Range) => void }) {
  return (
    <ToggleGroup
      type="single"
      size="sm"
      variant="outline"
      value={value}
      onValueChange={(next) => next && onChange(next as Range)}
    >
      {OPTIONS.map((option) => (
        <ToggleGroupItem key={option.value} value={option.value} className="px-3 text-xs">
          {option.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}

/** Keep the points from the start of the chosen range to the last month. */
export function inRange<T extends { m: string }>(points: T[], range: Range, last: string): T[] {
  if (range === "all") return points
  const years = range === "10y" ? 10 : 5
  const [y, m] = last.split("-").map(Number)
  const start = `${y - years}-${String(m).padStart(2, "0")}`
  return points.filter((p) => p.m >= start)
}
