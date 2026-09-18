"""
Task Classifier — Analyzes prompt complexity to determine the optimal Claude model tier.

Uses keyword matching, structural analysis, and token estimation to classify
prompts into SIMPLE, MODERATE, or COMPLEX tiers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ComplexityTier(str, Enum):
    """Complexity tiers that map to Claude model selections."""
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"


@dataclass
class ClassificationResult:
    """Result of classifying a prompt's complexity."""
    tier: ComplexityTier
    score: float
    model: str
    reasoning: str
    token_estimate: int
    estimated_savings_pct: float

    def __repr__(self) -> str:
        return (
            f"ClassificationResult(tier={self.tier.value}, score={self.score:.2f}, "
            f"model='{self.model}', savings={self.estimated_savings_pct:.0f}%)"
        )


@dataclass
class TaskClassifier:
    """
    Classifies prompt complexity to determine the cheapest suitable Claude model.

    Uses a weighted scoring system based on:
    - Keyword pattern matching (task type indicators)
    - Prompt length / token estimation
    - Structural complexity (multi-step detection)
    - Code analysis indicators
    """

    # Scoring thresholds
    simple_threshold: float = 0.3
    complex_threshold: float = 0.7

    # Keyword patterns with associated complexity weights
    simple_patterns: list[tuple[str, float]] = field(default_factory=lambda: [
        (r"\b(fix|correct)\s+(the\s+)?(typo|spelling|grammar|indent)", -0.3),
        (r"\bfix\s+.{0,20}\s+typo", -0.3),
        (r"\bformat\s+(as|to|into)\b", -0.3),
        (r"\b(convert|transform)\s+.{0,20}\s+(to|into)\b", -0.25),
        (r"\brename\b", -0.3),
        (r"\b(generate|create)\s+(getter|setter|constructor|boilerplate)\b", -0.3),
        (r"\bsort\s+(import|line|list)s?\b", -0.3),
        (r"\b(what\s+is|define|meaning\s+of)\b", -0.25),
        (r"\b(yes\s+or\s+no|true\s+or\s+false)\b", -0.35),
        (r"\b(parse|extract)\s+.{0,20}\s+(from|in)\b", -0.2),
        (r"\b(regex|regular\s+expression)\s+for\b", -0.2),
        (r"\badd\s+(import|comment|docstring|type\s+hint)\b", -0.25),
        (r"\blist\s+(all|the)\b", -0.2),
        (r"\btranslate\b", -0.2),
        (r"\b(mock|stub|dummy|fake)\s+(data|value|object)\b", -0.3),
    ])

    moderate_patterns: list[tuple[str, float]] = field(default_factory=lambda: [
        (r"\b(write|create|implement)\s+(unit\s+)?test", 0.1),
        (r"\b(review|check)\s+(this\s+)?(code|function|class)\b", 0.1),
        (r"\bexplain\s+(how|why|what)\b", 0.05),
        (r"\brefactor\b", 0.15),
        (r"\bdebug\b", 0.1),
        (r"\bdocument(ation)?\b", 0.05),
        (r"\bimplement\s+(a\s+)?function\b", 0.1),
        (r"\b(api|endpoint|route)\b", 0.1),
        (r"\b(query|sql|database)\b", 0.1),
        (r"\boptimize\s+(this|the)\s+(function|query|code)\b", 0.15),
        (r"\berror\s+handling\b", 0.1),
        (r"\bvalidat(e|ion)\b", 0.1),
    ])

    complex_patterns: list[tuple[str, float]] = field(default_factory=lambda: [
        (r"\b(architect|architecture|system\s+design)\b", 0.4),
        (r"\b(design\s+pattern|trade-?off)\b", 0.35),
        (r"\b(security|vulnerabilit|exploit|attack\s+vector)\b", 0.35),
        (r"\b(performance|profil|benchmark)\s+(analys|optimiz|strateg)\b", 0.35),
        (r"\b(microservice|distributed|event.?sourc|cqrs)\b", 0.4),
        (r"\b(algorithm|complexity|big-?o)\s+(design|analy)\b", 0.35),
        (r"\bmulti.?file\s+(refactor|chang|updat)\b", 0.3),
        (r"\b(proof|theorem|mathematical)\b", 0.35),
        (r"\b(scalab|high.?availab|fault.?toleran)\b", 0.35),
        (r"\b(migration\s+strateg|backward\s+compat)\b", 0.3),
        (r"\b(compare|evaluate)\s+.{0,30}\s+(approach|option|strateg)\b", 0.25),
        (r"\b(novel|creative|innovative)\s+(solution|approach)\b", 0.3),
    ])

    def classify(self, prompt: str, context: Optional[str] = None) -> ClassificationResult:
        """
        Classify a prompt's complexity and return the optimal model tier.

        Args:
            prompt: The user's prompt text.
            context: Optional additional context (e.g., code being referenced).

        Returns:
            ClassificationResult with tier, score, model, and reasoning.
        """
        full_text = f"{prompt} {context}" if context else prompt
        full_text_lower = full_text.lower()

        score = 0.5  # Start at midpoint
        reasons = []

        # 1. Keyword pattern scoring
        for pattern, weight in self.simple_patterns:
            if re.search(pattern, full_text_lower):
                score += weight
                reasons.append(f"Simple pattern match: {pattern}")

        for pattern, weight in self.moderate_patterns:
            if re.search(pattern, full_text_lower):
                score += weight
                reasons.append(f"Moderate pattern match: {pattern}")

        for pattern, weight in self.complex_patterns:
            if re.search(pattern, full_text_lower):
                score += weight
                reasons.append(f"Complex pattern match: {pattern}")

        # 2. Length-based scoring (longer prompts tend to be more complex)
        token_estimate = self._estimate_tokens(full_text)
        if token_estimate > 2000:
            score += 0.15
            reasons.append(f"Long prompt ({token_estimate} tokens)")
        elif token_estimate > 500:
            score += 0.05
            reasons.append(f"Medium prompt ({token_estimate} tokens)")
        elif token_estimate < 50:
            score -= 0.1
            reasons.append(f"Short prompt ({token_estimate} tokens)")

        # 3. Structural complexity indicators
        question_count = len(re.findall(r"\?", full_text))
        if question_count > 3:
            score += 0.1
            reasons.append(f"Multiple questions ({question_count})")

        step_indicators = len(re.findall(
            r"\b(step\s+\d|first|then|next|finally|after\s+that)\b",
            full_text_lower
        ))
        if step_indicators > 2:
            score += 0.1
            reasons.append(f"Multi-step task ({step_indicators} step indicators)")

        # 4. Code complexity indicators
        code_blocks = len(re.findall(r"```", full_text))
        if code_blocks > 4:
            score += 0.1
            reasons.append(f"Multiple code blocks ({code_blocks // 2})")

        file_references = len(re.findall(r"\b\w+\.(py|js|ts|java|go|rs|cpp|c)\b", full_text_lower))
        if file_references > 3:
            score += 0.1
            reasons.append(f"Multiple file references ({file_references})")

        # Clamp score to [0, 1]
        score = max(0.0, min(1.0, score))

        # Determine tier
        if score <= self.simple_threshold:
            tier = ComplexityTier.SIMPLE
            model = "claude-3-5-haiku-20241022"
            savings_pct = 94.7
        elif score >= self.complex_threshold:
            tier = ComplexityTier.COMPLEX
            model = "claude-opus-4-20250514"
            savings_pct = 0.0
        else:
            tier = ComplexityTier.MODERATE
            model = "claude-sonnet-4-20250514"
            savings_pct = 80.0

        reasoning = "; ".join(reasons[:5]) if reasons else "Default classification (no strong signals)"

        return ClassificationResult(
            tier=tier,
            score=score,
            model=model,
            reasoning=reasoning,
            token_estimate=token_estimate,
            estimated_savings_pct=savings_pct,
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Fast token count estimation.
        English text: ~4 chars per token. Code: ~3 chars per token.
        """
        has_code = bool(re.search(r"```|def |function |class |import |const |let |var ", text))
        chars_per_token = 3 if has_code else 4
        return max(1, len(text) // chars_per_token)
