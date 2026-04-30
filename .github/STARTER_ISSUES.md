# Starter Issues for Recombyne

This file is a curated backlog of issues that are ready to be picked up by new
and recurring contributors. Every entry has a one-click link that pre-fills a
GitHub issue with a clear title, description, and labels.

> Click the **"File this issue"** link next to a task. GitHub will open a new
> issue form with everything pre-filled. Adjust if you need, then submit.

If you start working on one, please leave a comment on the issue so two people
do not duplicate the same work.

---

## 1. Persist query history and watchlist in Postgres

**Why**
The current implementation uses an in-memory store for history and watchlist
entries. State is lost on restart. Phase 3 wants Postgres-backed persistence
that matches the SQLAlchemy models and the existing Alembic migration.

**Acceptance criteria**
- Replace `app.utils.store.history_store` and `watchlist_store` with
  SQLAlchemy-backed adapters using `app.models.QueryRecord` and
  `app.models.WatchlistRecord`.
- Add async repository functions that the routers consume.
- Update `backend/tests` so the history and watchlist tests run against an
  in-memory SQLite database via fixtures.

**Labels:** `enhancement`, `good first issue`, `backend`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Persist+query+history+and+watchlist+in+Postgres&labels=enhancement,good+first+issue,backend&body=See+%60.github/STARTER_ISSUES.md%60+%231+for+full+context.%0A%0A**Goal:**+Replace+the+in-memory+history+and+watchlist+stores+with+SQLAlchemy-backed+adapters+using+the+existing+%60QueryRecord%60+and+%60WatchlistRecord%60+models.%0A%0A**Acceptance%20Criteria:**%0A-+Replace+%60app.utils.store%60+history+and+watchlist+stores+with+SQLAlchemy+repositories.%0A-+Add+async+repository+functions+used+by+the+routers.%0A-+Update+backend+tests+to+run+against+an+in-memory+SQLite+database.%0A%0A**Files+likely+affected:**+%60backend/app/utils/store.py%60,+%60backend/app/routers/query.py%60,+%60backend/app/routers/watchlist.py%60,+%60backend/migrations/0001_phase2_persistence.py%60,+%60backend/tests/%60.)

---

## 2. Add YouTube ingestion adapter

**Why**
YouTube comments are a rich, under-used signal source for product, brand, and
news topics. Adding a YouTube ingester unlocks a third platform and exercises
the abstract `BaseIngester` contract.

**Acceptance criteria**
- New `backend/app/services/ingestion/youtube.py` implementing `BaseIngester`.
- Maps YouTube comment fields to `RawPost` (likes, replies as comments,
  channel age and subscribers as `AuthorMetrics`).
- BYOA via a `YOUTUBE_API_KEY` env var documented in `.env.example` and
  `docs/byoa-setup.md`.
- Add a fixture-based test in `backend/tests/test_ingestion.py`.

**Labels:** `enhancement`, `help wanted`, `backend`, `data-source`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Add+YouTube+ingestion+adapter&labels=enhancement,help+wanted,backend,data-source&body=See+%60.github/STARTER_ISSUES.md%60+%232+for+full+context.%0A%0A**Goal:**+Add+a+YouTube+comments+ingester+that+implements+%60BaseIngester%60+and+integrates+with+the+existing+pipeline.%0A%0A**Acceptance%20Criteria:**%0A-+Add+%60backend/app/services/ingestion/youtube.py%60+with+a+%60YouTubeIngester%60.%0A-+Map+YouTube+comment+fields+to+%60RawPost%60+and+%60AuthorMetrics%60.%0A-+Add+a+%60YOUTUBE_API_KEY%60+env+entry+in+%60.env.example%60+and+update+%60docs/byoa-setup.md%60.%0A-+Cover+with+fixture-based+tests+in+%60backend/tests/test_ingestion.py%60.)

---

## 3. Backtest harness for weighting changes

**Why**
We want contributors proposing weighting changes to back them with reproducible
numbers. A backtest harness replays a fixed dataset of posts under different
weighting configurations and prints a comparison table.

**Acceptance criteria**
- New `scripts/backtest_weighter.py` that loads a JSON dataset of posts and
  sentiments and reports raw, weighted, divergence, and timeline values.
- Accept multiple weighting configs and print a side-by-side table.
- Document the workflow in `docs/algorithm.md` under the "Improvement Path"
  section.

**Labels:** `enhancement`, `research`, `algorithm`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Backtest+harness+for+weighting+changes&labels=enhancement,research,algorithm&body=See+%60.github/STARTER_ISSUES.md%60+%233+for+full+context.%0A%0A**Goal:**+Provide+a+reproducible+harness+for+evaluating+changes+to+the+engagement+weighter.%0A%0A**Acceptance%20Criteria:**%0A-+Add+%60scripts/backtest_weighter.py%60+that+replays+a+JSON+dataset+through+%60EngagementWeighter%60.%0A-+Print+a+side-by-side+comparison+across+configs+(decay+rate,+author+scoring+toggle,+min_confidence).%0A-+Document+the+workflow+in+%60docs/algorithm.md%60.)

---

## 4. Public demo deployment

**Why**
A read-only public demo with seed data lets people evaluate Recombyne without
setting up keys or running Docker locally.

**Acceptance criteria**
- Add a Vercel deployment for the frontend with backend pointed at a hosted
  FastAPI instance (Fly.io, Render, or Railway are all fine).
- Pre-seed the demo with `scripts/seed_topics.py` so dashboards work without
  real API keys.
- Add a `/demo` link in the README header once the deployment is live.

**Labels:** `infra`, `help wanted`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Public+demo+deployment&labels=infra,help+wanted&body=See+%60.github/STARTER_ISSUES.md%60+%234+for+full+context.%0A%0A**Goal:**+Stand+up+a+public,+read-only+demo+of+Recombyne+seeded+with+mock+data.%0A%0A**Acceptance%20Criteria:**%0A-+Deploy+the+frontend+to+Vercel+pointing+at+a+hosted+FastAPI+backend.%0A-+Seed+the+demo+with+%60scripts/seed_topics.py%60.%0A-+Add+a+%60/demo%60+link+in+%60README.md%60.)

---

## 5. Improve sarcasm detection precision

**Why**
The current sarcasm heuristic in `text_preprocessor.py` is intentionally
lightweight. There is a clear opportunity to compare it against a small
labelled dataset and tighten precision without regressing recall.

**Acceptance criteria**
- Add a small labelled fixture (50-100 examples) to
  `backend/tests/fixtures/sarcasm.jsonl`.
- Extend the preprocessor with one or two new heuristics (e.g. emoji-driven
  sarcasm, ellipsis + positive contrast) backed by tests.
- Document the new rules in `docs/algorithm.md`.

**Labels:** `enhancement`, `research`, `algorithm`, `good first issue`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Improve+sarcasm+detection+precision&labels=enhancement,research,algorithm,good+first+issue&body=See+%60.github/STARTER_ISSUES.md%60+%235+for+full+context.%0A%0A**Goal:**+Improve+the+sarcasm+heuristic+in+%60text_preprocessor.py%60+with+a+small+labelled+fixture+and+a+couple+of+new+rules.%0A%0A**Acceptance%20Criteria:**%0A-+Add+%60backend/tests/fixtures/sarcasm.jsonl%60+with+50-100+labelled+samples.%0A-+Add+at+least+two+new+sarcasm+heuristics+backed+by+tests.%0A-+Update+%60docs/algorithm.md%60.)

---

## 6. Webhook alert subscriptions for watchlist deltas

**Why**
The watchlist already records meaningful score deltas. Letting users subscribe
to those deltas via webhook (Slack, Discord, custom) turns Recombyne into an
operational sentiment monitor.

**Acceptance criteria**
- Extend the watchlist schema with `alert_webhook_url` and a per-entry
  threshold.
- Send a JSON payload to the webhook when delta exceeds the threshold during a
  background refresh.
- Add tests using a `requests_mock`-style fixture.

**Labels:** `enhancement`, `feature`, `backend`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Webhook+alert+subscriptions+for+watchlist+deltas&labels=enhancement,feature,backend&body=See+%60.github/STARTER_ISSUES.md%60+%236+for+full+context.%0A%0A**Goal:**+Allow+watchlist+entries+to+POST+to+a+webhook+when+the+weighted+score+delta+crosses+a+threshold.%0A%0A**Acceptance%20Criteria:**%0A-+Extend+%60WatchlistEntry%60+schema+with+%60alert_webhook_url%60+and+%60alert_threshold%60.%0A-+POST+a+JSON+payload+from+%60_refresh_entry%60+when+the+threshold+is+crossed.%0A-+Cover+with+tests+that+stub+out+HTTP.)

---

## 7. CLI improvements for analyst workflows

**Why**
Analysts and traders prefer the CLI for repeatable workflows. The current CLI
covers the basics; we can make it noticeably more useful.

**Acceptance criteria**
- Add `recombyne diff <query_id_a> <query_id_b>` showing weighted score and
  divergence deltas between two stored queries.
- Add `recombyne watch --topic ... --interval 5m` to run a polling watcher
  locally without the backend background task.
- Update `docs/api-reference.md` and `README.md` with examples.

**Labels:** `enhancement`, `cli`, `good first issue`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=CLI+improvements+for+analyst+workflows&labels=enhancement,cli,good+first+issue&body=See+%60.github/STARTER_ISSUES.md%60+%237+for+full+context.%0A%0A**Goal:**+Add+%60diff%60+and+%60watch%60+commands+to+%60scripts/recombyne_cli.py%60.%0A%0A**Acceptance%20Criteria:**%0A-+%60recombyne+diff+%3Cquery_id_a%3E+%3Cquery_id_b%3E%60+prints+weighted+score+and+divergence+deltas.%0A-+%60recombyne+watch+--topic+...+--interval+5m%60+runs+a+local+polling+watcher.%0A-+Document+both+in+%60README.md%60+and+%60docs/api-reference.md%60.)

---

## 8. Frontend accessibility audit

**Why**
The dashboard is dark-mode by default and not yet audited for keyboard
navigation, color contrast, and screen-reader labels.

**Acceptance criteria**
- Run an automated accessibility audit (axe, Lighthouse) on the dashboard,
  query, and settings routes.
- File issues for any failures and fix the highest-impact ones in this PR
  (focus order, ARIA labels on the query controls, alt text on the logo).
- Add a short "Accessibility" section to `CONTRIBUTING.md`.

**Labels:** `enhancement`, `frontend`, `accessibility`, `good first issue`

[File this issue](https://github.com/rishabhkarnawat/recombynemodel/issues/new?title=Frontend+accessibility+audit&labels=enhancement,frontend,accessibility,good+first+issue&body=See+%60.github/STARTER_ISSUES.md%60+%238+for+full+context.%0A%0A**Goal:**+Audit+the+dashboard+for+keyboard+navigation,+color+contrast,+and+screen-reader+labels.%0A%0A**Acceptance%20Criteria:**%0A-+Run+axe+or+Lighthouse+on+the+dashboard,+query,+and+settings+routes.%0A-+Fix+focus+order,+ARIA+labels,+and+alt+text+on+priority+components.%0A-+Add+an+%22Accessibility%22+section+to+%60CONTRIBUTING.md%60.)
