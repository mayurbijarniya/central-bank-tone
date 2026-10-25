import { ViewTransition, type ReactNode } from "react"

/**
 * Slides a page in the direction of travel through the navigation, and crossfades
 * when a navigation carries no direction (the bank picker, the browser's back button).
 */
export function PageTransition({ children }: { children: ReactNode }) {
  return (
    <ViewTransition
      enter={{ "nav-forward": "nav-forward", "nav-back": "nav-back", default: "page-fade" }}
      exit={{ "nav-forward": "nav-forward", "nav-back": "nav-back", default: "page-fade" }}
      default="none"
    >
      <div>{children}</div>
    </ViewTransition>
  )
}
