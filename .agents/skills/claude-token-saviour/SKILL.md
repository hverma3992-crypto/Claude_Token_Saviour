---
name: claude-token-saviour
description: >-
  Use this skill when handling any Claude API request, coding task, or AI-assisted
  workflow to automatically classify task complexity and route to the cheapest
  suitable Claude model (Haiku/Sonnet/Opus). Activates when the user wants to
  optimize token usage, reduce API costs, or when making multiple Claude API calls
  that could benefit from intelligent model selection.
---

# Claude Token Saviour Skill

This skill teaches the agent to minimize Claude token consumption by intelligently
routing tasks to the most cost-effective model and applying prompt optimization
techniques.

---

## Core Principle

**Never use a more expensive model when a cheaper one will produce equivalent results.**

| Complexity | Model | Cost (Input/Output per 1M) |
|------------|-------|---------------------------|
| SIMPLE | Haiku 3.5 | $0.80 / $4.00 |
| MODERATE | Sonnet 4 | $3.00 / $15.00 |
| COMPLEX | Opus 4 | $15.00 / $75.00 |

---

## Step 1: Classify the Task

Before selecting a model, classify every prompt into a complexity tier.

### SIMPLE Tasks → Use Haiku 3.5
- Typo fixes, formatting, and simple text transformations
- Code boilerplate generation (getters/setters, CRUD scaffolding)
- Simple lookups, definitions, and factual Q&A
- JSON/YAML/CSV parsing and conversion
- Regex generation for straightforward patterns
- Simple summarization of short texts
- Variable renaming, import sorting
- Generating test data or mock values

### MODERATE Tasks → Use Sonnet 4
- Writing unit tests with logic
- Code review and bug identification
- Explaining complex code or concepts
- Refactoring functions or classes
- Writing documentation with examples
- API endpoint implementation
- Database query optimization
- Multi-step debugging
- Standard feature implementation

### COMPLEX Tasks → Use Opus 4
- System architecture design
- Complex algorithm design or optimization
- Multi-file refactoring with dependency analysis
- Security vulnerability analysis
- Performance profiling and optimization strategy
- Design pattern recommendations with trade-off analysis
- Complex debugging requiring deep reasoning
- Multi-step mathematical or logical proofs
- Novel problem-solving requiring creativity

---

## Step 2: Apply Prompt Optimization

Before sending any prompt, apply these token-saving techniques:

### 2a. Compress the Prompt
- Remove unnecessary whitespace, blank lines, and comments from code context
- Use abbreviations where the model will understand (e.g., "fn" → function)
- Strip boilerplate imports if not relevant to the question
- Only include the relevant code snippet, not the entire file

### 2b. Limit Output Tokens
- Set `max_tokens` appropriately for the task:
  - Simple lookups: 100-300 tokens
  - Code generation: 500-1500 tokens
  - Explanations: 300-800 tokens
  - Architecture docs: 1500-4000 tokens
- Use `stop_sequences` to prevent rambling

### 2c. Use System Prompts Efficiently
- Keep system prompts concise and reuse them across similar tasks
- Don't repeat instructions that are implicit in the model's training
- Use role-based system prompts: "You are a code formatter. Output only code."

### 2d. Batch Related Requests
- Group related small questions into a single prompt
- Use numbered lists for multi-part questions
- Request structured output (JSON) to avoid verbose natural language responses

---

## Step 3: Route and Track

1. Use the `token_saviour` Python package for programmatic routing:
   ```python
   from token_saviour import TaskClassifier, ModelRouter
   
   classifier = TaskClassifier()
   router = ModelRouter()
   
   tier = classifier.classify(prompt)
   response = router.route(prompt)
   ```

2. Track usage with:
   ```python
   from token_saviour import UsageTracker
   tracker = UsageTracker()
   tracker.log(prompt, tier, model, response)
   tracker.print_report()
   ```

---

## Step 4: Fallback Strategy

If a cheaper model produces an inadequate response:
1. Log the failure with the tracker
2. Automatically retry with the next tier up
3. Never retry more than once (SIMPLE → MODERATE → COMPLEX, max 2 attempts)

---

## Decision Flowchart

```
Is the task a simple transformation, lookup, or boilerplate?
  YES → Haiku 3.5
  NO  ↓
Does the task require multi-step reasoning or code analysis?
  NO  → Sonnet 4
  YES ↓
Does the task require architectural thinking, creativity, or deep analysis?
  YES → Opus 4
  NO  → Sonnet 4
```

---

## References

For detailed model information, see [Model Guide](./references/model_guide.md).
For prompt optimization techniques, see [Prompt Optimization](./references/prompt_optimization.md).
