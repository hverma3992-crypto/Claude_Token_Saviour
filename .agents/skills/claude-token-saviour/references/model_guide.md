# Claude Model Guide

Detailed reference on each Claude model's capabilities, pricing, and optimal use cases.

---

## Claude 3.5 Haiku

**API Name:** `claude-3-5-haiku-20241022`

### Pricing
| | Per 1M Tokens |
|---|---|
| Input | $0.80 |
| Output | $4.00 |

### Strengths
- Extremely fast response times (~0.5s for simple tasks)
- Very cost-effective for high-volume, simple operations
- Excellent at following strict formatting instructions
- Good at pattern matching and text transformation

### Ideal Use Cases
- Text formatting and transformation
- Simple code generation (boilerplate, getters/setters)
- Data extraction and parsing
- Classification and tagging
- Simple Q&A and lookups
- Template filling
- Regex pattern generation
- Input validation logic

### Limitations
- May struggle with multi-step reasoning
- Less reliable for nuanced code review
- Can produce shallow explanations
- May miss edge cases in complex logic

---

## Claude Sonnet 4

**API Name:** `claude-sonnet-4-20250514`

### Pricing
| | Per 1M Tokens |
|---|---|
| Input | $3.00 |
| Output | $15.00 |

### Strengths
- Excellent balance of quality and cost
- Strong code generation and review capabilities
- Good at multi-step reasoning
- Reliable documentation generation
- Solid debugging abilities

### Ideal Use Cases
- Writing and reviewing unit tests
- Implementing standard features
- Code refactoring
- Writing technical documentation
- Debugging with error messages
- API endpoint implementation
- Database query writing and optimization
- Code explanation and walkthroughs

### Limitations
- May not catch subtle architectural issues
- Less creative in novel problem-solving
- Can miss deep optimization opportunities

---

## Claude Opus 4

**API Name:** `claude-opus-4-20250514`

### Pricing
| | Per 1M Tokens |
|---|---|
| Input | $15.00 |
| Output | $75.00 |

### Strengths
- Superior reasoning and analysis
- Excellent at complex, multi-step problems
- Strong architectural thinking
- Creative and novel problem-solving
- Deep understanding of trade-offs
- Best at handling ambiguous requirements

### Ideal Use Cases
- System architecture design
- Complex algorithm design
- Security vulnerability analysis
- Performance optimization strategies
- Multi-file refactoring with dependency analysis
- Design pattern selection with trade-off analysis
- Complex mathematical reasoning
- Novel research and exploration tasks

### When to Use
- Only when the task genuinely requires deep, multi-step reasoning
- When accuracy on the first attempt is critical and costly to redo
- When the task involves synthesizing information from many sources
- When creative or novel approaches are needed

---

## Cost Comparison Matrix

Assuming average response of 500 tokens:

| Requests/Day | Haiku Cost | Sonnet Cost | Opus Cost | Savings (Haiku vs Opus) |
|--------------|-----------|-------------|-----------|------------------------|
| 100 | $0.24 | $0.90 | $4.50 | 94.7% |
| 500 | $1.20 | $4.50 | $22.50 | 94.7% |
| 1,000 | $2.40 | $9.00 | $45.00 | 94.7% |
| 5,000 | $12.00 | $45.00 | $225.00 | 94.7% |

---

## Model Selection Decision Matrix

| Factor | Haiku | Sonnet | Opus |
|--------|-------|--------|------|
| Speed Priority | ✅ Best | ✅ Good | ⚠️ Slower |
| Cost Priority | ✅ Cheapest | ✅ Moderate | ❌ Expensive |
| Reasoning Depth | ⚠️ Basic | ✅ Good | ✅ Best |
| Code Quality | ⚠️ Simple | ✅ Good | ✅ Best |
| Creativity | ❌ Limited | ✅ Good | ✅ Best |
| Accuracy | ⚠️ Variable | ✅ Reliable | ✅ Most Reliable |
