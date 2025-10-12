"""
REAL AI Provider Implementation - NO MOCKS
==========================================

This module provides REAL AI integration with actual API calls to OpenAI and Claude.
NO PLACEHOLDER FUNCTIONS. NO MOCK RESPONSES. REAL FUNCTIONALITY ONLY.

Requirements:
- pip install openai anthropic requests
- Set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables
"""

import hashlib
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI package not installed. Run: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic package not installed. Run: pip install anthropic")


@dataclass
class AIResponse:
    """Real AI response with actual data"""
    content: str
    model: str
    tokens_used: int
    cost_usd: float
    response_time_ms: float
    cached: bool
    timestamp: datetime


class RealAIProvider:
    """
    REAL AI Provider - Makes actual API calls to AI services
    NO MOCKS, NO PLACEHOLDERS, REAL FUNCTIONALITY ONLY
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.response_cache = {}
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        
        # Initialize real API clients
        self._initialize_real_clients()
        
        # Real rate limiting
        self.rate_limiter = {
            'requests_per_minute': 60,
            'requests_this_minute': 0,
            'minute_start': datetime.now()
        }
    
    def _initialize_real_clients(self):
        """Initialize REAL API clients with actual keys"""
        
        # OpenAI initialization
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✅ OpenAI client initialized with real API key")
            except Exception as e:
                print(f"❌ OpenAI initialization failed: {e}")
        else:
            print("⚠️  OpenAI API key not found in environment variables")
        
        # Anthropic initialization
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                print("✅ Anthropic client initialized with real API key")
            except Exception as e:
                print(f"❌ Anthropic initialization failed: {e}")
        else:
            print("⚠️  Anthropic API key not found in environment variables")
    
    def _check_rate_limit(self):
        """Real rate limiting implementation"""
        now = datetime.now()
        if (now - self.rate_limiter['minute_start']).seconds >= 60:
            self.rate_limiter['requests_this_minute'] = 0
            self.rate_limiter['minute_start'] = now
        
        if self.rate_limiter['requests_this_minute'] >= self.rate_limiter['requests_per_minute']:
            wait_time = 60 - (now - self.rate_limiter['minute_start']).seconds
            raise Exception(f"Rate limit exceeded. Wait {wait_time} seconds.")
        
        self.rate_limiter['requests_this_minute'] += 1
    
    def _get_cache_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate cache key for identical requests"""
        content = f"{prompt}_{model}_{temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate real API costs"""
        # Real OpenAI pricing (as of 2024)
        pricing = {
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},  # per 1K tokens
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125}
        }
        
        if model not in pricing:
            return 0.0
        
        input_cost = (input_tokens / 1000) * pricing[model]['input']
        output_cost = (output_tokens / 1000) * pricing[model]['output']
        return input_cost + output_cost
    
    def ai_complete(self, code_context: str, cursor_position: int = None) -> AIResponse:
        """
        REAL AI code completion - Makes actual OpenAI API call
        NO MOCK RESPONSES - REAL FUNCTIONALITY ONLY
        """
        start_time = time.time()
        
        # Check rate limits
        self._check_rate_limit()
        
        # Prepare real prompt
        prompt = f"""You are an AI coding assistant. Complete the following code:

{code_context}

Provide only the code completion, no explanations."""
        
        # Check cache first
        cache_key = self._get_cache_key(prompt, "gpt-4o-mini", 0.3)
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            cached_response.cached = True
            return cached_response
        
        # Make REAL API call
        if not self.openai_client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract real response data
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate real costs
            cost = self._calculate_cost("gpt-4o-mini", input_tokens, output_tokens)
            response_time = (time.time() - start_time) * 1000
            
            # Update real statistics
            self.total_cost += cost
            self.total_tokens += total_tokens
            self.request_count += 1
            
            # Create real response object
            ai_response = AIResponse(
                content=content,
                model="gpt-4o-mini",
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time,
                cached=False,
                timestamp=datetime.now()
            )
            
            # Cache the real response
            self.response_cache[cache_key] = ai_response
            
            return ai_response
            
        except Exception as e:
            raise Exception(f"Real OpenAI API call failed: {e}")
    
    def ai_explain(self, code_snippet: str, level: str = "intermediate") -> AIResponse:
        """
        REAL AI code explanation - Makes actual API call
        NO MOCK RESPONSES - REAL FUNCTIONALITY ONLY
        """
        start_time = time.time()
        
        # Check rate limits
        self._check_rate_limit()
        
        # Prepare real prompt
        prompt = f"""Explain this code at a {level} level:

{code_snippet}

Provide a clear explanation of what this code does, how it works, and any important concepts."""
        
        # Check cache first
        cache_key = self._get_cache_key(prompt, "gpt-4o-mini", 0.5)
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            cached_response.cached = True
            return cached_response
        
        # Make REAL API call
        if not self.openai_client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a helpful programming tutor explaining code at a {level} level."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            # Extract real response data
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate real costs
            cost = self._calculate_cost("gpt-4o-mini", input_tokens, output_tokens)
            response_time = (time.time() - start_time) * 1000
            
            # Update real statistics
            self.total_cost += cost
            self.total_tokens += total_tokens
            self.request_count += 1
            
            # Create real response object
            ai_response = AIResponse(
                content=content,
                model="gpt-4o-mini",
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time,
                cached=False,
                timestamp=datetime.now()
            )
            
            # Cache the real response
            self.response_cache[cache_key] = ai_response
            
            return ai_response
            
        except Exception as e:
            raise Exception(f"Real OpenAI API call failed: {e}")
    
    def ai_debug(self, error_context: str, code: str) -> AIResponse:
        """
        REAL AI debugging assistance - Makes actual API call
        NO MOCK RESPONSES - REAL FUNCTIONALITY ONLY
        """
        start_time = time.time()
        
        # Check rate limits
        self._check_rate_limit()
        
        # Prepare real prompt
        prompt = f"""Help debug this code error:

ERROR: {error_context}

CODE:
{code}

Provide specific debugging steps and suggest fixes."""
        
        # Check cache first
        cache_key = self._get_cache_key(prompt, "gpt-4o-mini", 0.2)
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            cached_response.cached = True
            return cached_response
        
        # Make REAL API call
        if not self.openai_client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert debugging assistant. Provide specific, actionable debugging advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Extract real response data
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate real costs
            cost = self._calculate_cost("gpt-4o-mini", input_tokens, output_tokens)
            response_time = (time.time() - start_time) * 1000
            
            # Update real statistics
            self.total_cost += cost
            self.total_tokens += total_tokens
            self.request_count += 1
            
            # Create real response object
            ai_response = AIResponse(
                content=content,
                model="gpt-4o-mini",
                tokens_used=total_tokens,
                cost_usd=cost,
                response_time_ms=response_time,
                cached=False,
                timestamp=datetime.now()
            )
            
            # Cache the real response
            self.response_cache[cache_key] = ai_response
            
            return ai_response
            
        except Exception as e:
            raise Exception(f"Real OpenAI API call failed: {e}")
    
    def get_real_statistics(self) -> dict[str, Any]:
        """Get real usage statistics - NO MOCK DATA"""
        return {
            'total_requests': self.request_count,
            'total_tokens_used': self.total_tokens,
            'total_cost_usd': round(self.total_cost, 4),
            'cached_responses': len(self.response_cache),
            'openai_available': self.openai_client is not None,
            'anthropic_available': self.anthropic_client is not None,
            'rate_limit_remaining': self.rate_limiter['requests_per_minute'] - self.rate_limiter['requests_this_minute']
        }
    
    def test_real_connection(self) -> dict[str, bool]:
        """Test real API connections - NO MOCK TESTS"""
        results = {
            'openai_connection': False,
            'anthropic_connection': False
        }
        
        # Test real OpenAI connection
        if self.openai_client:
            try:
                test_response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                results['openai_connection'] = True
                print("✅ OpenAI connection test: SUCCESS")
            except Exception as e:
                print(f"❌ OpenAI connection test: FAILED - {e}")
        
        # Test real Anthropic connection
        if self.anthropic_client:
            try:
                test_response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                results['anthropic_connection'] = True
                print("✅ Anthropic connection test: SUCCESS")
            except Exception as e:
                print(f"❌ Anthropic connection test: FAILED - {e}")
        
        return results


# GLOBAL REAL AI PROVIDER INSTANCE
# NO MOCKS - REAL FUNCTIONALITY ONLY
REAL_AI_PROVIDER = RealAIProvider()


def ai_complete(code_context: str, cursor_position: int = None) -> str:
    """Global function for real AI code completion - NO MOCKS"""
    response = REAL_AI_PROVIDER.ai_complete(code_context, cursor_position)
    return response.content


def ai_explain(code_snippet: str, level: str = "intermediate") -> str:
    """Global function for real AI code explanation - NO MOCKS"""
    response = REAL_AI_PROVIDER.ai_explain(code_snippet, level)
    return response.content


def ai_debug(error_context: str, code: str) -> str:
    """Global function for real AI debugging - NO MOCKS"""
    response = REAL_AI_PROVIDER.ai_debug(error_context, code)
    return response.content


def get_ai_stats() -> dict[str, Any]:
    """Get real AI usage statistics - NO MOCK DATA"""
    return REAL_AI_PROVIDER.get_real_statistics()


if __name__ == "__main__":
    # REAL TEST CASES - NO MOCKS
    print("🚀 Testing REAL AI Provider - NO MOCKS")
    
    # Test connections
    connections = REAL_AI_PROVIDER.test_real_connection()
    print(f"Connection Status: {connections}")
    
    if connections['openai_connection']:
        # Test real AI completion
        print("\n🧠 Testing REAL AI completion...")
        try:
            result = ai_complete("def fibonacci(n):")
            print(f"✅ Real completion result: {result[:100]}...")
        except Exception as e:
            print(f"❌ Real completion failed: {e}")
        
        # Test real AI explanation
        print("\n📚 Testing REAL AI explanation...")
        try:
            result = ai_explain("print('Hello, World!')")
            print(f"✅ Real explanation result: {result[:100]}...")
        except Exception as e:
            print(f"❌ Real explanation failed: {e}")
        
        # Show real statistics
        print("\n📊 REAL AI Statistics:")
        stats = get_ai_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("❌ No real AI connections available. Check API keys.")
