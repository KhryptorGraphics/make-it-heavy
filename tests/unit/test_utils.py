"""
Unit tests for utility functions and helper modules.
"""

import pytest
import yaml
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from utils import (
    load_config, validate_api_key, estimate_tokens, format_duration,
    truncate_text, safe_json_parse, validate_input_string, 
    validate_positive_integer, retry_with_backoff, create_safe_filename,
    merge_dictionaries, get_nested_value, set_nested_value
)
from exceptions import ConfigurationError, ValidationError


class TestConfigUtils:
    """Test configuration-related utility functions."""

    def test_load_config_success(self, temp_config_file):
        """Test successful config loading."""
        config = load_config(temp_config_file)
        
        assert isinstance(config, dict)
        assert "openrouter" in config
        assert "agent" in config
        assert "orchestrator" in config

    def test_load_config_missing_file(self):
        """Test loading non-existent config file."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("nonexistent.yaml")
        
        assert "not found" in str(exc_info.value)

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file."""
        invalid_config = tmp_path / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content:")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(invalid_config))
        
        assert "Invalid YAML format" in str(exc_info.value)

    def test_load_config_missing_sections(self, tmp_path):
        """Test loading config with missing required sections."""
        incomplete_config = tmp_path / "incomplete.yaml"
        incomplete_config.write_text("openrouter:\n  api_key: test")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(incomplete_config))
        
        assert "Missing required section" in str(exc_info.value)


class TestAPIKeyValidation:
    """Test API key validation functions."""

    def test_validate_api_key_valid(self):
        """Test validation of valid API keys."""
        valid_keys = [
            "sk-1234567890abcdef1234567890abcdef",
            "sk-or-v1-abcdef1234567890abcdef1234567890",
            "sk-proj-1234567890abcdef"
        ]
        
        for key in valid_keys:
            assert validate_api_key(key) is True

    def test_validate_api_key_invalid(self):
        """Test validation of invalid API keys."""
        invalid_keys = [
            "",
            "YOUR KEY",
            "YOUR_KEY", 
            "REPLACE_ME",
            "invalid-key",
            "sk-",
            "sk-short",
            None
        ]
        
        for key in invalid_keys:
            assert validate_api_key(key) is False

    def test_validate_api_key_wrong_format(self):
        """Test API keys with wrong format."""
        wrong_format_keys = [
            "pk-1234567890abcdef1234567890abcdef",  # Wrong prefix
            "1234567890abcdef1234567890abcdef",     # No prefix
            "sk_1234567890abcdef1234567890abcdef"   # Wrong separator
        ]
        
        for key in wrong_format_keys:
            assert validate_api_key(key) is False


class TestTextUtils:
    """Test text processing utility functions."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        test_cases = [
            ("", 0),
            ("hello", 1),  # 5 chars / 4 = 1.25 -> 1
            ("hello world", 2),  # 11 chars / 4 = 2.75 -> 2
            ("a" * 20, 5),  # 20 chars / 4 = 5
        ]
        
        for text, expected in test_cases:
            assert estimate_tokens(text) == expected

    def test_format_duration(self):
        """Test duration formatting."""
        test_cases = [
            (0.5, "0.50s"),
            (1.0, "1.0s"),
            (30.5, "30.5s"),
            (65, "1m 5s"),
            (3661, "1h 1m"),
            (7200, "2h 0m")
        ]
        
        for seconds, expected in test_cases:
            assert format_duration(seconds) == expected

    def test_truncate_text(self):
        """Test text truncation."""
        text = "This is a long text that should be truncated"
        
        # Default truncation
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")
        
        # Custom suffix
        result = truncate_text(text, 20, " [more]")
        assert result.endswith(" [more]")
        
        # Text shorter than limit
        short_text = "Short"
        result = truncate_text(short_text, 20)
        assert result == short_text

    def test_safe_json_parse(self):
        """Test safe JSON parsing."""
        # Valid JSON
        valid_json = '{"key": "value", "number": 42}'
        result = safe_json_parse(valid_json)
        assert result == {"key": "value", "number": 42}
        
        # Valid JSON array
        valid_array = '["item1", "item2"]'
        result = safe_json_parse(valid_array)
        assert result == ["item1", "item2"]
        
        # Invalid JSON
        invalid_json = '{"invalid": json}'
        result = safe_json_parse(invalid_json)
        assert result is None
        
        # Empty string
        result = safe_json_parse("")
        assert result is None


class TestValidationUtils:
    """Test input validation utility functions."""

    def test_validate_input_string_success(self):
        """Test successful string validation."""
        # Should not raise exception
        validate_input_string("valid string", "test_field")
        validate_input_string("a" * 100, "test_field", min_length=1, max_length=200)

    def test_validate_input_string_too_short(self):
        """Test string validation with too short input."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input_string("", "test_field", min_length=1)
        
        assert "at least 1 characters" in str(exc_info.value)

    def test_validate_input_string_too_long(self):
        """Test string validation with too long input."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input_string("a" * 100, "test_field", max_length=50)
        
        assert "at most 50 characters" in str(exc_info.value)

    def test_validate_input_string_wrong_type(self):
        """Test string validation with wrong type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input_string(123, "test_field")
        
        assert "must be a string" in str(exc_info.value)

    def test_validate_positive_integer_success(self):
        """Test successful positive integer validation."""
        # Should not raise exception
        validate_positive_integer(5, "test_field")
        validate_positive_integer(100, "test_field", min_value=10)

    def test_validate_positive_integer_too_small(self):
        """Test positive integer validation with too small value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer(0, "test_field", min_value=1)
        
        assert "at least 1" in str(exc_info.value)

    def test_validate_positive_integer_wrong_type(self):
        """Test positive integer validation with wrong type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer("5", "test_field")
        
        assert "must be an integer" in str(exc_info.value)


class TestRetryUtils:
    """Test retry utility functions."""

    def test_retry_with_backoff_success_first_try(self):
        """Test retry with success on first attempt."""
        func = Mock(return_value="success")
        
        result = retry_with_backoff(func, max_retries=3)
        
        assert result == "success"
        assert func.call_count == 1

    def test_retry_with_backoff_success_after_retries(self):
        """Test retry with success after some failures."""
        func = Mock()
        func.side_effect = [Exception("fail"), Exception("fail"), "success"]
        
        result = retry_with_backoff(func, max_retries=3, base_delay=0.01)
        
        assert result == "success"
        assert func.call_count == 3

    def test_retry_with_backoff_all_fail(self):
        """Test retry when all attempts fail."""
        func = Mock(side_effect=Exception("always fails"))
        
        with pytest.raises(Exception) as exc_info:
            retry_with_backoff(func, max_retries=2, base_delay=0.01)
        
        assert "always fails" in str(exc_info.value)
        assert func.call_count == 3  # 1 initial + 2 retries

    def test_retry_with_backoff_timing(self):
        """Test retry timing and backoff."""
        func = Mock(side_effect=[Exception("fail"), "success"])
        
        import time
        start_time = time.time()
        result = retry_with_backoff(func, max_retries=2, base_delay=0.1, backoff_factor=2.0)
        elapsed = time.time() - start_time
        
        assert result == "success"
        assert elapsed >= 0.1  # At least one delay occurred


class TestFileUtils:
    """Test file-related utility functions."""

    def test_create_safe_filename(self):
        """Test safe filename creation."""
        test_cases = [
            ("normal filename", "normal_filename"),
            ("file with spaces", "file_with_spaces"),
            ("file/with\\special*chars", "file_with_special_chars"),
            ("file:with\"dangerous<chars>", "file_with_dangerous_chars_"),
            ("", ""),
            ("a" * 300, "a" * 255)  # Test length limit
        ]
        
        for input_text, expected in test_cases:
            result = create_safe_filename(input_text)
            # Check that result matches expected pattern
            assert all(c.isalnum() or c in '-_.' for c in result)
            if expected:
                assert len(result) <= 255


class TestDictionaryUtils:
    """Test dictionary manipulation utility functions."""

    def test_merge_dictionaries_simple(self):
        """Test simple dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        
        result = merge_dictionaries(dict1, dict2)
        
        assert result == {"a": 1, "b": 3, "c": 4}
        # Ensure original dicts unchanged
        assert dict1 == {"a": 1, "b": 2}

    def test_merge_dictionaries_nested(self):
        """Test nested dictionary merging."""
        dict1 = {"outer": {"inner1": 1, "inner2": 2}}
        dict2 = {"outer": {"inner2": 3, "inner3": 4}}
        
        result = merge_dictionaries(dict1, dict2)
        
        expected = {"outer": {"inner1": 1, "inner2": 3, "inner3": 4}}
        assert result == expected

    def test_merge_dictionaries_type_override(self):
        """Test merging when types don't match."""
        dict1 = {"key": {"nested": "value"}}
        dict2 = {"key": "simple_value"}
        
        result = merge_dictionaries(dict1, dict2)
        
        assert result == {"key": "simple_value"}

    def test_get_nested_value_success(self):
        """Test getting nested values successfully."""
        data = {
            "level1": {
                "level2": {
                    "level3": "found"
                }
            }
        }
        
        result = get_nested_value(data, "level1.level2.level3")
        assert result == "found"

    def test_get_nested_value_not_found(self):
        """Test getting nested values that don't exist."""
        data = {"level1": {"level2": "value"}}
        
        result = get_nested_value(data, "level1.nonexistent.key", default="default")
        assert result == "default"

    def test_get_nested_value_empty_path(self):
        """Test getting value with empty path."""
        data = {"key": "value"}
        
        result = get_nested_value(data, "key")
        assert result == "value"

    def test_set_nested_value_new_path(self):
        """Test setting nested value creating new path."""
        data = {}
        
        set_nested_value(data, "level1.level2.level3", "new_value")
        
        expected = {"level1": {"level2": {"level3": "new_value"}}}
        assert data == expected

    def test_set_nested_value_existing_path(self):
        """Test setting nested value on existing path."""
        data = {"level1": {"level2": {"existing": "old"}}}
        
        set_nested_value(data, "level1.level2.new_key", "new_value")
        
        expected = {
            "level1": {
                "level2": {
                    "existing": "old",
                    "new_key": "new_value"
                }
            }
        }
        assert data == expected

    def test_set_nested_value_override(self):
        """Test setting nested value that overrides existing."""
        data = {"level1": {"level2": "old_value"}}
        
        set_nested_value(data, "level1.level2", "new_value")
        
        assert data == {"level1": {"level2": "new_value"}}