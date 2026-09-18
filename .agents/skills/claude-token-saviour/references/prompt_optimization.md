# Prompt Optimization Techniques

Strategies to reduce token consumption without sacrificing output quality.

---

## 1. Prompt Compression

### Remove Redundant Whitespace
```python
# Before (wastes tokens on whitespace):
code = """
def    hello_world():

    print(   "Hello, World!"   )

"""

# After (compact):
code = 'def hello_world():\n    print("Hello, World!")'
```

### Strip Irrelevant Code Context
Only include the function or class being discussed, not the entire file.

```python
# BAD: Including 500 lines when only 10 are relevant
# "Here's my entire app.py file: [500 lines]... Fix the bug on line 342"

# GOOD: Include only the relevant section
# "Fix the bug in this function:
# [10 relevant lines]
# Error: TypeError on line 5"
```

### Use Concise Instructions
```
# BAD (verbose):
"I would like you to please take a look at the following code and if you
could kindly identify any potential issues or bugs that might exist within
it, that would be very helpful."

# GOOD (concise):
"Find bugs in this code:"
```

---

## 2. Output Token Limiting

### Set Appropriate `max_tokens`

| Task Type | Recommended `max_tokens` |
|-----------|-------------------------|
| Yes/No answer | 10 |
| Classification | 50 |
| Short answer | 100-200 |
| Code snippet | 300-800 |
| Function implementation | 500-1500 |
| Full explanation | 500-1000 |
| Architecture document | 2000-4000 |

### Use Stop Sequences
```python
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=500,
    stop_sequences=["```\n", "---", "END"],
    messages=[{"role": "user", "content": prompt}]
)
```

### Request Structured Output
```
# BAD: "Explain the pros and cons of using Redis vs Memcached"
# → Long, verbose paragraph response

# GOOD: "Compare Redis vs Memcached. Output as JSON:
# {\"redis\": {\"pros\": [...], \"cons\": [...]}, \"memcached\": {\"pros\": [...], \"cons\": [...]}}"
# → Compact, structured response
```

---

## 3. Caching Strategies

### Prompt Caching (Anthropic Feature)
Use the `cache_control` parameter for frequently reused system prompts:
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=[
        {
            "type": "text",
            "text": large_system_prompt,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": prompt}]
)
```
Cached prompt tokens cost 90% less on subsequent calls.

### Response Caching (Application Level)
Cache responses for identical or near-identical prompts:
```python
import hashlib

def get_cache_key(prompt, model):
    return hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()
```

---

## 4. Batching Techniques

### Group Related Questions
```
# BAD: 3 separate API calls
# Call 1: "What type is the variable `x`?"
# Call 2: "Is `x` used after line 10?"
# Call 3: "Can `x` be renamed to `count`?"

# GOOD: 1 API call
# "Answer these about variable `x`:
# 1. What is its type?
# 2. Is it used after line 10?
# 3. Can it be safely renamed to `count`?
# Answer as numbered list, one line each."
```

### Batch Processing with Message Batches API
```python
# Use Anthropic's batch API for non-time-sensitive tasks
batch = client.messages.batches.create(
    requests=[
        {"custom_id": f"task-{i}", "params": {...}}
        for i in range(100)
    ]
)
# Batch API is 50% cheaper than standard API
```

---

## 5. System Prompt Optimization

### Role-Based Prompts (Shorter = Cheaper)
```python
# BAD (79 tokens):
system = """You are a helpful AI assistant that specializes in reviewing
Python code. When reviewing code, you should look for bugs, performance
issues, security vulnerabilities, and style problems. Please provide
your feedback in a clear and organized manner."""

# GOOD (15 tokens):
system = "Expert Python code reviewer. Output: bugs, performance, security, style issues."
```

### Reuse System Prompts with Caching
Define a few standard system prompts and reuse them:
- `CODE_REVIEWER`: For all code review tasks
- `FORMATTER`: For formatting/transformation tasks
- `ARCHITECT`: For design and architecture tasks

---

## 6. Token Estimation

Quick estimation rules:
- **English text**: ~1 token per 4 characters, or ~0.75 tokens per word
- **Code**: ~1 token per 3 characters (more special characters)
- **JSON/structured data**: ~1 token per 3-4 characters

### Fast Estimation Function
```python
def estimate_tokens(text: str, is_code: bool = False) -> int:
    chars_per_token = 3 if is_code else 4
    return max(1, len(text) // chars_per_token)
```

---

## Summary: Token Saving Checklist

- [ ] Strip unnecessary whitespace and comments from code context
- [ ] Include only relevant code sections, not entire files
- [ ] Use concise, direct instructions
- [ ] Set appropriate `max_tokens` for the task
- [ ] Use `stop_sequences` to prevent rambling
- [ ] Request structured output (JSON/lists) over prose
- [ ] Enable prompt caching for repeated system prompts
- [ ] Cache responses for identical prompts
- [ ] Batch related questions into single calls
- [ ] Use the cheapest model that can handle the task
- [ ] Use the Batch API for non-time-sensitive bulk operations
