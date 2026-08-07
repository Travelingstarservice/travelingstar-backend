"""
Unit tests for input validation utilities.
"""

import pytest
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.validators import (
    validate_4digit_password,
    validate_password_strength,
    validate_email,
    validate_phone,
    validate_required_fields,
    validate_positive_number,
    validate_date_string,
    validate_string_length,
    sanitize_string
)


class TestPasswordValidation:
    """Test password validation functions."""
    
    def test_valid_4digit_password(self):
        """Test valid 4-digit passwords."""
        assert validate_4digit_password("1234") == (True, "1234")
        assert validate_4digit_password("0000") == (True, "0000")
        assert validate_4digit_password("9999") == (True, "9999")
    
    def test_invalid_4digit_password(self):
        """Test invalid 4-digit passwords."""
        assert validate_4digit_password("123") == (False, "Password must be exactly 4 digits")
        assert validate_4digit_password("12345") == (False, "Password must be exactly 4 digits")
        assert validate_4digit_password("abcd") == (False, "Password must be exactly 4 digits")
        assert validate_4digit_password("") == (False, "Password is required")
        assert validate_4digit_password(None) == (False, "Password is required")
    
    def test_4digit_password_whitespace(self):
        """Test 4-digit password with whitespace."""
        assert validate_4digit_password(" 1234 ") == (True, "1234")
        assert validate_4digit_password("1234 ") == (True, "1234")
        assert validate_4digit_password(" 1234") == (True, "1234")
    
    def test_strong_password_valid(self):
        """Test valid strong passwords."""
        assert validate_password_strength("Secure123!")[0] == True
        assert validate_password_strength("MyP@ssw0rd")[0] == True
        assert validate_password_strength("Complex$Pass2024")[0] == True
    
    def test_strong_password_too_short(self):
        """Test strong password minimum length."""
        result = validate_password_strength("Short1!", min_length=8)
        assert result[0] == False
        assert "at least 8 characters" in result[1]
    
    def test_strong_password_no_uppercase(self):
        """Test strong password requires uppercase."""
        result = validate_password_strength("lowercase123!")
        assert result[0] == False
        assert "uppercase" in result[1]
    
    def test_strong_password_no_lowercase(self):
        """Test strong password requires lowercase."""
        result = validate_password_strength("UPPERCASE123!")
        assert result[0] == False
        assert "lowercase" in result[1]
    
    def test_strong_password_no_digit(self):
        """Test strong password requires digit."""
        result = validate_password_strength("NoDigits!")
        assert result[0] == False
        assert "digit" in result[1]
    
    def test_strong_password_no_special(self):
        """Test strong password requires special character."""
        result = validate_password_strength("NoSpecial123")
        assert result[0] == False
        assert "special character" in result[1]
    
    def test_strong_password_common_weak(self):
        """Test strong password rejects common weak passwords."""
        result = validate_password_strength("Password123!")
        assert result[0] == False
        assert "too common" in result[1]


class TestEmailValidation:
    """Test email validation."""
    
    def test_valid_emails(self):
        """Test valid email addresses."""
        assert validate_email("test@example.com")[0] == True
        assert validate_email("user.name@domain.co.uk")[0] == True
        assert validate_email("user+tag@example.org")[0] == True
    
    def test_invalid_emails(self):
        """Test invalid email addresses."""
        assert validate_email("invalid")[0] == False
        assert validate_email("@example.com")[0] == False
        assert validate_email("user@")[0] == False
        assert validate_email("user@.com")[0] == False
        assert validate_email("")[0] == False
        assert validate_email(None)[0] == False
    
    def test_email_too_long(self):
        """Test email length validation."""
        long_email = "a" * 130 + "@example.com"
        result = validate_email(long_email)
        assert result[0] == False
        assert "too long" in result[1]


class TestPhoneValidation:
    """Test phone number validation."""
    
    def test_valid_phones(self):
        """Test valid phone numbers."""
        assert validate_phone("252-886-5996")[0] == True
        assert validate_phone("(252) 886-5996")[0] == True
        assert validate_phone("252 886 5996")[0] == True
        assert validate_phone("+12528865996")[0] == True
    
    def test_invalid_phones(self):
        """Test invalid phone numbers."""
        assert validate_phone("abc")[0] == False
        assert validate_phone("123")[0] == False
        assert validate_phone("")[0] == False
        assert validate_phone(None)[0] == False


class TestRequiredFields:
    """Test required field validation."""
    
    def test_all_fields_present(self):
        """Test when all required fields are present."""
        data = {"field1": "value1", "field2": "value2"}
        result = validate_required_fields(data, ["field1", "field2"])
        assert result[0] == True
    
    def test_missing_fields(self):
        """Test when required fields are missing."""
        data = {"field1": "value1"}
        result = validate_required_fields(data, ["field1", "field2"])
        assert result[0] == False
        assert "field2" in result[1]
    
    def test_empty_fields(self):
        """Test when required fields are empty."""
        data = {"field1": "", "field2": None}
        result = validate_required_fields(data, ["field1", "field2"])
        assert result[0] == False


class TestNumericValidation:
    """Test numeric validation."""
    
    def test_valid_numbers(self):
        """Test valid positive numbers."""
        assert validate_positive_number(10, "value")[0] == True
        assert validate_positive_number(0.5, "value")[0] == True
        assert validate_positive_number("100", "value")[0] == True
    
    def test_invalid_numbers(self):
        """Test invalid numbers."""
        assert validate_positive_number(-5, "value")[0] == False
        assert validate_positive_number("abc", "value")[0] == False
        assert validate_positive_number(None, "value")[0] == False


class TestDateValidation:
    """Test date string validation."""
    
    def test_valid_dates(self):
        """Test valid date strings."""
        assert validate_date_string("2026-08-07", "date")[0] == True
        assert validate_date_string("2025-01-01", "date")[0] == True
    
    def test_invalid_dates(self):
        """Test invalid date strings."""
        assert validate_date_string("2026/08/07", "date")[0] == False
        assert validate_date_string("08-07-2026", "date")[0] == False
        assert validate_date_string("invalid", "date")[0] == False
        assert validate_date_string("", "date")[0] == False


class TestStringValidation:
    """Test string length validation."""
    
    def test_valid_strings(self):
        """Test valid string lengths."""
        assert validate_string_length("test", 1, 10, "field")[0] == True
        assert validate_string_length("a", 1, 10, "field")[0] == True
        assert validate_string_length("1234567890", 1, 10, "field")[0] == True
    
    def test_too_short(self):
        """Test string too short."""
        result = validate_string_length("ab", 5, 10, "field")
        assert result[0] == False
        assert "at least 5 characters" in result[1]
    
    def test_too_long(self):
        """Test string too long."""
        result = validate_string_length("very long string", 1, 5, "field")
        assert result[0] == False
        assert "not exceed 5 characters" in result[1]


class TestSanitization:
    """Test input sanitization."""
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        assert sanitize_string("test") == "test"
        assert sanitize_string("  test  ") == "test"
        assert sanitize_string("test\x00null") == "testnull"
        assert sanitize_string("") == ""
        assert sanitize_string(None) == ""
    
    def test_sanitize_truncation(self):
        """Test string truncation."""
        long_string = "a" * 300
        result = sanitize_string(long_string, 255)
        assert len(result) == 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])