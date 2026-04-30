"""Sentiment scoring and preprocessing tests."""

from app.services.scoring.text_preprocessor import TextPreprocessor


def test_score_and_confidence_in_expected_ranges(sample_sentiments) -> None:
    """All sentiment fixtures must respect documented bounds."""

    for result in sample_sentiments:
        assert -1.0 <= result.score <= 1.0
        assert 0.0 <= result.confidence <= 1.0


def test_negation_detection_flags_negated_sentence() -> None:
    """Negation tokens near sentiment tokens should set the flag."""

    processor = TextPreprocessor()
    result = processor.preprocess("This product is not good at all.")
    assert result.negation_detected is True
    assert result.confidence_modifier <= 0.75


def test_sarcasm_risk_elevated_for_obvious_sarcasm() -> None:
    """Sarcasm markers + negative context should raise sarcasm risk."""

    processor = TextPreprocessor()
    result = processor.preprocess("Great job, the app crashed again. Yeah right.")
    assert result.sarcasm_risk > 0.6
    assert result.confidence_modifier <= 0.60


def test_batch_score_count_matches_input(scorer, monkeypatch) -> None:
    """Batch scoring must return one result per input even via API path."""

    async def fake_api_score(self, processed):
        from app.schemas.sentiment import SentimentResult

        return SentimentResult(
            label="neutral",
            score=0.0,
            confidence=0.5,
            raw_logits=[0.33, 0.34, 0.33],
        )

    monkeypatch.setattr(
        "app.services.scoring.roberta.RoBERTaSentimentScorer._score_via_hf_api",
        fake_api_score,
    )

    import asyncio

    results = asyncio.run(scorer.batch_score(["hello", "world", "test"]))
    assert len(results) == 3


def test_confidence_modifier_applied_when_negation_detected(
    scorer, monkeypatch
) -> None:
    """Negation should reduce final confidence on the SentimentResult."""

    async def fake_api_score(self, processed):
        from app.services.scoring.roberta import RoBERTaSentimentScorer

        logits = [0.05, 0.15, 0.80]
        return RoBERTaSentimentScorer._normalize_logits(logits, processed)

    monkeypatch.setattr(
        "app.services.scoring.roberta.RoBERTaSentimentScorer._score_via_hf_api",
        fake_api_score,
    )

    import asyncio

    result = asyncio.run(scorer.score("This product is not good at all."))
    assert result.confidence <= 0.80 * 0.75 + 1e-6
