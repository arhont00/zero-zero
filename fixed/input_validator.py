"""
Input validation utilities for security.
Prevents common injection attacks and validates user input.
"""
import logging
import re
from typing import Any, Optional, Pattern
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes user input."""
    
    # Patterns for dangerous characters
    SQL_INJECTION_PATTERN: Pattern = re.compile(
        r"(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bexec\b|\bscript\b)",
        re.IGNORECASE
    )
    
    XSS_PATTERN: Pattern = re.compile(
        r'(<script|<iframe|javascript:|onerror|onload|onclick|<embed|\beval\b)',
        re.IGNORECASE
    )
    
    @staticmethod
    def validate_string(
        value: str,
        min_length: int = 1,
        max_length: int = 1000,
        allow_special: bool = False
    ) -> Optional[str]:
        """Validate and sanitize string input."""
        if not isinstance(value, str):
            return None
        
        # Check length
        if len(value) < min_length or len(value) > max_length:
            logger.warning(f"String length validation failed: {len(value)}")
            return None
        
        # URL decode if needed
        value = unquote(value).strip()
        
        # Check for SQL injection patterns
        if InputValidator.SQL_INJECTION_PATTERN.search(value):
            logger.warning(f"Potential SQL injection detected: {value[:50]}")
            return None
        
        # Check for XSS patterns
        if InputValidator.XSS_PATTERN.search(value):
            logger.warning(f"Potential XSS detected: {value[:50]}")
            return None
        
        return value
    
    @staticmethod
    def validate_integer(value: Any, min_val: int = 0, max_val: int = 2147483647) -> Optional[int]:
        """Validate integer input."""
        try:
            int_val = int(value)
            if min_val <= int_val <= max_val:
                return int_val
            logger.warning(f"Integer out of range: {int_val}")
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_email(email: str) -> Optional[str]:
        """Validate email format."""
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not pattern.match(email):
            logger.warning(f"Invalid email format: {email}")
            return None
        
        if len(email) > 254:
            logger.warning(f"Email too long: {email}")
            return None
        
        return email
    
    @staticmethod
    def validate_phone(phone: str) -> Optional[str]:
        """Validate phone number format."""
        # Remove non-digit characters
        cleaned = re.sub(r'\D', '', phone)
        
        # Check length (typically 10-15 digits)
        if not (10 <= len(cleaned) <= 15):
            logger.warning(f"Phone number invalid length: {cleaned}")
            return None
        
        return cleaned
    
    @staticmethod
    def validate_slug(slug: str, max_length: int = 100) -> Optional[str]:
        """Validate URL-safe slug."""
        pattern = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        
        if not pattern.match(slug) or len(slug) > max_length:
            logger.warning(f"Invalid slug: {slug}")
            return None
        
        return slug
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove dangerous HTML/script content."""
        # This is a basic implementation; use bleach library in production
        dangerous_chars = {
            '<script': '&lt;script',
            '</script>': '&lt;/script&gt;',
            'javascript:': '',
            'onerror=': '',
            'onclick=': '',
        }
        
        result = text
        for char, replacement in dangerous_chars.items():
            result = result.replace(char, replacement)
        
        return result