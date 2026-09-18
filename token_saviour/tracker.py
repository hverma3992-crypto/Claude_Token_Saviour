"""
Usage Tracker — Logs API calls, tracks token consumption, and calculates savings.

Persists usage data to a JSON file and generates reports comparing actual costs
to the "always use Opus" baseline.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class UsageEntry:
    """A single API usage log entry."""
    timestamp: str
    prompt_preview: str
    tier: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    opus_cost_usd: float
    savings_usd: float
    fallback_used: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UsageEntry":
        return cls(**data)


@dataclass
class UsageReport:
    """Aggregated usage report."""
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    total_opus_cost_usd: float
    total_savings_usd: float
    savings_percentage: float
    tier_breakdown: dict[str, int]
    model_breakdown: dict[str, int]
    period: str


@dataclass
class UsageTracker:
    """
    Tracks Claude API usage, logs every call, and calculates savings vs all-Opus baseline.

    Data is persisted to a JSON file for historical reporting.
    """

    data_file: str = "usage_data.json"
    _entries: list[UsageEntry] = field(default_factory=list, repr=False)
    _loaded: bool = field(default=False, repr=False)

    def _ensure_loaded(self) -> None:
        """Lazy-load entries from the data file."""
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self) -> None:
        """Load usage data from the JSON file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._entries = [UsageEntry.from_dict(entry) for entry in data]
            except (json.JSONDecodeError, KeyError):
                self._entries = []
        else:
            self._entries = []

    def _save(self) -> None:
        """Save usage data to the JSON file."""
        # Ensure parent directory exists
        parent = Path(self.data_file).parent
        if parent != Path("."):
            parent.mkdir(parents=True, exist_ok=True)

        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([entry.to_dict() for entry in self._entries], f, indent=2)

    def log(
        self,
        prompt: str,
        tier: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        fallback_used: bool = False,
    ) -> UsageEntry:
        """
        Log a single API call.

        Args:
            prompt: The original prompt text (will be truncated for storage).
            tier: The complexity tier (SIMPLE, MODERATE, COMPLEX).
            model: The model that was actually used.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            cost_usd: Actual cost of the call.
            fallback_used: Whether a fallback model was used.

        Returns:
            The created UsageEntry.
        """
        self._ensure_loaded()

        # Calculate what it would have cost with Opus
        opus_input_cost = input_tokens / 1_000_000 * 15.00
        opus_output_cost = output_tokens / 1_000_000 * 75.00
        opus_cost = round(opus_input_cost + opus_output_cost, 6)
        savings = round(opus_cost - cost_usd, 6)

        entry = UsageEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt_preview=prompt[:100] + "..." if len(prompt) > 100 else prompt,
            tier=tier,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            opus_cost_usd=opus_cost,
            savings_usd=max(0.0, savings),
            fallback_used=fallback_used,
        )

        self._entries.append(entry)
        self._save()
        return entry

    def log_from_route_result(self, route_result) -> UsageEntry:
        """
        Log usage from a RouteResult object (from ModelRouter.route()).

        Args:
            route_result: A RouteResult from ModelRouter.route().

        Returns:
            The created UsageEntry.
        """
        return self.log(
            prompt=route_result.prompt,
            tier=route_result.classification.tier.value,
            model=route_result.model_used,
            input_tokens=route_result.input_tokens,
            output_tokens=route_result.output_tokens,
            cost_usd=route_result.cost_usd,
            fallback_used=route_result.fallback_used,
        )

    def get_report(self, period: str = "all") -> UsageReport:
        """
        Generate an aggregated usage report.

        Args:
            period: "all", "today", "week", or "month".

        Returns:
            UsageReport with aggregated statistics.
        """
        self._ensure_loaded()
        entries = self._filter_entries(period)

        total_input = sum(e.input_tokens for e in entries)
        total_output = sum(e.output_tokens for e in entries)
        total_cost = sum(e.cost_usd for e in entries)
        total_opus_cost = sum(e.opus_cost_usd for e in entries)
        total_savings = sum(e.savings_usd for e in entries)

        tier_breakdown: dict[str, int] = {}
        model_breakdown: dict[str, int] = {}
        for entry in entries:
            tier_breakdown[entry.tier] = tier_breakdown.get(entry.tier, 0) + 1
            model_breakdown[entry.model] = model_breakdown.get(entry.model, 0) + 1

        savings_pct = (total_savings / total_opus_cost * 100) if total_opus_cost > 0 else 0.0

        return UsageReport(
            total_requests=len(entries),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_cost_usd=round(total_cost, 4),
            total_opus_cost_usd=round(total_opus_cost, 4),
            total_savings_usd=round(total_savings, 4),
            savings_percentage=round(savings_pct, 1),
            tier_breakdown=tier_breakdown,
            model_breakdown=model_breakdown,
            period=period,
        )

    def _filter_entries(self, period: str) -> list[UsageEntry]:
        """Filter entries by time period."""
        if period == "all":
            return self._entries

        now = datetime.now(timezone.utc)
        filtered = []
        for entry in self._entries:
            try:
                entry_time = datetime.fromisoformat(entry.timestamp)
                delta = now - entry_time
                if period == "today" and delta.days == 0:
                    filtered.append(entry)
                elif period == "week" and delta.days <= 7:
                    filtered.append(entry)
                elif period == "month" and delta.days <= 30:
                    filtered.append(entry)
            except ValueError:
                continue
        return filtered

    def print_report(self, period: str = "all") -> None:
        """Print a formatted usage report to the console."""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            self._print_rich_report(period)
        except ImportError:
            self._print_plain_report(period)

    def _print_rich_report(self, period: str) -> None:
        """Print a beautifully formatted report using Rich."""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        console = Console()
        report = self.get_report(period)

        # Header
        console.print()
        console.print(Panel(
            f"[bold cyan]Claude Token Saviour — Usage Report[/bold cyan]\n"
            f"[dim]Period: {period} | Total Requests: {report.total_requests}[/dim]",
            box=box.DOUBLE,
        ))

        if report.total_requests == 0:
            console.print("[yellow]No usage data found for this period.[/yellow]")
            return

        # Cost summary
        cost_table = Table(title="💰 Cost Summary", box=box.ROUNDED)
        cost_table.add_column("Metric", style="bold")
        cost_table.add_column("Value", justify="right")
        cost_table.add_row("Actual Cost", f"${report.total_cost_usd:.4f}")
        cost_table.add_row("All-Opus Cost", f"${report.total_opus_cost_usd:.4f}")
        cost_table.add_row(
            "💸 Savings",
            f"[bold green]${report.total_savings_usd:.4f} ({report.savings_percentage:.1f}%)[/bold green]"
        )
        console.print(cost_table)

        # Token usage
        token_table = Table(title="📊 Token Usage", box=box.ROUNDED)
        token_table.add_column("Type", style="bold")
        token_table.add_column("Count", justify="right")
        token_table.add_row("Input Tokens", f"{report.total_input_tokens:,}")
        token_table.add_row("Output Tokens", f"{report.total_output_tokens:,}")
        token_table.add_row("Total Tokens", f"{report.total_input_tokens + report.total_output_tokens:,}")
        console.print(token_table)

        # Tier breakdown
        if report.tier_breakdown:
            tier_table = Table(title="🏷️ Tier Breakdown", box=box.ROUNDED)
            tier_table.add_column("Tier", style="bold")
            tier_table.add_column("Requests", justify="right")
            tier_table.add_column("Percentage", justify="right")
            for tier, count in sorted(report.tier_breakdown.items()):
                pct = count / report.total_requests * 100
                tier_table.add_row(tier, str(count), f"{pct:.1f}%")
            console.print(tier_table)

        # Model breakdown
        if report.model_breakdown:
            model_table = Table(title="🤖 Model Breakdown", box=box.ROUNDED)
            model_table.add_column("Model", style="bold")
            model_table.add_column("Requests", justify="right")
            for model, count in sorted(report.model_breakdown.items()):
                model_table.add_row(model, str(count))
            console.print(model_table)

        console.print()

    def _print_plain_report(self, period: str) -> None:
        """Print a plain-text report (fallback without Rich)."""
        report = self.get_report(period)

        print(f"\n{'='*50}")
        print(f"  Claude Token Saviour — Usage Report")
        print(f"  Period: {period} | Requests: {report.total_requests}")
        print(f"{'='*50}")

        if report.total_requests == 0:
            print("No usage data found.")
            return

        print(f"\n  Actual Cost:   ${report.total_cost_usd:.4f}")
        print(f"  All-Opus Cost: ${report.total_opus_cost_usd:.4f}")
        print(f"  Savings:       ${report.total_savings_usd:.4f} ({report.savings_percentage:.1f}%)")
        print(f"\n  Input Tokens:  {report.total_input_tokens:,}")
        print(f"  Output Tokens: {report.total_output_tokens:,}")

        if report.tier_breakdown:
            print(f"\n  Tier Breakdown:")
            for tier, count in sorted(report.tier_breakdown.items()):
                print(f"    {tier}: {count}")

        print()

    def clear(self) -> None:
        """Clear all usage data."""
        self._entries = []
        self._save()

    @property
    def entries(self) -> list[UsageEntry]:
        """Get all usage entries."""
        self._ensure_loaded()
        return list(self._entries)
