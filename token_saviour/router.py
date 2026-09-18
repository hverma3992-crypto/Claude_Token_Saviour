"""
Model Router — Routes prompts to the optimal Claude model based on classification.

Supports automatic fallback to a more capable model if the cheaper one fails,
user overrides, and configurable routing rules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    from anthropic import Anthropic, APIError
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from token_saviour.classifier import TaskClassifier, ComplexityTier, ClassificationResult
from token_saviour.config import Config


# Tier ordering for fallback logic
_TIER_ORDER = [ComplexityTier.SIMPLE, ComplexityTier.MODERATE, ComplexityTier.COMPLEX]


@dataclass
class RouteResult:
    """Result of routing a prompt to a Claude model."""
    prompt: str
    classification: ClassificationResult
    model_used: str
    response_text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    fallback_used: bool = False
    fallback_from: Optional[str] = None


@dataclass
class ModelRouter:
    """
    Routes prompts to the optimal Claude model based on task complexity.

    Features:
    - Automatic classification and routing
    - Fallback to stronger models on failure
    - User overrides for forcing specific models
    - Configurable via Config object
    """

    config: Config = field(default_factory=Config)
    classifier: TaskClassifier = field(default_factory=TaskClassifier)
    _client: Optional[object] = field(default=None, repr=False)

    def __post_init__(self):
        if HAS_ANTHROPIC:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key:
                self._client = Anthropic(api_key=api_key)

    @property
    def client(self):
        if self._client is None:
            if not HAS_ANTHROPIC:
                raise ImportError(
                    "The 'anthropic' package is required. Install it with: pip install anthropic"
                )
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is not set. "
                    "Set it with: export ANTHROPIC_API_KEY='your-key-here'"
                )
            self._client = Anthropic(api_key=api_key)
        return self._client

    def get_model(self, tier: ComplexityTier) -> str:
        """Get the model name for a given complexity tier."""
        model_map = {
            ComplexityTier.SIMPLE: self.config.models.get("simple", "claude-3-5-haiku-20241022"),
            ComplexityTier.MODERATE: self.config.models.get("moderate", "claude-sonnet-4-20250514"),
            ComplexityTier.COMPLEX: self.config.models.get("complex", "claude-opus-4-20250514"),
        }
        return model_map[tier]

    def get_model_cost(self, model: str) -> tuple[float, float]:
        """
        Get the (input_cost_per_1m, output_cost_per_1m) for a model.

        Returns:
            Tuple of (input_cost, output_cost) per 1 million tokens.
        """
        costs = {
            "claude-3-5-haiku-20241022": (0.80, 4.00),
            "claude-sonnet-4-20250514": (3.00, 15.00),
            "claude-opus-4-20250514": (15.00, 75.00),
        }
        return costs.get(model, (3.00, 15.00))  # Default to Sonnet pricing

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost in USD for a given model and token counts."""
        input_cost_per_m, output_cost_per_m = self.get_model_cost(model)
        cost = (input_tokens / 1_000_000 * input_cost_per_m) + \
               (output_tokens / 1_000_000 * output_cost_per_m)
        return round(cost, 6)

    def classify_and_route(
        self,
        prompt: str,
        context: Optional[str] = None,
        force_model: Optional[str] = None,
        force_tier: Optional[ComplexityTier] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> ClassificationResult:
        """
        Classify a prompt and return the classification without sending to the API.

        Args:
            prompt: The user's prompt.
            context: Optional additional context.
            force_model: Force a specific model (skips classification).
            force_tier: Force a specific tier.

        Returns:
            ClassificationResult with the recommended model.
        """
        if force_tier:
            result = self.classifier.classify(prompt, context)
            result.tier = force_tier
            result.model = self.get_model(force_tier)
            return result

        result = self.classifier.classify(prompt, context)

        if force_model:
            result.model = force_model

        return result

    def route(
        self,
        prompt: str,
        context: Optional[str] = None,
        force_model: Optional[str] = None,
        force_tier: Optional[ComplexityTier] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> RouteResult:
        """
        Classify a prompt and send it to the optimal Claude model.

        Args:
            prompt: The user's prompt.
            context: Optional additional context to include.
            force_model: Force a specific model (bypasses classification).
            force_tier: Force a specific complexity tier.
            system_prompt: Optional system prompt.
            max_tokens: Override max tokens for the response.

        Returns:
            RouteResult with the response and cost information.
        """
        classification = self.classify_and_route(
            prompt, context, force_model, force_tier, system_prompt, max_tokens
        )
        model = classification.model

        if max_tokens is None:
            max_tokens = self._suggest_max_tokens(classification.tier)

        # Build the full prompt with context
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        # Attempt the API call
        fallback_used = False
        fallback_from = None

        try:
            response_text, input_tokens, output_tokens = self._call_api(
                model=model,
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )
        except Exception as e:
            # If auto_fallback is enabled, try the next tier up
            if self.config.routing.get("auto_fallback", True):
                next_model = self._get_fallback_model(classification.tier)
                if next_model and next_model != model:
                    fallback_used = True
                    fallback_from = model
                    model = next_model
                    response_text, input_tokens, output_tokens = self._call_api(
                        model=model,
                        prompt=full_prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                    )
                else:
                    raise
            else:
                raise

        cost = self.calculate_cost(model, input_tokens, output_tokens)

        return RouteResult(
            prompt=prompt,
            classification=classification,
            model_used=model,
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            fallback_used=fallback_used,
            fallback_from=fallback_from,
        )

    def _call_api(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        """Make the actual API call and return (response_text, input_tokens, output_tokens)."""
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        return (
            response_text,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

    def _get_fallback_model(self, current_tier: ComplexityTier) -> Optional[str]:
        """Get the next model up in the tier hierarchy."""
        current_idx = _TIER_ORDER.index(current_tier)
        if current_idx < len(_TIER_ORDER) - 1:
            next_tier = _TIER_ORDER[current_idx + 1]
            return self.get_model(next_tier)
        return None

    @staticmethod
    def _suggest_max_tokens(tier: ComplexityTier) -> int:
        """Suggest a max_tokens value based on task complexity."""
        suggestions = {
            ComplexityTier.SIMPLE: 512,
            ComplexityTier.MODERATE: 1536,
            ComplexityTier.COMPLEX: 4096,
        }
        return suggestions[tier]
