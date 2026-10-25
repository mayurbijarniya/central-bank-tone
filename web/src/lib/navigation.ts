export const PAGES = [
  { href: "/", label: "Overview" },
  { href: "/banks", label: "Central banks" },
  { href: "/findings", label: "Findings" },
  { href: "/score", label: "Score a speech" },
  { href: "/how-it-works", label: "How it works" },
] as const

export function pageIndex(pathname: string): number {
  return PAGES.findLastIndex((page) =>
    page.href === "/" ? pathname === "/" : pathname.startsWith(page.href),
  )
}

/** The slide direction for moving from the current page to `href`. */
export function direction(pathname: string, href: string): "nav-forward" | "nav-back" {
  return pageIndex(href) >= pageIndex(pathname) ? "nav-forward" : "nav-back"
}
