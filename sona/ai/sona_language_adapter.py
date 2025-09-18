"""
Sona Language Adapter for GPT-2

This module creates a Sona-aware layer on top of GPT-2 without requiring
full model fine-tuning. It uses prompt engineering and pattern matching
to make GPT-2 more effective at Sona code generation.
"""

import json
from pathlib import Path
from typing import Dict, List


class SonaLanguageAdapter:
    """Adapter that makes any LLM better at Sona language"""
    
    def __init__(self, base_gpt2=None):
        self.base_gpt2 = base_gpt2
        self.sona_patterns = self.load_sona_patterns()
        self.cognitive_templates = self.load_cognitive_templates()
        self.completion_cache = {}
        
    def load_sona_patterns(self) -> dict[str, list[str]]:
        """Load Sona syntax patterns from training data"""
        patterns = {
            'thinking_patterns': [
                'thinking("Planning", "Let me break this down step by step")',
                'thinking("Analysis", "Understanding the requirements")',
                'thinking("Implementation", "How should I structure this?")',
                'thinking("Debugging", "Let me trace through this logic")'
            ],
            'function_patterns': [
                'func calculate_sum(a, b) {\n    return a + b\n}',
                'func greet(name) {\n    return "Hello, " + name + "!"\n}',
                'func process_data(input) {\n    // Process the input\n    return result\n}',
                'func validate_input(data) {\n    if data.isEmpty() {\n        return false\n    }\n    return true\n}'
            ],
            'class_patterns': [
                'class Person {\n    constructor(name) {\n        self.name = name\n    }\n    \n    def greet() {\n        print("Hello, I\'m " + self.name)\n    }\n}',
                'class Calculator {\n    constructor() {\n        self.result = 0\n    }\n    \n    def add(value) {\n        self.result += value\n        return self\n    }\n}'
            ],
            'cognitive_patterns': [
                'working_memory {\n    let data = process_input()\n    remember("current_data", data)\n    focus_mode("analysis")\n}',
                'remember("user_preferences", settings)',
                'focus_mode("concentrated_coding")',
                'encompassing: [user_interface, data_processing, validation]'
            ],
            'variable_patterns': [
                'let message = "Hello, World!"',
                'let numbers = [1, 2, 3, 4, 5]',
                'let user = {"name": "Alice", "age": 25}',
                'let config = {"debug": true, "mode": "development"}'
            ]
        }
        
        # Try to load from dataset if available
        try:
            dataset_path = Path("sona_training_dataset.json")
            if dataset_path.exists():
                with open(dataset_path, encoding='utf-8') as f:
                    dataset = json.load(f)
                
                # Extract patterns from real data
                if 'syntax_patterns' in dataset:
                    for pattern_type, pattern_list in dataset['syntax_patterns'].items():
                        if pattern_type in patterns:
                            patterns[pattern_type].extend(pattern_list[:5])  # Add top 5
                            
        except Exception as e:
            print(f"⚠️ Could not load additional patterns: {e}")
        
        return patterns
    
    def load_cognitive_templates(self) -> dict[str, str]:
        """Load cognitive programming templates"""
        return {
            'planning': '''thinking("Planning phase", "{description}") {{
    // Break down the problem
    let steps = [{steps}]
    
    for step in steps {{
        focus_mode("concentrated")
        // Implement step
    }}
}}''',
            
            'analysis': '''thinking("Analysis", "Understanding {topic}") {{
    encompasses: [{aspects}]
    visual_metaphor: "{metaphor}"
    complexity_level: {level}
    
    working_memory {{
        let data = gather_information()
        remember("analysis_data", data)
    }}
}}''',
            
            'function_creation': '''func {name}({params}) {{
    thinking("Function logic", "Implementing {description}")
    
    {body}
    
    return {return_value}
}}''',
            
            'class_creation': '''class {name} {{
    thinking("Class design", "Creating {description}")
    
    constructor({params}) {{
        {constructor_body}
    }}
    
    {methods}
}}'''
        }
    
    def enhance_prompt_for_sona(self, prompt: str) -> str:
        """Enhance a prompt to be more Sona-aware"""
        # Add Sona context
        sona_context = """You are a Sona programming language expert. Sona is a cognitive-first programming language with these features:
- thinking() blocks for cognitive planning
- remember() for working memory
- focus_mode() for attention management
- working_memory blocks for structured thinking
- Standard syntax: func, class, let, if, for, while
- Neurodivergent-friendly design patterns

Generate Sona code that follows these patterns:"""
        
        enhanced_prompt = f"{sona_context}\n\n{prompt}"
        
        # Add relevant examples based on prompt content
        if 'function' in prompt.lower() or 'func' in prompt.lower():
            enhanced_prompt += f"\n\nExample Sona function:\n{self.sona_patterns['function_patterns'][0]}"
        
        if 'class' in prompt.lower():
            enhanced_prompt += f"\n\nExample Sona class:\n{self.sona_patterns['class_patterns'][0]}"
        
        if 'thinking' in prompt.lower() or 'cognitive' in prompt.lower():
            enhanced_prompt += f"\n\nExample cognitive pattern:\n{self.sona_patterns['thinking_patterns'][0]}"
        
        return enhanced_prompt
    
    def complete_sona_code(self, prompt: str, max_length: int = 50) -> str:
        """Complete Sona code using pattern matching and base GPT-2"""
        # Check cache first
        cache_key = f"{prompt}:{max_length}"
        if cache_key in self.completion_cache:
            return self.completion_cache[cache_key]
        
        completion = ""
        
        # Pattern-based completion for common Sona constructs
        if prompt.strip().endswith('thinking('):
            completion = '"Planning", "Let me think about this step by step")'
        
        elif prompt.strip().endswith('remember('):
            completion = '"key", value)'
        
        elif prompt.strip().endswith('focus_mode('):
            completion = '"concentrated_coding")'
        
        elif prompt.strip().endswith('func '):
            completion = 'process_data(input) {\n    // Process the input\n    return result\n}'
        
        elif prompt.strip().endswith('class '):
            completion = 'MyClass {\n    constructor() {\n        // Initialize\n    }\n}'
        
        elif prompt.strip().endswith('let '):
            completion = 'variable = "value"'
        
        elif 'working_memory' in prompt and prompt.strip().endswith('{'):
            completion = '\n    let data = process_input()\n    remember("current_state", data)\n    focus_mode("analysis")\n}'
        
        # If we have base GPT-2, use it with enhanced prompt
        elif self.base_gpt2:
            try:
                enhanced_prompt = self.enhance_prompt_for_sona(f"Complete this Sona code: {prompt}")
                completion = self.base_gpt2.generate_completion(enhanced_prompt, max_new_tokens=max_length)
                
                # Clean up the completion
                completion = self.clean_sona_completion(completion, prompt)
                
            except Exception as e:
                print(f"⚠️ GPT-2 completion failed: {e}")
                completion = self.fallback_completion(prompt)
        
        else:
            completion = self.fallback_completion(prompt)
        
        # Cache the result
        self.completion_cache[cache_key] = completion
        return completion
    
    def clean_sona_completion(self, completion: str, original_prompt: str) -> str:
        """Clean up generated completion for Sona syntax"""
        # Handle case where completion might be a list
        if isinstance(completion, list):
            completion = completion[0] if completion else ""
        
        # Ensure completion is a string
        completion = str(completion)
        
        # Remove the original prompt from completion if it was repeated
        if completion.startswith(original_prompt):
            completion = completion[len(original_prompt):]
        
        # Remove common artifacts
        completion = completion.replace('<|endoftext|>', '')
        completion = completion.replace('<|startoftext|>', '')
        completion = completion.replace('```', '')
        
        # Stop at natural endpoints
        for stop_token in ['\n\n\n', '---', 'Example:', 'Note:']:
            if stop_token in completion:
                completion = completion.split(stop_token)[0]
        
        return completion.strip()
    
    def fallback_completion(self, prompt: str) -> str:
        """Fallback completion when GPT-2 is not available"""
        fallbacks = {
            'thinking(': '"Task", "Working on this problem")',
            'remember(': '"data", value)',
            'focus_mode(': '"coding")',
            'func ': 'myFunction() {\n    // Function body\n}',
            'class ': 'MyClass {\n    constructor() {\n        // Constructor\n    }\n}',
            'let ': 'variable = "default"',
            'working_memory': ' {\n    // Working memory block\n}'
        }
        
        for pattern, completion in fallbacks.items():
            if pattern in prompt:
                return completion
        
        return '// Completion not available'
    
    def explain_sona_code(self, code: str, style: str = "simple") -> str:
        """Explain Sona code with cognitive-friendly descriptions"""
        explanations = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            explanation = self.explain_line(line, style)
            if explanation:
                explanations.append(f"• {explanation}")
        
        if style == "cognitive":
            intro = "🧠 Cognitive-friendly explanation:\n\n"
            outro = "\n\n💡 This code uses Sona's neurodivergent-friendly patterns to make programming more accessible."
            return intro + '\n'.join(explanations) + outro
        
        return '\n'.join(explanations)
    
    def explain_line(self, line: str, style: str) -> str:
        """Explain a single line of Sona code"""
        if line.startswith('thinking('):
            return "Creates a thinking block for cognitive planning and documentation"
        
        elif line.startswith('remember('):
            return "Stores information in working memory for later access"
        
        elif line.startswith('focus_mode('):
            return "Sets attention mode to help with concentration"
        
        elif line.startswith('working_memory'):
            return "Opens a structured thinking block for complex operations"
        
        elif line.startswith('func '):
            return "Defines a reusable function that can accept parameters"
        
        elif line.startswith('class '):
            return "Creates a class template for objects with shared properties"
        
        elif line.startswith('let '):
            return "Declares a variable to store data"
        
        elif 'encompasses:' in line:
            return "Lists the concepts or areas this code relates to"
        
        elif 'visual_metaphor:' in line:
            return "Provides a visual analogy to help understand the concept"
        
        elif 'complexity_level:' in line:
            return "Indicates the cognitive complexity level of this code"
        
        else:
            return f"Executes: {line}"
    
    def suggest_sona_improvements(self, code: str) -> list[str]:
        """Suggest Sona-specific improvements"""
        suggestions = []
        
        # Check for cognitive patterns
        if 'thinking(' not in code and 'func ' in code:
            suggestions.append("Add thinking() blocks to document your planning process")
        
        if 'remember(' not in code and len(code.split('\n')) > 10:
            suggestions.append("Consider using remember() to store intermediate results")
        
        if 'working_memory' not in code and 'for ' in code:
            suggestions.append("Use working_memory blocks for complex loop operations")
        
        # Check for accessibility
        if not any(pattern in code for pattern in ['encompasses:', 'visual_metaphor:', 'complexity_level:']):
            suggestions.append("Add cognitive accessibility annotations (encompasses, visual_metaphor)")
        
        # Check for structure
        if code.count('{') != code.count('}'):
            suggestions.append("Check bracket matching for proper code structure")
        
        if len([line for line in code.split('\n') if line.strip().startswith('//')]) == 0:
            suggestions.append("Add comments to explain your thinking process")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def generate_sona_template(self, template_type: str, **kwargs) -> str:
        """Generate Sona code templates"""
        if template_type == "function":
            name = kwargs.get('name', 'myFunction')
            params = kwargs.get('params', 'input')
            description = kwargs.get('description', 'performs an operation')
            
            return self.cognitive_templates['function_creation'].format(
                name=name,
                params=params,
                description=description,
                body='    // Implementation here',
                return_value='result'
            )
        
        elif template_type == "class":
            name = kwargs.get('name', 'MyClass')
            description = kwargs.get('description', 'a new class')
            
            return self.cognitive_templates['class_creation'].format(
                name=name,
                description=description,
                params='',
                constructor_body='        // Initialize properties',
                methods='    def method() {\n        // Method implementation\n    }'
            )
        
        elif template_type == "planning":
            description = kwargs.get('description', 'solving the problem')
            steps = kwargs.get('steps', '"analyze", "design", "implement", "test"')
            
            return self.cognitive_templates['planning'].format(
                description=description,
                steps=steps
            )
        
        return f"// Template for {template_type} not available"


# Global instance
_sona_adapter = None

def get_sona_adapter(base_gpt2=None) -> SonaLanguageAdapter:
    """Get the singleton Sona language adapter"""
    global _sona_adapter
    
    if _sona_adapter is None:
        _sona_adapter = SonaLanguageAdapter(base_gpt2)
    
    return _sona_adapter


def test_sona_adapter():
    """Test the Sona language adapter"""
    print("🧪 Testing Sona Language Adapter")
    print("=" * 40)
    
    adapter = get_sona_adapter()
    
    # Test completions
    test_prompts = [
        "thinking(",
        "func calculate_",
        "class Person",
        "let message =",
        "working_memory {"
    ]
    
    print("📝 Testing code completions:")
    for prompt in test_prompts:
        completion = adapter.complete_sona_code(prompt)
        print(f"   '{prompt}' → '{completion[:40]}...'")
    
    # Test explanations
    print("\n📖 Testing code explanation:")
    test_code = '''thinking("Planning", "Creating a calculator")
func add(a, b) {
    return a + b
}
let result = add(5, 3)'''
    
    explanation = adapter.explain_sona_code(test_code, "cognitive")
    print(f"   {explanation[:100]}...")
    
    # Test suggestions
    print("\n💡 Testing improvement suggestions:")
    suggestions = adapter.suggest_sona_improvements("func test() { return 1 }")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    print("\n✅ Sona Language Adapter test complete!")


if __name__ == "__main__":
    test_sona_adapter()
