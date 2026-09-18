"""
Tests for Claude Token Saviour.

Tests the classifier, optimizer, tracker, and config modules.
Does NOT test API calls (those require ANTHROPIC_API_KEY).
"""

import json
import os
import tempfile
import pytest

from token_saviour.classifier import TaskClassifier, ComplexityTier, ClassificationResult
from token_saviour.optimizer import PromptOptimizer
from token_saviour.tracker import UsageTracker, UsageEntry
from token_saviour.config import Config
from token_saviour.router import ModelRouter


# ============================================================================
# TaskClassifier Tests
# ============================================================================


class TestTaskClassifier:
    """Tests for the TaskClassifier."""

    def setup_method(self):
        self.classifier = TaskClassifier()

    def test_simple_typo_fix(self):
        result = self.classifier.classify("Fix the typo in this variable name: prnt_hello")
        assert result.tier == ComplexityTier.SIMPLE

    def test_simple_format_conversion(self):
        result = self.classifier.classify("Convert this JSON to YAML format")
        assert result.tier == ComplexityTier.SIMPLE

    def test_simple_rename(self):
        result = self.classifier.classify("Rename the variable 'x' to 'count'")
        assert result.tier == ComplexityTier.SIMPLE

    def test_simple_sort_imports(self):
        result = self.classifier.classify("Sort imports in this Python file")
        assert result.tier == ComplexityTier.SIMPLE

    def test_simple_mock_data(self):
        result = self.classifier.classify("Generate mock data for testing user profiles")
        assert result.tier == ComplexityTier.SIMPLE

    def test_moderate_write_tests(self):
        result = self.classifier.classify("Write unit tests for the authentication module")
        assert result.tier == ComplexityTier.MODERATE

    def test_moderate_refactor(self):
        result = self.classifier.classify("Refactor this function to use async/await")
        assert result.tier == ComplexityTier.MODERATE

    def test_moderate_debug(self):
        result = self.classifier.classify("Debug this function - it returns None unexpectedly")
        assert result.tier == ComplexityTier.MODERATE

    def test_moderate_code_review(self):
        result = self.classifier.classify("Review this code for potential issues")
        assert result.tier == ComplexityTier.MODERATE

    def test_complex_architecture(self):
        result = self.classifier.classify(
            "Design a microservices architecture with event sourcing for a trading platform"
        )
        assert result.tier == ComplexityTier.COMPLEX

    def test_complex_security_analysis(self):
        result = self.classifier.classify(
            "Analyze the security vulnerabilities in this OAuth implementation"
        )
        assert result.tier == ComplexityTier.COMPLEX

    def test_complex_system_design(self):
        result = self.classifier.classify(
            "Design a distributed system with high availability and fault tolerance"
        )
        assert result.tier == ComplexityTier.COMPLEX

    def test_classification_result_has_model(self):
        result = self.classifier.classify("Fix this typo")
        assert result.model is not None
        assert len(result.model) > 0

    def test_classification_result_has_score(self):
        result = self.classifier.classify("Some prompt")
        assert 0.0 <= result.score <= 1.0

    def test_classification_result_has_token_estimate(self):
        result = self.classifier.classify("A short prompt")
        assert result.token_estimate > 0

    def test_simple_returns_haiku(self):
        result = self.classifier.classify("Fix the typo in 'recieve'")
        assert "haiku" in result.model.lower()

    def test_complex_returns_opus(self):
        result = self.classifier.classify(
            "Design a microservices architecture with event sourcing"
        )
        assert "opus" in result.model.lower()

    def test_with_context(self):
        result = self.classifier.classify(
            "Fix the bug",
            context="def hello(): print('world')"
        )
        assert result is not None
        assert isinstance(result.tier, ComplexityTier)


# ============================================================================
# PromptOptimizer Tests
# ============================================================================


class TestPromptOptimizer:
    """Tests for the PromptOptimizer."""

    def test_compress_removes_trailing_whitespace(self):
        text = "hello   \nworld   "
        result = PromptOptimizer.compress_prompt(text)
        assert "   \n" not in result.optimized_text

    def test_compress_collapses_blank_lines(self):
        text = "hello\n\n\n\n\nworld"
        result = PromptOptimizer.compress_prompt(text)
        assert "\n\n\n" not in result.optimized_text

    def test_compress_trims_edges(self):
        text = "   \n  hello world  \n   "
        result = PromptOptimizer.compress_prompt(text)
        assert result.optimized_text == "hello world"

    def test_compress_collapses_spaces(self):
        text = "hello    world    test"
        result = PromptOptimizer.compress_prompt(text)
        assert "    " not in result.optimized_text

    def test_compress_preserves_code_blocks(self):
        text = "text ```\ndef foo():\n    pass\n``` more text"
        result = PromptOptimizer.compress_prompt(text)
        assert "def foo():" in result.optimized_text

    def test_compress_reports_savings(self):
        text = "   hello   \n\n\n\n   world   \n\n\n"
        result = PromptOptimizer.compress_prompt(text)
        assert result.tokens_saved >= 0
        assert result.savings_percentage >= 0

    def test_strip_python_comments(self):
        code = "# This is a comment\nx = 1  # inline comment\n"
        result = PromptOptimizer.strip_code_comments(code, "python")
        assert "This is a comment" not in result
        assert "inline comment" not in result

    def test_strip_js_comments(self):
        code = "// This is a comment\nconst x = 1; // inline\n/* block */\n"
        result = PromptOptimizer.strip_code_comments(code, "javascript")
        assert "This is a comment" not in result
        assert "block" not in result

    def test_truncate_within_budget(self):
        text = "Short text"
        result = PromptOptimizer.truncate_context(text, max_tokens=100)
        assert result == text

    def test_truncate_exceeds_budget(self):
        text = "x" * 10000  # Very long text
        result = PromptOptimizer.truncate_context(text, max_tokens=100)
        assert len(result) < len(text)
        assert "[truncated]" in result

    def test_truncate_start_strategy(self):
        text = "x" * 10000
        result = PromptOptimizer.truncate_context(text, max_tokens=100, strategy="start")
        assert "[truncated]" in result

    def test_truncate_middle_strategy(self):
        text = "x" * 10000
        result = PromptOptimizer.truncate_context(text, max_tokens=100, strategy="middle")
        assert "[middle truncated]" in result

    def test_estimate_tokens_short(self):
        tokens = PromptOptimizer.estimate_tokens("Hello")
        assert tokens >= 1

    def test_estimate_tokens_code(self):
        code = "def hello():\n    print('world')\n    import os"
        tokens = PromptOptimizer.estimate_tokens(code)
        assert tokens > 5

    def test_estimate_tokens_empty(self):
        tokens = PromptOptimizer.estimate_tokens("")
        assert tokens == 0

    def test_suggest_max_tokens_classify(self):
        tokens = PromptOptimizer.suggest_max_tokens("Classify this text")
        assert tokens <= 100

    def test_suggest_max_tokens_implement(self):
        tokens = PromptOptimizer.suggest_max_tokens("Implement a function to sort")
        assert tokens >= 500

    def test_suggest_max_tokens_design(self):
        tokens = PromptOptimizer.suggest_max_tokens("Design an architecture")
        assert tokens >= 1000

    def test_efficient_system_prompt(self):
        prompt = PromptOptimizer.create_efficient_system_prompt("reviewer")
        assert len(prompt) < 200
        assert "code" in prompt.lower() or "review" in prompt.lower()


# ============================================================================
# UsageTracker Tests
# ============================================================================


class TestUsageTracker:
    """Tests for the UsageTracker."""

    def setup_method(self):
        # Use a temp file for each test
        self.temp_file = tempfile.mktemp(suffix=".json")
        self.tracker = UsageTracker(data_file=self.temp_file)

    def teardown_method(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def test_log_entry(self):
        entry = self.tracker.log(
            prompt="Fix typo",
            tier="SIMPLE",
            model="claude-3-5-haiku-20241022",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.000280,
        )
        assert isinstance(entry, UsageEntry)
        assert entry.tier == "SIMPLE"
        assert entry.input_tokens == 100
        assert entry.output_tokens == 50

    def test_log_calculates_opus_cost(self):
        entry = self.tracker.log(
            prompt="Fix typo",
            tier="SIMPLE",
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.0028,
        )
        # Opus cost: (1000/1M * 15) + (500/1M * 75) = 0.015 + 0.0375 = 0.0525
        assert entry.opus_cost_usd > entry.cost_usd

    def test_log_calculates_savings(self):
        entry = self.tracker.log(
            prompt="Fix typo",
            tier="SIMPLE",
            model="claude-3-5-haiku-20241022",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.0028,
        )
        assert entry.savings_usd > 0

    def test_log_persists_to_file(self):
        self.tracker.log(
            prompt="Test prompt",
            tier="SIMPLE",
            model="claude-3-5-haiku-20241022",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.000280,
        )
        assert os.path.exists(self.temp_file)
        with open(self.temp_file, "r") as f:
            data = json.load(f)
        assert len(data) == 1

    def test_report_empty(self):
        report = self.tracker.get_report()
        assert report.total_requests == 0
        assert report.total_cost_usd == 0

    def test_report_with_entries(self):
        self.tracker.log("p1", "SIMPLE", "haiku", 100, 50, 0.001)
        self.tracker.log("p2", "MODERATE", "sonnet", 200, 100, 0.005)
        report = self.tracker.get_report()
        assert report.total_requests == 2
        assert report.total_cost_usd > 0
        assert report.savings_percentage > 0

    def test_report_tier_breakdown(self):
        self.tracker.log("p1", "SIMPLE", "haiku", 100, 50, 0.001)
        self.tracker.log("p2", "SIMPLE", "haiku", 100, 50, 0.001)
        self.tracker.log("p3", "COMPLEX", "opus", 500, 200, 0.05)
        report = self.tracker.get_report()
        assert report.tier_breakdown["SIMPLE"] == 2
        assert report.tier_breakdown["COMPLEX"] == 1

    def test_clear(self):
        self.tracker.log("p1", "SIMPLE", "haiku", 100, 50, 0.001)
        self.tracker.clear()
        assert len(self.tracker.entries) == 0

    def test_loads_from_existing_file(self):
        # Log some data and create a new tracker from the same file
        self.tracker.log("p1", "SIMPLE", "haiku", 100, 50, 0.001)
        new_tracker = UsageTracker(data_file=self.temp_file)
        assert len(new_tracker.entries) == 1


# ============================================================================
# Config Tests
# ============================================================================


class TestConfig:
    """Tests for the Config module."""

    def test_default_config(self):
        config = Config()
        assert "simple" in config.models
        assert "moderate" in config.models
        assert "complex" in config.models

    def test_default_models(self):
        config = Config()
        assert "haiku" in config.models["simple"]
        assert "sonnet" in config.models["moderate"]
        assert "opus" in config.models["complex"]

    def test_default_routing(self):
        config = Config()
        assert config.routing["auto_fallback"] is True

    def test_default_budget(self):
        config = Config()
        assert config.budget["daily_limit_usd"] > 0

    def test_to_dict(self):
        config = Config()
        data = config.to_dict()
        assert isinstance(data, dict)
        assert "models" in data

    def test_env_override(self):
        os.environ["CLAUDE_TS_MODEL_SIMPLE"] = "custom-haiku-model"
        try:
            config = Config()
            assert config.models["simple"] == "custom-haiku-model"
        finally:
            del os.environ["CLAUDE_TS_MODEL_SIMPLE"]

    def test_load_from_yaml(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        try:
            f.write("models:\n  simple: test-model\n")
            f.close()
            config = Config(config_path=f.name)
            assert config.models["simple"] == "test-model"
        finally:
            try:
                os.remove(f.name)
            except OSError:
                pass


# ============================================================================
# ModelRouter Tests (no API calls)
# ============================================================================


class TestModelRouter:
    """Tests for ModelRouter (classification only, no API calls)."""

    def setup_method(self):
        self.router = ModelRouter()

    def test_get_model_simple(self):
        model = self.router.get_model(ComplexityTier.SIMPLE)
        assert "haiku" in model.lower()

    def test_get_model_moderate(self):
        model = self.router.get_model(ComplexityTier.MODERATE)
        assert "sonnet" in model.lower()

    def test_get_model_complex(self):
        model = self.router.get_model(ComplexityTier.COMPLEX)
        assert "opus" in model.lower()

    def test_calculate_cost(self):
        cost = self.router.calculate_cost("claude-3-5-haiku-20241022", 1000, 500)
        assert cost > 0
        assert cost < 0.01  # Should be very cheap for small amounts

    def test_haiku_cheaper_than_opus(self):
        haiku_cost = self.router.calculate_cost("claude-3-5-haiku-20241022", 10000, 5000)
        opus_cost = self.router.calculate_cost("claude-opus-4-20250514", 10000, 5000)
        assert haiku_cost < opus_cost

    def test_classify_and_route(self):
        result = self.router.classify_and_route("Fix this typo")
        assert isinstance(result, ClassificationResult)
        assert result.model is not None

    def test_force_tier(self):
        result = self.router.classify_and_route(
            "Fix this typo", force_tier=ComplexityTier.COMPLEX
        )
        assert result.tier == ComplexityTier.COMPLEX
        assert "opus" in result.model.lower()

    def test_force_model(self):
        result = self.router.classify_and_route(
            "Fix this typo", force_model="custom-model-123"
        )
        assert result.model == "custom-model-123"

    def test_get_model_cost(self):
        input_cost, output_cost = self.router.get_model_cost("claude-3-5-haiku-20241022")
        assert input_cost == 0.80
        assert output_cost == 4.00
