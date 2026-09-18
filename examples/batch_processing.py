"""
Batch Processing Example — Claude Token Saviour

Demonstrates processing multiple prompts in batch mode with cost tracking.
Requires ANTHROPIC_API_KEY environment variable to be set for actual API calls.
"""

import os
from token_saviour import TaskClassifier, ModelRouter, UsageTracker, PromptOptimizer


def main():
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set. Running in dry-run mode (classification only).\n")
        dry_run()
        return

    router = ModelRouter()
    tracker = UsageTracker(data_file="batch_usage.json")

    prompts = [
        "Fix this typo: 'recieve' → 'receive'",
        "Write a Python function to validate email addresses",
        "Explain the difference between TCP and UDP",
        "Design a caching strategy for a high-traffic e-commerce API",
    ]

    print("🚀 Processing batch of prompts...\n")

    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] Processing: \"{prompt[:50]}...\"")

        try:
            result = router.route(prompt)
            tracker.log_from_route_result(result)
            print(f"   ✅ {result.classification.tier.value} → {result.model_used} (${result.cost_usd:.6f})")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 50)
    tracker.print_report()


def dry_run():
    """Run classification without API calls."""
    classifier = TaskClassifier()

    prompts = [
        "Fix this typo: 'recieve' → 'receive'",
        "Write a Python function to validate email addresses",
        "Explain the difference between TCP and UDP",
        "Design a caching strategy for a high-traffic e-commerce API",
        "Convert this CSV data to JSON format",
        "Review this authentication middleware for security issues",
        "Generate getter and setter methods for this class",
        "Architect a real-time notification system using WebSockets",
    ]

    total_savings = 0
    tier_counts = {"SIMPLE": 0, "MODERATE": 0, "COMPLEX": 0}

    print("📊 Batch Classification (Dry Run)\n")
    for prompt in prompts:
        result = classifier.classify(prompt)
        tier_counts[result.tier.value] += 1
        total_savings += result.estimated_savings_pct

        emoji = {"SIMPLE": "🟢", "MODERATE": "🟡", "COMPLEX": "🔴"}[result.tier.value]
        print(f"  {emoji} [{result.tier.value:8s}] {prompt[:55]}")

    avg_savings = total_savings / len(prompts) if prompts else 0
    print(f"\n  📈 Distribution: {tier_counts}")
    print(f"  💰 Average savings vs all-Opus: {avg_savings:.0f}%")
    print(f"  ✨ {tier_counts['SIMPLE']} of {len(prompts)} prompts can use Haiku (cheapest model)")


if __name__ == "__main__":
    main()
