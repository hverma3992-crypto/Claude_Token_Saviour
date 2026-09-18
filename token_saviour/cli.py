"""
CLI — Command-line interface for Claude Token Saviour.

Commands:
    classify <prompt>  — Show which model would be selected for a prompt
    route <prompt>     — Send a prompt to the optimal model
    report             — Show token usage and savings report
    config             — Display current configuration
    optimize <prompt>  — Show prompt optimization suggestions
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from token_saviour.classifier import TaskClassifier, ComplexityTier
from token_saviour.router import ModelRouter
from token_saviour.tracker import UsageTracker
from token_saviour.optimizer import PromptOptimizer
from token_saviour.config import Config


def _get_console():
    """Get a Rich console, or None if Rich is not available."""
    try:
        from rich.console import Console
        return Console()
    except ImportError:
        return None


def cmd_classify(args: argparse.Namespace) -> None:
    """Classify a prompt and show the recommended model."""
    prompt = " ".join(args.prompt)
    if not prompt:
        print("Error: Please provide a prompt to classify.")
        sys.exit(1)

    classifier = TaskClassifier()
    result = classifier.classify(prompt)

    console = _get_console()
    if console:
        from rich.panel import Panel
        from rich.table import Table
        from rich import box

        # Tier color mapping
        tier_colors = {
            ComplexityTier.SIMPLE: "green",
            ComplexityTier.MODERATE: "yellow",
            ComplexityTier.COMPLEX: "red",
        }
        color = tier_colors.get(result.tier, "white")

        console.print()
        console.print(Panel(
            f"[bold {color}]{result.tier.value}[/bold {color}] → [cyan]{result.model}[/cyan]\n\n"
            f"[dim]Score: {result.score:.2f} | "
            f"Est. Tokens: {result.token_estimate:,} | "
            f"Savings vs Opus: {result.estimated_savings_pct:.0f}%[/dim]\n\n"
            f"[dim]Reasoning: {result.reasoning}[/dim]",
            title="🧠 Classification Result",
            border_style=color,
        ))
        console.print()
    else:
        print(f"\n{'='*50}")
        print(f"  Tier:     {result.tier.value}")
        print(f"  Model:    {result.model}")
        print(f"  Score:    {result.score:.2f}")
        print(f"  Tokens:   {result.token_estimate:,}")
        print(f"  Savings:  {result.estimated_savings_pct:.0f}% vs Opus")
        print(f"  Reason:   {result.reasoning}")
        print(f"{'='*50}\n")


def cmd_route(args: argparse.Namespace) -> None:
    """Route a prompt to the optimal model and display the response."""
    prompt = " ".join(args.prompt)
    if not prompt:
        print("Error: Please provide a prompt to route.")
        sys.exit(1)

    config = Config()
    router = ModelRouter(config=config)
    tracker = UsageTracker(data_file=config.tracking.get("data_file", "usage_data.json"))

    # Parse force options
    force_tier = None
    if args.force_tier:
        try:
            force_tier = ComplexityTier(args.force_tier.upper())
        except ValueError:
            print(f"Error: Invalid tier '{args.force_tier}'. Use SIMPLE, MODERATE, or COMPLEX.")
            sys.exit(1)

    console = _get_console()

    try:
        if console:
            with console.status("[bold cyan]Classifying and routing...[/bold cyan]"):
                result = router.route(
                    prompt=prompt,
                    force_model=args.force_model,
                    force_tier=force_tier,
                    max_tokens=args.max_tokens,
                )
        else:
            print("Classifying and routing...")
            result = router.route(
                prompt=prompt,
                force_model=args.force_model,
                force_tier=force_tier,
                max_tokens=args.max_tokens,
            )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Log the usage
    tracker.log_from_route_result(result)

    # Display results
    if console:
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich import box

        console.print()
        console.print(Panel(
            f"[bold]Model:[/bold] {result.model_used}\n"
            f"[bold]Tier:[/bold] {result.classification.tier.value}\n"
            f"[bold]Cost:[/bold] ${result.cost_usd:.6f}\n"
            f"[bold]Tokens:[/bold] {result.input_tokens} in / {result.output_tokens} out"
            + (f"\n[yellow]⚠️ Fallback used from {result.fallback_from}[/yellow]" if result.fallback_used else ""),
            title="📡 Route Info",
            border_style="cyan",
        ))
        console.print()
        console.print(Panel(
            Markdown(result.response_text),
            title="💬 Response",
            border_style="green",
        ))
        console.print()
    else:
        print(f"\n--- Route Info ---")
        print(f"  Model: {result.model_used}")
        print(f"  Tier:  {result.classification.tier.value}")
        print(f"  Cost:  ${result.cost_usd:.6f}")
        print(f"  Tokens: {result.input_tokens} in / {result.output_tokens} out")
        if result.fallback_used:
            print(f"  ⚠️ Fallback from: {result.fallback_from}")
        print(f"\n--- Response ---")
        print(result.response_text)
        print()


def cmd_report(args: argparse.Namespace) -> None:
    """Display the usage and savings report."""
    config = Config()
    tracker = UsageTracker(data_file=config.tracking.get("data_file", "usage_data.json"))
    tracker.print_report(period=args.period)


def cmd_config(args: argparse.Namespace) -> None:
    """Display the current configuration."""
    config = Config()
    data = config.to_dict()

    console = _get_console()
    if console:
        from rich.panel import Panel
        from rich.syntax import Syntax
        import json

        console.print()
        formatted = json.dumps(data, indent=2)
        console.print(Panel(
            Syntax(formatted, "json", theme="monokai"),
            title="⚙️ Current Configuration",
            border_style="cyan",
        ))
        console.print()
    else:
        import json
        print(f"\n--- Configuration ---")
        print(json.dumps(data, indent=2))
        print()


def cmd_optimize(args: argparse.Namespace) -> None:
    """Show prompt optimization suggestions."""
    prompt = " ".join(args.prompt)
    if not prompt:
        print("Error: Please provide a prompt to optimize.")
        sys.exit(1)

    result = PromptOptimizer.compress_prompt(prompt)
    suggested_tokens = PromptOptimizer.suggest_max_tokens(prompt)

    console = _get_console()
    if console:
        from rich.panel import Panel
        from rich.table import Table
        from rich import box

        console.print()

        # Stats table
        table = Table(title="✨ Optimization Results", box=box.ROUNDED)
        table.add_column("Metric", style="bold")
        table.add_column("Before", justify="right")
        table.add_column("After", justify="right")
        table.add_row("Tokens (est.)", str(result.original_tokens), str(result.optimized_tokens))
        table.add_row(
            "Savings",
            "",
            f"[green]{result.tokens_saved} tokens ({result.savings_percentage}%)[/green]"
        )
        table.add_row("Suggested max_tokens", "", str(suggested_tokens))
        console.print(table)

        if result.techniques_applied:
            console.print(f"\n[dim]Techniques applied: {', '.join(result.techniques_applied)}[/dim]")

        if result.optimized_text != result.original_text:
            console.print(Panel(
                result.optimized_text,
                title="📝 Optimized Prompt",
                border_style="green",
            ))
        console.print()
    else:
        print(f"\n--- Optimization Results ---")
        print(f"  Before: {result.original_tokens} tokens")
        print(f"  After:  {result.optimized_tokens} tokens")
        print(f"  Saved:  {result.tokens_saved} tokens ({result.savings_percentage}%)")
        print(f"  Suggested max_tokens: {suggested_tokens}")
        if result.techniques_applied:
            print(f"  Techniques: {', '.join(result.techniques_applied)}")
        print()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="token-saviour",
        description="Claude Token Saviour — Auto-route to the cheapest suitable Claude model.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # classify
    classify_parser = subparsers.add_parser(
        "classify", help="Classify a prompt and show the recommended model"
    )
    classify_parser.add_argument("prompt", nargs="+", help="The prompt to classify")

    # route
    route_parser = subparsers.add_parser(
        "route", help="Route a prompt to the optimal model"
    )
    route_parser.add_argument("prompt", nargs="+", help="The prompt to route")
    route_parser.add_argument("--force-model", help="Force a specific model")
    route_parser.add_argument("--force-tier", help="Force a specific tier (SIMPLE/MODERATE/COMPLEX)")
    route_parser.add_argument("--max-tokens", type=int, help="Override max tokens")

    # report
    report_parser = subparsers.add_parser("report", help="Show usage and savings report")
    report_parser.add_argument(
        "--period", default="all", choices=["all", "today", "week", "month"],
        help="Report period"
    )

    # config
    subparsers.add_parser("config", help="Display current configuration")

    # optimize
    optimize_parser = subparsers.add_parser(
        "optimize", help="Show prompt optimization suggestions"
    )
    optimize_parser.add_argument("prompt", nargs="+", help="The prompt to optimize")

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "classify": cmd_classify,
        "route": cmd_route,
        "report": cmd_report,
        "config": cmd_config,
        "optimize": cmd_optimize,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
