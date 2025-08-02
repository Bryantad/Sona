"""
Sona-Specific GPT-2 Integration

This module integrates the fine-tuned Sona GPT-2 model into the Sona AI system,
replacing the base GPT-2 with our Sona-trained version.
"""

import torch
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SonaSpecializedGPT2:
    """Sona-specialized GPT-2 model interface"""
    
    def __init__(self, model_path: str = "./sona_gpt2_finetuned"):
        self.model_path = Path(model_path)
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.loaded = False
        
    def load_model(self) -> bool:
        """Load the fine-tuned Sona GPT-2 model"""
        if not TRANSFORMERS_AVAILABLE:
            print("⚠️ Transformers not available")
            return False
        
        try:
            print("🤖 Loading Sona-specialized GPT-2 model...")
            
            # Check if fine-tuned model exists
            if not self.model_path.exists():
                print(f"⚠️ Fine-tuned model not found at {self.model_path}")
                print("   Using base GPT-2 model instead")
                self.model_path = "gpt2"
            
            # Load model and tokenizer
            self.tokenizer = GPT2Tokenizer.from_pretrained(str(self.model_path))
            self.model = GPT2LMHeadModel.from_pretrained(str(self.model_path))
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.loaded = True
            print(f"   ✅ Sona GPT-2 model loaded on {self.device}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load Sona GPT-2 model: {e}")
            return False
    
    def generate_sona_completion(self, prompt: str, max_length: int = 50, 
                                temperature: float = 0.8) -> str:
        """Generate Sona code completion"""
        if not self.loaded:
            if not self.load_model():
                return "# Model not available"
        
        try:
            # Add Sona context markers
            sona_prompt = f"<|sona_code|>{prompt}"
            
            # Tokenize
            inputs = self.tokenizer(sona_prompt, return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    max_length=inputs['input_ids'].shape[1] + max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode and extract completion
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            completion = generated_text[len(sona_prompt):]
            
            # Clean up completion
            completion = self.clean_completion(completion)
            
            return completion
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return "# Generation failed"
    
    def clean_completion(self, text: str) -> str:
        """Clean up generated completion"""
        # Remove unwanted tokens
        text = text.replace('<|endoftext|>', '')
        text = text.replace('<|startoftext|>', '')
        
        # Stop at natural endpoints
        for stop_token in ['\n\n\n', '---', '# Example:', '## Example:']:
            if stop_token in text:
                text = text.split(stop_token)[0]
        
        # Clean up whitespace
        text = text.strip()
        
        return text
    
    def explain_sona_code(self, code: str, style: str = "simple") -> str:
        """Generate explanation for Sona code"""
        prompts = {
            "simple": f"Explain this Sona code simply:\n{code}\nExplanation:",
            "detailed": f"Provide detailed explanation of this Sona code:\n{code}\nDetailed explanation:",
            "cognitive": f"Explain this Sona code for neurodivergent programmers:\n{code}\nCognitive-friendly explanation:"
        }
        
        prompt = prompts.get(style, prompts["simple"])
        explanation = self.generate_sona_completion(prompt, max_length=100, temperature=0.7)
        
        return explanation
    
    def suggest_sona_improvements(self, code: str) -> List[str]:
        """Suggest improvements for Sona code"""
        prompt = f"Suggest improvements for this Sona code:\n{code}\nSuggestions:\n1."
        
        suggestions_text = self.generate_sona_completion(prompt, max_length=150, temperature=0.8)
        
        # Parse suggestions
        suggestions = []
        lines = suggestions_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*'))):
                # Clean up the suggestion
                suggestion = line.lstrip('12345.-* ')
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def generate_sona_function(self, description: str) -> str:
        """Generate Sona function from description"""
        prompt = f"Create a Sona function that {description}:\n\nfunc "
        
        function_code = self.generate_sona_completion(prompt, max_length=80, temperature=0.7)
        
        return f"func {function_code}"
    
    def complete_cognitive_pattern(self, pattern_start: str) -> str:
        """Complete Sona cognitive programming patterns"""
        cognitive_prompts = {
            "thinking(": "thinking(",
            "remember(": "remember(",
            "focus_mode(": "focus_mode(",
            "working_memory": "working_memory {",
            "encompasses:": "encompasses: [",
            "visual_metaphor:": 'visual_metaphor: "'
        }
        
        # Use specialized prompt for cognitive patterns
        prompt = f"<|cognitive|>{pattern_start}"
        completion = self.generate_sona_completion(prompt, max_length=30, temperature=0.6)
        
        return completion
    
    def get_sona_examples(self, topic: str) -> List[str]:
        """Get Sona code examples for a specific topic"""
        prompt = f"Show Sona code examples for {topic}:\n\nExample 1:\n"
        
        examples_text = self.generate_sona_completion(prompt, max_length=200, temperature=0.8)
        
        # Parse examples
        examples = []
        current_example = ""
        
        for line in examples_text.split('\n'):
            if line.strip().startswith(('Example', 'example', '#')):
                if current_example.strip():
                    examples.append(current_example.strip())
                current_example = ""
            else:
                current_example += line + '\n'
        
        if current_example.strip():
            examples.append(current_example.strip())
        
        return examples[:2]  # Return top 2 examples


# Global instance for the Sona AI system
_sona_gpt2_instance = None

def get_sona_gpt2_instance() -> SonaSpecializedGPT2:
    """Get the singleton Sona GPT-2 instance"""
    global _sona_gpt2_instance
    
    if _sona_gpt2_instance is None:
        _sona_gpt2_instance = SonaSpecializedGPT2()
    
    return _sona_gpt2_instance


def test_sona_gpt2():
    """Test the Sona-specialized GPT-2 model"""
    print("🧪 Testing Sona-specialized GPT-2...")
    
    sona_gpt2 = get_sona_gpt2_instance()
    
    if not sona_gpt2.load_model():
        print("❌ Failed to load model")
        return
    
    # Test different capabilities
    tests = [
        {
            'name': 'Code Completion',
            'func': lambda: sona_gpt2.generate_sona_completion("func calculate_"),
            'expected_contains': ['func', 'calculate']
        },
        {
            'name': 'Cognitive Pattern',
            'func': lambda: sona_gpt2.complete_cognitive_pattern("thinking("),
            'expected_contains': ['thinking']
        },
        {
            'name': 'Code Explanation',
            'func': lambda: sona_gpt2.explain_sona_code("let x = 5\nprint(x)"),
            'expected_contains': ['variable', 'print']
        },
        {
            'name': 'Function Generation',
            'func': lambda: sona_gpt2.generate_sona_function("adds two numbers"),
            'expected_contains': ['func', 'add']
        }
    ]
    
    results = {}
    
    for test in tests:
        try:
            print(f"   Testing {test['name']}...")
            result = test['func']()
            
            # Check if result contains expected elements
            success = any(expected in result.lower() for expected in test['expected_contains'])
            
            print(f"   {'✅' if success else '⚠️'} {test['name']}: '{result[:50]}...'")
            results[test['name']] = success
            
        except Exception as e:
            print(f"   ❌ {test['name']} failed: {e}")
            results[test['name']] = False
    
    # Summary
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n📊 Sona GPT-2 Test Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    test_sona_gpt2()
