# Claude Desktop Integration Guide

## Overview

Claude Desktop supports integration through the **Model Context Protocol (MCP)**. This guide shows you how to add Token Saviour as an MCP tool server, giving Claude Desktop the ability to classify prompts, suggest optimal models, and track your savings.

---

## Setup

### Step 1: Install Token Saviour

```bash
git clone https://github.com/hverma3992-crypto/Claude_Token_Saviour.git
cd Claude_Token_Saviour
pip install -e .
```

### Step 2: Configure Claude Desktop

Add the Token Saviour MCP server to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this to your config (or merge with existing `mcpServers`):

```json
{
  "mcpServers": {
    "token-saviour": {
      "command": "python",
      "args": ["-m", "token_saviour.mcp_server"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

After saving the config, restart Claude Desktop. You should see "token-saviour" in the MCP tools list (🔌 icon).

---

## Available Tools

Once connected, Claude Desktop will have access to these tools:

| Tool | Description |
|------|-------------|
| `classify_prompt` | Classify a prompt's complexity tier (SIMPLE/MODERATE/COMPLEX) |
| `get_optimal_model` | Get the cheapest suitable model for a task |
| `optimize_prompt` | Compress a prompt to reduce token usage |
| `estimate_tokens` | Estimate token count for a text |
| `get_usage_report` | Show token usage and savings report |
| `suggest_max_tokens` | Recommend output token limit for a task |

---

## Usage Examples

Once configured, you can ask Claude Desktop:

- *"Classify this task: write unit tests for my auth module"*
- *"What model should I use for fixing this typo?"*
- *"Show my token usage report"*
- *"Optimize this prompt before sending it"*

---

## Using Token Saviour Without MCP

Even without MCP, you can paste the classification rules directly into your Claude Desktop system prompt:

1. Open Claude Desktop Settings → **Custom Instructions**
2. Paste the content from `CLAUDE.md` into the system prompt
3. Claude will now apply the token-saving rules to every conversation

---

## Using the Project Knowledge Feature

Claude Desktop's **Project Knowledge** feature lets you upload reference files:

1. Create a new Project in Claude Desktop
2. Click **Add to Project Knowledge**
3. Upload these files:
   - `CLAUDE.md` (core classification rules)
   - `config.yaml` (model configuration)
4. Claude will reference these rules in all conversations within that project
