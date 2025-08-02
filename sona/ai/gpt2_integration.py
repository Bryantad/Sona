"""
GPT-2 Integration for Sona v0.8.2

Provides core GPT-2 model interface for AI-powered cognitive programming features.
Handles model loading, inference, and text generation for code completion and assistance.
"""

import os
import torch
from pathlib import Path
from typing import List, Optional, Dict, Any
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Import Sona language adapter
try:
    from .sona_language_adapter import get_sona_adapter
    SONA_ADAPTER_AVAILABLE = True
except ImportError:
    SONA_ADAPTER_AVAILABLE = False


class GPT2Integration:
    """Core GPT-2 integration for Sona AI features"""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize GPT-2 integration
        
        Args:
            model_path: Path to GPT-2 model directory. If None, uses default.
        """
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 1024
        self.is_loaded = False
        
    def _get_default_model_path(self) -> str:
        """Get default model path"""
        return str(Path(__file__).parent.parent.parent / "models" / "gpt2")
    
    def load_model(self) -> bool:
        """Load GPT-2 model and tokenizer
        
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        try:
            print(f"🤖 Loading GPT-2 model from {self.model_path}...")
            
            # Load tokenizer
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_path)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = GPT2LMHeadModel.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            print(f"✅ GPT-2 model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load GPT-2 model: {e}")
            return False
    
    def generate_completion(self, 
                          prompt: str, 
                          max_new_tokens: int = 50,
                          temperature: float = 0.7,
                          do_sample: bool = True,
                          num_return_sequences: int = 1) -> List[str]:
        """Generate text completion using GPT-2
        
        Args:
            prompt: Input text to complete
            max_new_tokens: Maximum number of new tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            do_sample: Whether to use sampling
            num_return_sequences: Number of completions to generate
            
        Returns:
            List of generated completions
        """
        if not self.is_loaded:
            if not self.load_model():
                return ["Error: Model not loaded"]
        
        try:
            # Encode input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            inputs = inputs.to(self.device)
            
            # Generate completion
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + max_new_tokens,
                    temperature=temperature,
                    do_sample=do_sample,
                    num_return_sequences=num_return_sequences,
                    pad_token_id=self.tokenizer.eos_token_id,
                    attention_mask=inputs.ne(self.tokenizer.pad_token_id)
                )
            
            # Decode outputs
            completions = []
            for output in outputs:
                completion = self.tokenizer.decode(output, skip_special_tokens=True)
                # Remove the original prompt from completion
                completion = completion[len(prompt):].strip()
                completions.append(completion)
                
            return completions
            
        except Exception as e:
            print(f"❌ Error generating completion: {e}")
            return [f"Error: {e}"]
    
    def generate_sona_completion(self, prompt: str, max_new_tokens: int = 50) -> str:
        """Generate Sona-specific code completion
        
        Args:
            prompt: Sona code prompt
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Sona code completion
        """
        # Use Sona adapter if available for better results
        if SONA_ADAPTER_AVAILABLE:
            try:
                adapter = get_sona_adapter(self)
                return adapter.complete_sona_code(prompt, max_new_tokens)
            except Exception as e:
                print(f"⚠️ Sona adapter failed, using base GPT-2: {e}")
        
        # Fallback to base completion
        completions = self.generate_completion(prompt, max_new_tokens)
        return completions[0] if completions else "// Completion not available"
        """Generate code completion specifically for programming context
        
        Args:
            code_context: Current code context
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated code completion
        """
        # Add programming-specific prompts to improve code generation
        enhanced_prompt = f"# Programming context:\n{code_context}"
        
        completions = self.generate_completion(
            enhanced_prompt,
            max_new_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for more deterministic code
            do_sample=True,
            num_return_sequences=1
        )
        
        if completions and completions[0]:
            # Clean up the completion for code context
            completion = completions[0]
            # Remove comment prefix if added
            if completion.startswith("# Programming context:\n"):
                completion = completion[len("# Programming context:\n"):]
            
            return completion.strip()
        
        return ""
    
    def generate_code_completion(self, code: str, max_new_tokens: int = 50) -> str:
        """Generate code completion for given code context
        
        Args:
            code: Code context to complete
            max_new_tokens: Maximum number of new tokens to generate
            
        Returns:
            Generated code completion
        """
        # Use Sona-specific completion if available
        if SONA_ADAPTER_AVAILABLE:
            adapter = get_sona_adapter(self)
            return adapter.complete_sona_code(code, max_new_tokens)
        
        # Fallback to general completion
        return self.generate_completion(
            f"Complete this code:\n{code}",
            max_new_tokens=max_new_tokens
        )
    
    def explain_code(self, code: str) -> str:
        """Generate natural language explanation of code
        
        Args:
            code: Code to explain
            
        Returns:
            Natural language explanation
        """
        prompt = f"Explain this code in simple terms:\n\n{code}\n\nExplanation:"
        
        explanations = self.generate_completion(
            prompt,
            max_new_tokens=100,
            temperature=0.5,
            do_sample=True,
            num_return_sequences=1
        )
        
        if explanations and explanations[0]:
            return explanations[0].strip()
        
        return "Unable to generate explanation."
    
    def suggest_improvements(self, code: str) -> str:
        """Suggest code improvements
        
        Args:
            code: Code to analyze
            
        Returns:
            Improvement suggestions
        """
        prompt = f"Suggest improvements for this code:\n\n{code}\n\nSuggestions:"
        
        suggestions = self.generate_completion(
            prompt,
            max_new_tokens=150,
            temperature=0.6,
            do_sample=True,
            num_return_sequences=1
        )
        
        if suggestions and suggestions[0]:
            return suggestions[0].strip()
        
        return "No suggestions available."
    
    def natural_language_to_code(self, description: str, language: str = "python") -> str:
        """Convert natural language description to code
        
        Args:
            description: Natural language description
            language: Target programming language
            
        Returns:
            Generated code
        """
        prompt = f"Convert this description to {language} code:\n\n{description}\n\nCode:\n"
        
        code_generations = self.generate_completion(
            prompt,
            max_new_tokens=100,
            temperature=0.4,
            do_sample=True,
            num_return_sequences=1
        )
        
        if code_generations and code_generations[0]:
            return code_generations[0].strip()
        
        return f"# Unable to generate {language} code for: {description}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_path": self.model_path,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "max_length": self.max_length,
            "vocab_size": self.tokenizer.vocab_size if self.tokenizer else None,
            "model_parameters": sum(p.numel() for p in self.model.parameters()) if self.model else None
        }
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        self.is_loaded = False
        
        # Clear GPU memory if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("✅ GPT-2 model unloaded")


# Global instance for easy access
_gpt2_instance = None


def get_gpt2_instance() -> GPT2Integration:
    """Get global GPT-2 instance (singleton pattern)"""
    global _gpt2_instance
    if _gpt2_instance is None:
        _gpt2_instance = GPT2Integration()
    return _gpt2_instance


def initialize_gpt2(model_path: Optional[str] = None) -> bool:
    """Initialize GPT-2 with optional custom model path"""
    global _gpt2_instance
    _gpt2_instance = GPT2Integration(model_path)
    return _gpt2_instance.load_model()


def cleanup_gpt2():
    """Cleanup GPT-2 instance"""
    global _gpt2_instance
    if _gpt2_instance:
        _gpt2_instance.unload_model()
        _gpt2_instance = None
