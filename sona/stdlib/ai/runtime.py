"""
AI Runtime System - Enterprise Grade
===================================

Central runtime for AI operations with provider abstraction,
policy enforcement, and comprehensive monitoring.

Features:
- Provider abstraction (OpenAI, Azure, local models)
- Policy-based access control
- Request/response logging
- Rate limiting and quota management
- Circuit breaker pattern for resilience
- Metrics collection and monitoring
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .cache import get_global_cache
from .errors import (
    AIPolicyError,
    AIProviderError,
    AIQuotaError,
    AIRuntimeError,
)


class ProviderType(Enum):
    """Supported AI provider types"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    LOCAL_MODEL = "local_model"
    HUGGINGFACE = "huggingface"


@dataclass
class AIRequest:
    """Represents an AI operation request"""
    operation: str
    prompt: str
    model: str
    provider: ProviderType
    parameters: dict[str, Any]
    context: dict[str, Any]
    user_id: str | None = None
    session_id: str | None = None


@dataclass
class AIResponse:
    """Represents an AI operation response"""
    content: str
    metadata: dict[str, Any]
    usage: dict[str, Any]
    provider: ProviderType
    model: str
    latency_ms: float
    cached: bool = False


class PolicyEngine:
    """Policy enforcement for AI operations"""
    
    def __init__(self):
        self.policies = {
            'max_prompt_length': 10000,
            'allowed_models': [],
            'allowed_operations': [],
            'rate_limit_per_minute': 60,
            'max_tokens_per_request': 4000,
            'content_filters': []
        }
        self._rate_limits = {}
    
    def validate_request(self, request: AIRequest) -> bool:
        """Validate request against policies"""
        # Check prompt length
        if len(request.prompt) > self.policies['max_prompt_length']:
            raise AIPolicyError(
                "max_prompt_length",
                f"Prompt exceeds maximum length: {len(request.prompt)}"
            )
        
        # Check allowed models
        if (self.policies['allowed_models'] and
                request.model not in self.policies['allowed_models']):
            raise AIPolicyError("allowed_models", f"Model not allowed: {request.model}")
        
        # Check allowed operations
        if (self.policies['allowed_operations'] and
                request.operation not in self.policies['allowed_operations']):
            raise AIPolicyError("allowed_operations", f"Operation not allowed: {request.operation}")
        
        # Check rate limits
        self._check_rate_limit(request.user_id or 'anonymous')
        
        return True
    
    def _check_rate_limit(self, user_id: str) -> None:
        """Check rate limits for user"""
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = {}
        
        user_limits = self._rate_limits[user_id]
        
        # Clean old windows
        old_windows = [w for w in user_limits.keys() if w < minute_window - 1]
        for window in old_windows:
            del user_limits[window]
        
        # Check current window
        current_count = user_limits.get(minute_window, 0)
        if current_count >= self.policies['rate_limit_per_minute']:
            raise AIQuotaError(f"Rate limit exceeded for user: {user_id}")
        
        # Increment counter
        user_limits[minute_window] = current_count + 1


class CircuitBreaker:
    """Circuit breaker for AI provider resilience"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise AIProviderError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class AIProvider:
    """Base class for AI providers"""
    
    def __init__(self, provider_type: ProviderType, config: dict[str, Any]):
        self.provider_type = provider_type
        self.config = config
        self.circuit_breaker = CircuitBreaker()
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate AI response"""
        raise NotImplementedError("Subclasses must implement generate")
    
    def get_available_models(self) -> list[str]:
        """Get list of available models"""
        raise NotImplementedError("Subclasses must implement get_available_models")


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(ProviderType.OPENAI, config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
    
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using OpenAI API"""
        start_time = time.time()
        
        try:
            # Simulate API call (actual implementation would use openai client)
            await asyncio.sleep(0.1)  # Simulate network latency
            
            response_content = f"Generated response for: {request.prompt[:50]}..."
            usage = {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
            
            return AIResponse(
                content=response_content,
                metadata={'model_version': request.model},
                usage=usage,
                provider=self.provider_type,
                model=request.model,
                latency_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            raise AIProviderError(f"OpenAI API error: {str(e)}")
    
    def get_available_models(self) -> list[str]:
        """Get OpenAI models"""
        return ['gpt-4', 'gpt-3.5-turbo', 'text-davinci-003']


class AIRuntime:
    """
    Central AI runtime system
    
    Manages AI operations with enterprise features:
    - Provider abstraction and routing
    - Policy enforcement and access control
    - Caching and performance optimization
    - Comprehensive logging and monitoring
    """
    
    def __init__(self):
        self.providers: dict[ProviderType, AIProvider] = {}
        self.policy_engine = PolicyEngine()
        self.cache = get_global_cache()
        self.logger = logging.getLogger('sona.ai.runtime')
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'total_latency_ms': 0
        }
    
    def register_provider(self, provider: AIProvider) -> None:
        """Register an AI provider"""
        self.providers[provider.provider_type] = provider
        self.logger.info(f"Registered provider: {provider.provider_type.value}")
    
    async def execute(self, request: AIRequest) -> AIResponse:
        """
        Execute AI operation with full enterprise pipeline
        
        Args:
            request: AI operation request
            
        Returns:
            AI response with metadata
        """
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            # Validate request against policies
            self.policy_engine.validate_request(request)
            
            # Check cache first
            cache_key = self.cache.generate_key(
                operation=request.operation,
                prompt=request.prompt,
                model_config={'model': request.model, **request.parameters},
                inputs=request.context
            )
            
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                self.metrics['cache_hits'] += 1
                self.logger.info(f"Cache hit for operation: {request.operation}")
                
                # Create response from cached data
                if isinstance(cached_result, dict):
                    # Convert provider string back to enum
                    if 'provider' in cached_result and isinstance(cached_result['provider'], str):
                        cached_result['provider'] = ProviderType(cached_result['provider'])
                    response = AIResponse(**cached_result)
                else:
                    # Handle case where cached_result is already an object
                    response = cached_result
                response.cached = True
                return response
            
            self.metrics['cache_misses'] += 1
            
            # Execute with provider
            provider = self.providers.get(request.provider)
            if not provider:
                raise AIProviderError(f"Provider not available: {request.provider}")
            
            response = await provider.circuit_breaker.call(
                provider.generate, request
            )
            
            # Cache the result - convert response to dict format
            cache_data = {
                'content': response.content,
                'metadata': response.metadata,
                'usage': response.usage,
                'provider': response.provider.value,  # Convert enum to string
                'model': response.model,
                'latency_ms': response.latency_ms,
                'cached': False
            }
            
            self.cache.put(
                key=cache_key,
                value=cache_data,
                metadata={
                    'operation': request.operation,
                    'provider': request.provider.value,
                    'model': request.model,
                    'user_id': request.user_id,
                    'timestamp': time.time()
                }
            )
            
            # Update metrics
            self.metrics['total_latency_ms'] += response.latency_ms
            
            self.logger.info(
                f"AI operation completed: {request.operation} "
                f"(provider: {request.provider.value}, "
                f"latency: {response.latency_ms:.1f}ms)"
            )
            
            return response
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.logger.error(f"AI operation failed: {str(e)}")
            raise AIRuntimeError("execute", f"Failed to execute AI operation: {str(e)}")
    
    def get_metrics(self) -> dict[str, Any]:
        """Get runtime metrics"""
        total_requests = self.metrics['total_requests']
        avg_latency = (
            self.metrics['total_latency_ms'] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            **self.metrics,
            'average_latency_ms': round(avg_latency, 2),
            'cache_hit_rate': (
                self.metrics['cache_hits'] / 
                (self.metrics['cache_hits'] + self.metrics['cache_misses']) * 100
                if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 
                else 0
            ),
            'error_rate': (
                self.metrics['errors'] / total_requests * 100 
                if total_requests > 0 else 0
            )
        }
    
    def configure_policy(self, policy_name: str, value: Any) -> None:
        """Configure runtime policy"""
        if policy_name in self.policy_engine.policies:
            self.policy_engine.policies[policy_name] = value
            self.logger.info(f"Updated policy {policy_name}: {value}")
        else:
            raise ValueError(f"Unknown policy: {policy_name}")


# Global runtime instance
_global_runtime: AIRuntime | None = None


def get_global_runtime() -> AIRuntime:
    """Get or create global AI runtime instance"""
    global _global_runtime
    if _global_runtime is None:
        _global_runtime = AIRuntime()
    return _global_runtime
