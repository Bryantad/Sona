"""
AI Security Manager - Enterprise Grade
=====================================

Comprehensive security framework for AI operations including
input validation, output sanitization, and threat detection.

Features:
- Input sanitization and validation
- Output content filtering
- Prompt injection detection
- Data leakage prevention
- Audit logging for compliance
- Role-based access control
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .errors import AISecurityError


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityPolicy(Enum):
    """Security policies for AI operations"""
    STRICT = "strict"      # Block any suspicious content
    MODERATE = "moderate"  # Warn and sanitize
    PERMISSIVE = "permissive"  # Log only


@dataclass
class SecurityViolation:
    """Represents a security violation"""
    violation_type: str
    threat_level: ThreatLevel
    description: str
    content: str
    suggested_action: str
    metadata: dict[str, Any]


class InputValidator:
    """Validates and sanitizes AI inputs"""
    
    def __init__(self):
        # Patterns for prompt injection detection
        self.injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything\s+above',
            r'act\s+as\s+if\s+you\s+are',
            r'pretend\s+to\s+be',
            r'roleplay\s+as',
            r'system\s*:\s*',
            r'assistant\s*:\s*',
            r'human\s*:\s*',
            r'\[INST\]|\[/INST\]',
            r'<\|im_start\|>|<\|im_end\|>',
        ]
        
        # Patterns for sensitive data detection
        self.sensitive_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # Phone
        ]
        
        # Blocked content categories
        self.blocked_categories = {
            'malware': [r'(?i)malware', r'(?i)virus', r'(?i)trojan'],
            'phishing': [r'(?i)phishing', r'(?i)credential', r'(?i)harvest'],
            'explicit': [r'(?i)explicit content patterns here'],
            'violence': [r'(?i)violence patterns here'],
        }
    
    def validate_input(self, content: str, context: dict[str, Any]) -> list[SecurityViolation]:
        """
        Validate input content for security violations
        
        Args:
            content: Input content to validate
            context: Context information (user_id, session_id, etc.)
            
        Returns:
            List of security violations found
        """
        violations = []
        
        # Check for prompt injection
        violations.extend(self._check_prompt_injection(content))
        
        # Check for sensitive data
        violations.extend(self._check_sensitive_data(content))
        
        # Check for blocked content
        violations.extend(self._check_blocked_content(content))
        
        # Check input length
        violations.extend(self._check_input_length(content))
        
        return violations
    
    def sanitize_input(self, content: str) -> str:
        """Sanitize input content"""
        # Remove potential injection markers
        sanitized = re.sub(r'\[INST\]|\[/INST\]', '', content, flags=re.IGNORECASE)
        sanitized = re.sub(r'<\|im_start\|>|<\|im_end\|>', '', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limit line breaks
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
        
        return sanitized
    
    def _check_prompt_injection(self, content: str) -> list[SecurityViolation]:
        """Check for prompt injection attempts"""
        violations = []
        
        for pattern in self.injection_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(SecurityViolation(
                    violation_type="prompt_injection",
                    threat_level=ThreatLevel.HIGH,
                    description=f"Potential prompt injection detected: {match.group()}",
                    content=content[max(0, match.start()-20):match.end()+20],
                    suggested_action="Block request or sanitize content",
                    metadata={"pattern": pattern, "position": match.start()}
                ))
        
        return violations
    
    def _check_sensitive_data(self, content: str) -> list[SecurityViolation]:
        """Check for sensitive data exposure"""
        violations = []
        
        for pattern in self.sensitive_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                violations.append(SecurityViolation(
                    violation_type="sensitive_data",
                    threat_level=ThreatLevel.MEDIUM,
                    description="Potential sensitive data detected",
                    content="[REDACTED]",  # Don't include actual sensitive data
                    suggested_action="Redact or block sensitive information",
                    metadata={"data_type": "pii", "position": match.start()}
                ))
        
        return violations
    
    def _check_blocked_content(self, content: str) -> list[SecurityViolation]:
        """Check for blocked content categories"""
        violations = []
        
        for category, patterns in self.blocked_categories.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    violations.append(SecurityViolation(
                        violation_type="blocked_content",
                        threat_level=ThreatLevel.HIGH,
                        description=f"Blocked content category: {category}",
                        content="[BLOCKED]",
                        suggested_action="Block request",
                        metadata={"category": category}
                    ))
        
        return violations
    
    def _check_input_length(self, content: str) -> list[SecurityViolation]:
        """Check for excessive input length"""
        violations = []
        
        max_length = 50000  # Configurable limit
        if len(content) > max_length:
            violations.append(SecurityViolation(
                violation_type="excessive_length",
                threat_level=ThreatLevel.MEDIUM,
                description=f"Input exceeds maximum length: {len(content)} > {max_length}",
                content=content[:100] + "...",
                suggested_action="Truncate or reject input",
                metadata={"length": len(content), "limit": max_length}
            ))
        
        return violations


class OutputFilter:
    """Filters and sanitizes AI outputs"""
    
    def __init__(self):
        # Patterns for sensitive information in outputs
        self.output_filters = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        ]
    
    def filter_output(self, content: str) -> str:
        """Filter potentially sensitive information from output"""
        filtered = content
        
        # Replace credit card numbers
        filtered = re.sub(
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            '[CREDIT_CARD_REDACTED]',
            filtered
        )
        
        # Replace SSNs
        filtered = re.sub(
            r'\b\d{3}-\d{2}-\d{4}\b',
            '[SSN_REDACTED]',
            filtered
        )
        
        # Replace email addresses
        filtered = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            filtered
        )
        
        return filtered


class SecurityAuditor:
    """Audit logging for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('sona.ai.security')
    
    def log_violation(self, violation: SecurityViolation, context: dict[str, Any]) -> None:
        """Log security violation"""
        self.logger.warning(
            f"Security violation: {violation.violation_type} "
            f"(threat_level: {violation.threat_level.value})",
            extra={
                'violation_type': violation.violation_type,
                'threat_level': violation.threat_level.value,
                'description': violation.description,
                'user_id': context.get('user_id'),
                'session_id': context.get('session_id'),
                'timestamp': context.get('timestamp'),
                'metadata': violation.metadata
            }
        )
    
    def log_access(self, operation: str, user_id: str, allowed: bool) -> None:
        """Log access attempt"""
        level = logging.INFO if allowed else logging.WARNING
        self.logger.log(
            level,
            f"Access {'granted' if allowed else 'denied'} for operation: {operation}",
            extra={
                'operation': operation,
                'user_id': user_id,
                'allowed': allowed,
                'access_type': 'ai_operation'
            }
        )


class RoleBasedAccessControl:
    """Role-based access control for AI operations"""
    
    def __init__(self):
        self.roles = {
            'admin': {'*'},  # Full access
            'developer': {
                'generate', 'summarize', 'translate', 'analyze'
            },
            'user': {
                'generate', 'summarize'
            },
            'readonly': set()  # No AI operations
        }
        
        self.user_roles: dict[str, set[str]] = {}
    
    def assign_role(self, user_id: str, role: str) -> None:
        """Assign role to user"""
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}")
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        
        self.user_roles[user_id].add(role)
    
    def check_permission(self, user_id: str, operation: str) -> bool:
        """Check if user has permission for operation"""
        user_roles = self.user_roles.get(user_id, set())
        
        for role in user_roles:
            allowed_operations = self.roles.get(role, set())
            if '*' in allowed_operations or operation in allowed_operations:
                return True
        
        return False


class AISecurityManager:
    """
    Comprehensive AI security management
    
    Provides enterprise-grade security for AI operations:
    - Input validation and sanitization
    - Output filtering and data loss prevention
    - Threat detection and response
    - Access control and audit logging
    """
    
    def __init__(self, policy: SecurityPolicy = SecurityPolicy.MODERATE):
        self.policy = policy
        self.input_validator = InputValidator()
        self.output_filter = OutputFilter()
        self.auditor = SecurityAuditor()
        self.rbac = RoleBasedAccessControl()
        
        # Security metrics
        self.metrics = {
            'violations_detected': 0,
            'requests_blocked': 0,
            'outputs_filtered': 0,
            'access_denied': 0
        }
    
    def validate_request(self, content: str, operation: str, 
                        user_id: str, context: dict[str, Any]) -> bool:
        """
        Validate AI request for security compliance
        
        Args:
            content: Request content to validate
            operation: AI operation being requested
            user_id: User making the request
            context: Additional context information
            
        Returns:
            True if request is allowed, False otherwise
            
        Raises:
            AISecurityError: If security violation is detected
        """
        # Check RBAC permissions
        if not self.rbac.check_permission(user_id, operation):
            self.metrics['access_denied'] += 1
            self.auditor.log_access(operation, user_id, False)
            raise AISecurityError(f"Access denied for operation: {operation}")
        
        self.auditor.log_access(operation, user_id, True)
        
        # Validate input content
        violations = self.input_validator.validate_input(content, context)
        
        if violations:
            self.metrics['violations_detected'] += len(violations)
            
            # Log all violations
            for violation in violations:
                self.auditor.log_violation(violation, context)
            
            # Determine action based on policy and threat level
            critical_violations = [
                v for v in violations 
                if v.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
            ]
            
            if critical_violations and self.policy == SecurityPolicy.STRICT:
                self.metrics['requests_blocked'] += 1
                raise AISecurityError(
                    f"Request blocked due to security violations: "
                    f"{[v.violation_type for v in critical_violations]}"
                )
        
        return True
    
    def filter_response(self, content: str) -> str:
        """Filter AI response for sensitive information"""
        filtered_content = self.output_filter.filter_output(content)
        
        if filtered_content != content:
            self.metrics['outputs_filtered'] += 1
        
        return filtered_content
    
    def sanitize_input(self, content: str) -> str:
        """Sanitize input content"""
        return self.input_validator.sanitize_input(content)
    
    def get_security_metrics(self) -> dict[str, Any]:
        """Get security metrics"""
        return dict(self.metrics)
    
    def configure_policy(self, policy: SecurityPolicy) -> None:
        """Configure security policy"""
        self.policy = policy


# Global security manager instance
_global_security: AISecurityManager | None = None


def get_global_security() -> AISecurityManager:
    """Get or create global AI security manager instance"""
    global _global_security
    if _global_security is None:
        _global_security = AISecurityManager()
    return _global_security
