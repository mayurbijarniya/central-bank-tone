/**
 * The archive's tone scorer, run in the browser.
 *
 * Mirrors the Python pipeline step by step: the same cleaning, sentence split and
 * policy filter (cbtone/ingest.py, cbtone/sentences.py), the same ONNX export of
 * bge-small-en-v1.5 that fastembed uses, its BERT tokenizer, first-token pooling,
 * and the logistic regression saved in outputs/tables/scorer.json. Pasted text
 * never leaves the visitor's machine.
 */

import type { InferenceSession, Tensor } from "onnxruntime-web"

const MODEL_REPO =
  "https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/resolve/aa8f8b060edb00e03bfdd08813a2949946c8ba55"
export const MODEL_URL = `${MODEL_REPO}/model_optimized.onnx`
export const TOKENIZER_URL = `${MODEL_REPO}/tokenizer.json`
const CACHE_NAME = "cbtone-model-v1"

export const MAX_CHARACTERS = 50_000
export const MAX_SENTENCES = 400
const MIN_WORDS = 8
const MAX_WORDS = 80
const MAX_TOKENS = 512
const BATCH = 32

// ---- Sentences (cbtone/ingest.py) ----

const LINE_BREAK = /\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/
const BOILERPLATE =
  /^(?:#.*|\**\s*(?:\*\s*)+|\d+(?:\/\d+)?\.?|bis (?:central bankers['’] speeches|review).*)$/i
const LINK = /\[([^\]]*)\]\([^)]*\)/g
const SENTENCE_END = /(?<=[.!?])["”’)]?\s+(?=[A-Z“"(])/
const ABBREVIATION =
  /\b(?:Mr|Mrs|Ms|Dr|Prof|St|No|vs|e\.g|i\.e|cf|etc|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|U\.S|U\.K|Fig|Vol|p|pp)\.$/

export function clean(text: string): string {
  const kept = text.split(LINE_BREAK).map((raw) => {
    const line = raw.replace(LINK, "$1").replaceAll("\\_", " ").trim()
    return !line || BOILERPLATE.test(line) ? "" : line
  })
  return kept
    .join("\n")
    .split(/\n\s*\n/)
    .filter((p) => p.trim())
    .map((p) => p.replace(/\s+/g, " ").trim())
    .join("\n\n")
}

function wordCount(sentence: string): number {
  return sentence.split(/\s+/).filter(Boolean).length
}

export function sentences(text: string): string[] {
  const out: string[] = []
  for (const paragraph of text.split("\n\n")) {
    const merged: string[] = []
    for (const piece of paragraph.split(SENTENCE_END)) {
      // "Mr. Powell" and "U.S. inflation" end in a full stop but are not sentence ends.
      if (merged.length && ABBREVIATION.test(merged[merged.length - 1])) {
        merged[merged.length - 1] += ` ${piece}`
      } else {
        merged.push(piece)
      }
    }
    out.push(...merged)
  }
  return out.filter((s) => {
    const words = wordCount(s)
    return words >= MIN_WORDS && words <= MAX_WORDS
  })
}

// ---- Policy filter (cbtone/sentences.py) ----

const POLICY_TERMS = [
  "inflation\\w*", "disinflation\\w*", "deflation\\w*", "prices?", "price stability",
  "interest rates?", "policy rates?", "(?:bank|repo|cash|discount|deposit|lending) rate",
  "federal funds", "monetary policy", "monetary conditions", "policy stance",
  "tighten\\w*", "eas(?:e|es|ed|ing)", "accommodat\\w*", "restrictive\\w*", "stimul\\w*",
  "rate (?:increase|rise|hike|cut|reduction)s?", "hik\\w+", "asset purchases?",
  "quantitative easing", "balance sheet", "forward guidance",
  "unemployment", "employment", "labou?r market\\w*", "wages?", "output gap",
  "economic growth", "growth", "gdp", "economic activity", "demand", "recession\\w*",
  "overheat\\w*", "slack", "productivity", "expectations", "exchange rate", "currency",
]
const POLICY = new RegExp(`\\b(?:${POLICY_TERMS.join("|")})\\b`, "i")

export function isPolicy(sentence: string): boolean {
  return POLICY.test(sentence)
}

export function policySentences(text: string): string[] {
  return sentences(clean(text)).filter(isPolicy)
}

// ---- BERT tokenizer (lowercase, accents stripped, WordPiece) ----

interface TokenizerFile {
  model: { vocab: Record<string, number>; unk_token: string; max_input_chars_per_word: number }
}

const CONTROL = /\p{C}/u
const SPACE = /[\s\p{Zs}]/u
const PUNCTUATION = /[!-/:-@[-`{-~]|\p{P}/u
const MARK = /\p{Mn}/gu

function isChinese(code: number): boolean {
  return (
    (code >= 0x4e00 && code <= 0x9fff) ||
    (code >= 0x3400 && code <= 0x4dbf) ||
    (code >= 0x20000 && code <= 0x2a6df) ||
    (code >= 0x2a700 && code <= 0x2b73f) ||
    (code >= 0x2b740 && code <= 0x2b81f) ||
    (code >= 0x2b820 && code <= 0x2ceaf) ||
    (code >= 0xf900 && code <= 0xfaff) ||
    (code >= 0x2f800 && code <= 0x2fa1f)
  )
}

export class WordPiece {
  private vocab: Map<string, number>
  private unk: number
  private maxChars: number
  readonly cls: number
  readonly sep: number

  constructor(file: TokenizerFile) {
    this.vocab = new Map(Object.entries(file.model.vocab))
    this.unk = this.vocab.get(file.model.unk_token)!
    this.maxChars = file.model.max_input_chars_per_word
    this.cls = this.vocab.get("[CLS]")!
    this.sep = this.vocab.get("[SEP]")!
  }

  private normalize(text: string): string {
    let out = ""
    for (const char of text) {
      const code = char.codePointAt(0)!
      if (char === "\t" || char === "\n" || char === "\r" || SPACE.test(char)) out += " "
      else if (code === 0 || code === 0xfffd || CONTROL.test(char)) continue
      else if (isChinese(code)) out += ` ${char} `
      else out += char
    }
    return out.normalize("NFD").replace(MARK, "").toLowerCase()
  }

  private words(text: string): string[] {
    const out: string[] = []
    for (const chunk of text.split(" ")) {
      let word = ""
      for (const char of chunk) {
        if (PUNCTUATION.test(char)) {
          if (word) out.push(word)
          out.push(char)
          word = ""
        } else {
          word += char
        }
      }
      if (word) out.push(word)
    }
    return out
  }

  private pieces(word: string): number[] {
    const chars = Array.from(word)
    if (chars.length > this.maxChars) return [this.unk]
    const ids: number[] = []
    let start = 0
    while (start < chars.length) {
      let end = chars.length
      let found: number | undefined
      while (start < end) {
        const piece = (start > 0 ? "##" : "") + chars.slice(start, end).join("")
        found = this.vocab.get(piece)
        if (found !== undefined) break
        end -= 1
      }
      if (found === undefined) return [this.unk]
      ids.push(found)
      start = end
    }
    return ids
  }

  /** Token ids with [CLS] and [SEP], truncated to the model's 512 positions. */
  encode(text: string): number[] {
    const ids = this.words(this.normalize(text)).flatMap((w) => this.pieces(w))
    return [this.cls, ...ids.slice(0, MAX_TOKENS - 2), this.sep]
  }
}

// ---- Classifier (cbtone/scorer.py, SavedScorer) ----

export interface Weights {
  classes: string[]
  coef: number[][]
  intercept: number[]
}

export interface SentenceScore {
  sentence: string
  tone: number
  label: "hawkish" | "dovish" | "neutral"
  hawkish: number
  dovish: number
  neutral: number
}

export interface ScoreResult {
  tone: number | null
  policySentences: number
  sentences: SentenceScore[]
}

type Ort = typeof import("onnxruntime-web")

function probabilities(vector: Float32Array, weights: Weights): number[] {
  const logits = weights.coef.map(
    (row, k) => row.reduce((sum, w, i) => sum + w * vector[i], weights.intercept[k]),
  )
  const top = Math.max(...logits)
  const exp = logits.map((l) => Math.exp(l - top))
  const total = exp.reduce((a, b) => a + b, 0)
  return exp.map((e) => e / total)
}

const round = (value: number) => Math.round(value * 1e4) / 1e4

export class ToneModel {
  private ort: Ort
  private session: InferenceSession
  private tokenizer: WordPiece
  private weights: Weights

  constructor(ort: Ort, session: InferenceSession, tokenizer: WordPiece, weights: Weights) {
    this.ort = ort
    this.session = session
    this.tokenizer = tokenizer
    this.weights = weights
  }

  /** Unit-length embeddings of the first token, as fastembed computes them, in input order. */
  async embed(texts: string[]): Promise<Float32Array[]> {
    const all = texts.map((t) => this.tokenizer.encode(t))
    // Batching sentences of similar length keeps padding, and so wasted work, small.
    const order = all.map((_, i) => i).sort((a, b) => all[a].length - all[b].length)
    const out: Float32Array[] = new Array(texts.length)
    for (let start = 0; start < order.length; start += BATCH) {
      const batch = order.slice(start, start + BATCH)
      const encoded = batch.map((i) => all[i])
      const width = Math.max(...encoded.map((ids) => ids.length))
      const ids = new BigInt64Array(encoded.length * width)
      const mask = new BigInt64Array(encoded.length * width)
      encoded.forEach((row, r) =>
        row.forEach((id, c) => {
          ids[r * width + c] = BigInt(id)
          mask[r * width + c] = BigInt(1)
        }),
      )
      const shape = [encoded.length, width]
      const result = await this.session.run({
        input_ids: new this.ort.Tensor("int64", ids, shape),
        attention_mask: new this.ort.Tensor("int64", mask, shape),
        token_type_ids: new this.ort.Tensor("int64", new BigInt64Array(ids.length), shape),
      })
      const hidden = result.last_hidden_state as Tensor
      const data = hidden.data as Float32Array
      const size = hidden.dims[2]
      for (let r = 0; r < encoded.length; r++) {
        const first = data.slice(r * width * size, r * width * size + size)
        const norm = Math.hypot(...first)
        out[batch[r]] = first.map((v) => v / norm)
      }
    }
    return out
  }

  async score(text: string): Promise<ScoreResult> {
    if (text.length > MAX_CHARACTERS) {
      throw new Error(`Paste at most ${MAX_CHARACTERS.toLocaleString("en")} characters at a time.`)
    }
    const found = policySentences(text)
    if (found.length > MAX_SENTENCES) {
      throw new Error(`Paste at most ${MAX_SENTENCES} policy sentences at a time.`)
    }
    if (!found.length) return { tone: null, policySentences: 0, sentences: [] }

    const column = Object.fromEntries(this.weights.classes.map((c, i) => [c, i]))
    const vectors = await this.embed(found)
    const all = vectors.map((v) => probabilities(v, this.weights))
    const tones = all.map((p) => p[column.hawkish] - p[column.dovish])
    const rows = found.map((sentence, i) => {
      const p = all[i]
      return {
        sentence,
        tone: round(tones[i]),
        label: this.weights.classes[p.indexOf(Math.max(...p))] as SentenceScore["label"],
        hawkish: round(p[column.hawkish]),
        dovish: round(p[column.dovish]),
        neutral: round(p[column.neutral]),
      }
    })
    const mean = tones.reduce((a, b) => a + b, 0) / tones.length
    return { tone: round(mean), policySentences: rows.length, sentences: rows }
  }
}

// ---- Loading in the browser ----

/** Fetch once, then serve from Cache Storage so later visits skip the 66 MB download. */
async function cachedBytes(url: string, onProgress?: (share: number) => void) {
  const cache = typeof caches === "undefined" ? null : await caches.open(CACHE_NAME).catch(() => null)
  const hit = await cache?.match(url)
  if (hit) return new Uint8Array(await hit.arrayBuffer())

  const response = await fetch(url)
  if (!response.ok || !response.body) throw new Error(`Could not download the model (${response.status}).`)
  const total = Number(response.headers.get("content-length")) || 0
  const reader = response.body.getReader()
  const chunks: Uint8Array[] = []
  let received = 0
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    chunks.push(value)
    received += value.length
    if (total) onProgress?.(received / total)
  }
  const bytes = new Uint8Array(received)
  let offset = 0
  for (const chunk of chunks) {
    bytes.set(chunk, offset)
    offset += chunk.length
  }
  await cache?.put(url, new Response(bytes)).catch(() => undefined)
  return bytes
}

let loading: Promise<ToneModel> | null = null

export function loadToneModel(onProgress?: (share: number) => void): Promise<ToneModel> {
  loading ??= (async () => {
    const ort = await import("onnxruntime-web/wasm")
    ort.env.wasm.numThreads = 1
    const [model, tokenizer, weights] = await Promise.all([
      cachedBytes(MODEL_URL, onProgress),
      cachedBytes(TOKENIZER_URL).then((b) => JSON.parse(new TextDecoder().decode(b)) as TokenizerFile),
      fetch("/data/scorer.json").then((r) => r.json() as Promise<Weights>),
    ])
    const session = await ort.InferenceSession.create(model, { executionProviders: ["wasm"] })
    return new ToneModel(ort, session, new WordPiece(tokenizer), weights)
  })().catch((error) => {
    loading = null
    throw error
  })
  return loading
}
