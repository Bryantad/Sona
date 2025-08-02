"""
Supporting components for Claude-like chatbot implementation
"""

import time
import re
from typing import Dict, List, Any
from collections import deque
from datetime import datetime

from .claude_like_chatbot import ConversationTopic, UserContext


class ResponseQualityScorer:
    """Scores response quality based on Claude-like criteria"""
    
    def score_response(self, response: str, context: Dict) -> float:
        """Score response quality on scale of 0-10"""
        scores = []
        
        # Helpfulness score (0-1)
        helpfulness = self._score_helpfulness(response)
        scores.append(helpfulness)
        
        # Clarity score (0-1)
        clarity = self._score_clarity(response)
        scores.append(clarity)
        
        # Engagement score (0-1)
        engagement = self._score_engagement(response)
        scores.append(engagement)
        
        # Structure score (0-1)
        structure = self._score_structure(response)
        scores.append(structure)
        
        # Accuracy score (0-1) - basic heuristics
        accuracy = self._score_accuracy(response, context)
        scores.append(accuracy)
        
        # Convert to 0-10 scale
        return sum(scores) / len(scores) * 10
        
    def _score_helpfulness(self, response: str) -> float:
        """Score how helpful the response appears"""
        helpful_indicators = [
            'i can help', 'let me', 'here\'s how', 'i\'ll show you',
            'step by step', 'for example', 'specifically'
        ]
        
        score = 0.5  # Base score
        for indicator in helpful_indicators:
            if indicator in response.lower():
                score += 0.1
                
        return min(score, 1.0)
        
    def _score_clarity(self, response: str) -> float:
        """Score response clarity and readability"""
        score = 0.5  # Base score
        
        # Check for clear structure
        if any(marker in response for marker in ['1.', '2.', '•', '-']):
            score += 0.2
            
        # Check for explanatory language
        clarity_markers = ['because', 'since', 'therefore', 'this means', 'in other words']
        for marker in clarity_markers:
            if marker in response.lower():
                score += 0.1
                
        # Penalize very long sentences
        sentences = response.split('.')
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_length > 30:
            score -= 0.1
            
        return min(max(score, 0.0), 1.0)
        
    def _score_engagement(self, response: str) -> float:
        """Score how engaging the response is"""
        engagement_markers = [
            '?', 'would you like', 'what do you think', 'any questions',
            'let me know', 'feel free to ask', 'anything else'
        ]
        
        score = 0.3  # Base score
        for marker in engagement_markers:
            if marker in response.lower():
                score += 0.15
                
        return min(score, 1.0)
        
    def _score_structure(self, response: str) -> float:
        """Score response organization and structure"""
        score = 0.4  # Base score
        
        # Check for logical flow
        if 'first' in response.lower() and ('then' in response.lower() or 'next' in response.lower()):
            score += 0.2
            
        # Check for summaries or conclusions
        if any(word in response.lower() for word in ['summary', 'conclusion', 'in summary', 'overall']):
            score += 0.2
            
        # Check for clear sections
        if response.count('\n\n') >= 1:
            score += 0.2
            
        return min(score, 1.0)
        
    def _score_accuracy(self, response: str, context: Dict) -> float:
        """Basic accuracy heuristics (placeholder for more sophisticated checking)"""
        # For now, return base score - in production, this would check facts
        return 0.7


class AdvancedContextManager:
    """Manages conversation state and context for Claude-like continuity"""
    
    def __init__(self, max_turns=50, max_context_tokens=1500):
        self.conversation_history = deque(maxlen=max_turns)
        self.user_preferences = {}
        self.topic_tracking = TopicTracker()
        self.memory_bank = ConversationMemory()
        
    def update_context(self, user_input: str, bot_response: str, topic: ConversationTopic):
        """Update conversation state with intelligent context compression"""
        
        # Store turn
        turn = {
            'user_input': user_input,
            'bot_response': bot_response,
            'timestamp': time.time(),
            'topic': topic,
            'importance': self._calculate_importance(user_input, bot_response)
        }
        
        self.conversation_history.append(turn)
        
        # Update topic tracking
        self.topic_tracking.update(turn)
        
        # Compress context if needed
        if self._context_size_exceeded():
            self._compress_context_intelligently()
    
    def get_relevant_context(self, current_query: str) -> str:
        """Retrieve most relevant context for current query"""
        if not self.conversation_history:
            return ""
            
        # Get recent turns
        recent_turns = list(self.conversation_history)[-5:]
        
        context_summary = "Recent conversation:\n"
        for turn in recent_turns:
            context_summary += f"Human: {turn['user_input'][:100]}...\n"
            context_summary += f"Claude: {turn['bot_response'][:100]}...\n\n"
            
        return context_summary
        
    def _calculate_importance(self, user_input: str, bot_response: str) -> float:
        """Calculate turn importance for context retention"""
        importance = 0.5  # Base importance
        
        # Important keywords increase importance
        important_words = ['help', 'problem', 'error', 'issue', 'understand', 'explain']
        for word in important_words:
            if word in user_input.lower():
                importance += 0.1
                
        # Longer responses might be more important
        if len(bot_response) > 200:
            importance += 0.1
            
        return min(importance, 1.0)
        
    def _context_size_exceeded(self) -> bool:
        """Check if context needs compression"""
        # Simple heuristic - in production, count tokens
        total_chars = sum(len(turn['user_input']) + len(turn['bot_response']) 
                         for turn in self.conversation_history)
        return total_chars > 5000
        
    def _compress_context_intelligently(self):
        """Intelligently compress context while preserving important information"""
        # Remove least important turns
        sorted_turns = sorted(self.conversation_history, key=lambda x: x['importance'])
        # Keep the most important half
        keep_count = len(sorted_turns) // 2
        important_turns = sorted_turns[-keep_count:]
        
        # Sort back by timestamp
        important_turns.sort(key=lambda x: x['timestamp'])
        
        self.conversation_history.clear()
        self.conversation_history.extend(important_turns)


class TopicTracker:
    """Tracks conversation topics for better context management"""
    
    def __init__(self):
        self.current_topic = ConversationTopic.GENERAL
        self.topic_history = []
        
    def identify_topic(self, user_input: str) -> ConversationTopic:
        """Identify the topic of user input"""
        input_lower = user_input.lower()
        
        # Technical keywords
        if any(word in input_lower for word in ['algorithm', 'machine learning', 'ai', 'technical', 'system']):
            return ConversationTopic.TECHNICAL
            
        # Coding keywords  
        if any(word in input_lower for word in ['code', 'function', 'python', 'programming', 'debug']):
            return ConversationTopic.CODING
            
        # Cognitive keywords
        if any(word in input_lower for word in ['focus', 'memory', 'cognitive', 'thinking', 'neurodivergent']):
            return ConversationTopic.COGNITIVE
            
        # Creative keywords
        if any(word in input_lower for word in ['creative', 'brainstorm', 'idea', 'write', 'story']):
            return ConversationTopic.CREATIVE
            
        # Problem-solving keywords
        if any(word in input_lower for word in ['problem', 'solve', 'issue', 'analyze', 'solution']):
            return ConversationTopic.PROBLEM_SOLVING
            
        return ConversationTopic.GENERAL
        
    def update(self, turn: Dict):
        """Update topic tracking with new turn"""
        topic = self.identify_topic(turn['user_input'])
        self.current_topic = topic
        self.topic_history.append({
            'topic': topic,
            'timestamp': turn['timestamp']
        })


class ConversationMemory:
    """Long-term memory for important conversation elements"""
    
    def __init__(self):
        self.important_facts = []
        self.user_preferences = {}
        self.recurring_topics = {}
        
    def store_important_fact(self, fact: str, context: Dict):
        """Store important information for future reference"""
        self.important_facts.append({
            'fact': fact,
            'timestamp': time.time(),
            'context': context
        })
        
    def get_relevant_memories(self, query: str) -> List[str]:
        """Retrieve relevant stored memories"""
        # Simple keyword matching - in production, use semantic similarity
        relevant = []
        query_words = query.lower().split()
        
        for fact in self.important_facts:
            if any(word in fact['fact'].lower() for word in query_words):
                relevant.append(fact['fact'])
                
        return relevant[:3]  # Return top 3 relevant memories


class ConversationSafetyFilter:
    """Safety and content filtering for responses"""
    
    def __init__(self):
        self.harmful_patterns = [
            r'harmful\s+content',
            r'illegal\s+activity',
            r'violence',
            r'hate\s+speech'
        ]
        
    def check_safety(self, response: str) -> List[str]:
        """Check response for safety issues"""
        flags = []
        
        for pattern in self.harmful_patterns:
            if re.search(pattern, response.lower()):
                flags.append(f"Potential harmful content: {pattern}")
                
        # Check for overly personal information requests
        if any(phrase in response.lower() for phrase in ['give me your password', 'personal information']):
            flags.append("Requests personal information")
            
        return flags
        
    def filter_response(self, response: str) -> str:
        """Apply safety filtering to response"""
        flags = self.check_safety(response)
        
        if flags:
            return "I can't provide that type of response. Let me help you with something else instead."
            
        return response


class SonaCognitiveIntegration:
    """Integrates Claude-like chatbot with Sona's cognitive programming features"""
    
    def __init__(self, cognitive_assistant):
        self.cognitive_assistant = cognitive_assistant
        
    def enhance_response_with_cognitive_awareness(self, 
                                                 response: str, 
                                                 user_context: UserContext) -> str:
        """Add Sona's cognitive programming insights to Claude-like responses"""
        
        enhanced_response = response
        
        # Analyze cognitive load
        if self._shows_cognitive_stress(user_context):
            enhanced_response = self._add_cognitive_support(enhanced_response)
            
        # Suggest Sona cognitive features when relevant
        if self._detect_coding_struggle(user_context):
            enhanced_response += "\n\n💡 Consider using Sona's thinking() blocks to organize your approach."
            
        # Add break suggestions
        if self._should_suggest_break(user_context):
            enhanced_response += "\n\n🧠 You've been working hard - consider taking a short break!"
            
        return enhanced_response
        
    def _shows_cognitive_stress(self, context: UserContext) -> bool:
        """Detect signs of cognitive stress"""
        return (context.current_session_duration > 3600 or  # Over 1 hour
                context.cognitive_state in [context.cognitive_state.OVERWHELMED, 
                                           context.cognitive_state.DISTRACTED])
        
    def _add_cognitive_support(self, response: str) -> str:
        """Add cognitive support messaging"""
        support_msg = "\n\n🧠 I notice you might be feeling overwhelmed. Let's break this down into smaller, manageable steps."
        return response + support_msg
        
    def _detect_coding_struggle(self, context: UserContext) -> bool:
        """Detect if user is struggling with coding tasks"""
        recent_inputs = [turn.get('user_input', '') for turn in context.conversation_history[-3:]]
        struggle_indicators = ['stuck', 'confused', 'not working', 'error', 'help']
        
        return any(indicator in ' '.join(recent_inputs).lower() for indicator in struggle_indicators)
        
    def _should_suggest_break(self, context: UserContext) -> bool:
        """Determine if a break should be suggested"""
        return (context.current_session_duration > 2400 and  # Over 40 minutes
                context.cognitive_state == context.cognitive_state.FOCUSED)
