# Recombyne

**Signal from the scatter.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/rishabhkarnawat/recombynemodel/actions/workflows/ci.yml/badge.svg)](https://github.com/rishabhkarnawat/recombynemodel/actions/workflows/ci.yml)
[![Issues](https://img.shields.io/github/issues/rishabhkarnawat/recombynemodel.svg)](https://github.com/rishabhkarnawat/recombynemodel/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/rishabhkarnawat/recombynemodel/pulls)

Recombyne is a real-time engagement-weighted sentiment intelligence platform that ingests public conversation from Twitter and Reddit, scores each post with transformer-based NLP, and weights sentiment by earned engagement so analysts can separate high-impact signal from low-visibility noise.

## How It Works

### 1) Ingest
Recombyne fetches topic-matching posts from Twitter and Reddit through source-specific ingestion services with normalized output models.

### 2) Score
Each post is scored with RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment-latest`) to produce signed sentiment and confidence.

### 3) Weight
Sentiment is reweighted using platform-specific engagement formulas and log normalization, ensuring influential posts contribute proportionally more signal.

### 4) Surface
The platform returns weighted summaries, top signals, timeline buckets, and divergence flags that highlight narrative concentration among high-engagement voices.

## Project Status

Recombyne is under active development. Major milestones to date:

### Phase 1 — Foundation (shipped)
- [x] Repository scaffold with backend, frontend, docs, Docker, and CI
- [x] FastAPI backend with typed routes, schemas, and BYOA configuration
- [x] Twitter and Reddit ingestion services with normalized post models
- [x] RoBERTa sentiment scoring engine
- [x] Engagement weighting and divergence detection (initial version)
- [x] Next.js dashboard with `QueryTerminal` and timeline visualization

### Phase 2 — Refinement and automation (shipped)
- [x] Time decay weighting with configurable rate
- [x] Author credibility scoring for Twitter and Reddit
- [x] Sarcasm + negation handling in the text preprocessor
- [x] Three new divergence types: platform, temporal, and volume
- [x] Query history store and dashboard history panel
- [x] Topic watchlist with scheduled background refresh
- [x] Entity co-mention extraction (spaCy with regex fallback)
- [x] CSV and JSON export endpoints with one-click frontend buttons
- [x] Real backend test suite with mocked API fixtures
- [x] Pre-commit hooks (Black, isort, Flake8, Prettier, ESLint, spelling guard)
- [x] Auto-generated `CHANGELOG.md` from conventional commits
- [x] Post filtering pipeline with configurable rejection rules
- [x] Confidence thresholding with soft downweighting
- [x] Language detection and non-English post flagging
- [x] Recombyne CLI tool (`scripts/recombyne_cli.py`)
- [x] Local seed data so contributors can run end-to-end without API keys
- [x] Standardized exception hierarchy and structured error responses

### Phase 3 — What is next
- [ ] Additional data sources: YouTube, news, forums
- [ ] Historical backtesting workspace and replayable query windows
- [ ] Configurable weighting coefficients per domain (finance, sports, brand)
- [ ] User-defined alert subscriptions (email, Slack, webhook)
- [ ] Persistent Postgres-backed history and watchlist (replaces in-memory store)
- [ ] Public demo deployment with seed data
- [ ] Benchmarks against human-labeled sentiment datasets
- [ ] Authenticated multi-user sessions and saved workspaces

## Getting Started

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```
2. Fill your own API keys in `.env`.
3. Launch local stack:
   ```bash
   docker compose up --build
   ```
4. Open frontend: `http://localhost:3000`
5. Backend API docs: `http://localhost:8000/docs`

## Bring Your Own API Keys

Recombyne is BYOA by design. Read setup instructions in [`docs/byoa-setup.md`](docs/byoa-setup.md).

## Running Without API Keys

You can explore Recombyne end-to-end without any social API credentials by
seeding the local instance with realistic mock data.

```bash
docker compose up backend
python scripts/seed_topics.py
python scripts/recombyne_cli.py history
```

`scripts/seed_topics.py` injects five themed topics (Waymo, Arc Browser,
Kalshi, New Balance 1906R, Polymarket) into the local history store. The
dashboard, watchlist, and CLI all read from this store, so contributors can
iterate on UX, scoring, and weighting changes without any keys configured.

## Reporting Issues

We rely on contributors and users to flag bugs, propose features, and tell us
when scoring or weighting outputs look wrong.

Please open issues using the dedicated templates:

- [Report a bug](https://github.com/rishabhkarnawat/recombynemodel/issues/new?template=bug_report.md)
- [Request a feature](https://github.com/rishabhkarnawat/recombynemodel/issues/new?template=feature_request.md)
- [Flag a data quality concern](https://github.com/rishabhkarnawat/recombynemodel/issues/new?template=data_quality.md)

For a curated list of starter tasks ready to be picked up, see
[`.github/STARTER_ISSUES.md`](.github/STARTER_ISSUES.md). Each task includes a
one-click link that pre-fills a GitHub issue you can adjust and submit.

## Contributing

We welcome pull requests for ingestion improvements, weighting research,
visualization upgrades, and documentation clarity. Full workflow is documented
in [`CONTRIBUTING.md`](CONTRIBUTING.md). All commits should follow the
[`COMMIT_CONVENTION.md`](COMMIT_CONVENTION.md) so the changelog stays accurate.

## Community

- Issue templates: bug, feature, and data-quality
- Pre-commit hooks enforce formatting and the project spelling rule
- Conventional Commits drive an auto-updated `CHANGELOG.md`
- Pull requests are welcome on every roadmap item above
