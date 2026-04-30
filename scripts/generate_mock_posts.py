"""Generate mock RawPost JSON for offline development without API keys."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone

POSITIVE_TEMPLATES = [
    "{topic} just shipped a great update. The team keeps delivering.",
    "Honestly impressed with what {topic} is doing. Big upgrade.",
    "{topic} feels like the right tool for the job today.",
]
NEGATIVE_TEMPLATES = [
    "{topic} is broken again. Same bug as last week.",
    "{topic} keeps slowing down for me. Disappointing rollout.",
    "Not sure why {topic} insists on this design choice. Frustrating.",
]
NEUTRAL_TEMPLATES = [
    "Curious to see where {topic} goes next quarter.",
    "Trying out {topic} for the first time. No strong opinion yet.",
    "Looking at {topic} alongside competitors before deciding.",
]


def _make_text(topic: str, mood: str) -> str:
    """Render a templated post for the requested mood."""

    pool = {
        "positive": POSITIVE_TEMPLATES,
        "negative": NEGATIVE_TEMPLATES,
        "neutral": NEUTRAL_TEMPLATES,
    }[mood]
    return random.choice(pool).format(topic=topic)


def generate_posts(
    topic: str, count: int, source: str, window_hours: int
) -> list[dict]:
    """Return ``count`` mock posts spread across ``window_hours``."""

    now = datetime.now(timezone.utc)
    posts: list[dict] = []
    for index in range(count):
        mood = random.choices(
            ["positive", "neutral", "negative"], weights=[0.4, 0.35, 0.25], k=1
        )[0]
        likes = random.randint(0, 5000)
        reposts = random.randint(0, max(1, likes // 5))
        comments = random.randint(0, max(1, likes // 4))
        upvote_ratio = (
            round(random.uniform(0.55, 0.99), 2) if source == "reddit" else None
        )
        views = random.randint(likes * 5, likes * 200) if source == "twitter" else None
        post = {
            "id": f"{source}-mock-{index}",
            "source": source,
            "text": _make_text(topic, mood),
            "author": f"mock-author-{index}",
            "created_at": (
                now - timedelta(hours=random.randint(0, max(1, window_hours - 1)))
            ).isoformat(),
            "url": f"https://example.com/{source}/{index}",
            "raw_engagement": {
                "likes": likes,
                "reposts": reposts,
                "comments": comments,
                "views": views,
                "upvote_ratio": upvote_ratio,
            },
            "metadata": {"mood": mood},
            "is_english": True,
        }
        posts.append(post)
    return posts


def main() -> None:
    """CLI entrypoint that prints mock posts as JSON."""

    parser = argparse.ArgumentParser(description="Generate mock Recombyne posts")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--source", choices=["twitter", "reddit"], default="twitter")
    parser.add_argument("--window", type=int, default=168, help="Window hours")
    args = parser.parse_args()
    posts = generate_posts(args.topic, args.count, args.source, args.window)
    print(json.dumps(posts, indent=2))


if __name__ == "__main__":
    main()
