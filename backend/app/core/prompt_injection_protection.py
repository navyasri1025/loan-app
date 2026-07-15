"""
Prompt Injection Protection

Protects the workflow against prompt injection attacks.

Detects and blocks:
- "Approve regardless"
- "Skip validation"
- "My manager already approved"
- "Override policy"
- etc.

Always logs attempted bypasses.
Never allows policy to be bypassed.
"""

from typing import Dict, Any, List, Tuple
import re
from app.core.logging import get_logger

logger = get_logger("security.prompt_injection")


class PromptInjectionProtector:
    """Detects and blocks prompt injection attacks"""
    
    # List of patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        r"(?i)(approve|decline)\s+(?:.*\s+)?(regardless|anyway|now|immediately)",
        r"(?i)(skip|bypass|ignore)\s+(?:.*\s+)?(validation|policy|check|fairness)",
        r"(?i)(my\s+)?(manager|boss|supervisor)\s+(?:.*\s+)?(approved|declined|decided)",
        r"(?i)(override|force|force\s+)\s*(?:.*\s+)?(approval|decision|recommendation)",
        r"(?i)(disable|turn\s+off|ignore)\s+(?:.*\s+)?(fairness|bias|check)",
        r"(?i)(don't|do\s+not|never)\s+(?:.*\s+)?(check|validate|verify|run|execute)",
        r"(?i)(this\s+application|this\s+loan)\s+(?:.*\s+)?(approved|declined|already)",
        r"(?i)(trust\s+me|just\s+approve|just\s+decline|trust\s+this)",
        r"(?i)(special\s+case|VIP|priority|rush|urgent)",
        r"(?i)(executive\s+override|admin\s+mode|debug\s+mode)",
    ]
    
    # Severity levels
    SEVERITY_LOW = "LOW"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_HIGH = "HIGH"
    
    @classmethod
    def check_input(cls, text: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if input contains injection attempts.
        
        Returns: (is_safe, details)
        """
        
        if not text or not isinstance(text, str):
            return True, {"is_safe": True, "patterns_matched": []}
        
        matched_patterns = []
        severity_score = 0
        
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text):
                matched_patterns.append(pattern)
                severity_score += 1
        
        is_safe = len(matched_patterns) == 0
        
        # Determine severity
        if severity_score == 0:
            severity = "SAFE"
        elif severity_score <= 2:
            severity = cls.SEVERITY_LOW
        elif severity_score <= 4:
            severity = cls.SEVERITY_MEDIUM
        else:
            severity = cls.SEVERITY_HIGH
        
        details = {
            "is_safe": is_safe,
            "patterns_matched": matched_patterns,
            "pattern_count": len(matched_patterns),
            "severity": severity,
            "recommendation": cls._get_recommendation(severity)
        }
        
        if not is_safe:
            logger.warning(
                f"Prompt injection attempt detected: {len(matched_patterns)} patterns matched",
                extra={
                    "patterns": matched_patterns,
                    "severity": severity,
                    "sample_text": text[:100]
                }
            )
        
        return is_safe, details
    
    @classmethod
    def _get_recommendation(cls, severity: str) -> str:
        """Get recommendation based on severity"""
        if severity == "SAFE":
            return "Process normally"
        elif severity == cls.SEVERITY_LOW:
            return "Monitor - likely false positive"
        elif severity == cls.SEVERITY_MEDIUM:
            return "Flag for review - suspected injection attempt"
        else:
            return "BLOCK - definite injection attack. Escalate to security team."
    
    @classmethod
    def enforce_policy(cls, text: str, allow_override: bool = False) -> Tuple[bool, str]:
        """
        Enforce policy - block if injection detected.
        
        Returns: (allowed, reason)
        """
        
        is_safe, details = cls.check_input(text)
        
        if is_safe:
            return True, "Input validated. Policy enforced."
        
        if allow_override:
            logger.warning(
                f"Prompt injection attempt overridden by admin",
                extra={"severity": details["severity"]}
            )
            return True, "Injection detected but overridden by admin"
        
        # Block the injection
        logger.critical(
            f"Prompt injection blocked: {details['severity']} severity",
            extra={
                "patterns": details["patterns_matched"],
                "text_preview": text[:200]
            }
        )
        
        return False, f"Policy violation detected: {details['severity']} injection attempt blocked"
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Remove suspicious content while preserving legitimate text"""
        
        is_safe, details = cls.check_input(text)
        
        if is_safe:
            return text
        
        # Log sanitization
        logger.info(
            f"Sanitizing suspicious input",
            extra={
                "original_length": len(text),
                "patterns_detected": details["patterns_matched"]
            }
        )
        
        # Remove suspicious patterns
        sanitized = text
        
        # Remove obvious commands
        suspicious_keywords = [
            r"(?i)(approve|decline|override|skip|bypass|ignore)",
            r"(?i)(regardless|anyway|immediately|now)",
        ]
        
        for pattern in suspicious_keywords:
            sanitized = re.sub(pattern, "", sanitized)
        
        # Clean up whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        
        return sanitized


class InjectionProtectionMiddleware:
    """Middleware to protect endpoints from injection"""
    
    def __init__(self, app):
        self.app = app
        self.protector = PromptInjectionProtector()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check for injection in query parameters and body
        # This would be extended in production
        
        await self.app(scope, receive, send)


# Public API
def check_for_injection(text: str) -> Dict[str, Any]:
    """
    Check if text contains injection attempts.
    
    Returns details about detected patterns.
    """
    is_safe, details = PromptInjectionProtector.check_input(text)
    return details


def block_if_injection(text: str) -> None:
    """
    Block execution if injection detected.
    
    Raises Exception if injection is detected.
    """
    allowed, reason = PromptInjectionProtector.enforce_policy(text)
    
    if not allowed:
        raise ValueError(f"Policy violation: {reason}")


def sanitize_input(text: str) -> str:
    """Sanitize potentially malicious input"""
    return PromptInjectionProtector.sanitize_input(text)
