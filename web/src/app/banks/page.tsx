import { Radio } from "lucide-react"
import type { Metadata } from "next"

import { BankDirectory } from "@/components/bank-directory"
import { NextStep } from "@/components/next-step"
import { getBanks } from "@/lib/data"

export const metadata: Metadata = { title: "Central banks" }

export default async function BanksPage() {
  const banks = await getBanks()

  return (
    <div className="space-y-10">
      <header className="max-w-3xl space-y-3 pt-6">
        <h1 className="text-4xl font-semibold tracking-tight">Central banks</h1>
        <p className="text-lg text-muted-foreground text-pretty">
          {banks.length} monetary areas with speeches in the archive. Pick one to see its tone
          against its policy rate and its latest speeches.
        </p>
        <p className="text-sm text-muted-foreground">
          The badge is each bank&apos;s tone over the last six months. Banks marked{" "}
          <Radio className="inline size-3.5" /> publish live feeds and are current to the week;
          euro-area national banks count with the ECB from the day their country joins.
        </p>
      </header>
      <BankDirectory banks={banks} />
      <NextStep
        href="/findings"
        label="What the tone tells us"
        text="Whether tone moves with rates, and whether it predicts the next decision."
      />
    </div>
  )
}
