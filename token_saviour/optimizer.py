"""
Prompt Optimizer — Techniques to reduce token count without losing semantic meaning.

Provides utilities for prompt compression, context truncation, token estimation,
and max_tokens suggestion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class OptimizationResult:
    """Result of optimizing a prompt."""
    original_text: str
    optimized_text: str
    original_tokens: int
    optimized_tokens: int
    tokens_saved: int
    savings_percentage: float
    techniques_applied: list[str]


class PromptOptimizer:
    """
    Collection of static methods for reducing prompt token consumption.
    """

    @staticmethod
    def compress_prompt(text: str) -> OptimizationResult:
        """
        Compress a prompt by removing redundant whitespace, blank lines, and
        unnecessary formatting while preserving semantic meaning.

        Args:
            text: The original prompt text.

        Returns:
            OptimizationResult with the compressed text and savings stats.
        """
        original = text
        techniques = []

        # 1. Remove trailing whitespace on each line
        text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
        if text != original:
            techniques.append("trailing_whitespace")

        # 2. Collapse multiple blank lines to a single blank line
        prev = text
        text = re.sub(r"\n{3,}", "\n\n", text)
        if text != prev:
            techniques.append("collapsed_blank_lines")

        # 3. Remove leading/trailing whitespace from the entire prompt
        prev = text
        text = text.strip()
        if text != prev:
            techniques.append("trimmed_edges")

        # 4. Collapse multiple spaces (but not in code blocks)
        prev = text
        parts = re.split(r"(```[\s\S]*?```)", text)
        compressed_parts = []
        for i, part in enumerate(parts):
            if part.startswith("```"):
                compressed_parts.append(part)
            else:
                compressed_parts.append(re.sub(r"  +", " ", part))
        text = "".join(compressed_parts)
        if text != prev:
            techniques.append("collapsed_spaces")

        original_tokens = PromptOptimizer.estimate_tokens(original)
        optimized_tokens = PromptOptimizer.estimate_tokens(text)
        tokens_saved = original_tokens - optimized_tokens
        savings_pct = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0.0

        return OptimizationResult(
            original_text=original,
            optimized_text=text,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=tokens_saved,
            savings_percentage=round(savings_pct, 1),
            techniques_applied=techniques,
        )

    @staticmethod
    def strip_code_comments(code: str, language: str = "python") -> str:
        """
        Remove comments from code to reduce token count.

        Args:
            code: Source code string.
            language: Programming language ("python", "javascript", "java", "c").

        Returns:
            Code with comments stripped.
        """
        if language in ("python", "ruby", "bash", "shell"):
            # Remove single-line comments (# ...)
            code = re.sub(r"#[^\n]*", "", code)
            # Remove docstrings
            code = re.sub(r'"""[\s\S]*?"""', '', code)
            code = re.sub(r"'''[\s\S]*?'''", '', code)
        elif language in ("javascript", "typescript", "java", "c", "cpp", "go", "rust"):
            # Remove single-line comments (// ...)
            code = re.sub(r"//[^\n]*", "", code)
            # Remove multi-line comments (/* ... */)
            code = re.sub(r"/\*[\s\S]*?\*/", "", code)
        elif language == "html":
            code = re.sub(r"<!--[\s\S]*?-->", "", code)
        elif language == "css":
            code = re.sub(r"/\*[\s\S]*?\*/", "", code)

        # Clean up resulting blank lines
        code = re.sub(r"\n{3,}", "\n\n", code)
        return code.strip()

    @staticmethod
    def truncate_context(
        text: str,
        max_tokens: int = 2000,
        strategy: str = "end",
    ) -> str:
        """
        Intelligently truncate text to fit within a token budget.

        Args:
            text: The text to truncate.
            max_tokens: Maximum token budget.
            strategy: "end" (keep start), "start" (keep end), "middle" (keep start+end).

        Returns:
            Truncated text within the token budget.
        """
        current_tokens = PromptOptimizer.estimate_tokens(text)
        if current_tokens <= max_tokens:
            return text

        # Approximate character count from tokens
        target_chars = max_tokens * 4  # ~4 chars per token

        if strategy == "end":
            truncated = text[:target_chars]
            return truncated + "\n\n... [truncated]"
        elif strategy == "start":
            truncated = text[-target_chars:]
            return "[truncated] ...\n\n" + truncated
        elif strategy == "middle":
            half = target_chars // 2
            start = text[:half]
            end = text[-half:]
            return start + "\n\n... [middle truncated] ...\n\n" + end
        else:
            raise ValueError(f"Unknown strategy: {strategy}. Use 'end', 'start', or 'middle'.")

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Fast token count estimation without requiring a tokenizer library.

        Rules:
        - English text: ~4 characters per token
        - Code: ~3 characters per token
        - Minimum: 1 token

        Args:
            text: The text to estimate.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0

        has_code = bool(re.search(
            r"```|def |function |class |import |const |let |var |public |private ",
            text
        ))
        chars_per_token = 3 if has_code else 4
        return max(1, len(text) // chars_per_token)

    @staticmethod
    def suggest_max_tokens(task_description: str) -> int:
        """
        Suggest an appropriate max_tokens value based on the task type.

        Args:
            task_description: Brief description of the task.

        Returns:
            Suggested max_tokens value.
        """
        desc_lower = task_description.lower()

        # Very short outputs
        if re.search(r"\b(yes|no|true|false|classify|categorize|label)\b", desc_lower):
            return 50

        # Short outputs
        if re.search(r"\b(fix|correct|rename|format|convert|parse|extract)\b", desc_lower):
            return 300

        # Medium outputs
        if re.search(r"\b(explain|describe|summarize|review|comment)\b", desc_lower):
            return 800

        # Code generation
        if re.search(r"\b(implement|write|create|generate|build)\s+(a\s+)?(function|class|test|api)\b", desc_lower):
            return 1500

        # Long outputs
        if re.search(r"\b(architect|design|document|analyz|compar)\b", desc_lower):
            return 3000

        # Default
        return 1024

    @staticmethod
    def create_efficient_system_prompt(role: str) -> str:
        """
        Generate a concise, token-efficient system prompt for common roles.

        Args:
            role: One of "reviewer", "formatter", "debugger", "architect", "documenter".

        Returns:
            A concise system prompt string.
        """
        prompts = {
            "reviewer": "Expert code reviewer. Report: bugs, performance, security, style. Be concise.",
            "formatter": "Code formatter. Output only formatted code, no explanations.",
            "debugger": "Expert debugger. Identify root cause, suggest fix. Be concise.",
            "architect": "Senior software architect. Focus on trade-offs, scalability, maintainability.",
            "documenter": "Technical writer. Clear, concise documentation with examples.",
            "tester": "Test engineer. Write thorough, focused tests. Cover edge cases.",
        }
        return prompts.get(role, f"Expert {role}. Be concise and precise.")
