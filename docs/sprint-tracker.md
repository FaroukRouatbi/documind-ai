# DocuMind AI — Sprint Tracker

Living checklist. Check items off as they're completed; commit the tracker update in the
same commit as the work it tracks.

**Project shape (revised Oct 2026).** A production-grade **text** RAG platform on AWS:
multi-tenant with database-enforced isolation, measured retrieval quality, guarded
generation, and the full set of production concerns beyond retrieve-and-generate —
conversation state, streaming, data lifecycle, evaluation, continuous deployment,
autoscaling, backups with a tested restore, OpenTelemetry observability, resilience
drills, cost control and a security review.

Multimodal ingestion (voice, and two competing image strategies) was in the original
plan and has been deliberately removed from scope — see decisions-log entry 28. The
`modality` and `ingestion_strategy` columns and the ingestion-strategy protocol remain,
so it is an extension rather than a rewrite if it ever returns.

Time is not the constraint. Depth and learning are prioritised over speed, explicitly.

**Working agreement (re-establish in any new session):** Farouk writes all code; Claude
advises and reviews only — explains concepts before code is written, reviews by severity
(bugs that break plan/apply first, then design issues, then style), and writes full code
only when explicitly asked. Every resource, data source and module gets explained: what
it is, why it's used, how it ties into the rest of the system.

**Output-scoping rule (apply automatically):**
1. Consumed only within the same module file → no output, reference the resource directly.
2. Consumed by a different module in the same environment → module-level output only.
3. Needed by a human or an external process (CI, `.env`) → also re-expose at environment
   root (`environments/dev/outputs.tf`).

---

## Cross-cutting baseline — applies to every sprint from here on

Before marking ANY sprint done, confirm:

- [ ] Structured JSON logging with a correlation ID flowing API → SQS → worker
- [ ] OpenTelemetry spans on new external calls once Sprint 22 lands; correlation ID and
      trace ID unified
- [ ] Every external call (Bedrock, RDS, Redis, S3, Textract) wrapped in
      retry-with-backoff at the point it's written
- [ ] New IAM permissions scoped to specific resources and actions, never `["*"]`
- [ ] Success / failure / latency metrics emitted for new components
- [ ] Mutating actions written to the audit log once Sprint 16 lands
- [ ] No secrets in code or committed env files
- [ ] Real unit/integration tests for new logic as it's written, not an eval harness at
      the end
- [ ] Any new tenant-scoped table has an RLS policy with both `USING` and `WITH CHECK`,
      and a test proving isolation that has been seen to fail with the policy disabled

---

## COMPLETE — Sprints 0–10

| Sprint | Focus | Tag |
|---|---|---|
| 0 | Foundations | |
| 1 | Core AWS services (IAM, storage, secrets) | |
| 2 | Data layer (RDS, pgvector, Redis) | |
| 3 | Auth (Cognito, JWT validation) | |
| 4 | Compute + messaging scaffolding (ECS, ALB, SQS) | `sprint-4-complete` |
| 5 | Backend API skeleton (FastAPI, Alembic, RLS, pagination, versioning) | |
| 6 | Text ingestion pipeline (presign, S3→SQS, structure-aware chunking, embeddings) | |
| 7 | Multi-tenancy hardening (RLS tests, isolation suite) | |
| 8 | CI foundation + tooling (uv, ruff, mypy, Actions, dep scanning) | |
| 9 | RAG query pipeline + safety (retrieval, generation, Guardrails, rate limiting) | `v0.9.0` |
| 10 | Retrieval benchmark harness (Recall@k, MRR, latency instrumentation) | `v0.10.0` |

Baseline recorded: MRR 0.6181, recall@1 0.4762, recall@10 1.0000.

---

## Sprint 11 — PDF ingestion

The first input format beyond Markdown, and the one that validates the
ingestion-strategy abstraction built in Sprint 6.

- [ ] **Extraction-path decision, documented:** Textract LAYOUT vs `pypdf` /
      `pdfplumber` vs Bedrock multimodal. Weigh cost per page, extraction fidelity, and
      whether the output carries structure the existing structure-aware chunker can use
- [ ] `PdfIngestionStrategy` behind the existing protocol; dispatch on content type, not
      file extension
- [ ] Scanned vs digital PDFs handled as distinct cases (OCR needed or not), detected
      rather than assumed
- [ ] Page numbers carried into chunk metadata so citations can say *where*
- [ ] **Chunk-quality checks (never built in Sprint 6):** reject suspiciously tiny or
      huge chunks; strip binary and garbage from bad extraction rather than embedding it
- [ ] **Format validation (never built in Sprint 6):** corrupt, empty and wrong-type
      files get a clear `failed` status with a reason, not a crash
- [ ] Content-hash idempotency and DLQ handling to the same standard as text
- [ ] A PDF arm in the benchmark corpus, so extraction quality is measured not assumed
- [ ] Unit tests for the extraction and chunking branches

## Sprint 12 — Retrieval quality: ranking and query

Everything here is measured against the Sprint 10 baseline. Results go in the benchmark
README's comparison table.

- [ ] **Deferred embedding column** — `defer(Chunk.embedding)` (or `raiseload`) in
      `ChunkRepository.search`, and hoist `SET LOCAL hnsw.iterative_scan` out of the
      method. Quality must be unchanged; search latency should fall ~10×
- [ ] **Stable gold chunk IDs** in `questions.jsonl` (filename + heading path) replacing
      substring ground truth — do this before the experiments, since every comparison
      inherits the ground truth's bias
- [ ] Cross-encoder or Claude-based **reranking** over a wider first pass (top 20–50 → k)
- [ ] **Hybrid search**: Postgres `tsvector` alongside vector similarity, merged with RRF
- [ ] **Query rewriting** before retrieval; evaluate HyDE as a benchmark arm
- [ ] **Query decomposition** for compound questions — retrieve per sub-question, combine
- [ ] **MMR** for diversity; **metadata filtering** (document, date, tags) alongside vector search
- [ ] **Contextual compression** of retrieved chunks before generation
- [ ] **Near-duplicate dedup** with a benchmark-tuned similarity threshold
- [ ] `ef_search` tuning; `hnsw.iterative_scan` strict → relaxed order once a reranker exists
- [ ] Raw-vs-deduplicated comparison arm — does dedup help or hurt?
- [ ] Distance-score distributions for answerable vs unanswerable questions → an
      evidence-based **abstention threshold**
- [ ] Latency cost recorded for every technique, not just quality

## Sprint 13 — Retrieval quality: chunking and embedding

Separated from Sprint 12 because each of these requires re-ingesting the corpus, and
they change what gets embedded rather than how results are ranked.

- [ ] **Chunk overlap** (~10–15%) — currently zero; `pack()` produces non-overlapping slices
- [ ] **Heading-path prepend at embed** — `heading_path` is stored but never embedded, so
      it does not influence the vector today
- [ ] **Contextual retrieval** — an LLM-generated per-chunk context header at ingest
- [ ] **Parent/child retrieval activated** — `parent_index` is currently `None`
      unconditionally; retrieve small, return large
- [ ] Chunk-size sweep, and **fixed-window chunking** kept only as a comparison baseline
- [ ] Treat "what text gets embedded" as one axis: raw / heading-prepended /
      contextual-header / both
- [ ] Consider table partitioning on `chunks` by `tenant_id` if data volume justifies it

## Sprint 14 — Conversation and streaming

The system is currently single-shot. This is the largest remaining functional gap.

- [ ] `conversations` and `messages` tables, tenant-scoped with RLS policies and
      isolation tests
- [ ] Multi-turn history in the prompt with an explicit token budget and a truncation
      strategy that doesn't silently drop the system instructions
- [ ] Follow-up and coreference handling ("what about the second one?") via the query
      rewriting built in Sprint 12 — history-aware rewriting
- [ ] **SSE streaming** from Bedrock through Fargate and the ALB; verify ALB buffering
      and idle-timeout behaviour rather than assuming
- [ ] Citations delivered with the stream, and validated against retrieved chunks before
      the stream closes
- [ ] Client abort / cancellation propagated so an abandoned request stops costing money
- [ ] Guardrail behaviour under streaming — a mid-stream intervention must not leave a
      half-answer presented as complete
- [ ] Conversation-level rate limiting and history-length caps

## Sprint 15 — Frontend and deployed demo

- [ ] React + TypeScript scaffold; Cognito auth flow (login, signup, refresh)
- [ ] Upload UI with status polling
- [ ] Chat UI consuming the SSE stream, rendering citations with page numbers
- [ ] Loading and error states on every async action, not just the happy path
- [ ] Accessibility pass: semantic HTML, keyboard navigation, alt text
- [ ] Build pipeline to S3 + CloudFront
- [ ] **Public demo URL** in the README and on the CV
- [ ] Demo account and seed corpus so a reviewer can click through without uploading
- [ ] Screenshots in the README

## Sprint 16 — Data lifecycle and audit

- [ ] **Document deletion** cascading to chunks, embeddings and the S3 object, with tests
      querying for orphaned rows and objects afterwards
- [ ] S3 lifecycle rule expiring incomplete multipart uploads
- [ ] Reconciliation sweep marking long-stale `pending` documents as `failed`
- [ ] **Zero-downtime reindexing** using the existing `embedding_model` /
      `embedding_version` columns: dual-write, backfill, per-tenant cutover, rollback
      path. The columns exist for exactly this; use them rather than a
      re-embed-with-downtime script
- [ ] **Audit log** — append-only, tenant-scoped: who uploaded, queried, deleted, when,
      and from where. Insert-only privileges for the app role
- [ ] Retention policy and right-to-erasure path documented and implemented
- [ ] Tests proving deletion is complete and the audit record survives it

## Sprint 17 — Generation evaluation

Retrieval has been measured since Sprint 10; generation has not.

- [ ] Golden set extended with expected answers, not just expected chunks
- [ ] **Faithfulness / groundedness** metric via RAGAS or Claude-as-judge
- [ ] **Answer correctness** and **citation validity** (does every cited chunk actually
      support the claim?)
- [ ] **Abstention correctness** measured on the unanswerable questions, using the
      threshold derived in Sprint 12
- [ ] Variance handling — judge runs are stochastic; report spread, not a single number
- [ ] **Eval regression gate in CI**, behind the `integration` marker so the default
      per-PR run stays credential-free
- [ ] Guardrail intervention rate tracked as an eval output

## Sprint 18 — External benchmark arm and comparison report

- [ ] One standard retrieval dataset as a second arm — SciFact from BEIR is the right
      size. Gives an externally comparable number alongside the own-corpus number
- [ ] Data-loading script; document that pre-chunked passage collections bypass the
      chunker, so this arm measures embedding and search only
- [ ] **Comparison report artifact** consolidating every experiment from Sprints 12, 13
      and 17 — this is the portfolio deliverable; treat its quality accordingly
- [ ] Tag milestone

## Sprint 19 — Continuous deployment

- [ ] `deploy-dev.yml`: build, push to ECR, update ECS on merge to `main`
- [ ] **Migration-on-deploy automated** — currently a manual Alembic CLI run before ECS
      updates, which is the single most likely source of a bad deploy
- [ ] Staging environment separate from dev and prod
- [ ] **ECS deployment circuit breaker enabled with rollback** — currently disabled
- [ ] Blue/green or canary for prod with automated rollback
- [ ] Feature flags for retrieval configuration, so Sprint 12/13 settings can be changed
      without a deploy
- [ ] Immutable image tags enforced; no `:latest` in any task definition

## Sprint 20 — Autoscaling and infrastructure hardening

- [ ] ECS autoscaling: target tracking on CPU / request count for `api`, on SQS queue
      depth for `worker`
- [ ] **RDS Proxy** — a decision, not a consideration: Fargate scale-out multiplies
      connections against a hard RDS limit
- [ ] WAF in front of the ALB with a managed rule set (SQLi, common exploits)
- [ ] ElastiCache HA: `num_cache_clusters` 1 → 2 with `automatic_failover_enabled`
- [ ] Single NAT gateway → one per AZ
- [ ] VPC interface endpoints for `bedrock-runtime` and SQS so worker traffic leaves NAT
- [ ] RDS `engine_version` pinned to a minor version for reproducibility
- [ ] HTTPS at the ALB with ACM, and HTTP → HTTPS redirect (currently HTTP only)

## Sprint 21 — Backups, disaster recovery and SLOs

The sprint that converts "production-grade" from a claim into something tested.

- [ ] Automated backups with point-in-time recovery; `skip_final_snapshot = false`;
      deletion protection on
- [ ] **A restore actually performed and timed**, in a scratch environment, with the
      procedure written down. An untested backup is a hope
- [ ] Documented RTO and RPO, and whether the current architecture meets them
- [ ] Prod posture built, not just documented: RDS Multi-AZ
- [ ] **SLOs defined** — p95 query latency, p95 ingestion time, ingestion success rate,
      availability — with error budgets. Sprint 22's alarms burn against these
- [ ] S3 versioning and KMS key rotation verified, not assumed

## Sprint 22 — Observability on OpenTelemetry

- [ ] OTel SDK instrumentation: FastAPI, SQLAlchemy, boto3, Redis — auto-instrumentation
      where it exists, manual spans around retrieval, generation and chunking
- [ ] **ADOT collector as an ECS sidecar**; traces to X-Ray, metrics to CloudWatch.
      Vendor-neutral instrumentation so the backend can change without touching
      application code — record this as a decision
- [ ] Existing correlation ID unified with the OTel trace ID so logs join traces
- [ ] **RAG-specific metrics**: retrieval hit rate, guardrail intervention rate, tokens
      per query, cost per query, abstention rate, time-to-first-token
- [ ] Dashboards per service, and **alarms that burn against Sprint 21's SLOs** rather
      than against raw CPU
- [ ] Trace a single request end to end: API → SQS → worker → Bedrock → RDS, visually

## Sprint 23 — Resilience validation

- [ ] Failover drill: kill an ECS task, verify recovery and that no message is lost
- [ ] Throttling drill: force a Bedrock 429, verify backoff and that the circuit breaker
      opens and recovers
- [ ] RDS failover drill against Multi-AZ; verify connection-pool recovery
- [ ] Redis unavailable: verify rate limiting fails **open** as designed, under load
- [ ] DLQ review process: poison messages inspectable and replayable, not quarantined
      and forgotten
- [ ] Load test that genuinely exercises Sprint 20's autoscaling — confirm it scales out,
      not merely that the policy exists
- [ ] Record what broke; fix or document each finding

## Sprint 24 — Cost and abuse protection

- [ ] AWS Budgets alerts and Cost Anomaly Detection
- [ ] Per-tenant usage tracking and visibility
- [ ] **Per-tenant cost circuit breaker** — a hard spend ceiling, since request rate
      limiting caps calls but not Bedrock spend
- [ ] **Upload-cap reconciliation**: the presign endpoint allows 50MB, which the pipeline
      cannot realistically process. Lower the cap, or chunk processing across messages
- [ ] Max documents and max total bytes per tenant
- [ ] ECR lifecycle policy expiring untagged images
- [ ] Evaluate **Bedrock prompt caching** for the repeated system-prompt prefix
- [ ] Revisit Redis answer caching now that there is traffic to measure — keyed on
      retrieved chunk IDs, never caching blocked or truncated responses
- [ ] Guardrails per-text-unit billing reviewed explicitly

## Sprint 25 — Security review

- [ ] Full IAM audit: every role, every scope. Bedrock `["*"]` → specific model ARNs
- [ ] Security group egress restricted (currently `0.0.0.0/0` outbound everywhere; RDS
      needs none, ECS needs 443)
- [ ] Dead `secretsmanager:GetSecretValue` on the task roles removed (ECS injects via the
      execution role)
- [ ] **Secrets Manager rotation** for the RDS credentials, implemented not just reviewed
- [ ] Cognito: `ALLOW_USER_PASSWORD_AUTH` → `ALLOW_USER_SRP_AUTH`; password minimum
      8 → 12 (symbols stay off, per NIST)
- [ ] **Guardrail version pinning** — currently `DRAFT`, so a Terraform change hits live
      traffic with no review gate
- [ ] Adversarial prompt-injection testing with real malicious documents, not unit tests
- [ ] **In-tenant authorization decided**: roles and per-document ACLs, or a documented
      non-goal. Today every user in a tenant sees every document
- [ ] **Data residency decided**: everything runs in `us-east-1`; document what changes
      to serve EU customers, and the retention and erasure story
- [ ] Dependency scan findings reviewed, not merely enabled
- [ ] `sync_env.py` hardcoded local credentials removed

## Sprint 26 — Polish and case study

- [ ] README final: architecture, demo URL, screenshots, benchmark results, setup
- [ ] `docs/architecture-design.md` updated to reflect everything that changed
- [ ] `docs/decisions-log.md` finalised and **verified against the code** (the five
      outstanding checks: HNSW params, grounding threshold, circuit-breaker values,
      sprint attributions, RDS limitations)
- [ ] Explicit "what I'd add for true production scale" section
- [ ] Small code debt cleared: `pyproject.toml` transitives trimmed; RLS downgrade typo
      (`DISABLE ROWLEVEL SECURITY`); `environment` split into `LOG_FORMAT` / `DEBUG`;
      `text.py` `__main__` demo block → a real test; test-folder convention settled;
      `benchmark` added to `[tool.mypy] files`
- [ ] Phase exit criteria checked in full
- [ ] Tag `v1.0.0`

---

## Declared non-goals

Recorded so they read as decisions rather than omissions. Each belongs in the decisions
log.

- **Multimodal ingestion** (voice, two image strategies) — entry 28
- **Multi-region / active-active** — single region, documented RTO/RPO instead
- **Database sharding** — table partitioning by `tenant_id` considered instead
- **Kubernetes** — ECS Fargate chosen and justified (entry 1)
- **Agent orchestration** — query decomposition in Sprint 12 is the closest this project
  comes, deliberately

---

## Git workflow

Trunk-based and lightweight: `main` stays deployable in spirit, feature branches for
anything more than a one-line fix. `main` is protected.

Branch naming: `infra/rds-module`, `feat/pdf-ingestion`, `fix/cors-headers`,
`docs/sprint-tracker`.

Commit convention: `infra:`, `feat:`, `fix:`, `chore:`, `docs:`, `test:`. Subject line
under ~72 characters, imperative, no trailing period. A body only when the reasoning
isn't visible in the diff — and then wrapped at ~72 characters after a blank line.

Run `git status` from the repo root **before and after** `git add`, every time. Several
infra modules once went uncommitted for multiple sprints because this wasn't habitual.

Tag at the end of each sprint. Turn on "Automatically delete head branches" so merged
branches don't accumulate.
