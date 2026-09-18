# Claude Token Saviour — Project Instructions

> **This file is automatically read by Claude Code when working in this project.**
> It teaches Claude to minimize token consumption by routing tasks to the cheapest suitable model.

---

## Core Rule

**Never use a more expensive model when a cheaper one will produce equivalent results.**

| Complexity | Model | Input $/1M | Output $/1M | Use When |
|------------|-------|-----------|-------------|----------|
| SIMPLE | Haiku 3.5 | $0.80 | $4.00 | Typo fixes, formatting, boilerplate, lookups |
| MODERATE | Sonnet 4 | $3.00 | $15.00 | Tests, reviews, refactoring, debugging |
| COMPLEX | Opus 4 | $15.00 | $75.00 | Architecture, security analysis, novel solutions |

---

## Task Classification Guide

### SIMPLE → Haiku 3.5 (saves ~94% vs Opus)
- Fix typos, spelling, grammar, indentation
- Format/convert between data formats (JSON ↔ YAML ↔ CSV)
- Generate boilerplate (getters, setters, constructors, CRUD)
- Rename variables, sort imports, add type hints
- Simple lookups, definitions, factual Q&A
- Generate mock/test data
- Regex pattern generation
- Add comments or docstrings

### MODERATE → Sonnet 4 (saves ~80% vs Opus)
- Write unit tests with real logic
- Code review and bug identification
- Explain complex code or concepts
- Refactor functions or classes
- Write documentation with examples
- Implement API endpoints
- Database query optimization
- Multi-step debugging
- Standard feature implementation
- Error handling and validation logic

### COMPLEX → Opus 4 (use only when needed)
- System architecture design
- Complex algorithm design or optimization
- Multi-file refactoring with dependency analysis
- Security vulnerability analysis
- Performance profiling and optimization strategy
- Design pattern recommendations with trade-off analysis
- Complex debugging requiring deep reasoning
- Multi-step mathematical proofs
- Novel problem-solving requiring creativity
- Migration strategies and backward compatibility

---

## Token-Saving Best Practices

### 1. Compress Prompts
- Remove unnecessary whitespace and blank lines from code context
- Only include the relevant code snippet, not entire files
- Strip boilerplate imports if not relevant to the question

### 2. Limit Output Tokens
- Simple lookups: max 100-300 tokens
- Code generation: max 500-1500 tokens
- Explanations: max 300-800 tokens
- Architecture docs: max 1500-4000 tokens

### 3. Batch Related Requests
- Group related small questions into a single prompt
- Use numbered lists for multi-part questions
- Request structured output (JSON) over verbose prose

### 4. Use Concise System Prompts
- "Expert code reviewer. Report: bugs, performance, security, style."
- "Code formatter. Output only formatted code, no explanations."
- "Test engineer. Write thorough, focused tests. Cover edge cases."

---

## Python Toolkit

This project includes a Python package for programmatic model routing:

```bash
# Classify a prompt
python -m token_saviour classify "Fix this typo in my README"

# Route to optimal model
python -m token_saviour route "Explain how async/await works"

# View savings report
python -m token_saviour report
```

```python
from token_saviour import TaskClassifier, ModelRouter, UsageTracker

classifier = TaskClassifier()
router = ModelRouter()

tier = classifier.classify(prompt)    # → SIMPLE / MODERATE / COMPLEX
response = router.route(prompt)       # → auto-routes to cheapest model
```

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
