# Retrieval benchmark

A reproducible measurement of how well retrieval finds the right chunks, so that
later changes to the retrieval pipeline — reranking, hybrid search, chunk overlap,
query rewriting, parent/child retrieval — can be judged against numbers instead of
impressions.

Every result is written to `results/<timestamp>.json` and stamped with the git SHA of
the commit it ran against, so any two runs can be compared and attributed to a
specific state of the code.

## What this measures

The benchmark exercises the **real** pipeline, not a reimplementation of it:

- the real chunker (`app.ingestion.chunking`) via the real ingestion strategy
- the real embedding client (Titan Text Embeddings V2 through Bedrock)
- the real repository search (`ChunkRepository.search`, pgvector cosine distance)
- the real tenant isolation — retrieval runs as the least-privilege `documind_app`
  role with `app.tenant_id` set, so row-level security applies exactly as it does in
  production

If retrieval changes, this number changes. That is the entire point.

## Running it

Two steps, from `backend/api`, with Docker Postgres up and AWS credentials available.

```bash
# 1. wipe and re-ingest the benchmark corpus (makes real Bedrock embedding calls)
uv run python -m benchmark.ingest

# 2. run the questions and write a results file
uv run python -m benchmark.run
```

`ingest` resets the benchmark tenant first, so the corpus is identical on every run
and results are comparable. Re-run it whenever the chunker or the embedding model
changes; otherwise step 2 alone is enough.

Both steps cost real money (one embedding call per chunk, then one per question —
39 + 23 calls). When changing `run.py`, add `questions = questions[:3]` after
`load_questions()` to smoke-test the plumbing for three calls instead of twenty-three,
then remove it.

### Database credentials: why the two scripts differ

`ingest.py` connects with `settings.migration_db` (the owner role) and `run.py` with
`settings.db` (the `documind_app` role). **Same database, same endpoint, different
credentials** — this is deliberate, not a misconfiguration.

Ingestion needs to create the benchmark tenant and delete prior rows, which the
application role cannot do. Retrieval deliberately uses the restricted role, because
PostgreSQL exempts table owners from row-level security: benchmarking as the owner
would silently measure retrieval with tenant isolation switched off. The thing being
measured has to run under the same constraints as production.

## The corpus

Three sections of the PostgreSQL 17 documentation, 39 chunks total:

| File | Chunks |
|---|---|
| `corpus/row-security-policies.md` | 15 |
| `corpus/privileges.md` | 11 |
| `corpus/transaction-isolation.md` | 13 |

Chosen for three reasons: the content is genuinely technical, so questions can be
hard; it is dense in a way that creates real retrieval ambiguity (three documents that
all discuss roles and permissions); and the PostgreSQL Licence explicitly permits
redistribution, so it can live in a public repository. The full licence text is in
`corpus/NOTICE.md`, which `ingest.py` skips.

**Caveat worth stating plainly:** this is public documentation that the embedding model
has almost certainly seen during training. Absolute scores here are optimistic relative
to what the same pipeline would achieve on private corpus. The harness is built for
*relative* comparison between retrieval configurations, not for predicting absolute
quality on customer data.

## The questions

`questions.jsonl`, 23 questions — 21 answerable, 2 unanswerable.

```json
{"id": "rls-001",
 "question": "Which roles bypass row-level security?",
 "expected_chunks": ["Superusers and roles with the BYPASSRLS attribute always bypass"],
 "expected_heading": "Row Security Policies > Who bypasses row security"}
```

They are deliberately uneven in difficulty. Some are near-verbatim lookups; others
paraphrase heavily, use vocabulary absent from the source, or require material from a
document other than the obvious one (`cross-001` is a deliberate cross-document trap).
A question set where everything scores at rank 1 cannot distinguish a good retriever
from a bad one.

## Metrics

**Recall@k** — the fraction of answerable questions whose first relevant chunk appears
within the top *k*. Answers "does the right material make it into the context window at
all?"

**MRR** (mean reciprocal rank) — the mean of `1/rank` over the first relevant chunk per
question; 0 if never found. Answers "how high up?" Rank 1 contributes 1.0, rank 2
contributes 0.5, rank 10 contributes 0.1. It is deliberately top-heavy, which matches
how retrieval is consumed: the generation model attends most strongly to the beginning
and end of its context, so a correct chunk at rank 8 is worth much less than the same
chunk at rank 1.

The two together separate two failure modes that need different fixes. Low recall@10
means retrieval genuinely cannot find the material — an embedding, chunking, or query
problem. High recall@10 with low recall@1 means retrieval finds it but ranks it badly —
an ordering problem, which is what reranking addresses.

## Methodology decisions

**Binary relevance, not graded.** Each chunk is either relevant or it is not; there is
no "partially relevant" tier. Graded relevance (and nDCG over it) is more informative in
principle, but it requires per-chunk judgements that are subjective and that drift as the
chunker changes, which is precisely when the benchmark must stay stable. Binary
relevance with a single-annotator corpus is the defensible choice at this scale.

**Measured before reordering, after deduplication.** `run.py` calls the repository
search and `dedup_chunks`, but deliberately does not apply
`reorder_lost_in_middle`. That reorder moves the most relevant chunks to both ends of
the list for the generation model's benefit; it cannot change *which* chunks were
retrieved, so recall@k is unaffected by it, and it scrambles positions, so it would
corrupt MRR without being measurable by either metric. Deduplication is kept because it
removes chunks before they reach the model, which does affect what is available to
answer from.

**Substring ground truth, and this is the known weak point.** A hit is recorded when a
retrieved chunk's text contains one of `expected_chunks`. This is brittle in both
directions: a semantically correct chunk that paraphrases the expected wording is scored
as a miss, and an expected phrase appearing incidentally in an irrelevant chunk is
scored as a hit. Stable gold chunk identifiers (filename plus heading path, since chunk
UUIDs are regenerated on every ingest) would be more rigorous and are the first planned
improvement to the harness itself.

**Unanswerable questions are scored separately.** Questions with empty
`expected_chunks` are excluded from the MRR and recall denominators, because retrieval
returning nothing relevant for them is correct behaviour, not a failure. They are
recorded with what *was* retrieved, so the top results can be inspected for
plausible-looking-but-wrong material. Whether the system correctly declines to answer
them is a property of the generation layer, not of retrieval, and is not measured here.

## Baseline

Run `20261002T211542Z`, 21 answerable questions, k=10:

| Metric | Value |
|---|---|
| MRR | 0.6181 |
| recall@1 | 0.4762 |
| recall@3 | 0.6667 |
| recall@5 | 0.7143 |
| recall@10 | 1.0000 |
| misses | none |

**Reading:** retrieval reliably *finds* the answer — recall@10 is perfect, every
question's answer is somewhere in the top ten — but ranks it first less than half the
time. That is an ordering problem, not a finding problem, and it is the specific thing
reranking is for. It also means increasing *k* buys nothing here; the material is
already in the window.

The questions that rank worst show *why*, and they are not random:

- `iso-003` (rank 9) — the question's vocabulary does not appear in the source, and the
  answer sits inside a blockquoted note rather than body prose
- `cross-001` (rank 7) — the deliberate cross-document trap; the obvious document is
  retrieved first
- `rls-007` (rank 7) — the answer is one sentence inside a chunk otherwise dominated by
  SQL, so the chunk's embedding is pulled toward "code" and away from the sentence's
  meaning
- `iso-002` (rank 4) — heavy paraphrase distance

`rls-007` is the most actionable: it suggests chunks mixing prose and code embed poorly,
which is a chunking question rather than a ranking one.

## Latency

Measured per question inside `retrieve`, split into embedding, vector search, and
deduplication.

| | Value |
|---|---|
| total, mean | 378.7 ms |
| total, p50 | 348.9 ms |
| total, p95 | 424.8 ms |
| embedding, mean | 320.7 ms (median 292.4, min 216.5, max 1040.3) |
| vector search, mean | 57.9 ms (median 56.8, min 49.8, max 82.4) |
| deduplication | below 0.1 ms |

p95 over 23 samples is barely meaningful; the median is the number to trust. The
embedding maximum of 1040 ms is the first call, which pays for boto3 client
construction, credential resolution and the TLS handshake.

**Embedding dominates at ~85% of retrieval time**, and it is a round trip from Tunisia
to `us-east-1`. The consequence for future work: any technique that adds an API call —
query rewriting through Claude, a hosted reranker — costs roughly another 300 ms, while
anything computed locally (BM25 hybrid, different chunk sizes, overlap) is close to free
by comparison. That asymmetry should decide the order experiments are tried in.

### Finding: vector search spends 93% of its time deserialising unused data

57.9 ms for a cosine scan over 39 rows is wrong by two orders of magnitude, and the
instrumentation made it visible. Tracing it:

| Measured | Time |
|---|---|
| Postgres execution (`EXPLAIN ANALYZE`) | 0.49 ms, `Seq Scan` |
| round trip through Docker loopback (`SET LOCAL`, via psql) | 0.61 ms |
| full query including payload (psql, `SELECT *`) | 3.23 ms |
| same query selecting only `id, content` (psql) | 3.18 ms |
| **as measured from Python** | **~57 ms** |

So Postgres and the wire account for roughly 3.8 ms, and the remaining ~53 ms is spent
inside the Python process. `ChunkRepository.search` issues `select(Chunk)`, which
fetches every column of all ten rows — including `embedding`, 1024 floats each. pgvector
transmits vectors as text, so each result row requires parsing a ~9 KB string into a
1024-element list, and SQLAlchemy then builds ten fully instrumented ORM objects around
them. Nothing downstream reads those vectors.

psql shows the payload as nearly free precisely because psql never interprets it — it
holds the vectors as raw text. The cost is deserialisation, not transport.

Two fixes, deferred to Sprint 11 so the slow baseline above stays on record for
comparison:

1. `select(Chunk).options(defer(Chunk.embedding))` — keeps the ORM return type, so no
   caller changes, but does not fetch the column. (`raiseload` instead of `defer` would
   make any accidental later access fail loudly rather than silently re-issuing a query.)
2. Hoist `SET LOCAL hnsw.iterative_scan` out of `search`. It is transaction-scoped, so
   issuing it on every call is a category error — in this benchmark's single transaction
   it is set once and then redundantly re-set 22 times.

Expected effect: search from ~57 ms to ~4 ms. Total retrieval improves by about 14%,
since Bedrock still dominates — real, but not transformative. It matters more as *k*
grows, as the corpus grows, and in production, where the database is across a VPC rather
than on loopback and the 90 KB per query stops being cheap.

### What these absolute numbers are not

Local development: Postgres in Docker on the same machine, Bedrock across an ocean. In
production both reverse — the database gets further away, Bedrock gets much closer. Use
these figures to compare retrieval configurations against each other on the same
machine, never to predict production latency.

## Planned experiments

Each is a bet whose value depends on the corpus, which is why the harness came first.

| Configuration | MRR | recall@1 | recall@5 | recall@10 |
|---|---|---|---|---|
| Dense baseline (Titan V2, k=10) | 0.6181 | 0.4762 | 0.7143 | 1.0000 |
| + deferred embedding column | — | — | — | — |
| + reranking | — | — | — | — |
| + hybrid BM25 | — | — | — | — |
| + chunk overlap | — | — | — | — |
| + query rewriting | — | — | — | — |

Given a baseline with perfect recall@10 and recall@1 below 0.5, reranking is the
best-motivated first experiment: the material is already being retrieved, so the problem
is ordering.

Harness improvements also outstanding: stable gold chunk identifiers instead of
substring matching; a raw-versus-deduplicated comparison arm, to show whether
deduplication helps or hurts; and distance-score distributions for answerable versus
unanswerable questions, which would give an evidence-based abstention threshold.
