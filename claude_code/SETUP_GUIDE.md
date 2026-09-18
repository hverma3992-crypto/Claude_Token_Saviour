# Claude Code Integration Guide

## Overview

**Claude Code** is Anthropic's agentic coding tool that runs in your terminal. It automatically reads `CLAUDE.md` files from your project for context and instructions.

Token Saviour integrates natively — just having this repo cloned is enough for Claude Code to learn the token-saving rules.

---

## How It Works

Claude Code reads `CLAUDE.md` from your project root on every interaction. This project's `CLAUDE.md` contains:
- Task classification rules (SIMPLE / MODERATE / COMPLEX)
- Model routing matrix (Haiku / Sonnet / Opus)
- Token-saving best practices
- Decision flowchart for model selection

---

## Setup Options

### Option 1: Project-Level (This Repo Only)

The `CLAUDE.md` at the root of this repo is automatically loaded when you open Claude Code in this directory. No setup needed.

```bash
cd Claude_Token_Saviour
claude  # Token Saviour rules are automatically active
```

### Option 2: Global (All Projects)

Copy the global config to make the rules active across ALL your Claude Code projects:

**Linux/macOS:**
```bash
mkdir -p ~/.claude
cp claude_code/CLAUDE.md.global ~/.claude/CLAUDE.md
```

**Windows:**
```powershell
mkdir -Force "$env:USERPROFILE\.claude"
Copy-Item "claude_code\CLAUDE.md.global" "$env:USERPROFILE\.claude\CLAUDE.md"
```

### Option 3: Slash Command

Copy the command file to add a `/token-saviour` slash command:

```bash
# In your target project:
mkdir -p .claude/commands
cp path/to/Claude_Token_Saviour/.claude/commands/token-saviour.md .claude/commands/
```

Then in Claude Code, type `/token-saviour` to activate the skill.

---

## Using the Python CLI with Claude Code

You can also use the CLI tools directly within Claude Code:

```bash
# Ask Claude Code to classify a task
python -m token_saviour classify "write unit tests for auth module"

# Optimize a prompt before sending
python -m token_saviour optimize "I would like you to please review this code..."

# Check your savings
python -m token_saviour report
```

---

## Verification

To verify the rules are loaded, start Claude Code and ask:

```
What model routing rules are you following for token optimization?
```

Claude should describe the SIMPLE/MODERATE/COMPLEX classification system.
