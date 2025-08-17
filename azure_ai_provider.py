#!/usr/bin/env python3
"""
REAL Azure OpenAI Provider Implementation for Sona
==================================================

NO MORE MOCKS - This connects to actual Azure OpenAI APIs
Provides real AI code completion, explanation, and debugging assistance.
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from openai import AzureOpenAI

# Load environment variables from .env file if available (fallback only)
try:
    from dotenv import load_dotenv
    load_dotenv()  # This loads variables from .env file (deprecated for repo use)
    print("[OK] Loaded environment variables from .env file (fallback)")
except ImportError:
    # Don't require python-dotenv; prefer user-level config
    pass

# User-level configuration stored at ~/.sona/config.json (Windows: %USERPROFILE%/.sona/config.json)
import json
from pathlib import Path


def _get_user_config_path() -> Path:
    home = Path.home()
    cfg_dir = home / ".sona"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"


def _load_user_config() -> dict:
    path = _get_user_config_path()
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_user_config(config: dict) -> None:
    path = _get_user_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


# Expose user config for the module
USER_CONFIG_PATH = _get_user_config_path()
USER_CONFIG = _load_user_config()


@dataclass
class AIResponse:
    """Real AI response structure"""
    content: str
    model: str
    usage: Dict[str, int]
    latency_ms: float
    cached: bool = False
    error: Optional[str] = None


class AzureAIProvider:
    """REAL Azure OpenAI Provider - NO MOCKS"""
    
    def __init__(self):
        """Initialize with real Azure OpenAI configuration"""
        self.client = None
        self.api_key = None
        self.endpoint = None
        self.deployment_name = None
        self.api_version = "2024-02-15-preview"
        self.cache = {}  # Simple response cache
        self.stats = {
            "requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_tokens": 0
        }
        
        # Load user config (preferred) into runtime
        self.user_config = USER_CONFIG
        
        # Try to initialize Azure OpenAI
        self._initialize_azure_client()
    
    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client with real credentials"""
        try:
            # Prefer user-level config stored in ~/.sona/config.json
            self.api_key = self.user_config.get('AZURE_OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
            self.endpoint = self.user_config.get('AZURE_OPENAI_ENDPOINT') or os.getenv('AZURE_OPENAI_ENDPOINT')
            self.deployment_name = self.user_config.get('AZURE_OPENAI_DEPLOYMENT_NAME') or os.getenv(
                'AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4'
            )
            
            if not self.api_key or not self.endpoint:
                print("⚠️  Azure OpenAI credentials not found in user config or environment variables")
                print("   Run: sona setup --provider azure")
                return False
                
            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            
            print("[OK] Azure OpenAI client initialized successfully")
            print(f"   Endpoint: {self.endpoint}")
            print(f"   Deployment: {self.deployment_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Azure OpenAI client: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Azure OpenAI is available"""
        return self.client is not None
    
    async def ai_complete(
        self, code_context: str, cursor_position: int = 0
    ) -> AIResponse:
        """REAL AI code completion using Azure OpenAI"""
        if not self.is_available():
            return AIResponse(
                content="Error: Azure OpenAI not available",
                model="none",
                usage={},
                latency_ms=0,
                error="Azure OpenAI client not initialized"
            )
        
        # Check cache first
        cache_key = f"complete:{hash(code_context)}:{cursor_position}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            cached_response = self.cache[cache_key]
            cached_response.cached = True
            return cached_response
        
        start_time = time.perf_counter()
        
        try:
            # Prepare completion prompt
            prompt = f"""You are an AI coding assistant for the Sona programming language. 
Complete the following code. Provide only the completion, no explanations:

Code context:
{code_context}

Cursor position: {cursor_position}

Complete this code with proper Sona syntax:"""

            # Make REAL API call to Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a Sona programming language expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            # Extract real response
            completion = response.choices[0].message.content.strip()
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Create response
            ai_response = AIResponse(
                content=completion,
                model=self.deployment_name,
                usage=usage,
                latency_ms=latency_ms,
                cached=False
            )
            
            # Cache the response
            self.cache[cache_key] = ai_response
            
            # Update stats
            self.stats["requests"] += 1
            self.stats["total_tokens"] += usage["total_tokens"]
            
            return ai_response
            
        except Exception as e:
            self.stats["errors"] += 1
            return AIResponse(
                content=f"Error: {str(e)}",
                model=self.deployment_name,
                usage={},
                latency_ms=(time.perf_counter() - start_time) * 1000,
                error=str(e)
            )
    
    async def ai_explain(self, code_snippet: str, level: str = "intermediate") -> AIResponse:
        """REAL AI code explanation using Azure OpenAI"""
        if not self.is_available():
            return AIResponse(
                content="Error: Azure OpenAI not available",
                model="none",
                usage={},
                latency_ms=0,
                error="Azure OpenAI client not initialized"
            )
        
        # Check cache
        cache_key = f"explain:{hash(code_snippet)}:{level}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            cached_response = self.cache[cache_key]
            cached_response.cached = True
            return cached_response
        
        start_time = time.perf_counter()
        
        try:
            # Prepare explanation prompt
            prompt = f"""Explain this Sona programming language code for a {level} developer.
Be clear, concise, and educational:

Code:
{code_snippet}

Provide a clear explanation of what this code does, how it works, and any important concepts."""

            # Make REAL API call
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert programming educator specializing in the Sona language."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.5
            )
            
            explanation = response.choices[0].message.content.strip()
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            ai_response = AIResponse(
                content=explanation,
                model=self.deployment_name,
                usage=usage,
                latency_ms=latency_ms,
                cached=False
            )
            
            # Cache and update stats
            self.cache[cache_key] = ai_response
            self.stats["requests"] += 1
            self.stats["total_tokens"] += usage["total_tokens"]
            
            return ai_response
            
        except Exception as e:
            self.stats["errors"] += 1
            return AIResponse(
                content=f"Error: {str(e)}",
                model=self.deployment_name,
                usage={},
                latency_ms=(time.perf_counter() - start_time) * 1000,
                error=str(e)
            )
    
    async def ai_debug(self, error_context: str, code_snippet: str) -> AIResponse:
        """REAL AI debugging assistance using Azure OpenAI"""
        if not self.is_available():
            return AIResponse(
                content="Error: Azure OpenAI not available",
                model="none",
                usage={},
                latency_ms=0,
                error="Azure OpenAI client not initialized"
            )
        
        # Check cache
        cache_key = f"debug:{hash(error_context + code_snippet)}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            cached_response = self.cache[cache_key]
            cached_response.cached = True
            return cached_response
        
        start_time = time.perf_counter()
        
        try:
            # Prepare debugging prompt
            prompt = f"""Help debug this Sona programming language code. 
Analyze the error and provide specific, actionable solutions:

Error/Context:
{error_context}

Code:
{code_snippet}

Provide:
1. What's causing the error
2. How to fix it
3. Best practices to prevent similar issues"""

            # Make REAL API call
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert Sona programming language debugger."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            debug_help = response.choices[0].message.content.strip()
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            ai_response = AIResponse(
                content=debug_help,
                model=self.deployment_name,
                usage=usage,
                latency_ms=latency_ms,
                cached=False
            )
            
            # Cache and update stats
            self.cache[cache_key] = ai_response
            self.stats["requests"] += 1
            self.stats["total_tokens"] += usage["total_tokens"]
            
            return ai_response
            
        except Exception as e:
            self.stats["errors"] += 1
            return AIResponse(
                content=f"Error: {str(e)}",
                model=self.deployment_name,
                usage={},
                latency_ms=(time.perf_counter() - start_time) * 1000,
                error=str(e)
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get real usage statistics"""
        cache_hit_rate = 0
        if self.stats["requests"] > 0:
            cache_hit_rate = (self.stats["cache_hits"] / 
                            (self.stats["requests"] + self.stats["cache_hits"])) * 100
        
        return {
            "provider": "Azure OpenAI",
            "endpoint": self.endpoint,
            "deployment": self.deployment_name,
            "available": self.is_available(),
            "requests": self.stats["requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "errors": self.stats["errors"],
            "total_tokens": self.stats["total_tokens"],
            "cached_responses": len(self.cache)
        }
    
    def clear_cache(self):
        """Clear response cache"""
        self.cache.clear()
        print("✅ AI response cache cleared")


# Global instance
azure_ai = AzureAIProvider()


# Convenience functions for easy use
async def ai_complete(code_context: str, cursor_position: int = 0) -> str:
    """REAL AI code completion - public API"""
    response = await azure_ai.ai_complete(code_context, cursor_position)
    if response.error:
        return f"AI Error: {response.error}"
    return response.content


async def ai_explain(code_snippet: str, level: str = "intermediate") -> str:
    """REAL AI code explanation - public API"""
    response = await azure_ai.ai_explain(code_snippet, level)
    if response.error:
        return f"AI Error: {response.error}"
    return response.content


async def ai_debug(error_context: str, code_snippet: str) -> str:
    """REAL AI debugging assistance - public API"""
    response = await azure_ai.ai_debug(error_context, code_snippet)
    if response.error:
        return f"AI Error: {response.error}"
    return response.content


def ai_stats() -> Dict[str, Any]:
    """Get AI usage statistics"""
    return azure_ai.get_stats()


if __name__ == "__main__":
    # Test the Azure AI provider
    import asyncio
    
    async def test_azure_ai():
        print("🧪 Testing REAL Azure OpenAI Integration")
        print("=" * 50)
        
        # Test initialization
        if not azure_ai.is_available():
            print("❌ Azure OpenAI not available - check credentials")
            print("\nRequired environment variables:")
            print("  AZURE_OPENAI_API_KEY")
            print("  AZURE_OPENAI_ENDPOINT")
            print("  AZURE_OPENAI_DEPLOYMENT_NAME")
            return
        
        print("✅ Azure OpenAI client initialized")
        print(f"Stats: {azure_ai.get_stats()}")
        
        # Test AI completion
        print("\n🤖 Testing AI code completion...")
        test_code = """
def process_data(data):
    # TODO: implement data processing
"""
        completion = await ai_complete(test_code, 45)
        print(f"Completion: {completion[:100]}...")
        
        # Test AI explanation
        print("\n📚 Testing AI code explanation...")
        test_snippet = "for item in data: result.append(transform(item))"
        explanation = await ai_explain(test_snippet, "beginner")
        print(f"Explanation: {explanation[:100]}...")
        
        # Test AI debugging
        print("\n🐛 Testing AI debugging...")
        error_context = "IndexError: list index out of range"
        debug_help = await ai_debug(error_context, test_snippet)
        print(f"Debug help: {debug_help[:100]}...")
        
        # Final stats
        print(f"\n📊 Final stats: {azure_ai.get_stats()}")
        print("\n✅ Azure AI provider test complete!")
    
    asyncio.run(test_azure_ai())
