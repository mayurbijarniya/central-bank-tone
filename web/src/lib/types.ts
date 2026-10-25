export type Decision = "hike" | "hold" | "cut" | null

export type Region = "Americas" | "Europe" | "Asia-Pacific" | "Middle East and Africa" | "Other"

export interface Bank {
  code: string
  name: string
  region: Region
  speeches: number
  first: string
  last: string
  recentTone: number | null
  recentSpeeches: number
  hasRates: boolean
  tested: boolean
  live: boolean
  rho: number | null
}

export interface TonePoint {
  m: string
  tone: number
  n: number
}

export interface RatePoint {
  m: string
  rate: number
  decision: Decision
}

export interface Speech {
  date: string
  speaker: string | null
  title: string | null
  url: string | null
  tone: number | null
  source: "bis" | "feed"
}

export interface BankDetail {
  code: string
  name: string
  region: Region
  tone: TonePoint[]
  rates: RatePoint[]
  speeches: Speech[]
}

export interface GlobalPoint {
  m: string
  tone: number
  banks: number
}

export interface Scores {
  accuracy: number
  macro_f1: number
  weighted_f1: number
  n: number
}

export interface ModelScores {
  log_loss: number
  macro_f1: number
  move_accuracy: number
  rows: number
  moves: number
}

export interface Summary {
  lastSpeech: string
  data: {
    speeches: number
    archive_speeches: number
    feed_speeches: number
    first_speech: string
    archive_last_speech: string
    last_speech: string
    central_banks: number
    policy_sentences: number
    tested_banks: number
  }
  labeling: {
    llm_fomc_test: Scores
    scorer_fomc_test: Scores
    crosscheck: {
      models: [string, string]
      sentences: number
      banks: number
      agreement: number
      kappa: number
      scorer_vs_first: number
      scorer_vs_second: number
      consensus_sentences: number
      scorer_on_consensus: number
    }
  }
  policy: {
    pooled_rho: number
    pooled_p: number
    months: number
    banks_positive: number
    banks_total: number
    sign_test_p: number
    banks: { area: string; name: string; rho: number; months: number }[]
  }
  beforeDecisions: {
    decision: "cut" | "hold" | "hike"
    months: number
    mean_tone: number
    low: number
    high: number
  }[]
  leadsOrFollows: {
    with_next_3m_change: number
    with_past_3m_change: number
    with_inflation: number
    next_given_past: number
    months: number
  }
  prediction: {
    rows: { train: number; validation: number; test: number }
    chosen: string
    models: Record<
      string,
      Record<"baseline" | "with_tone", { validation: ModelScores; test: ModelScores }>
    >
  }
  placebo: {
    actual_gain: number
    shuffled_gain_mean: number
    shuffled_gain_95th: number
    p_value: number
    runs: number
    shuffled_gains: number[]
  }
}
