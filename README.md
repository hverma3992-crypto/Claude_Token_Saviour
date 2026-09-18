# Claude Token Saviour 🧠💰

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/claude-haiku%20%7C%20sonnet%20%7C%20opus-purple.svg" alt="Claude Models">
</p>

<p align="center">
  <strong>Automatically route Claude API requests to the cheapest suitable model — save up to 18× on token costs.</strong>
</p>

<p align="center">
  Works with <b>Claude Code</b> · <b>Claude Desktop</b> · <b>Antigravity IDE</b>
</p>

---

## 🎯 What It Does

Claude Token Saviour analyzes your prompts in real-time, classifies their complexity, and automatically routes them to the most cost-effective Claude model:

| Task Type | Example | Model Selected | Cost vs Opus |
|-----------|---------|---------------|--------------|
| **Simple** | "Fix this typo", "Format as JSON" | Haiku 3.5 | **~18× cheaper** |
| **Moderate** | "Write unit tests", "Explain this code" | Sonnet 4 | **~5× cheaper** |
| **Complex** | "Design microservices architecture" | Opus 4 | Baseline |

### How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌──────────────┐
│  Your Prompt │────▶│ Task Classifier  │────▶│  Model Router  │────▶│ Claude API   │
│              │     │ (complexity      │     │ (picks cheapest│     │ (Haiku/      │
│              │     │  scoring)        │     │  capable model)│     │  Sonnet/Opus)│
└──────────────┘     └──────────────────┘     └────────────────┘     └──────┬───────┘
                                                                            │
                     ┌──────────────────┐                                   │
                     │  Usage Tracker   │◀──────────────────────────────────┘
                     │ (savings report) │
                     └──────────────────┘
```

---

## 🔌 Platform Support

### Claude Code (CLI)

Claude Code automatically reads the `CLAUDE.md` file from your project root. Token Saviour's rules are loaded on every interaction.

**Project-level** (this repo only):
```bash
cd Claude_Token_Saviour
claude  # Rules auto-loaded from CLAUDE.md
```

**Global** (all projects):
```bash
# Linux/macOS
cp claude_code/CLAUDE.md.global ~/.claude/CLAUDE.md

# Windows
Copy-Item "claude_code\CLAUDE.md.global" "$env:USERPROFILE\.claude\CLAUDE.md"
```

📖 Full guide: [`claude_code/SETUP_GUIDE.md`](claude_code/SETUP_GUIDE.md)

---

### Claude Desktop (GUI)

Integrates via the **Model Context Protocol (MCP)** as a tool server.

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "token-saviour": {
      "command": "python",
      "args": ["-m", "token_saviour.mcp_server"]
    }
  }
}
```

This gives Claude Desktop access to tools like `classify_prompt`, `optimize_prompt`, `get_usage_report`, and more.

📖 Full guide: [`claude_desktop/SETUP_GUIDE.md`](claude_desktop/SETUP_GUIDE.md)

---

### Antigravity IDE

Loads as a skill from `.agents/skills/claude-token-saviour/`:

- Automatically picked up when Antigravity opens this workspace
- Teaches the agent task classification, model routing, and prompt optimization
- Includes detailed reference docs in `references/`

To use globally, copy the skill folder to `~/.gemini/config/skills/`.

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hverma3992-crypto/Claude_Token_Saviour.git
cd Claude_Token_Saviour

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Set your API key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Usage

#### Python API

```python
from token_saviour import TaskClassifier, ModelRouter, UsageTracker

classifier = TaskClassifier()
router = ModelRouter()
tracker = UsageTracker()

# Classify and route automatically
prompt = "Fix the typo in this variable name: prnt_hello"
tier = classifier.classify(prompt)        # → "SIMPLE"
model = router.get_model(tier)            # → "claude-3-5-haiku-20241022"

# Send to Claude with tracking
response = router.route(prompt)
tracker.log(prompt, tier, model, response)

# See your savings
tracker.print_report()
```

#### CLI

```bash
# Classify a prompt
python -m token_saviour classify "Fix this typo in my README"
# Output: SIMPLE → claude-3-5-haiku (saves ~94% vs Opus)

# Route a prompt to the optimal model
python -m token_saviour route "Explain how async/await works in Python"

# View savings report
python -m token_saviour report

# Show current config
python -m token_saviour config

# Optimize a prompt
python -m token_saviour optimize "your verbose prompt here"
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize model routing:

```yaml
models:
  simple: claude-3-5-haiku-20241022
  moderate: claude-sonnet-4-20250514
  complex: claude-opus-4-20250514

routing:
  default_tier: moderate
  auto_fallback: true    # Retry with stronger model on failure
  max_retries: 1

budget:
  daily_limit_usd: 10.00
  alert_threshold_pct: 80
```

---

## 📊 Savings Calculator

| Monthly Requests | All-Opus Cost | With Token Saviour | Savings |
|-----------------|---------------|-------------------|---------|
| 1,000 | ~$90 | ~$15 | **$75 (83%)** |
| 10,000 | ~$900 | ~$150 | **$750 (83%)** |
| 100,000 | ~$9,000 | ~$1,500 | **$7,500 (83%)** |

*Assumes typical distribution: 60% simple, 30% moderate, 10% complex tasks.*

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=token_saviour
```

---

## 📁 Project Structure

```
Claude_Token_Saviour/
├── CLAUDE.md                              # 🔵 Claude Code — auto-loaded instructions
├── .claude/commands/                      # 🔵 Claude Code — slash commands
│   └── token-saviour.md
├── claude_code/                           # 🔵 Claude Code — setup guide & global config
│   ├── SETUP_GUIDE.md
│   └── CLAUDE.md.global
├── claude_desktop/                        # 🟣 Claude Desktop — MCP integration
│   ├── SETUP_GUIDE.md
│   └── claude_desktop_config.example.json
├── .agents/skills/claude-token-saviour/   # 🟢 Antigravity IDE — skill
│   ├── SKILL.md
│   └── references/
│       ├── model_guide.md
│       └── prompt_optimization.md
├── token_saviour/                         # Python package
│   ├── __init__.py
│   ├── classifier.py                      # Task complexity classifier
│   ├── router.py                          # Model routing engine
│   ├── tracker.py                         # Usage & savings tracker
│   ├── optimizer.py                       # Prompt optimization
│   ├── config.py                          # Configuration loader
│   ├── cli.py                             # CLI interface
│   └── mcp_server.py                      # MCP server for Claude Desktop
├── examples/                              # Usage examples
├── tests/                                 # Test suite (62 tests)
├── config.yaml                            # Default configuration
├── setup.py                               # Package metadata
└── requirements.txt                       # Dependencies
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ to save your Claude tokens
</p>
