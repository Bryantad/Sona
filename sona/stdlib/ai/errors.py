"""
AI Integration Error Classes - Enterprise Grade
==============================================

Comprehensive error hierarchy for AI operations with detailed context
and enterprise-ready error handling.
"""


class AIError(Exception):
    """Base class for all AI-related errors"""
    def __init__(self, message: str, context: dict = None, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.error_code = error_code or "AI_GENERIC_ERROR"
        
    def to_dict(self) -> dict:
        """Convert error to dictionary for logging/serialization"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context
        }


class AITimeoutError(AIError):
    """Raised when AI operations exceed timeout limits"""
    def __init__(self, operation: str, timeout_seconds: int, context: dict = None):
        message = f"AI operation '{operation}' timed out after {timeout_seconds}s"
        super().__init__(message, context, "AI_TIMEOUT")
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class AIPolicyError(AIError):
    """Raised when AI operations violate policy constraints"""
    def __init__(self, policy_name: str, violation_details: str, context: dict = None):
        message = f"Policy violation: {policy_name} - {violation_details}"
        super().__init__(message, context, "AI_POLICY_VIOLATION")
        self.policy_name = policy_name
        self.violation_details = violation_details


class AIQuotaExceededError(AIError):
    """Raised when AI operations exceed usage quotas"""
    def __init__(self, quota_type: str, current_usage: int, limit: int, context: dict = None):
        message = f"Quota exceeded: {quota_type} ({current_usage}/{limit})"
        super().__init__(message, context, "AI_QUOTA_EXCEEDED")
        self.quota_type = quota_type
        self.current_usage = current_usage
        self.limit = limit


class AISecurityError(AIError):
    """Raised when AI operations encounter security violations"""
    def __init__(self, security_issue: str, threat_level: str = "MEDIUM", context: dict = None):
        message = f"Security violation: {security_issue} (threat level: {threat_level})"
        super().__init__(message, context, "AI_SECURITY_VIOLATION")
        self.security_issue = security_issue
        self.threat_level = threat_level


class AINonDeterministicError(AIError):
    """Raised when AI operations produce non-reproducible results"""
    def __init__(self, operation: str, expected_hash: str, actual_hash: str, context: dict = None):
        message = f"Non-deterministic result in '{operation}': expected {expected_hash}, got {actual_hash}"
        super().__init__(message, context, "AI_NON_DETERMINISTIC")
        self.operation = operation
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash


class AIModelError(AIError):
    """Raised when AI model operations fail"""
    def __init__(self, model_name: str, operation: str, details: str, context: dict = None):
        message = f"Model error in {model_name} during {operation}: {details}"
        super().__init__(message, context, "AI_MODEL_ERROR")
        self.model_name = model_name
        self.operation = operation
        self.details = details


class AICacheError(AIError):
    """Raised when AI cache operations fail"""
    def __init__(self, cache_operation: str, details: str, context: dict = None):
        message = f"Cache error during {cache_operation}: {details}"
        super().__init__(message, context, "AI_CACHE_ERROR")
        self.cache_operation = cache_operation
        self.details = details


class AINetworkError(AIError):
    """Raised when AI network operations fail"""
    def __init__(self, endpoint: str, status_code: int = None, details: str = None, context: dict = None):
        message = f"Network error connecting to {endpoint}"
        if status_code:
            message += f" (HTTP {status_code})"
        if details:
            message += f": {details}"
        super().__init__(message, context, "AI_NETWORK_ERROR")
        self.endpoint = endpoint
        self.status_code = status_code
        self.details = details


class AIRuntimeError(AIError):
    """Raised when AI runtime operations fail"""
    def __init__(self, operation: str, details: str, context: dict = None):
        message = f"Runtime error during {operation}: {details}"
        super().__init__(message, context, "AI_RUNTIME_ERROR")
        self.operation = operation
        self.details = details


class AIProviderError(AIError):
    """Raised when AI provider operations fail"""
    def __init__(self, provider: str, details: str, context: dict = None):
        message = f"Provider error from {provider}: {details}"
        super().__init__(message, context, "AI_PROVIDER_ERROR")
        self.provider = provider
        self.details = details


class AIQuotaError(AIError):
    """Raised when AI quota is exceeded"""
    def __init__(self, details: str, context: dict = None):
        message = f"Quota error: {details}"
        super().__init__(message, context, "AI_QUOTA_ERROR")
        self.details = details


# Keep the original AIQuotaExceededError for backward compatibility
AIQuotaExceededError = AIQuotaError


# Error category mappings for enterprise monitoring
ERROR_CATEGORIES = {
    'TIMEOUT': [AITimeoutError],
    'POLICY': [AIPolicyError, AISecurityError],
    'QUOTA': [AIQuotaError, AIQuotaExceededError],
    'RELIABILITY': [AINonDeterministicError, AICacheError],
    'INFRASTRUCTURE': [AIModelError, AINetworkError, AIRuntimeError, AIProviderError],
    'GENERIC': [AIError]
}

# Severity levels for enterprise alerting
ERROR_SEVERITY = {
    AITimeoutError: 'LOW',
    AIPolicyError: 'HIGH',
    AIQuotaError: 'MEDIUM',
    AIQuotaExceededError: 'MEDIUM',
    AISecurityError: 'CRITICAL',
    AINonDeterministicError: 'HIGH',
    AIModelError: 'MEDIUM',
    AICacheError: 'LOW',
    AINetworkError: 'MEDIUM',
    AIRuntimeError: 'HIGH',
    AIProviderError: 'MEDIUM',
    AIError: 'LOW'
}
