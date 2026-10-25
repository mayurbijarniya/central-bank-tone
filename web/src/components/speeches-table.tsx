import { ArrowUpRight, Radio } from "lucide-react"

import { Section } from "@/components/section"
import { ToneBadge } from "@/components/tone-badge"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { dateLabel } from "@/lib/format"
import type { Speech } from "@/lib/types"

export function SpeechesTable({ speeches }: { speeches: Speech[] }) {
  return (
    <Section
      title="Latest speeches"
      description="Each speech's tone is the average over its sentences about policy, prices, rates or the economy. Open a speech to read it in full."
    >
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-32">Date</TableHead>
            <TableHead>Speech</TableHead>
            <TableHead className="w-24 text-right">Tone</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {speeches.map((speech) => (
            <TableRow key={`${speech.date}-${speech.url}`}>
              <TableCell className="align-top text-muted-foreground tabular-nums">
                {dateLabel(speech.date)}
              </TableCell>
              <TableCell className="whitespace-normal">
                <div className="flex flex-wrap items-start gap-x-2 gap-y-1">
                  {speech.url ? (
                    <a
                      href={speech.url}
                      target="_blank"
                      rel="noreferrer"
                      className="group font-medium underline-offset-4 hover:underline"
                    >
                      {speech.title ?? "Untitled speech"}
                      <ArrowUpRight className="ml-0.5 inline size-3.5 opacity-40 group-hover:opacity-100" />
                    </a>
                  ) : (
                    <span className="font-medium">{speech.title}</span>
                  )}
                  {speech.source === "feed" && (
                    <Badge variant="outline">
                      <Radio data-icon="inline-start" /> Live feed
                    </Badge>
                  )}
                </div>
                {speech.speaker && <p className="mt-0.5 text-xs text-muted-foreground">{speech.speaker}</p>}
              </TableCell>
              <TableCell className="text-right align-top">
                <ToneBadge tone={speech.tone} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Section>
  )
}
