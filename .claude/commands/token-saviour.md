# Claude Token Saviour — Claude Code Commands

> **Place this file in your project root as `.claude/commands/token-saviour.md`**
> to add a `/token-saviour` slash command in Claude Code.

## Usage

When working on any project with Claude Code, use these guidelines to minimize token costs:

### Quick Classification

Before processing any task, mentally classify it:

1. **SIMPLE** (use Haiku): Typo fixes, formatting, boilerplate, simple lookups, data conversion
2. **MODERATE** (use Sonnet): Unit tests, code review, refactoring, debugging, feature implementation
3. **COMPLEX** (use Opus): Architecture design, security analysis, complex algorithms, multi-file refactoring

### Slash Command Usage

```
/token-saviour classify "your prompt here"
/token-saviour route "your prompt here"
/token-saviour report
```

### Model Selection Shortcuts

When using Claude Code, you can explicitly request a model:

- For simple tasks: "Using Haiku, fix this typo..."
- For moderate tasks: "Using Sonnet, write tests for..."
- For complex tasks: "Using Opus, design the architecture for..."

### Integration with Claude Code

Claude Code reads `CLAUDE.md` from the project root automatically. The token-saving rules in this project's `CLAUDE.md` are applied to every interaction within the project.

To apply these rules globally across all projects, copy `CLAUDE.md` to:
- **Linux/macOS**: `~/.claude/CLAUDE.md`
- **Windows**: `%USERPROFILE%\.claude\CLAUDE.md`
