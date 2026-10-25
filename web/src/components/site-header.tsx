"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useLayoutEffect, useRef, useState } from "react"

import { GitHubMark, Logo } from "@/components/logo"
import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { direction, pageIndex, PAGES } from "@/lib/navigation"
import { REPOSITORY } from "@/lib/site"
import { cn } from "@/lib/utils"

interface Indicator {
  left: number
  width: number
}

export function SiteHeader() {
  const pathname = usePathname()
  const current = pageIndex(pathname)
  const links = useRef<(HTMLAnchorElement | null)[]>([])
  const [indicator, setIndicator] = useState<Indicator | null>(null)

  // The active page is marked by a bar along the header's bottom edge that slides
  // to the current link with a CSS transition.
  useLayoutEffect(() => {
    const measure = () => {
      const link = links.current[current]
      setIndicator(link ? { left: link.offsetLeft, width: link.offsetWidth } : null)
    }
    measure()
    window.addEventListener("resize", measure)
    return () => window.removeEventListener("resize", measure)
  }, [current])

  return (
    <header
      style={{ viewTransitionName: "site-header" }}
      className="sticky top-0 z-40 border-b bg-background"
    >
      <div className="mx-auto flex h-14 w-full max-w-6xl items-stretch gap-4 px-4 sm:px-6">
        <Link
          href="/"
          transitionTypes={["nav-back"]}
          className="flex shrink-0 items-center gap-2.5 font-semibold tracking-tight"
        >
          <Logo className="size-7" />
          <span className="hidden md:inline">Central Bank Tone</span>
        </Link>
        <nav className="relative flex flex-1 items-stretch gap-1 overflow-x-auto text-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {indicator && (
            <span
              aria-hidden
              className="absolute bottom-0 h-0.5 bg-foreground transition-[left,width] duration-300 ease-out motion-reduce:transition-none"
              style={{ left: indicator.left, width: indicator.width }}
            />
          )}
          {PAGES.map((page, i) => {
            const active = i === current
            return (
              <Link
                key={page.href}
                ref={(node) => {
                  links.current[i] = node
                }}
                href={page.href}
                transitionTypes={[direction(pathname, page.href)]}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center px-2.5 whitespace-nowrap text-muted-foreground transition-colors hover:text-foreground focus-visible:text-foreground",
                  active && "font-medium text-foreground",
                )}
              >
                {page.label}
              </Link>
            )
          })}
        </nav>
        <div className="flex items-center gap-1">
          <Button asChild variant="ghost" size="icon" aria-label="Source code on GitHub">
            <a href={REPOSITORY} target="_blank" rel="noreferrer">
              <GitHubMark className="size-4" />
            </a>
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
