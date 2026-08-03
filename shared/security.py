"""
shared/security.py
Security & Input Sanitization module.
Defends against XSS, Script Injection, and Prompt Injection attacks.
"""

import re
import html


def sanitize_input_text(text: str, max_length: int = 300) -> str:
    """
    Làm sạch văn bản đầu vào từ hành khách.
    Loại bỏ các thẻ HTML, script, escape ký tự đặc biệt, và giới hạn độ dài.
    """
    if not text:
        return ""

    # Truncate to max length to prevent buffer overflow or memory flooding
    text = text[:max_length].strip()

    # Escape HTML special chars (<, >, &, ", ')
    text = html.escape(text)

    # Strip dangerous script / SQL injection tokens
    text = re.sub(r"(?i)(?:<script.*?>.*?</script>|javascript:|onerror=|onload=)", "", text)
    text = re.sub(r"(?i)(?:exec\s*\(|eval\s*\(|system\s*\()", "", text)
    
    sql_injection_patterns = [
        r"(?i)\b(?:SELECT|UPDATE|DELETE|INSERT|DROP|ALTER)\b.*\b(?:FROM|INTO|TABLE)\b",
        r"(?i)(?:--|\bUNION\b|\bOR\b\s+1\s*=\s*1)"
    ]
    for pattern in sql_injection_patterns:
        text = re.sub(pattern, "", text)
    
    # Strip prompt injection override attempts (e.g. "Ignore previous instructions", "SYSTEM PROMPT:")
    prompt_injection_patterns = [
        r"(?i)ignore\s+(?:all\s+)?previous\s+instructions",
        r"(?i)system\s*prompt\s*:",
        r"(?i)you\s+are\s+now\s+a",
        r"(?i)disregard\s+the\s+rules",
        r"(?i)bỏ qua các chỉ thị",
        r"(?i)quên các lệnh trước",
        r"(?i)mày là",
        r"(?i)từ giờ (?:trở đi)? hãy",
        r"(?i)in ra (?:tất cả)? prompt",
        r"(?i)developer mode"
    ]
    for pattern in prompt_injection_patterns:
        text = re.sub(pattern, "", text)

    return text.strip()
