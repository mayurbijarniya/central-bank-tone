# Design

Written after profiling the data and before any modeling, so the questions,
labels and tests are fixed before the answers are known.

## Data

**BIS Central bankers' speeches**, one archive per year from
`bis.org/cbspeeches/download.htm` (downloaded 2026-10-25). Each row has the
speech's address, title, a one-line description, the date, the speaker and the
full text. There is no institution column.

| | |
|---|---|
| Speeches | 20,726 published, 1996-09-10 to 2026-06-22 |
| Kept | 20,690 English speeches after removing 8 in French and 28 published twice |
| Text | 382 million characters; median speech about 16,000 characters |
| Sentences | 2.29 million of 8 to 80 words |
| Bank identified | 20,235 speeches (97.8%) |

**BIS Central bank policy rates** (`WS_CBPOL`), daily, 50 reference areas, to
October 2026. Days without a rate are published as the text `NaN`, not left
empty, so they must be dropped explicitly: read as numbers they count as
values and turn every gap into a fake rate change.

**BIS consumer prices** (`WS_LONG_CPI`), monthly, for inflation.

**Live feeds.** The archive is published with a lag (in October 2026 it ended
on 22 June). The Federal Reserve, ECB, Bank of England, Bank of Canada and
Reserve Bank of Australia publish new speeches as RSS feeds the same day;
`cbtone update` reads those, and the archive fills in every other bank when the
BIS publishes.

### What profiling found

- **The bank is in the description.** "Speech by Mr X, Governor of the Reserve
  Bank of India, at ..." A speech is assigned to the central bank named first,
  because a host or second role ("and Chairman of the Board of the BIS") comes
  later. The 2.2% unassigned are mostly BIS officials and small central banks.
- **Euro area governors set euro rates.** From the day their country joins, a
  national central bank governor's speeches count towards the euro area, since
  they vote on the ECB Governing Council.
- **Layout noise.** The text is converted from PDF and web pages: separators,
  headings, page numbers and links are removed before splitting sentences.
- **Most sentences are not about rates.** Speeches cover payments, supervision,
  financial inclusion and anniversaries. Only sentences that mention monetary
  policy, inflation, rates, growth or employment are scored (the keyword list
  is in `cbtone/sentences.py`), as in the Trillion Dollar Words study.
- **Market-rate drift.** Some banks targeted market rates in the 1990s and
  early 2000s, whose daily values drift by a few basis points. A decision needs
  a move of at least 0.10 points at month end.

## Labels

Each policy sentence is **hawkish** (leans towards tighter policy: inflation
risks, rate increases, overheating), **dovish** (towards easier policy: weak
growth, unemployment, rate cuts, support) or **neutral**, following the
annotation guide of Shah, Paturi and Chava (2023).

1. **Answer key.** Their human-labeled FOMC sentences (train and test files,
   CC BY-NC 4.0) measure how well any labeler agrees with people.
2. **LLM labels.** A language model labels a sample of about 8,000 policy
   sentences, spread across banks so that no single bank dominates. The model
   is chosen by its accuracy on the answer key's training file, then fixed.
3. **Check outside the Fed.** 150 sampled sentences from 20 other banks test
   whether labeling carries over from Fed language.
4. **Local scorer.** A small sentence-embedding model plus logistic regression,
   trained on the human and LLM labels, scores every sentence for free. It is
   evaluated on the answer key's test file and the check outside the Fed; a
   word-count (TF-IDF) model is the baseline it must beat.

**Sentence tone** = the scorer's hawkish probability minus its dovish
probability, from −1 to +1. Probabilities rather than hard labels, so a
sentence the model is unsure about counts for little.
**Speech tone** = the mean over its policy sentences.
**Bank tone** for a month = the mean over its speeches in the last three
months, each speech counted once.

## Questions

**Q1. How well can a cheap local model read central bank tone?**
Accuracy and macro F1 of the LLM and the local scorer against human labels,
on Fed sentences and on other banks'.

**Q2. Does tone move with policy?**
Bank tone against the rate change over the following three months, and in the
months before hikes, holds and cuts.

**Q3. Does tone predict the next decision, beyond inflation and past rates?**
For each bank and month, predict next month's decision (hike, hold, cut).
Baseline features: recent rate changes, months since the last move, the rate
level and the latest inflation rate. The test adds speech tone. Models are
trained on 1999–2016, tuned on 2017–2019 and tested once on 2020 to 2026,
which includes the 2022 hiking cycle. Measured by log loss and macro F1.

Any added column lets a model fit a little noise, so a small gain proves
nothing. The **placebo test** shuffles each bank's tone across months 100
times and refits; real tone counts only if it beats nearly all shuffles.

## Banks tested in Q2 and Q3

Banks with a published policy rate and at least 100 English speeches since
1999. Hong Kong and Denmark are left out: their rates follow the US dollar and
the euro by design, so their speeches cannot move them.

## What this does not claim

- **Not causal.** Speeches and decisions both respond to the economy; Q3 asks
  whether tone adds information, not whether it causes moves.
- **Not every speaker votes.** A deputy governor's view is counted like the
  governor's; the archive does not say who sits on each committee.
- **Not real time for every bank.** Only the five banks with live feeds are
  current; the rest follow the BIS publication lag.
- **Not a trading signal.** Decisions are usually signalled well in advance;
  markets price that, and this project does not test returns.

## Decided during the build

Recorded here so the choices are visible. All but the last were made before
the test results were read; the last does not touch the prediction test.

- **Language model.** Three models were compared on 200 sentences from the
  FOMC *training* file: DeepSeek V4.1 Flash (66.0%), GLM 5.3 (65.5%) and
  Nemotron 3.5 Super (64.5%). DeepSeek was kept: as accurate, and about 50 times
  faster because it does not write out its reasoning. The instructions were
  revised once, on the same training sentences, to count descriptions of the
  economy as hawkish or dovish as the human annotators did; adding labeled
  examples to the prompt did not help and was dropped.
- **Local scorer.** Embeddings against TF-IDF, and four regularization
  strengths, compared by five-fold cross-validation grouped by speech on the
  training labels. Embeddings with C = 1 won (macro F1 0.65 against 0.63).
- **Prediction models** use no class weights, because log loss judges the
  probabilities and reweighting classes would distort them. The model used
  for the verdict is the one with the lower validation log loss.
- **The average across banks** needs at least 11 of the 21 tested banks in a
  month, so it never rests on a different handful of banks, as it would after
  the archive ends and only the five live feeds remain.
- **The sample** gives each bank a share proportional to the square root of
  its policy sentences, rather than stratifying by decade as first planned:
  banks differ far more in size than decades do.
- **The check outside the Fed** was planned as hand labels. It became a
  second-model check instead: GLM 5.3, from a different model family, labeled
  the same 150 sentences, and the report gives their agreement and Cohen's
  kappa. That measures agreement between models, not accuracy, and is
  reported as such.
- **Scoring on the website** was planned as calls to the FastAPI service. It
  moved into the browser instead, so the site needs no server: the same ONNX
  model file and tokenizer, ONNX Runtime Web, and the saved weights. Before
  switching, it was checked against Python: identical tokens on all 8,647
  label-set sentences, identical policy sentences in 300 speeches, and tone
  within 0.002 on 2,000 sentences.
