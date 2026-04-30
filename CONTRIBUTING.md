# Contributing to Recombyne

Thank you for contributing to Recombyne.

## Fork and Clone
1. Fork the repository on GitHub.
2. Clone your fork locally.
3. Create a feature branch from `main`.

## Set Up the Dev Environment (Docker)
1. Copy `.env.example` to `.env` and provide your own keys.
2. Run `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`.
3. Confirm frontend on `localhost:3000` and backend on `localhost:8000`.

## Coding Standards
- Python: format with Black and organize imports with isort.
- TypeScript: format with Prettier and keep strict typing enabled.
- Add docstrings/JSDoc for all functions.

## Run Tests Before PR
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run type-check && npm run lint && npm test`

## Open Issues
Please use dedicated templates for:
- Bug reports
- Feature requests
- Data quality concerns

## PR Review Process
1. Open a pull request with the provided template.
2. Ensure CI passes and docs are updated.
3. A maintainer will review for correctness, readability, and reproducibility.
4. Address review feedback and keep commits focused.

## High-Need Contribution Areas
- New data source adapters
- Improved engagement weighting models
- Richer visualizations and analyst tooling
- Documentation and onboarding improvements
