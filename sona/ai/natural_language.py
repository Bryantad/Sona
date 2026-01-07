"""
Natural Language Processor for Sona v0.8.2

Converts natural language descriptions to Sona code and provides
AI-powered explanations and documentation generation.
"""

import re
from typing import Dict, List

from .ai_backend import get_ai_backend


class NaturalLanguageProcessor:
    """Natural language to code converter and explainer"""
    
    def __init__(self):
        """Initialize natural language processor"""
        self.gpt2 = get_ai_backend()
        self.code_patterns = {
            'create_function': r'create|make|build.*function',
            'process_data': r'process|handle|work with.*data',
            'validate_input': r'validate|check|verify.*input',
            'loop_through': r'loop|iterate|go through',
            'conditional': r'if|when|check if',
            'store_data': r'save|store|keep.*data'
        }
        
    def text_to_code(self, description: str, target_language: str = 'sona') -> dict[str, str]:
        """Convert natural language description to code
        
        Args:
            description: Natural language description
            target_language: Target programming language
            
        Returns:
            Dictionary with generated code and metadata
        """
        # Clean and analyze the description
        cleaned_description = self._clean_description(description)
        intent = self._analyze_intent(cleaned_description)
        
        # Generate code based on intent
        if intent['type'] == 'function_creation':
            code = self._generate_function_code(cleaned_description, intent)
        elif intent['type'] == 'data_processing':
            code = self._generate_data_processing_code(cleaned_description, intent)
        elif intent['type'] == 'control_flow':
            code = self._generate_control_flow_code(cleaned_description, intent)
        else:
            # Use AI for general code generation
            code = self._generate_ai_code(cleaned_description, target_language)
        
        # Add cognitive elements if appropriate
        if self._should_add_cognitive_elements(description):
            code = self._add_cognitive_elements(code, intent)
        
        return {
            'code': code,
            'language': target_language,
            'intent': intent,
            'description': cleaned_description,
            'confidence': self._calculate_confidence(intent)
        }
    
    def explain_code(self, code: str, style: str = 'simple') -> str:
        """Generate natural language explanation of code
        
        Args:
            code: Code to explain
            style: Explanation style ('simple', 'detailed', 'cognitive')
            
        Returns:
            Natural language explanation
        """
        if style == 'cognitive':
            return self._generate_cognitive_explanation(code)
        elif style == 'detailed':
            return self._generate_detailed_explanation(code)
        else:
            return self._generate_simple_explanation(code)
    
    def generate_documentation(self, code: str, doc_type: str = 'function') -> str:
        """Generate documentation for code
        
        Args:
            code: Code to document
            doc_type: Type of documentation ('function', 'class', 'module')
            
        Returns:
            Generated documentation
        """
        if doc_type == 'function':
            return self._generate_function_docs(code)
        elif doc_type == 'class':
            return self._generate_class_docs(code)
        else:
            return self._generate_module_docs(code)
    
    def suggest_improvements(self, description: str, current_code: str) -> list[str]:
        """Suggest improvements based on natural language description
        
        Args:
            description: Original description
            current_code: Current implementation
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Analyze description for missing elements
        intent = self._analyze_intent(description)
        code_analysis = self._analyze_code_completeness(current_code, intent)
        
        if not code_analysis['has_error_handling']:
            suggestions.append("Add error handling for robustness")
        
        if not code_analysis['has_validation']:
            suggestions.append("Add input validation")
        
        if not code_analysis['has_documentation']:
            suggestions.append("Add documentation comments")
        
        # Use AI for additional suggestions
        try:
            ai_suggestions = self.gpt2.suggest_improvements(current_code)
            if ai_suggestions:
                suggestions.extend(ai_suggestions.split('\n')[:2])
        except:
            pass
        
        return suggestions[:5]
    
    def _clean_description(self, description: str) -> str:
        """Clean and normalize natural language description"""
        # Remove extra whitespace
        cleaned = ' '.join(description.split())
        
        # Convert to lowercase for analysis
        cleaned = cleaned.lower()
        
        # Remove filler words
        filler_words = ['um', 'uh', 'like', 'you know', 'basically']
        for word in filler_words:
            cleaned = cleaned.replace(f' {word} ', ' ')
        
        return cleaned.strip()
    
    def _analyze_intent(self, description: str) -> dict[str, any]:
        """Analyze intent from natural language description"""
        intent = {
            'type': 'general',
            'action': None,
            'data_type': None,
            'complexity': 'simple',
            'cognitive_elements': False
        }
        
        # Check for function creation
        if re.search(self.code_patterns['create_function'], description):
            intent['type'] = 'function_creation'
            intent['action'] = 'create_function'
        
        # Check for data processing
        elif re.search(self.code_patterns['process_data'], description):
            intent['type'] = 'data_processing'
            intent['action'] = 'process_data'
        
        # Check for control flow
        elif any(re.search(pattern, description) for pattern in [
            self.code_patterns['loop_through'],
            self.code_patterns['conditional']
        ]):
            intent['type'] = 'control_flow'
            intent['action'] = 'control_structure'
        
        # Detect data types
        if 'list' in description or 'array' in description:
            intent['data_type'] = 'list'
        elif 'object' in description or 'dictionary' in description:
            intent['data_type'] = 'object'
        elif 'string' in description or 'text' in description:
            intent['data_type'] = 'string'
        elif 'number' in description or 'integer' in description:
            intent['data_type'] = 'number'
        
        # Detect complexity
        complexity_indicators = ['complex', 'advanced', 'sophisticated', 'multiple']
        if any(indicator in description for indicator in complexity_indicators):
            intent['complexity'] = 'complex'
        
        # Detect cognitive elements request
        cognitive_keywords = ['think', 'remember', 'focus', 'cognitive', 'accessible']
        if any(keyword in description for keyword in cognitive_keywords):
            intent['cognitive_elements'] = True
        
        return intent
    
    def _generate_function_code(self, description: str, intent: dict) -> str:
        """Generate function code based on description"""
        # Extract function name from description
        function_name = self._extract_function_name(description)
        
        # Generate basic function structure
        code = f"function {function_name}(input) {{\n"
        
        # Add cognitive thinking if requested
        if intent['cognitive_elements']:
            code += f'    think("Processing {function_name} request");\n'
        
        # Add basic implementation based on intent
        if intent['action'] == 'create_function':
            if 'validate' in description:
                code += "    if (!input || input.length === 0) {\n"
                code += "        return false;\n"
                code += "    }\n"
            
            code += "    // Process the input\n"
            code += "    result = process_input(input);\n"
            
            if intent['cognitive_elements']:
                code += '    remember("Processing completed successfully");\n'
            
            code += "    return result;\n"
        
        code += "}"
        
        return code
    
    def _generate_data_processing_code(self, description: str, intent: dict) -> str:
        """Generate data processing code"""
        code = "// Data processing function\n"
        
        if intent['cognitive_elements']:
            code += 'think("Starting data processing");\n\n'
        
        if intent['data_type'] == 'list':
            code += "data.forEach(item => {\n"
            code += "    processItem(item);\n"
            code += "});\n"
        elif intent['data_type'] == 'object':
            code += "for (key in data) {\n"
            code += "    processProperty(key, data[key]);\n"
            code += "}\n"
        else:
            code += "processedData = transformData(data);\n"
        
        if intent['cognitive_elements']:
            code += '\nremember("Data processing completed");\n'
        
        return code
    
    def _generate_control_flow_code(self, description: str, intent: dict) -> str:
        """Generate control flow code"""
        code = ""
        
        if 'loop' in description or 'iterate' in description:
            if intent['cognitive_elements']:
                code += 'think("Setting up iteration loop");\n'
            
            code += "for (i = 0; i < items.length; i++) {\n"
            code += "    processItem(items[i]);\n"
            code += "}\n"
        
        if 'if' in description or 'check' in description:
            if intent['cognitive_elements']:
                code += 'focus("Checking condition");\n'
            
            code += "if (condition) {\n"
            code += "    handleTrue();\n"
            code += "} else {\n"
            code += "    handleFalse();\n"
            code += "}\n"
        
        return code
    
    def _generate_ai_code(self, description: str, language: str) -> str:
        """Use AI to generate code from description"""
        try:
            prompt = f"Convert this to {language} code: {description}\n\nCode:\n"
            ai_code = self.gpt2.natural_language_to_code(description, language)
            
            if ai_code and not ai_code.startswith("# Unable"):
                return ai_code
        except:
            pass
        
        # Fallback to template
        return f"// Generated from: {description}\n// TODO: Implement functionality"
    
    def _should_add_cognitive_elements(self, description: str) -> bool:
        """Check if cognitive elements should be added"""
        cognitive_keywords = ['accessible', 'cognitive', 'adhd', 'autism', 'neurodivergent']
        return any(keyword in description.lower() for keyword in cognitive_keywords)
    
    def _add_cognitive_elements(self, code: str, intent: dict) -> str:
        """Add cognitive programming elements to code"""
        if 'think(' not in code and intent['complexity'] != 'simple':
            # Add thinking at the beginning
            lines = code.split('\n')
            if lines and not lines[0].strip().startswith('think('):
                lines.insert(0, 'think("Starting to work on this task");')
                code = '\n'.join(lines)
        
        return code
    
    def _extract_function_name(self, description: str) -> str:
        """Extract function name from description"""
        # Simple heuristics to extract function name
        words = description.split()
        
        # Look for action words
        action_words = ['create', 'make', 'build', 'process', 'handle', 'validate']
        for i, word in enumerate(words):
            if word in action_words and i + 1 < len(words):
                next_word = words[i + 1]
                if next_word not in ['a', 'an', 'the']:
                    return f"{word}_{next_word.replace(' ', '_')}"
        
        # Default function name
        return "processData"
    
    def _calculate_confidence(self, intent: dict) -> float:
        """Calculate confidence score for code generation"""
        confidence = 0.5  # Base confidence
        
        if intent['type'] != 'general':
            confidence += 0.2
        
        if intent['action']:
            confidence += 0.2
        
        if intent['data_type']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_cognitive_explanation(self, code: str) -> str:
        """Generate cognitive-friendly code explanation"""
        explanation = "This code helps you by:\n\n"
        
        # Analyze code structure
        if 'think(' in code:
            explanation += "• Using 'think()' to help you understand the logic\n"
        
        if 'remember(' in code:
            explanation += "• Using 'remember()' to store important information\n"
        
        if 'focus(' in code:
            explanation += "• Using 'focus()' to highlight critical parts\n"
        if '@intent' in code:
            explanation += "• Declaring intent annotations to preserve context\n"

        if 'focus {' in code or 'focus{' in code:
            explanation += "• Using focus blocks to reduce noise during execution\n"

        
        if 'function' in code:
            explanation += "• Breaking work into manageable functions\n"
        
        if 'if' in code:
            explanation += "• Making decisions based on conditions\n"
        
        if 'for' in code or 'while' in code:
            explanation += "• Repeating actions efficiently\n"
        
        # Add AI explanation
        try:
            ai_explanation = self.gpt2.explain_code(code)
            if ai_explanation:
                explanation += f"\nDetailed explanation: {ai_explanation}"
        except:
            pass
        
        return explanation
    
    def _generate_simple_explanation(self, code: str) -> str:
        """Generate simple code explanation"""
        try:
            return self.gpt2.explain_code(code)
        except:
            return "This code performs a programming task."
    
    def _generate_detailed_explanation(self, code: str) -> str:
        """Generate detailed code explanation"""
        explanation = self._generate_simple_explanation(code)
        
        # Add structural analysis
        lines = code.split('\n')
        explanation += "\n\nCode structure:\n"
        explanation += f"• {len(lines)} lines of code\n"
        explanation += f"• {code.count('function')} function(s)\n"
        explanation += f"• {code.count('if')} conditional(s)\n"
        explanation += f"• {code.count('for') + code.count('while')} loop(s)\n"
        
        return explanation
    
    def _generate_function_docs(self, code: str) -> str:
        """Generate function documentation"""
        # Extract function name
        function_match = re.search(r'function\s+(\w+)', code)
        function_name = function_match.group(1) if function_match else "function"
        
        docs = f'"""\n{function_name.title()} Function\n\n'
        docs += "Purpose: [Describe what this function does]\n"
        docs += "Parameters: [List input parameters]\n"
        docs += "Returns: [Describe return value]\n"
        docs += "Example: [Show usage example]\n"
        docs += '"""'
        
        return docs
    
    def _generate_class_docs(self, code: str) -> str:
        """Generate class documentation"""
        return '"""\nClass documentation\n\nDescription of class purpose and usage.\n"""'
    
    def _generate_module_docs(self, code: str) -> str:
        """Generate module documentation"""
        return '"""\nModule documentation\n\nDescription of module purpose and API.\n"""'
    
    def _analyze_code_completeness(self, code: str, intent: dict) -> dict[str, bool]:
        """Analyze code completeness"""
        return {
            'has_error_handling': 'try' in code or 'catch' in code or 'if' in code,
            'has_validation': 'validate' in code or 'check' in code,
            'has_documentation': '/*' in code or '//' in code or '"""' in code
        }
