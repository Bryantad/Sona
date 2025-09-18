"""
Cognitive Assistant for Sona v0.8.2

AI-powered cognitive assistance for neurodivergent programmers.
Provides executive function support, attention management, and cognitive load monitoring.
"""

import time
from typing import Any, Dict, List, Optional

from .gpt2_integration import get_gpt2_instance


class CognitiveAssistant:
    """AI-powered cognitive assistant for neurodivergent programming"""
    
    def __init__(self):
        """Initialize cognitive assistant"""
        self.gpt2 = get_gpt2_instance()
        self.session_start = time.time()
        self.typing_patterns = []
        self.break_history = []
        self.focus_sessions = []
        self.cognitive_profile = {
            'attention_span': 25,  # minutes
            'break_frequency': 5,  # minutes
            'hyperfocus_threshold': 90,  # minutes
            'preferred_break_type': 'gentle'
        }
    
    def analyze_working_memory(self, current_task: str, context: str) -> dict[str, Any]:
        """Analyze working memory load and provide suggestions"""
        analysis = {
            'cognitive_load': 'medium',
            'complexity_score': 0,
            'suggestions': [],
            'break_needed': False,
            'focus_score': 0
        }
        
        # Calculate complexity based on code structure
        lines = context.split('\n')
        complexity_factors = {
            'lines': len(lines),
            'functions': context.count('function ') + context.count('def '),
            'loops': context.count('for ') + context.count('while '),
            'conditionals': context.count('if ') + context.count('elif '),
            'classes': context.count('class '),
            'nested_blocks': self._count_nested_blocks(context)
        }
        
        # Calculate complexity score
        complexity_score = (
            complexity_factors['lines'] * 0.1 +
            complexity_factors['functions'] * 2 +
            complexity_factors['loops'] * 1.5 +
            complexity_factors['conditionals'] * 1 +
            complexity_factors['classes'] * 3 +
            complexity_factors['nested_blocks'] * 2
        )
        
        analysis['complexity_score'] = complexity_score
        
        # Determine cognitive load
        if complexity_score < 10:
            analysis['cognitive_load'] = 'low'
        elif complexity_score < 25:
            analysis['cognitive_load'] = 'medium'
        else:
            analysis['cognitive_load'] = 'high'
        
        # Generate suggestions based on load
        analysis['suggestions'] = self._generate_cognitive_suggestions(
            analysis['cognitive_load'], 
            complexity_factors,
            current_task
        )
        
        # Check if break is needed
        session_time = (time.time() - self.session_start) / 60  # minutes
        analysis['break_needed'] = session_time > self.cognitive_profile['attention_span']
        
        return analysis
    
    def detect_hyperfocus(self, typing_data: list[dict]) -> dict[str, Any]:
        """Detect hyperfocus patterns and provide gentle interventions"""
        self.typing_patterns.extend(typing_data)
        
        # Keep only recent patterns (last 2 hours)
        current_time = time.time()
        self.typing_patterns = [
            pattern for pattern in self.typing_patterns
            if current_time - pattern.get('timestamp', 0) < 7200  # 2 hours
        ]
        
        if not self.typing_patterns:
            return {'hyperfocus_detected': False}
        
        # Analyze patterns
        session_duration = current_time - self.typing_patterns[0]['timestamp']
        session_minutes = session_duration / 60
        
        # Check for hyperfocus indicators
        hyperfocus_indicators = {
            'long_session': session_minutes > self.cognitive_profile['hyperfocus_threshold'],
            'consistent_typing': self._analyze_typing_consistency(),
            'no_breaks': len(self.break_history) == 0 and session_minutes > 60,
            'high_intensity': self._calculate_typing_intensity() > 0.8
        }
        
        hyperfocus_detected = sum(hyperfocus_indicators.values()) >= 2
        
        intervention = None
        if hyperfocus_detected:
            intervention = self._generate_hyperfocus_intervention(session_minutes)
        
        return {
            'hyperfocus_detected': hyperfocus_detected,
            'session_duration_minutes': session_minutes,
            'indicators': hyperfocus_indicators,
            'intervention': intervention
        }
    
    def suggest_break_activity(self, cognitive_state: str = 'medium') -> dict[str, Any]:
        """Suggest appropriate break activities based on cognitive state"""
        break_activities = {
            'low': [
                'Take a 2-minute breathing exercise',
                'Look away from screen for 30 seconds',
                'Stretch your hands and wrists',
                'Drink some water'
            ],
            'medium': [
                'Take a 5-minute walk',
                'Do some light stretching',
                'Practice mindfulness for 3 minutes',
                'Get a healthy snack'
            ],
            'high': [
                'Take a 15-minute walk outside',
                'Do physical exercise for 10 minutes',
                'Take a power nap (10-20 minutes)',
                'Have a proper meal break'
            ],
            'hyperfocus': [
                'Save your work and step away for 30 minutes',
                'Set a timer and do something completely different',
                'Talk to someone about non-work topics',
                'Do a physical activity to reset your mind'
            ]
        }
        
        activities = break_activities.get(cognitive_state, break_activities['medium'])
        
        # Use AI to personalize suggestion
        try:
            ai_suggestion = self._get_ai_break_suggestion(cognitive_state)
            if ai_suggestion:
                activities.insert(0, ai_suggestion)
        except:
            pass
        
        return {
            'suggested_activities': activities[:3],
            'recommended_duration': self._get_break_duration(cognitive_state),
            'cognitive_state': cognitive_state,
            'break_type': self.cognitive_profile['preferred_break_type']
        }
    
    def analyze_executive_function(self, task_description: str) -> dict[str, Any]:
        """Analyze task for executive function support"""
        analysis = {
            'task_breakdown': [],
            'estimated_time': 0,
            'cognitive_demands': {},
            'support_strategies': []
        }
        
        # Use AI to break down complex tasks
        try:
            ai_breakdown = self._get_ai_task_breakdown(task_description)
            analysis['task_breakdown'] = ai_breakdown
        except:
            # Fallback to pattern-based breakdown
            analysis['task_breakdown'] = self._pattern_task_breakdown(task_description)
        
        # Estimate time and cognitive demands
        analysis['estimated_time'] = len(analysis['task_breakdown']) * 15  # 15 min per subtask
        analysis['cognitive_demands'] = self._analyze_cognitive_demands(task_description)
        
        # Generate support strategies
        analysis['support_strategies'] = self._generate_executive_strategies(
            analysis['cognitive_demands']
        )
        
        return analysis
    
    def _count_nested_blocks(self, code: str) -> int:
        """Count nested code blocks"""
        lines = code.split('\n')
        max_nesting = 0
        current_nesting = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.endswith('{'):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stripped == '}':
                current_nesting = max(0, current_nesting - 1)
        
        return max_nesting
    
    def _generate_cognitive_suggestions(self, load: str, factors: dict, task: str) -> list[str]:
        """Generate cognitive load management suggestions"""
        suggestions = []
        
        if load == 'high':
            suggestions.extend([
                "Consider breaking this into smaller functions",
                "Add comments to reduce cognitive overhead",
                "Use descriptive variable names",
                "Take a break before continuing"
            ])
        
        if factors['nested_blocks'] > 3:
            suggestions.append("Reduce nesting depth for better readability")
        
        if factors['functions'] > 5:
            suggestions.append("Consider organizing functions into classes")
        
        # Use AI for personalized suggestions
        try:
            ai_suggestion = self.gpt2.suggest_improvements(f"Task: {task}\nLoad: {load}")
            if ai_suggestion and len(ai_suggestion) < 100:
                suggestions.append(ai_suggestion)
        except:
            pass
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def _analyze_typing_consistency(self) -> bool:
        """Analyze typing patterns for consistency"""
        if len(self.typing_patterns) < 10:
            return False
        
        # Simple consistency check based on timing intervals
        intervals = []
        for i in range(1, len(self.typing_patterns)):
            interval = self.typing_patterns[i]['timestamp'] - self.typing_patterns[i-1]['timestamp']
            intervals.append(interval)
        
        if not intervals:
            return False
        
        # Check for consistent typing (low variance in intervals)
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        
        return variance < avg_interval * 0.5  # Low variance indicates consistency
    
    def _calculate_typing_intensity(self) -> float:
        """Calculate typing intensity score"""
        if not self.typing_patterns:
            return 0.0
        
        recent_patterns = self.typing_patterns[-20:]  # Last 20 events
        if len(recent_patterns) < 5:
            return 0.0
        
        time_span = recent_patterns[-1]['timestamp'] - recent_patterns[0]['timestamp']
        if time_span == 0:
            return 1.0
        
        events_per_second = len(recent_patterns) / time_span
        
        # Normalize to 0-1 scale (5 events/sec = 1.0)
        return min(events_per_second / 5.0, 1.0)
    
    def _generate_hyperfocus_intervention(self, session_minutes: float) -> dict[str, str]:
        """Generate gentle hyperfocus intervention"""
        if session_minutes > 180:  # 3 hours
            urgency = 'high'
            message = "You've been coding for over 3 hours. Time for a substantial break!"
        elif session_minutes > 120:  # 2 hours
            urgency = 'medium'
            message = "You've been in deep focus for 2+ hours. Consider taking a break soon."
        else:
            urgency = 'low'
            message = "Great focus! Remember to take breaks to maintain productivity."
        
        return {
            'urgency': urgency,
            'message': message,
            'recommended_action': self._get_intervention_action(urgency)
        }
    
    def _get_intervention_action(self, urgency: str) -> str:
        """Get recommended intervention action"""
        actions = {
            'low': "Save your work and continue, but set a 30-minute timer",
            'medium': "Finish your current thought and take a 10-minute break",
            'high': "Stop coding now and take at least a 20-minute break"
        }
        return actions.get(urgency, actions['medium'])
    
    def _get_ai_break_suggestion(self, cognitive_state: str) -> str | None:
        """Get AI-powered break suggestion"""
        prompt = f"Suggest a {cognitive_state} cognitive load break activity for a programmer:"
        suggestions = self.gpt2.generate_completion(prompt, max_new_tokens=20, temperature=0.7)
        
        if suggestions and suggestions[0]:
            return suggestions[0].strip()
        return None
    
    def _get_break_duration(self, cognitive_state: str) -> int:
        """Get recommended break duration in minutes"""
        durations = {
            'low': 2,
            'medium': 5,
            'high': 15,
            'hyperfocus': 30
        }
        return durations.get(cognitive_state, 5)
    
    def _get_ai_task_breakdown(self, task: str) -> list[str]:
        """Use AI to break down complex tasks"""
        prompt = f"Break down this programming task into subtasks:\n{task}\nSubtasks:"
        
        breakdown_text = self.gpt2.generate_completion(
            prompt, 
            max_new_tokens=100, 
            temperature=0.6
        )
        
        if breakdown_text and breakdown_text[0]:
            # Parse AI response into list
            lines = breakdown_text[0].split('\n')
            subtasks = []
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('1.') or line.startswith('•')):
                    # Clean up formatting
                    line = line.lstrip('-•').strip()
                    if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                        line = line[2:].strip()
                    subtasks.append(line)
            
            return subtasks[:5]  # Limit to 5 subtasks
        
        return []
    
    def _pattern_task_breakdown(self, task: str) -> list[str]:
        """Pattern-based task breakdown as fallback"""
        generic_breakdown = [
            "Plan the approach",
            "Set up basic structure", 
            "Implement core functionality",
            "Add error handling",
            "Test and refine"
        ]
        return generic_breakdown
    
    def _analyze_cognitive_demands(self, task: str) -> dict[str, float]:
        """Analyze cognitive demands of a task"""
        demands = {
            'working_memory': 0.5,
            'attention': 0.5,
            'processing_speed': 0.5,
            'executive_function': 0.5
        }
        
        task_lower = task.lower()
        
        # Adjust based on task complexity indicators
        if any(word in task_lower for word in ['algorithm', 'optimize', 'complex']):
            demands['working_memory'] += 0.3
            demands['processing_speed'] += 0.2
        
        if any(word in task_lower for word in ['debug', 'fix', 'error']):
            demands['attention'] += 0.3
            demands['executive_function'] += 0.2
        
        if any(word in task_lower for word in ['design', 'architecture', 'plan']):
            demands['executive_function'] += 0.3
            demands['working_memory'] += 0.2
        
        # Normalize to 0-1 range
        for key in demands:
            demands[key] = min(demands[key], 1.0)
        
        return demands
    
    def _generate_executive_strategies(self, demands: dict[str, float]) -> list[str]:
        """Generate executive function support strategies"""
        strategies = []
        
        if demands['working_memory'] > 0.7:
            strategies.append("Use external memory aids (comments, notes)")
            strategies.append("Break into smaller, manageable chunks")
        
        if demands['attention'] > 0.7:
            strategies.append("Minimize distractions in environment")
            strategies.append("Use focused time blocks (Pomodoro technique)")
        
        if demands['executive_function'] > 0.7:
            strategies.append("Create step-by-step checklist")
            strategies.append("Set clear milestones and deadlines")
        
        if demands['processing_speed'] > 0.7:
            strategies.append("Allow extra time for complex tasks")
            strategies.append("Use visual aids and diagrams")
        
        return strategies
