import Link from "next/link"

import { GitHubMark, Logo } from "@/components/logo"
import { AUTHOR, REPOSITORY } from "@/lib/site"

const SOURCES = [
  { href: "https://www.bis.org/cbspeeches/download.htm", label: "BIS central bankers' speeches" },
  { href: "https://www.bis.org/statistics/dataportal/cbpol.htm", label: "BIS policy rates" },
  { href: "https://arxiv.org/abs/2305.07972", label: "Trillion Dollar Words labels" },
]

export function SiteFooter() {
  return (
    <footer className="mt-16 border-t">
      <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 text-sm sm:grid-cols-3 sm:px-6">
        <div className="space-y-3">
          <div className="flex items-center gap-2 font-semibold">
            <Logo className="size-6" /> Central Bank Tone
          </div>
          <p className="text-muted-foreground">
            A research project by {AUTHOR}: what central bankers say, and whether it tells you
            what they will do.
          </p>
          <a
            href={REPOSITORY}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground"
          >
            <GitHubMark className="size-4" /> Source code and data pipeline
          </a>
        </div>
        <div className="space-y-3">
          <p className="font-medium">Explore</p>
          <ul className="space-y-2 text-muted-foreground">
            <li><Link href="/banks" className="hover:text-foreground">Central banks</Link></li>
            <li><Link href="/findings" className="hover:text-foreground">Findings</Link></li>
            <li><Link href="/score" className="hover:text-foreground">Score a speech</Link></li>
            <li><Link href="/how-it-works" className="hover:text-foreground">How it works</Link></li>
          </ul>
        </div>
        <div className="space-y-3">
          <p className="font-medium">Data</p>
          <ul className="space-y-2 text-muted-foreground">
            {SOURCES.map((source) => (
              <li key={source.href}>
                <a href={source.href} target="_blank" rel="noreferrer" className="hover:text-foreground">
                  {source.label}
                </a>
              </li>
            ))}
            <li>For non-commercial use.</li>
          </ul>
        </div>
      </div>
    </footer>
  )
}
