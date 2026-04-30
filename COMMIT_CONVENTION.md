# Recombyne Commit Convention

Recombyne uses [Conventional Commits](https://www.conventionalcommits.org/) so
the changelog can be generated automatically from commit history.

## Format

```
<type>(<optional scope>): <imperative summary>

<optional body>
<optional footer>
```

## Allowed Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only
- `refactor`: Code refactor without functional change
- `test`: Adding or updating tests
- `chore`: Tooling, config, or housekeeping
- `perf`: Performance improvements

## Recombyne-specific Examples

```
feat: add Reddit ingestion for new subreddit
fix: correct engagement weight for Reddit upvote_ratio
refactor: simplify divergence detection threshold logic
docs: update byoa-setup.md with new Twitter API tier guidance
test: add weighting tests for time decay edge cases
```

Keep summaries imperative ("add", "fix", "update") and concise. Reference
issues with `#<id>` in the body when applicable.
