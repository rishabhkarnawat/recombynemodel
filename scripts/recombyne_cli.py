"""Recombyne command-line tool.

Usage:
    python scripts/recombyne_cli.py query --topic "Waymo" --sources twitter,reddit --window 7d

The CLI talks to the local Recombyne backend over HTTP so contributors and
power users can run queries, manage the watchlist, and inspect history without
opening the dashboard.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from typing import Any

import click
import requests

API_BASE_URL = os.environ.get("RECOMBYNE_API_URL", "http://localhost:8000")
SEPARATOR = "─" * 56


def _print_header(title: str) -> None:
    """Print a CLI banner consistent with the dashboard QueryTerminal style."""

    click.echo(f"Recombyne CLI  |  {title}")
    click.echo(SEPARATOR)


def _format_score(value: float) -> str:
    """Format a sentiment score with a leading sign for clarity."""

    return f"{value:+.3f}"


def _parse_window(window: str) -> int:
    """Convert window strings like '24h' or '7d' into hours."""

    window = window.strip().lower()
    if window.endswith("d"):
        return int(window[:-1]) * 24
    if window.endswith("h"):
        return int(window[:-1])
    return int(window)


@click.group(help="Recombyne developer CLI.")
def cli() -> None:
    """Top-level click group for Recombyne commands."""


@cli.command()
@click.option("--topic", required=True, help="Topic or keyword to query.")
@click.option(
    "--sources", default="twitter,reddit", help="Comma-separated list of sources."
)
@click.option("--window", default="7d", help="Lookback window (e.g. 24h, 7d, 30d).")
@click.option("--limit", default=300, show_default=True, help="Max posts to ingest.")
def query(topic: str, sources: str, window: str, limit: int) -> None:
    """Run a sentiment intelligence query against the local API."""

    payload: dict[str, Any] = {
        "topic": topic,
        "sources": [s.strip() for s in sources.split(",") if s.strip()],
        "window_hours": _parse_window(window),
        "limit": limit,
    }
    response = requests.post(f"{API_BASE_URL}/api/query", json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()
    weighted = data["weighted_result"]

    _print_header(f'Querying: "{topic}"')
    click.echo(f"Sources: {', '.join(payload['sources'])}")
    click.echo(f"Time window: last {payload['window_hours'] // 24} days")
    click.echo(SEPARATOR)
    click.echo("SENTIMENT SUMMARY")
    click.echo(f"  Overall score:     {_format_score(weighted['raw_score'])}")
    click.echo(f"  Weighted score:    {_format_score(weighted['weighted_score'])}")
    click.echo(f"  Divergence:        {_format_score(weighted['divergence'])}")
    click.echo(f"  Total posts:       {weighted['total_posts']}")
    click.echo("")
    click.echo("TOP SIGNALS")
    for index, signal in enumerate(weighted.get("top_signals", []), start=1):
        click.echo(
            f"  {index}. [{signal['post']['source']}] "
            f"{_format_score(signal['sentiment']['score'])} | "
            f"{signal['post']['text'][:80]}"
        )
    click.echo(SEPARATOR)
    click.echo(f"Query complete.  |  Runtime: {data['runtime_ms']:.1f}ms")


@cli.group()
def watchlist() -> None:
    """Manage the Recombyne watchlist."""


@watchlist.command("add")
@click.option("--topic", required=True, help="Topic to track.")
@click.option("--sources", default="twitter,reddit", help="Comma-separated sources.")
@click.option("--window", default="7d", help="Lookback window per refresh.")
@click.option(
    "--interval", default=60, show_default=True, help="Refresh interval in minutes."
)
def watchlist_add(topic: str, sources: str, window: str, interval: int) -> None:
    """Add a watchlist topic."""

    payload = {
        "topic": topic,
        "sources": [s.strip() for s in sources.split(",") if s.strip()],
        "window_hours": _parse_window(window),
        "refresh_interval_minutes": interval,
    }
    response = requests.post(f"{API_BASE_URL}/api/watchlist", json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    _print_header("Watchlist Added")
    click.echo(json.dumps(data, indent=2))


@watchlist.command("list")
def watchlist_list() -> None:
    """List all watchlist entries."""

    response = requests.get(f"{API_BASE_URL}/api/watchlist", timeout=30)
    response.raise_for_status()
    entries = response.json().get("entries", [])
    _print_header("Watchlist")
    for entry in entries:
        score = entry.get("last_weighted_score")
        score_text = _format_score(score) if score is not None else "n/a"
        delta = entry.get("delta_since_last")
        delta_text = _format_score(delta) if delta is not None else "n/a"
        click.echo(
            f"  - {entry['topic']} (sources={entry['sources']}, score={score_text}, delta={delta_text})"
        )


@cli.group()
def keys() -> None:
    """Validate API credentials."""


@keys.command("test")
def keys_test() -> None:
    """Run the BYOA key validation script."""

    import importlib.util
    import pathlib

    script_path = pathlib.Path(__file__).resolve().parent / "test_keys.py"
    spec = importlib.util.spec_from_file_location("test_keys", script_path)
    if spec is None or spec.loader is None:
        click.echo("Could not load test_keys.py")
        sys.exit(1)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    module.main()


@cli.command()
@click.option(
    "--limit", default=10, show_default=True, help="Number of history rows to show."
)
def history(limit: int) -> None:
    """Show recent queries from the local backend."""

    response = requests.get(
        f"{API_BASE_URL}/api/query/history", params={"limit": limit}, timeout=30
    )
    response.raise_for_status()
    entries = response.json().get("entries", [])
    _print_header("Recent Queries")
    for entry in entries:
        click.echo(
            f"  {entry['queried_at']} | {entry['topic']:<24} | "
            f"raw={_format_score(entry['raw_score'])} | "
            f"weighted={_format_score(entry['weighted_score'])} | "
            f"posts={entry['post_count']}"
        )


@cli.command()
@click.option("--query-id", required=True, help="Query ID to export.")
@click.option("--format", "fmt", default="json", show_default=True, help="json or csv")
@click.option("--output", required=True, help="Path to write the export to.")
def export(query_id: str, fmt: str, output: str) -> None:
    """Export a stored query result to disk."""

    response = requests.get(
        f"{API_BASE_URL}/api/query/{query_id}/export",
        params={"format": fmt},
        timeout=30,
    )
    response.raise_for_status()
    if fmt.lower() == "json":
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(response.text)
    else:
        with open(output, "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            for line in response.text.splitlines():
                writer.writerow(line.split(","))
    _print_header("Export Complete")
    click.echo(f"Wrote {fmt} export to {output}")


if __name__ == "__main__":
    cli()
