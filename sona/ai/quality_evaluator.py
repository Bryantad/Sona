"""
Quality Evaluator for Claude-like Responses
==========================================

Automated response quality assessment system targeting 8.5/10 quality scores
for Claude-like conversational AI responses.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ResponseCategory(Enum):
    HELPFUL = "helpful"
    CLEAR = "clear"  
    THOUGHTFUL = "thoughtful"
    EMPATHETIC = "empathetic"
    ACCURATE = "accurate"
    ENGAGING = "engaging"


@dataclass
class QualityMetrics:
    """Detailed quality assessment metrics"""
    overall_score: float
    helpfulness: float
    clarity: float
    thoughtfulness: float
    empathy: float
    accuracy: float
    engagement: float
    detailed_feedback: list[str]
    improvement_suggestions: list[str]


class QualityEvaluator:
    """
    Evaluates response quality using Claude-like criteria
    Target: 8.5/10 overall quality score
    """
    
    def __init__(self):
        self.quality_patterns = self._load_quality_patterns()
        self.evaluation_weights = {
            'helpfulness': 0.25,    # 25% - Most important
            'clarity': 0.20,       # 20% - Very important
            'thoughtfulness': 0.20, # 20% - Claude's hallmark
            'empathy': 0.15,       # 15% - Human connection
            'accuracy': 0.15,      # 15% - Factual correctness
            'engagement': 0.05     # 5% - Follow-up potential
        }
    
    def _load_quality_patterns(self) -> dict:
        """Load patterns that indicate quality responses"""
        return {
            'helpfulness_indicators': [
                'let me help', 'i can assist', 'here\'s how', 'step by step',
                'i\'ll show you', 'to solve this', 'the solution is',
                'you can try', 'i recommend', 'this will help'
            ],
            'clarity_indicators': [
                'first', 'second', 'then', 'next', 'finally',
                'in other words', 'to clarify', 'simply put',
                'the key point', 'the main idea', 'essentially'
            ],
            'thoughtfulness_indicators': [
                'let me think', 'considering', 'it depends',
                'on one hand', 'however', 'alternatively',
                'it\'s worth noting', 'keep in mind', 'importantly'
            ],
            'empathy_indicators': [
                'i understand', 'that sounds', 'i can see',
                'it\'s natural to', 'many people', 'you\'re not alone',
                'that\'s frustrating', 'i appreciate', 'great question'
            ],
            'engagement_indicators': [
                '?', 'would you like', 'what do you think',
                'let me know', 'feel free to ask', 'any questions',
                'want to explore', 'shall we', 'how about'
            ]
        }
    
    def evaluate_response(self, response: str, user_input: str, 
                         context: dict = None) -> QualityMetrics:
        """
        Comprehensive response quality evaluation
        
        Args:
            response: The AI response to evaluate
            user_input: The original user question/input
            context: Additional context (conversation history, user profile, etc.)
        
        Returns:
            QualityMetrics with detailed scoring and feedback
        """
        
        # Individual quality assessments
        helpfulness = self._evaluate_helpfulness(response, user_input)
        clarity = self._evaluate_clarity(response)
        thoughtfulness = self._evaluate_thoughtfulness(response)
        empathy = self._evaluate_empathy(response, user_input)
        accuracy = self._evaluate_accuracy(response, user_input)
        engagement = self._evaluate_engagement(response)
        
        # Calculate weighted overall score
        overall_score = (
            helpfulness * self.evaluation_weights['helpfulness'] +
            clarity * self.evaluation_weights['clarity'] +
            thoughtfulness * self.evaluation_weights['thoughtfulness'] +
            empathy * self.evaluation_weights['empathy'] +
            accuracy * self.evaluation_weights['accuracy'] +
            engagement * self.evaluation_weights['engagement']
        )
        
        # Generate feedback and suggestions
        feedback = self._generate_detailed_feedback(
            helpfulness, clarity, thoughtfulness, empathy, accuracy, engagement
        )
        
        suggestions = self._generate_improvement_suggestions(
            response, helpfulness, clarity, thoughtfulness, empathy, accuracy, engagement
        )
        
        return QualityMetrics(
            overall_score=overall_score,
            helpfulness=helpfulness,
            clarity=clarity,
            thoughtfulness=thoughtfulness,
            empathy=empathy,
            accuracy=accuracy,
            engagement=engagement,
            detailed_feedback=feedback,
            improvement_suggestions=suggestions
        )
    
    def _evaluate_helpfulness(self, response: str, user_input: str) -> float:
        """Evaluate how helpful the response is (0-10 scale)"""
        score = 5.0  # Base score
        response_lower = response.lower()
        
        # Check for direct helpfulness indicators
        help_indicators = self.quality_patterns['helpfulness_indicators']
        indicator_count = sum(1 for indicator in help_indicators 
                            if indicator in response_lower)
        score += min(indicator_count * 0.5, 2.0)
        
        # Check if response addresses the user's question
        user_keywords = set(user_input.lower().split())
        response_keywords = set(response.lower().split())
        relevance = len(user_keywords & response_keywords) / max(len(user_keywords), 1)
        score += relevance * 2.0
        
        # Bonus for providing examples or concrete steps
        if 'example' in response_lower or 'for instance' in response_lower:
            score += 0.5
        if re.search(r'\d+\.', response):  # Numbered steps
            score += 0.5
        
        # Length consideration - too short might not be helpful
        if len(response) < 50:
            score -= 1.0
        elif len(response) > 200:
            score += 0.5
        
        return min(max(score, 0.0), 10.0)
    
    def _evaluate_clarity(self, response: str) -> float:
        """Evaluate response clarity and structure (0-10 scale)"""
        score = 5.0  # Base score
        response_lower = response.lower()
        
        # Check for clarity indicators
        clarity_indicators = self.quality_patterns['clarity_indicators']
        indicator_count = sum(1 for indicator in clarity_indicators 
                            if indicator in response_lower)
        score += min(indicator_count * 0.4, 2.0)
        
        # Check sentence structure
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Optimal sentence length is 15-25 words
        if 15 <= avg_sentence_length <= 25:
            score += 1.0
        elif avg_sentence_length > 35:
            score -= 1.0  # Too complex
        
        # Check for organization (bullet points, numbers, sections)
        if re.search(r'[•\-\*]', response) or re.search(r'\d+\.', response):
            score += 1.0
        
        # Check for transitions and connectors
        transitions = ['however', 'therefore', 'additionally', 'furthermore', 'meanwhile']
        if any(trans in response_lower for trans in transitions):
            score += 0.5
        
        return min(max(score, 0.0), 10.0)
    
    def _evaluate_thoughtfulness(self, response: str) -> float:
        """Evaluate depth of reasoning and consideration (0-10 scale)"""
        score = 5.0  # Base score
        response_lower = response.lower()
        
        # Check for thoughtfulness indicators
        thought_indicators = self.quality_patterns['thoughtfulness_indicators']
        indicator_count = sum(1 for indicator in thought_indicators 
                            if indicator in response_lower)
        score += min(indicator_count * 0.6, 2.5)
        
        # Check for reasoning patterns
        reasoning_patterns = [
            'because', 'since', 'therefore', 'as a result',
            'this means', 'consequently', 'due to'
        ]
        reasoning_count = sum(1 for pattern in reasoning_patterns 
                            if pattern in response_lower)
        score += min(reasoning_count * 0.3, 1.5)
        
        # Check for consideration of alternatives
        alternative_phrases = ['alternatively', 'on the other hand', 'another option',
                             'you could also', 'another approach']
        if any(phrase in response_lower for phrase in alternative_phrases):
            score += 1.0
        
        # Bonus for showing uncertainty appropriately
        uncertainty_phrases = ['i think', 'it seems', 'might be', 'possibly']
        if any(phrase in response_lower for phrase in uncertainty_phrases):
            score += 0.5
        
        return min(max(score, 0.0), 10.0)
    
    def _evaluate_empathy(self, response: str, user_input: str) -> float:
        """Evaluate empathetic and supportive tone (0-10 scale)"""
        score = 5.0  # Base score
        response_lower = response.lower()
        user_lower = user_input.lower()
        
        # Check for empathy indicators
        empathy_indicators = self.quality_patterns['empathy_indicators']
        indicator_count = sum(1 for indicator in empathy_indicators 
                            if indicator in response_lower)
        score += min(indicator_count * 0.5, 2.0)
        
        # Detect if user seems frustrated or confused
        frustration_indicators = ['stuck', 'confused', 'frustrated', 'help', 'problem']
        user_shows_frustration = any(indicator in user_lower 
                                   for indicator in frustration_indicators)
        
        if user_shows_frustration:
            # Check for appropriate supportive response
            supportive_phrases = ['understand', 'help you', 'work through',
                                'take it step by step', 'break it down']
            if any(phrase in response_lower for phrase in supportive_phrases):
                score += 1.5
        
        # Check for positive, encouraging language
        positive_phrases = ['great question', 'excellent point', 'good thinking',
                          'you\'re on the right track', 'that makes sense']
        if any(phrase in response_lower for phrase in positive_phrases):
            score += 1.0
        
        return min(max(score, 0.0), 10.0)
    
    def _evaluate_accuracy(self, response: str, user_input: str) -> float:
        """Evaluate factual accuracy and appropriateness (0-10 scale)"""
        score = 7.0  # Start with good baseline
        
        # This is a simplified accuracy check
        # In production, this would use fact-checking APIs
        
        # Check for confidence indicators
        confidence_phrases = ['i\'m certain', 'definitely', 'always', 'never']
        overconfident = any(phrase in response.lower() for phrase in confidence_phrases)
        
        if overconfident:
            score -= 1.0  # Penalize overconfidence
        
        # Check for appropriate uncertainty
        uncertainty_phrases = ['i believe', 'it seems', 'likely', 'probably']
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            score += 0.5  # Reward appropriate uncertainty
        
        # Check for disclaimers when appropriate
        if 'technical' in user_input.lower() or 'medical' in user_input.lower():
            disclaimers = ['consult', 'professional', 'expert', 'specialist']
            if any(disclaimer in response.lower() for disclaimer in disclaimers):
                score += 1.0
        
        return min(max(score, 0.0), 10.0)
    
    def _evaluate_engagement(self, response: str) -> float:
        """Evaluate how engaging and interactive the response is (0-10 scale)"""
        score = 5.0  # Base score
        response_lower = response.lower()
        
        # Check for engagement indicators
        engagement_indicators = self.quality_patterns['engagement_indicators']
        indicator_count = sum(1 for indicator in engagement_indicators 
                            if indicator in response_lower)
        score += min(indicator_count * 0.6, 3.0)
        
        # Count questions (indicates engagement)
        question_count = response.count('?')
        score += min(question_count * 0.5, 2.0)
        
        # Check for follow-up opportunities
        followup_phrases = ['what do you think', 'would you like to',
                          'shall we explore', 'want to try']
        if any(phrase in response_lower for phrase in followup_phrases):
            score += 1.0
        
        return min(max(score, 0.0), 10.0)
    
    def _generate_detailed_feedback(self, helpfulness: float, clarity: float, 
                                  thoughtfulness: float, empathy: float, 
                                  accuracy: float, engagement: float) -> list[str]:
        """Generate detailed feedback based on scores"""
        feedback = []
        
        score_map = {
            'Helpfulness': helpfulness,
            'Clarity': clarity,
            'Thoughtfulness': thoughtfulness,
            'Empathy': empathy,
            'Accuracy': accuracy,
            'Engagement': engagement
        }
        
        for category, score in score_map.items():
            if score >= 8.0:
                feedback.append(f"✅ {category}: Excellent ({score:.1f}/10)")
            elif score >= 6.5:
                feedback.append(f"👍 {category}: Good ({score:.1f}/10)")
            elif score >= 5.0:
                feedback.append(f"⚠️ {category}: Acceptable ({score:.1f}/10)")
            else:
                feedback.append(f"❌ {category}: Needs improvement ({score:.1f}/10)")
        
        return feedback
    
    def _generate_improvement_suggestions(self, response: str, helpfulness: float, 
                                        clarity: float, thoughtfulness: float, 
                                        empathy: float, accuracy: float, 
                                        engagement: float) -> list[str]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        if helpfulness < 7.0:
            suggestions.append("Add more concrete examples or step-by-step guidance")
        
        if clarity < 7.0:
            suggestions.append("Break down complex ideas into simpler parts")
            suggestions.append("Use bullet points or numbered lists for structure")
        
        if thoughtfulness < 7.0:
            suggestions.append("Show more reasoning process (e.g., 'Let me think through this...')")
            suggestions.append("Consider multiple perspectives or alternatives")
        
        if empathy < 7.0:
            suggestions.append("Use more understanding and supportive language")
            suggestions.append("Acknowledge the user's situation or feelings")
        
        if accuracy < 7.0:
            suggestions.append("Add appropriate disclaimers for technical/medical advice")
            suggestions.append("Express uncertainty when appropriate rather than overconfidence")
        
        if engagement < 7.0:
            suggestions.append("Ask follow-up questions to encourage dialogue")
            suggestions.append("Invite the user to share more or ask for clarification")
        
        return suggestions
    
    def get_quality_status(self, overall_score: float) -> str:
        """Get quality status description"""
        if overall_score >= 8.5:
            return "🏆 Excellent - Claude-like quality achieved!"
        elif overall_score >= 7.5:
            return "✅ Good - High quality response"
        elif overall_score >= 6.5:
            return "👍 Acceptable - Meets basic standards"
        elif overall_score >= 5.0:
            return "⚠️ Below target - Needs improvement"
        else:
            return "❌ Poor - Significant issues detected"
