"""Seed script for default tracked topics."""


def seed_topics() -> list[str]:
    """Return default topic seeds for initial experimentation."""

    return ["NVDA", "AAPL", "TSLA", "BTC", "OpenAI"]


if __name__ == "__main__":
    print("Seeding topics:")
    for topic in seed_topics():
        print(f"- {topic}")
