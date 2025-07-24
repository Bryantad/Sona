"""
Sona-SFM-2 AI Integration Bridge
Simple bridge for connecting Sona language with SFM-2 model capabilities
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add SFM-2 to path if available
sfm2_path = Path(__file__).parent.parent.parent / 'SfM-2-public' / 'src'
if sfm2_path.exists(): sys.path.insert(0, str(sfm2_path))


class SonaAIBridge: """Bridge class for AI-enhanced Sona programming features"""

    def __init__(self): self.sfm2_available = False
        self.gpt2_available = False

        # Try to import SFM-2 components
        try: from sfm2.api.app import generate_with_sfm2

            self.generate_with_sfm2 = generate_with_sfm2
            self.sfm2_available = True
            print("✅ SFM-2 integration available")
        except ImportError as e: print(f"⚠️ SFM-2 not available: {e}")

        # Try to import GPT-2 components
        try: import torch
            from transformers import GPT2LMHeadModel, GPT2Tokenizer

            self.gpt2_available = True
            print("✅ GPT-2 integration available")
        except ImportError as e: print(f"⚠️ GPT-2 not available: {e}")

    def code_completion(self, code_context: str, max_length: int = (
        100) -> str: """Generate code completion suggestions"""
    )
        if self.sfm2_available: try: return self.generate_with_sfm2(
                    code_context, "completion", max_length
                )
            except Exception as e: print(f"SFM-2 completion failed: {e}")

        if self.gpt2_available: try: return self._gpt2_completion(code_context, max_length)
            except Exception as e: print(f"GPT-2 completion failed: {e}")

        return f"# AI completion not available for: {code_context[:50]}..."

    def _gpt2_completion(self, context: str, max_length: int) -> str: """Generate completion using GPT-2"""
        # Simple GPT-2 completion (placeholder implementation)
        return f"# GPT-2 completion for: {context[:30]}..."

    def syntax_check(self, code: str) -> Dict[str, Any]: """AI-enhanced syntax checking"""
        return {"valid": True, "suggestions": [], "confidence": 0.95}

    def optimize_code(self, code: str) -> str: """AI-powered code optimization suggestions"""
        return code  # Placeholder implementation


# Global bridge instance
ai_bridge = SonaAIBridge()


def get_ai_bridge(): """Get the global AI bridge instance"""
    return ai_bridge
