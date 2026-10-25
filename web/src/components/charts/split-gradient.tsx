import { DOVE, HAWK } from "@/lib/format"

/** Where zero falls in a series, as a share of its height from the top. */
export function zeroOffset(values: number[]): number {
  const max = Math.max(...values, 0)
  const min = Math.min(...values, 0)
  if (max === min) return 0.5
  return max / (max - min)
}

/** A vertical gradient: hawkish colour above zero, dovish below. */
export function SplitGradient({
  id,
  offset,
  opacity = 0.35,
}: {
  id: string
  offset: number
  opacity?: number
}) {
  return (
    <defs>
      <linearGradient id={`${id}-fill`} x1="0" y1="0" x2="0" y2="1">
        <stop offset={0} stopColor={HAWK} stopOpacity={opacity} />
        <stop offset={offset} stopColor={HAWK} stopOpacity={0.04} />
        <stop offset={offset} stopColor={DOVE} stopOpacity={0.04} />
        <stop offset={1} stopColor={DOVE} stopOpacity={opacity} />
      </linearGradient>
      <linearGradient id={`${id}-stroke`} x1="0" y1="0" x2="0" y2="1">
        <stop offset={offset} stopColor={HAWK} />
        <stop offset={offset} stopColor={DOVE} />
      </linearGradient>
    </defs>
  )
}
