# Recombyne

**Signal from the scatter.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

## Contributing

We welcome pull requests for ingestion improvements, weighting research, visualization upgrades, and documentation clarity. Full workflow is documented in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Roadmap

- [x] Initial ingestion and scoring skeleton
- [x] Engagement weighting and divergence output
- [x] Query API and dashboard foundation
- [ ] Additional data sources (YouTube, forums, news)
- [ ] Historical backtesting workspace
- [ ] Configurable weighting coefficients per domain
- [ ] User-defined alert subscriptions
