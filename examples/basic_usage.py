"""
Basic Usage Example — Claude Token Saviour

Demonstrates how to classify prompts and see which model would be selected,
without making any API calls.
"""

from token_saviour import TaskClassifier, PromptOptimizer

def main():
    classifier = TaskClassifier()

    # Example prompts of varying complexity
    prompts = [
        "Fix the typo in this variable name: prnt_hello",
        "Write unit tests for this authentication module",
        "Design a microservices architecture with event sourcing for a real-time trading platform",
        "Convert this JSON to YAML format",
        "Explain how async/await works in Python with examples",
        "Rename the variable 'x' to 'count' in this function",
        "Analyze the security vulnerabilities in this OAuth implementation",
        "Format this code according to PEP 8",
    ]

    print("=" * 70)
    print("  Claude Token Saviour — Classification Demo")
    print("=" * 70)

    for prompt in prompts:
        result = classifier.classify(prompt)
        print(f"\n📝 Prompt: \"{prompt[:60]}...\"" if len(prompt) > 60 else f"\n📝 Prompt: \"{prompt}\"")
        print(f"   🏷️  Tier:    {result.tier.value}")
        print(f"   🤖 Model:   {result.model}")
        print(f"   📊 Score:   {result.score:.2f}")
        print(f"   💰 Savings: {result.estimated_savings_pct:.0f}% vs Opus")

    print("\n" + "=" * 70)
    print("  Prompt Optimization Demo")
    print("=" * 70)

    verbose_prompt = """
    I would like you to please take a look at the following code and
    if you    could kindly     identify any potential issues or bugs
    that might     exist within it,    that would be very helpful.


    Please also    suggest improvements.

    """
    opt_result = PromptOptimizer.compress_prompt(verbose_prompt)
    print(f"\n   Before:  {opt_result.original_tokens} tokens")
    print(f"   After:   {opt_result.optimized_tokens} tokens")
    print(f"   Saved:   {opt_result.tokens_saved} tokens ({opt_result.savings_percentage}%)")
    print(f"   Methods: {', '.join(opt_result.techniques_applied)}")


if __name__ == "__main__":
    main()
