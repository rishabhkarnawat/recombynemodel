"""Sentiment scoring service tests."""

import pytest
from app.services.scoring.roberta import RoBERTaSentimentScorer


@pytest.mark.asyncio
async def test_batch_score_returns_expected_length() -> None:
    """Verify scorer returns one result per input text."""

    scorer = RoBERTaSentimentScorer()
    results = await scorer.batch_score(["good", "bad"])
    assert len(results) == 2
