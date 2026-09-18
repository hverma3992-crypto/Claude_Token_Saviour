"""
MCP Server — Model Context Protocol server for Claude Desktop integration.

Exposes Token Saviour tools (classify, optimize, report) as MCP tools
that Claude Desktop can invoke directly.

Usage:
    python -m token_saviour.mcp_server

Configure in Claude Desktop's claude_desktop_config.json:
    {
        "mcpServers": {
            "token-saviour": {
                "command": "python",
                "args": ["-m", "token_saviour.mcp_server"]
            }
        }
    }
"""

from __future__ import annotations

import json
import sys
from typing import Any

from token_saviour.classifier import TaskClassifier
from token_saviour.optimizer import PromptOptimizer
from token_saviour.tracker import UsageTracker
from token_saviour.router import ModelRouter
from token_saviour.config import Config


def handle_request(request: dict) -> dict:
    """Handle a single MCP JSON-RPC request."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "token-saviour",
                    "version": "1.0.0",
                },
            },
        }

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "classify_prompt",
                        "description": "Classify a prompt's complexity and recommend the cheapest suitable Claude model (Haiku/Sonnet/Opus).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The prompt text to classify",
                                },
                            },
                            "required": ["prompt"],
                        },
                    },
                    {
                        "name": "get_optimal_model",
                        "description": "Get the optimal Claude model for a given task description.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "task_description": {
                                    "type": "string",
                                    "description": "Description of the task",
                                },
                            },
                            "required": ["task_description"],
                        },
                    },
                    {
                        "name": "optimize_prompt",
                        "description": "Compress and optimize a prompt to reduce token consumption.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The prompt to optimize",
                                },
                            },
                            "required": ["prompt"],
                        },
                    },
                    {
                        "name": "estimate_tokens",
                        "description": "Estimate the token count for a given text.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "The text to estimate tokens for",
                                },
                            },
                            "required": ["text"],
                        },
                    },
                    {
                        "name": "get_usage_report",
                        "description": "Get a token usage and savings report.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "period": {
                                    "type": "string",
                                    "description": "Report period: 'all', 'today', 'week', or 'month'",
                                    "default": "all",
                                },
                            },
                        },
                    },
                    {
                        "name": "suggest_max_tokens",
                        "description": "Suggest an appropriate max_tokens value for a given task.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "task_description": {
                                    "type": "string",
                                    "description": "Description of the task",
                                },
                            },
                            "required": ["task_description"],
                        },
                    },
                ],
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result_text = _call_tool(tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": result_text}],
            },
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }


def _call_tool(name: str, arguments: dict) -> str:
    """Dispatch a tool call and return the result as a string."""
    classifier = TaskClassifier()
    config = Config()

    if name == "classify_prompt":
        prompt = arguments.get("prompt", "")
        result = classifier.classify(prompt)
        return (
            f"Complexity Tier: {result.tier.value}\n"
            f"Recommended Model: {result.model}\n"
            f"Confidence Score: {result.score:.2f}\n"
            f"Estimated Tokens: {result.token_estimate:,}\n"
            f"Savings vs Opus: {result.estimated_savings_pct:.0f}%\n"
            f"Reasoning: {result.reasoning}"
        )

    elif name == "get_optimal_model":
        task = arguments.get("task_description", "")
        result = classifier.classify(task)
        router = ModelRouter(config=config)
        cost_in, cost_out = router.get_model_cost(result.model)
        return (
            f"Optimal Model: {result.model}\n"
            f"Tier: {result.tier.value}\n"
            f"Cost: ${cost_in:.2f}/1M input, ${cost_out:.2f}/1M output\n"
            f"Savings vs Opus: {result.estimated_savings_pct:.0f}%"
        )

    elif name == "optimize_prompt":
        prompt = arguments.get("prompt", "")
        result = PromptOptimizer.compress_prompt(prompt)
        return (
            f"Original Tokens: {result.original_tokens}\n"
            f"Optimized Tokens: {result.optimized_tokens}\n"
            f"Tokens Saved: {result.tokens_saved} ({result.savings_percentage}%)\n"
            f"Techniques: {', '.join(result.techniques_applied) or 'none needed'}\n"
            f"\n--- Optimized Prompt ---\n{result.optimized_text}"
        )

    elif name == "estimate_tokens":
        text = arguments.get("text", "")
        tokens = PromptOptimizer.estimate_tokens(text)
        return f"Estimated Tokens: {tokens:,}\nCharacters: {len(text):,}"

    elif name == "get_usage_report":
        period = arguments.get("period", "all")
        tracker = UsageTracker(data_file=config.tracking.get("data_file", "usage_data.json"))
        report = tracker.get_report(period)
        return (
            f"Period: {report.period}\n"
            f"Total Requests: {report.total_requests}\n"
            f"Total Tokens: {report.total_input_tokens + report.total_output_tokens:,}\n"
            f"Actual Cost: ${report.total_cost_usd:.4f}\n"
            f"All-Opus Cost: ${report.total_opus_cost_usd:.4f}\n"
            f"Savings: ${report.total_savings_usd:.4f} ({report.savings_percentage:.1f}%)\n"
            f"Tier Breakdown: {json.dumps(report.tier_breakdown)}\n"
            f"Model Breakdown: {json.dumps(report.model_breakdown)}"
        )

    elif name == "suggest_max_tokens":
        task = arguments.get("task_description", "")
        suggested = PromptOptimizer.suggest_max_tokens(task)
        return f"Suggested max_tokens: {suggested}"

    else:
        return f"Unknown tool: {name}"


def main():
    """Run the MCP server using stdio transport."""
    # Read JSON-RPC messages from stdin, write responses to stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = handle_request(request)

        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
