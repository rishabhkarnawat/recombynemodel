"""Post filtering pipeline run between ingestion and scoring.

Filters low-quality content out of the scoring pipeline so the engagement
weighter operates on signal rather than noise. Each rule is configurable so
contributors can disable individual rules during experiments and tests.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.ingestion.base import RawPost

logger = logging.getLogger(__name__)


@dataclass
class RejectedPost:
    """Container describing why a post was filtered out."""

    post: RawPost
    reason: str


@dataclass
class FilterResult:
    """Outcome of a filter pass over a batch of posts."""

    passed: list[RawPost] = field(default_factory=list)
    rejected: list[RejectedPost] = field(default_factory=list)
    rejection_summary: dict[str, int] = field(default_factory=dict)


_HASHTAG_OR_MENTION_RE = re.compile(r"(@\w+|#\w+)")
_LINK_ONLY_RE = re.compile(r"^\s*https?://\S+\s*$")


class PostFilter:
    """Apply Recombyne quality rules to a batch of raw posts."""

    def __init__(
        self,
        min_text_length: int = 10,
        reject_short: bool = True,
        reject_low_content: bool = True,
        reject_retweets: bool = True,
        reject_decontextualized_replies: bool = True,
        reject_link_only: bool = True,
        reject_low_credibility: bool = True,
        reject_duplicates: bool = True,
    ) -> None:
        """Configure the filter pipeline.

        Args:
            min_text_length: Minimum text length to retain (characters).
            reject_short: Apply rule 1 - reject very short posts.
            reject_low_content: Apply rule 2 - reject hashtag/mention spam.
            reject_retweets: Apply rule 3 - reject "RT @" reposts.
            reject_decontextualized_replies: Apply rule 4 - reject empty replies.
            reject_link_only: Apply rule 5 - reject link-only posts.
            reject_low_credibility: Apply rule 6 - reject low credibility authors.
            reject_duplicates: Apply rule 7 - reject duplicates within a batch.
        """

        self._min_text_length = int(min_text_length)
        self._reject_short = bool(reject_short)
        self._reject_low_content = bool(reject_low_content)
        self._reject_retweets = bool(reject_retweets)
        self._reject_decontextualized_replies = bool(reject_decontextualized_replies)
        self._reject_link_only = bool(reject_link_only)
        self._reject_low_credibility = bool(reject_low_credibility)
        self._reject_duplicates = bool(reject_duplicates)

    def _classify(self, post: RawPost, seen_texts: set[str]) -> str | None:
        """Return the first rejection reason that applies, or None."""

        text = (post.text or "").strip()
        lower_text = text.lower()

        if self._reject_short and len(text) < self._min_text_length:
            return "too_short"

        if self._reject_low_content and text:
            tag_chars = sum(
                len(match.group(0)) for match in _HASHTAG_OR_MENTION_RE.finditer(text)
            )
            if tag_chars / max(len(text), 1) > 0.80:
                return "low_content"

        if self._reject_retweets and lower_text.startswith("rt @"):
            return "retweet"

        metadata = post.metadata or {}
        if (
            self._reject_decontextualized_replies
            and metadata.get("is_reply") is True
            and not metadata.get("quoted_text")
        ):
            return "decontextualized_reply"

        if self._reject_link_only and _LINK_ONLY_RE.match(text):
            return "link_only"

        if self._reject_low_credibility and post.author_metrics is not None:
            followers = post.author_metrics.followers_count or 0
            tweets = post.author_metrics.tweet_count or 0
            if followers < 10 and tweets < 5:
                return "low_credibility_author"

        if self._reject_duplicates:
            normalized = lower_text
            if normalized in seen_texts:
                return "duplicate"
            seen_texts.add(normalized)

        return None

    def filter(self, posts: list[RawPost]) -> FilterResult:
        """Apply all enabled rules in order and return classification results.

        Args:
            posts: Raw posts coming out of the ingestion layer.

        Returns:
            FilterResult containing kept posts, rejections, and a summary.
        """

        passed: list[RawPost] = []
        rejected: list[RejectedPost] = []
        seen_texts: set[str] = set()

        for post in posts:
            reason = self._classify(post, seen_texts)
            if reason is None:
                passed.append(post)
            else:
                rejected.append(RejectedPost(post=post, reason=reason))

        summary = dict(Counter(item.reason for item in rejected))
        if summary:
            logger.info("post_filter rejection summary: %s", summary)

        return FilterResult(passed=passed, rejected=rejected, rejection_summary=summary)


__all__: list[str] = ["FilterResult", "PostFilter", "RejectedPost"]
