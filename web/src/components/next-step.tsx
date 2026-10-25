import { ArrowRight } from "lucide-react"
import Link from "next/link"

/** The link at the foot of each page to the natural next one. */
export function NextStep({ href, label, text }: { href: string; label: string; text: string }) {
  return (
    <Link
      href={href}
      transitionTypes={["nav-forward"]}
      className="group flex flex-col gap-1 bg-muted/60 p-6 transition-colors hover:bg-muted sm:flex-row sm:items-center sm:justify-between sm:p-8"
    >
      <span className="space-y-1">
        <span className="block text-xl font-semibold tracking-tight">Next: {label}</span>
        <span className="block text-muted-foreground">{text}</span>
      </span>
      <span className="mt-3 flex size-10 shrink-0 items-center justify-center rounded-full bg-background transition-transform group-hover:translate-x-1 sm:mt-0">
        <ArrowRight className="size-4" />
      </span>
    </Link>
  )
}
