import { Section } from "@/components/section"

const POINTS = [
  {
    label: "Dovish",
    tone: "−1",
    text: "Points to easier policy: weak growth, rising unemployment, inflation below target, the case for lower rates.",
    className: "text-dove",
  },
  {
    label: "Balanced",
    tone: "0",
    text: "Neither way, or both at once: facts without a direction, or risks weighed evenly.",
    className: "text-muted-foreground",
  },
  {
    label: "Hawkish",
    tone: "+1",
    text: "Points to tighter policy: inflation too high, an overheating economy, the case for higher rates.",
    className: "text-hawk",
  },
]

/** What a tone score means, for readers new to the terms. */
export function ToneScale() {
  return (
    <Section
      eyebrow="Reading the numbers"
      title="What tone means"
      description="Every sentence about policy, prices, rates or the economy gets a score from −1 to +1: how strongly it leans towards higher or lower interest rates. A speech's tone is the average of its sentences; a bank's is the average of its recent speeches."
    >
      <div className="space-y-6">
        <div className="h-2 rounded-full bg-linear-to-r from-dove via-muted to-hawk" />
        <div className="grid gap-6 sm:grid-cols-3">
          {POINTS.map((point) => (
            <div key={point.label} className="space-y-1.5 sm:text-center sm:first:text-left sm:last:text-right">
              <p className={`font-medium ${point.className}`}>
                {point.label} <span className="font-mono">{point.tone}</span>
              </p>
              <p className="text-sm text-muted-foreground">{point.text}</p>
            </div>
          ))}
        </div>
        <p className="text-sm text-muted-foreground">
          In practice most speeches sit between −0.2 and +0.2: central bankers mix
          descriptions of the economy with policy signals, so averages move by small amounts and
          a shift of 0.1 is large.
        </p>
      </div>
    </Section>
  )
}
