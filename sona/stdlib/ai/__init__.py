"""
Sona AI Standard Library
========================

Enterprise-grade AI integration for the Sona programming language.

Design Principles:
- Parser Purity: AI operations are explicitly declared at compile-time
- Explicit Surfaces: All AI interactions are visible and auditable
- Enterprise Guardrails: Comprehensive security, logging, and monitoring
- Performance First: Caching, batching, and optimization built-in

Features:
- Multi-provider AI integration (OpenAI, Azure, Anthropic, local models)
- Hash-based caching for reproducible results
- Comprehensive security and policy enforcement
- Structured logging and audit trails
- Performance monitoring and optimization
- Type-safe AI operations with schema validation

Usage:
    from sona.stdlib.ai import AIRuntime, AIRequest, ProviderType
    
    runtime = AIRuntime()
    request = AIRequest(
        operation="generate",
        prompt="Write a function to sort an array",
        model="gpt-4",
        provider=ProviderType.OPENAI,
        parameters={"temperature": 0.7}
    )
    
    response = await runtime.execute(request)
    print(response.content)
"""

# Import errors first (no dependencies)
# Import cache (depends only on errors)
from .cache import AICache, CacheEntry, get_global_cache
from .errors import (
    AICacheError,
    AIError,
    AIPolicyError,
    AIProviderError,
    AIQuotaError,
    AIRuntimeError,
    AISecurityError,
    AITimeoutError,
)

# Import logging (depends on errors)
from .logging import AILogEntry, AILogger, configure_logging, get_global_logger

# Import runtime (depends on all above)
from .runtime import (
    AIRequest,
    AIResponse,
    AIRuntime,
    OpenAIProvider,
    PolicyEngine,
    ProviderType,
    get_global_runtime,
)

# Import security (depends on errors)
from .security import (
    AISecurityManager,
    SecurityPolicy,
    SecurityViolation,
    ThreatLevel,
    get_global_security,
)


# Version information
__version__ = "1.0.0"
__author__ = "Sona Language Team"

# Global instances for convenience
runtime = get_global_runtime()
cache = get_global_cache()
security = get_global_security()
logger = get_global_logger()

# Public API
__all__ = [
    # Runtime components
    "AIRuntime", "AIRequest", "AIResponse", "ProviderType",
    "OpenAIProvider", "PolicyEngine",
    
    # Caching
    "AICache", "CacheEntry",
    
    # Security
    "AISecurityManager", "SecurityPolicy", "ThreatLevel", "SecurityViolation",
    
    # Logging
    "AILogger", "AILogEntry", "configure_logging",
    
    # Errors
    "AIError", "AIRuntimeError", "AIProviderError", "AIPolicyError",
    "AISecurityError", "AICacheError", "AITimeoutError", "AIQuotaError",
    
    # Global instances
    "runtime", "cache", "security", "logger",
    
    # Convenience functions
    "get_global_runtime", "get_global_cache", 
    "get_global_security", "get_global_logger"
]


# Convenience functions for common operations
async def generate(prompt: str, 
                  model: str = "gpt-4",
                  provider: ProviderType = ProviderType.OPENAI,
                  temperature: float = 0.7,
                  max_tokens: int = 1000,
                  user_id: str = None) -> str:
    """
    Generate AI response with sensible defaults
    
    Args:
        prompt: Input prompt
        model: AI model to use
        provider: AI provider
        temperature: Response randomness (0.0-1.0)
        max_tokens: Maximum response length
        user_id: User identifier for logging
        
    Returns:
        Generated response text
    """
    request = AIRequest(
        operation="generate",
        prompt=prompt,
        model=model,
        provider=provider,
        parameters={
            "temperature": temperature,
            "max_tokens": max_tokens
        },
        context={},
        user_id=user_id
    )
    
    response = await runtime.execute(request)
    return response.content


async def summarize(text: str,
                   max_length: int = 100,
                   model: str = "gpt-3.5-turbo",
                   user_id: str = None) -> str:
    """
    Summarize text with AI
    
    Args:
        text: Text to summarize
        max_length: Maximum summary length in words
        model: AI model to use
        user_id: User identifier for logging
        
    Returns:
        Generated summary
    """
    prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}"
    
    request = AIRequest(
        operation="summarize",
        prompt=prompt,
        model=model,
        provider=ProviderType.OPENAI,
        parameters={"temperature": 0.3, "max_tokens": max_length * 2},
        context={"original_length": len(text)},
        user_id=user_id
    )
    
    response = await runtime.execute(request)
    return response.content


def get_system_status() -> dict:
    """
    Get comprehensive system status
    
    Returns:
        Dictionary with runtime, cache, and security metrics
    """
    return {
        "runtime": runtime.get_metrics(),
        "cache": cache.get_stats(),
        "security": security.get_security_metrics(),
        "logging": logger.get_metrics()
    }
