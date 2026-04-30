"""Validate BYOA keys for Twitter and Reddit APIs."""

import os
from dataclasses import dataclass

import praw
import requests
from dotenv import load_dotenv
from prawcore import PrawcoreException


@dataclass
class KeyCheckResult:
    """Stores the outcome of a key validation check."""

    source: str
    passed: bool
    message: str


def test_twitter_key(token: str | None) -> KeyCheckResult:
    """Validate Twitter bearer token with a minimal endpoint call."""

    if not token:
        return KeyCheckResult("twitter", False, "Missing TWITTER_BEARER_TOKEN.")
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/recent",
        headers={"Authorization": f"Bearer {token}"},
        params={"query": "recombyne", "max_results": 10},
        timeout=15,
    )
    if response.status_code == 200:
        return KeyCheckResult("twitter", True, "Twitter key is valid.")
    if response.status_code == 401:
        return KeyCheckResult("twitter", False, "Twitter key is invalid or expired.")
    if response.status_code == 429:
        return KeyCheckResult(
            "twitter", False, "Twitter key is valid but currently rate limited."
        )
    return KeyCheckResult(
        "twitter",
        False,
        f"Twitter call failed: HTTP {response.status_code} {response.text}",
    )


def test_reddit_key(
    client_id: str | None, client_secret: str | None, user_agent: str | None
) -> KeyCheckResult:
    """Validate Reddit credentials by loading one known subreddit."""

    if not client_id or not client_secret:
        return KeyCheckResult(
            "reddit", False, "Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET."
        )
    if not user_agent:
        return KeyCheckResult("reddit", False, "Missing REDDIT_USER_AGENT.")
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            check_for_async=False,
        )
        _ = list(reddit.subreddit("all").hot(limit=1))
        return KeyCheckResult("reddit", True, "Reddit credentials are valid.")
    except PrawcoreException as exc:
        message = str(exc)
        if "401" in message:
            return KeyCheckResult("reddit", False, "Reddit credentials are invalid.")
        if "429" in message:
            return KeyCheckResult("reddit", False, "Reddit API rate limit hit.")
        return KeyCheckResult("reddit", False, f"Reddit auth/network issue: {message}")
    except Exception as exc:
        return KeyCheckResult("reddit", False, f"Reddit validation failed: {exc}")


def main() -> None:
    """Load env file, run key checks, and print a clear summary."""

    load_dotenv()
    results = [
        test_twitter_key(os.getenv("TWITTER_BEARER_TOKEN")),
        test_reddit_key(
            os.getenv("REDDIT_CLIENT_ID"),
            os.getenv("REDDIT_CLIENT_SECRET"),
            os.getenv("REDDIT_USER_AGENT"),
        ),
    ]
    print("Recombyne BYOA key validation")
    print("=" * 40)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.source}: {result.message}")


if __name__ == "__main__":
    main()
