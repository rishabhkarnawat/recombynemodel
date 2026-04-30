# Recombyne Algorithm

## Core Thesis
Raw sentiment without attention weighting can misrepresent reality. Recombyne treats engagement as evidence strength: a highly-engaged post contributes more signal than a low-visibility comment.

## Four Stages
1. **Ingest**: Pull recent topic-matching posts from Twitter and Reddit.
2. **Score**: Run RoBERTa sentiment inference to produce signed scores.
3. **Weight**: Apply source-specific engagement equations and log normalization.
4. **Surface**: Build timelines, top signals, and divergence explanations.

## Weighting Formula
For Twitter:

`raw_score = (likes * 1.0) + (reposts * 2.5) + (comments * 1.5) + (views * 0.01 if views else 0)`

For Reddit:

`raw_score = (likes * 1.0) + (comments * 2.0) + (upvote_ratio * 100 if upvote_ratio else 50)`

Normalization:

`weight = log(1 + raw_score)`

### Coefficient Rationale
- `reposts` are weighted heavily because amplification broadens narrative spread.
- `comments` indicate deeper engagement than passive likes.
- `views` influence Twitter weights while staying bounded with a small coefficient.
- `upvote_ratio` helps distinguish controversial threads from broad approval on Reddit.

## RoBERTa Scoring Approach
Recombyne uses `cardiffnlp/twitter-roberta-base-sentiment-latest` for robust short-text polarity. Model labels map to signed anchors (`positive=+1`, `neutral=0`, `negative=-1`) scaled by confidence.

## Divergence as First-Class Signal
Divergence is `weighted_score - raw_score`.
- Positive divergence means influential voices are more optimistic than the average.
- Negative divergence means influential voices are more pessimistic.

A divergence magnitude above `0.15` is flagged and surfaced in API and UI outputs.

## Known Limitations
- Social APIs can constrain recall under strict rate limits.
- Sarcasm and domain slang may reduce sentiment precision.
- Fixed coefficients may underfit specific verticals without calibration.

## Improvement Path
Contributors can propose weighting updates via pull requests with:
- rationale for coefficient changes,
- offline backtests over fixed topic windows,
- regression tests in `backend/tests/test_weighting.py`.
