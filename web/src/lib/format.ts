export const HAWK = "var(--hawk)"
export const DOVE = "var(--dove)"
export const RATE = "var(--rate)"

const SPECIAL_FLAGS: Record<string, string> = { XM: "EU" }

/** The flag emoji for a BIS area code; the euro area uses the EU flag. */
export function flag(code: string): string {
  const iso = SPECIAL_FLAGS[code] ?? code
  if (!/^[A-Z]{2}$/.test(iso)) return "🏦"
  return String.fromCodePoint(...[...iso].map((c) => 0x1f1a5 + c.charCodeAt(0)))
}

export function signed(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "–"
  return `${value > 0 ? "+" : value < 0 ? "−" : ""}${Math.abs(value).toFixed(digits)}`
}

export function percent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`
}

export function count(value: number): string {
  return value.toLocaleString("en-US")
}

export function monthLabel(month: string): string {
  const [year, m] = month.split("-").map(Number)
  return new Date(Date.UTC(year, m - 1, 1)).toLocaleString("en-US", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  })
}

export function dateLabel(date: string): string {
  return new Date(`${date}T00:00:00Z`).toLocaleString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  })
}

export type Stance = "hawkish" | "dovish" | "balanced"

/** A tone this close to zero reads as balanced. */
const BALANCED = 0.02

export function stance(tone: number | null): Stance | null {
  if (tone === null) return null
  if (tone > BALANCED) return "hawkish"
  if (tone < -BALANCED) return "dovish"
  return "balanced"
}
