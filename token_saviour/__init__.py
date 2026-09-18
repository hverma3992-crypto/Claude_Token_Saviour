"""
Claude Token Saviour — Automatically route Claude API requests to the cheapest suitable model.

Save up to 18× on token costs by intelligently classifying task complexity
and routing to Haiku, Sonnet, or Opus based on what the task actually requires.
"""

__version__ = "1.0.0"
__author__ = "Verma"

from token_saviour.classifier import TaskClassifier, ComplexityTier
from token_saviour.router import ModelRouter
from token_saviour.tracker import UsageTracker
from token_saviour.optimizer import PromptOptimizer
from token_saviour.config import Config

__all__ = [
    "TaskClassifier",
    "ComplexityTier",
    "ModelRouter",
    "UsageTracker",
    "PromptOptimizer",
    "Config",
]
