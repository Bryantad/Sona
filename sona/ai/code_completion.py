"""
Code Completion Engine for Sona v0.8.2

AI-powered code completion using GPT-2 for cognitive programming.
Provides intelligent suggestions based on context and coding patterns.
"""

import re
from typing import List, Dict, Optional, Tuple
from .gpt2_integration import get_gpt2_instance


class CodeCompletion:
    """AI-powered code completion engine"""
    
    def __init__(self):
        """Initialize code completion engine"""
        self.gpt2 = get_gpt2_instance()
        self.completion_cache = {}
        self.cognitive_patterns = {
            'think': 'cognitive reflection and planning',
            'remember': 'memory storage and recall',
            'focus': 'attention and concentration',
            'working_memory': 'temporary storage and processing'
        }
    
    def get_completion(self, code_context: str, cursor_position: int = -1) -> List[str]:
        """Get AI-powered code completions
        
        Args:
            code_context: Current code content
            cursor_position: Position of cursor (-1 for end)
            
        Returns:
            List of completion suggestions
        """
        # Extract context around cursor
        if cursor_position == -1:
            cursor_position = len(code_context)
        
        context_before = code_context[:cursor_position]
        context_after = code_context[cursor_position:]
        
        # Analyze context for better completions
        context_analysis = self._analyze_context(context_before)
        
        # Generate completions based on context
        completions = []
        
        # Check for cognitive keywords
        cognitive_completion = self._get_cognitive_completion(context_before)
        if cognitive_completion:
            completions.extend(cognitive_completion)
        
        # Get AI-generated completions
        ai_completions = self._get_ai_completions(context_before, context_analysis)
        completions.extend(ai_completions)
        
        # Get pattern-based completions
        pattern_completions = self._get_pattern_completions(context_before)
        completions.extend(pattern_completions)
        
        # Remove duplicates and rank
        completions = list(dict.fromkeys(completions))  # Remove duplicates
        return self._rank_completions(completions, context_analysis)[:5]
    
    def _analyze_context(self, code: str) -> Dict:
        """Analyze code context for intelligent completion"""
        analysis = {
            'language': 'sona',
            'indentation_level': 0,
            'in_function': False,
            'in_class': False,
            'in_comment': False,
            'current_line': '',
            'previous_lines': [],
            'keywords_present': [],
            'cognitive_context': False
        }
        
        lines = code.split('\n')
        if lines:
            analysis['current_line'] = lines[-1]
            analysis['previous_lines'] = lines[:-1]
            analysis['indentation_level'] = len(lines[-1]) - len(lines[-1].lstrip())
        
        # Check for function/class context
        for line in reversed(lines):
            if 'function ' in line or 'def ' in line:
                analysis['in_function'] = True
                break
            elif 'class ' in line:
                analysis['in_class'] = True
                break
        
        # Check for cognitive keywords
        cognitive_keywords = ['think', 'remember', 'focus', 'working_memory']
        for keyword in cognitive_keywords:
            if keyword in code.lower():
                analysis['keywords_present'].append(keyword)
                analysis['cognitive_context'] = True
        
        # Check for comments
        if '//' in analysis['current_line'] or '#' in analysis['current_line']:
            analysis['in_comment'] = True
        
        return analysis
    
    def _get_cognitive_completion(self, context: str) -> List[str]:
        """Get completions for cognitive programming patterns"""
        completions = []
        current_line = context.split('\n')[-1].strip()
        
        # Cognitive keyword completions
        if current_line.endswith('think('):
            completions.extend([
                '"Processing user input"',
                '"Analyzing data structure"',
                '"Planning algorithm approach"',
                '"Considering edge cases"'
            ])
        
        elif current_line.endswith('remember('):
            completions.extend([
                '"Save current state"',
                '"Store user preferences"',
                '"Cache computed result"',
                '"Log important decision"'
            ])
        
        elif current_line.endswith('focus('):
            completions.extend([
                '"Error handling"',
                '"Performance optimization"',
                '"User experience"',
                '"Data validation"'
            ])
        
        # Working memory block completion
        elif 'working_memory' in current_line and '{' in current_line:
            completions.extend([
                '\n    current_task = "processing data";',
                '\n    cognitive_load = "medium";',
                '\n    break_needed = false;',
                '\n    focus_pattern = "deep_work";'
            ])
        
        return completions
    
    def _get_ai_completions(self, context: str, analysis: Dict) -> List[str]:
        """Get AI-generated completions using GPT-2"""
        try:
            # Prepare context for AI
            ai_context = self._prepare_ai_context(context, analysis)
            
            # Generate completions
            ai_suggestions = self.gpt2.generate_code_completion(ai_context, max_new_tokens=20)
            
            if ai_suggestions:
                # Clean and format AI suggestions
                cleaned_suggestions = self._clean_ai_suggestions(ai_suggestions)
                return cleaned_suggestions
            
        except Exception as e:
            print(f"⚠️ AI completion error: {e}")
        
        return []
    
    def _prepare_ai_context(self, context: str, analysis: Dict) -> str:
        """Prepare context for AI completion"""
        # Add cognitive programming context
        if analysis['cognitive_context']:
            context = "// Cognitive programming with Sona\n" + context
        
        # Add function context if in function
        if analysis['in_function']:
            context = "// Function implementation\n" + context
        
        return context
    
    def _clean_ai_suggestions(self, suggestion: str) -> List[str]:
        """Clean and format AI suggestions"""
        if not suggestion:
            return []
        
        # Split into logical completions
        lines = suggestion.split('\n')
        cleaned = []
        
        for line in lines[:3]:  # Limit to 3 lines
            line = line.strip()
            if line and not line.startswith('//') and not line.startswith('#'):
                cleaned.append(line)
        
        return cleaned
    
    def _get_pattern_completions(self, context: str) -> List[str]:
        """Get pattern-based completions"""
        completions = []
        current_line = context.split('\n')[-1].strip()
        
        # Function patterns
        if current_line.endswith('function '):
            completions.extend([
                'processData(input) {',
                'validateInput(data) {',
                'handleError(error) {',
                'calculateResult(values) {'
            ])
        
        # Control structure patterns
        elif current_line.endswith('if ('):
            completions.extend([
                'input.valid',
                'data.length > 0',
                'result !== null',
                'error === null'
            ])
        
        # Variable assignments
        elif ' = ' in current_line and current_line.endswith('= '):
            completions.extend([
                'null;',
                'true;',
                'false;',
                '[];',
                '{};'
            ])
        
        return completions
    
    def _rank_completions(self, completions: List[str], analysis: Dict) -> List[str]:
        """Rank completions by relevance"""
        if not completions:
            return []
        
        # Simple ranking: cognitive > AI > pattern
        ranked = []
        
        # Prioritize cognitive completions
        for completion in completions:
            if any(keyword in completion.lower() for keyword in self.cognitive_patterns.keys()):
                ranked.append(completion)
        
        # Add remaining completions
        for completion in completions:
            if completion not in ranked:
                ranked.append(completion)
        
        return ranked
    
    def get_cognitive_suggestions(self, context: str) -> List[str]:
        """Get cognitive programming suggestions"""
        suggestions = []
        
        # Analyze for cognitive opportunities
        if 'function ' in context and 'think(' not in context:
            suggestions.append("Add think() for cognitive planning")
        
        if 'error' in context.lower() and 'remember(' not in context:
            suggestions.append("Add remember() to log error handling")
        
        if len(context.split('\n')) > 20 and 'working_memory' not in context:
            suggestions.append("Consider adding working_memory block for complex logic")
        
        return suggestions
    
    def explain_completion(self, completion: str) -> str:
        """Explain what a completion does"""
        explanations = {
            'think(': 'Cognitive reflection - helps plan and understand code logic',
            'remember(': 'Memory storage - saves important information or state',
            'focus(': 'Attention direction - highlights critical code sections',
            'working_memory': 'Cognitive workspace - manages complex mental tasks'
        }
        
        for pattern, explanation in explanations.items():
            if pattern in completion:
                return explanation
        
        # Use AI to explain if no pattern match
        try:
            return self.gpt2.explain_code(completion)
        except:
            return "Code completion suggestion"
