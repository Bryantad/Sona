"""
Claude-like Conversation Engine - Main Implementation
===================================================

Production-grade conversational AI engine that delivers Claude-like responses
using Sona's existing GPT-2 CUDA infrastructure.

This is the main conversation engine that orchestrates all components to
achieve Claude-like conversation quality with 8.5/10 target performance.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import Sona's existing components
try:
    from .gpt2_integration import GPT2Integration
    from .cognitive_assistant import CognitiveAssistant
except ImportError:
    # Use our new Claude-optimized GPT-2 integration
    from .gpt2_integration_claude import GPT2Integration
    from .cognitive_assistant import CognitiveAssistant

# Import our Claude-like components
from .quality_evaluator import QualityEvaluator, QualityMetrics

logger = logging.getLogger(__name__)


class ConversationResponse:
    """Enhanced response structure for Claude-like interactions"""
    
    def __init__(self, content: str, quality_score: float = 0.0, 
                 confidence_score: float = 0.0, generation_time: float = 0.0,
                 context_tokens_used: int = 0, safety_score: float = 10.0,
                 reasoning_trace: List[str] = None, engagement_level: float = 0.0):
        self.content = content
        self.quality_score = quality_score
        self.confidence_score = confidence_score
        self.generation_time = generation_time
        self.context_tokens_used = context_tokens_used
        self.safety_score = safety_score
        self.reasoning_trace = reasoning_trace or []
        self.engagement_level = engagement_level


class ConversationContext:
    """Manages conversation context and history"""
    
    def __init__(self, user_id: str, conversation_history: List[Dict] = None):
        self.user_id = user_id
        self.conversation_history = conversation_history or []
        self.session_start = datetime.now()
        self.total_turns = len(self.conversation_history)
        self.context_summary = ""
        self.user_preferences = {}


class ClaudeLikeConversationEngine:
    """
    Main conversation engine that orchestrates Claude-like responses
    
    Integrates:
    - GPT-2 text generation
    - Claude-style prompt engineering
    - Quality evaluation and improvement
    - Conversation context management
    - Performance optimization
    """
    
    def __init__(self, gpt2_integration: GPT2Integration = None):
        # Core components
        self.gpt2 = gpt2_integration or GPT2Integration()
        self.quality_evaluator = QualityEvaluator()
        
        # Try to load cognitive assistant if available
        try:
            self.cognitive_assistant = CognitiveAssistant()
        except:
            self.cognitive_assistant = None
            logger.warning("Cognitive assistant not available")
        
        # Claude-style prompt templates
        self.claude_prompts = self._initialize_claude_prompts()
        
        # Performance tracking
        self.performance_metrics = {
            'total_conversations': 0,
            'average_quality_score': 0.0,
            'average_response_time': 0.0,
            'quality_scores': [],
            'response_times': [],
            'target_quality': 8.5,
            'target_response_time': 0.5
        }
        
        logger.info("Claude-like Conversation Engine initialized")
    
    def _initialize_claude_prompts(self) -> Dict:
        """Initialize Claude-style prompt templates"""
        return {
            'system_prompt': """You are Claude, a helpful and thoughtful AI assistant. You are known for:
- Providing detailed, step-by-step explanations
- Being genuinely helpful and supportive
- Showing your reasoning process clearly
- Asking clarifying questions when needed
- Using examples to illustrate concepts
- Being warm and empathetic in your responses

When responding, think carefully about what would be most helpful to the user.""",
            
            'reasoning_templates': [
                "Let me think through this step by step:",
                "I'll break this down systematically:",
                "Here's how I'd approach this:",
                "Let me work through this with you:"
            ],
            
            'clarification_templates': [
                "To make sure I understand correctly,",
                "Just to clarify,", 
                "Could you help me understand",
                "I want to make sure I'm addressing"
            ],
            
            'supportive_templates': [
                "That's a thoughtful question.",
                "I understand why this might be confusing.",
                "This is actually a common challenge.",
                "You're asking about something important."
            ]
        }
    
    async def generate_response(self, 
                              user_input: str, 
                              user_id: str = "default_user",
                              conversation_history: List[Dict] = None) -> ConversationResponse:
        """
        Main response generation method
        
        Process:
        1. Prepare conversation context
        2. Create Claude-style prompt
        3. Generate response using GPT-2
        4. Evaluate and refine quality
        5. Add cognitive support if needed
        6. Return enhanced response
        """
        
        start_time = time.time()
        
        try:
            # Step 1: Prepare context
            context = ConversationContext(user_id, conversation_history)
            
            # Step 2: Create Claude-style prompt
            claude_prompt = self._create_claude_prompt(user_input, context)
            
            # Step 3: Generate initial response
            raw_response, generation_metrics = await self.gpt2.generate_text(
                prompt=claude_prompt,
                max_tokens=200,
                temperature=0.7,
                top_p=0.9
            )
            
            # Step 4: Clean and enhance response
            enhanced_response = self._enhance_response_with_claude_patterns(
                raw_response, user_input, context
            )
            
            # Step 5: Evaluate quality
            quality_metrics = self.quality_evaluator.evaluate_response(
                enhanced_response, user_input, {'context': context}
            )
            
            # Step 6: Add cognitive support if available
            if self.cognitive_assistant:
                enhanced_response = self._add_cognitive_support(
                    enhanced_response, user_input, context
                )
            
            # Step 7: Calculate final metrics
            total_time = time.time() - start_time
            confidence_score = self._calculate_confidence_score(
                quality_metrics.overall_score, generation_metrics
            )
            
            # Create response object
            response = ConversationResponse(
                content=enhanced_response,
                quality_score=quality_metrics.overall_score,
                confidence_score=confidence_score,
                generation_time=total_time,
                context_tokens_used=len(claude_prompt.split()),
                reasoning_trace=quality_metrics.detailed_feedback,
                engagement_level=quality_metrics.engagement
            )
            
            # Update performance tracking
            self._update_performance_metrics(response)
            
            logger.info(f"Generated response: Quality={quality_metrics.overall_score:.1f}/10, "
                       f"Time={total_time:.3f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in response generation: {str(e)}")
            return self._create_error_response(str(e), time.time() - start_time)
    
    def _create_claude_prompt(self, user_input: str, context: ConversationContext) -> str:
        """Create a Claude-optimized prompt for GPT-2"""
        
        # Start with system prompt
        prompt_parts = [self.claude_prompts['system_prompt']]
        
        # Add conversation context if available
        if context.conversation_history:
            prompt_parts.append("Previous conversation:")
            for turn in context.conversation_history[-3:]:  # Last 3 turns
                prompt_parts.append(f"Human: {turn.get('user_input', '')}")
                prompt_parts.append(f"Claude: {turn.get('bot_response', '')}")
        
        # Add current query with Claude-style introduction
        reasoning_intro = self._select_reasoning_template(user_input)
        prompt_parts.extend([
            f"Human: {user_input}",
            f"Claude: {reasoning_intro}"
        ])
        
        return "\n\n".join(prompt_parts)
    
    def _select_reasoning_template(self, user_input: str) -> str:
        """Select appropriate reasoning template based on user input"""
        user_lower = user_input.lower()
        
        # Complex questions need systematic breakdown
        if any(word in user_lower for word in ['how', 'why', 'explain', 'analyze']):
            return "Let me think through this step by step."
        
        # Unclear requests need clarification
        if len(user_input.split()) < 3 or '?' not in user_input:
            return "To make sure I understand correctly,"
        
        # Support-seeking requests need empathy
        if any(word in user_lower for word in ['help', 'stuck', 'confused', 'problem']):
            return "I understand this can be challenging. Let me help you work through this."
        
        # Default to thoughtful approach
        return "I'd be happy to help with that."
    
    def _enhance_response_with_claude_patterns(self, response: str, 
                                             user_input: str, 
                                             context: ConversationContext) -> str:
        """Enhance GPT-2 response with Claude-like patterns"""
        
        enhanced = response.strip()
        
        # Ensure appropriate greeting/acknowledgment
        if not any(phrase in enhanced.lower() for phrase in 
                  ['i understand', 'great question', 'i\'d be happy', 'let me']):
            enhanced = "I'd be happy to help with that. " + enhanced
        
        # Add examples if explaining concepts
        if any(word in user_input.lower() for word in ['what', 'how', 'explain']):
            if 'example' not in enhanced.lower() and len(enhanced) > 100:
                enhanced = self._add_example_if_appropriate(enhanced, user_input)
        
        # Add follow-up engagement
        if not enhanced.endswith('?') and len(enhanced) > 50:
            enhanced += self._add_followup_question(user_input)
        
        # Ensure proper structure for long responses
        if len(enhanced) > 200:
            enhanced = self._improve_response_structure(enhanced)
        
        return enhanced
    
    def _add_example_if_appropriate(self, response: str, user_input: str) -> str:
        """Add an example to the response if it would be helpful"""
        # Simple heuristic - in production, this would be more sophisticated
        if any(word in user_input.lower() for word in ['code', 'program', 'function']):
            if 'example' not in response.lower():
                response += "\n\nFor example, if you're working with Python, you might start with something like this."
        return response
    
    def _add_followup_question(self, user_input: str) -> str:
        """Add an appropriate follow-up question"""
        followup_options = [
            "\n\nWould you like me to elaborate on any particular aspect?",
            "\n\nIs there a specific part you'd like me to explain further?",
            "\n\nDoes this help address your question?",
            "\n\nWhat would be most helpful to explore next?"
        ]
        
        # Select based on input type
        if any(word in user_input.lower() for word in ['technical', 'complex', 'detail']):
            return followup_options[1]
        elif 'help' in user_input.lower():
            return followup_options[3]
        else:
            return followup_options[0]
    
    def _improve_response_structure(self, response: str) -> str:
        """Improve the structure of longer responses"""
        # Add paragraph breaks for readability
        sentences = response.split('. ')
        if len(sentences) > 4:
            # Group sentences into paragraphs
            paragraphs = []
            current_paragraph = []
            
            for i, sentence in enumerate(sentences):
                current_paragraph.append(sentence if sentence.endswith('.') else sentence + '.')
                
                # Start new paragraph every 2-3 sentences
                if (i + 1) % 3 == 0 or i == len(sentences) - 1:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
            
            response = '\n\n'.join(paragraphs)
        
        return response
    
    def _add_cognitive_support(self, response: str, user_input: str, 
                             context: ConversationContext) -> str:
        """Add cognitive programming support if appropriate"""
        if not self.cognitive_assistant:
            return response
        
        # Check if user seems overwhelmed
        if any(word in user_input.lower() for word in ['overwhelmed', 'confused', 'stuck']):
            response += "\n\n💡 If this feels overwhelming, try breaking it down into smaller steps. "
            response += "Sona's thinking() blocks can help organize your approach."
        
        # Suggest focus techniques for long tasks
        if any(word in user_input.lower() for word in ['focus', 'concentrate', 'distracted']):
            response += "\n\n🧠 For better focus, consider using Sona's focus_mode() to minimize distractions."
        
        return response
    
    def _calculate_confidence_score(self, quality_score: float, 
                                  generation_metrics: Dict) -> float:
        """Calculate confidence score based on quality and generation metrics"""
        base_confidence = quality_score / 10.0
        
        # Adjust based on generation speed (faster = more confident)
        speed_factor = min(generation_metrics.get('generation_time', 1.0), 1.0)
        confidence_adjustment = (1.0 - speed_factor) * 0.1
        
        return min(base_confidence + confidence_adjustment, 1.0)
    
    def _update_performance_metrics(self, response: ConversationResponse):
        """Update running performance metrics"""
        self.performance_metrics['total_conversations'] += 1
        self.performance_metrics['quality_scores'].append(response.quality_score)
        self.performance_metrics['response_times'].append(response.generation_time)
        
        # Calculate running averages
        total = self.performance_metrics['total_conversations']
        self.performance_metrics['average_quality_score'] = (
            sum(self.performance_metrics['quality_scores']) / total
        )
        self.performance_metrics['average_response_time'] = (
            sum(self.performance_metrics['response_times']) / total
        )
    
    def _create_error_response(self, error_message: str, 
                             generation_time: float) -> ConversationResponse:
        """Create error response in proper format"""
        return ConversationResponse(
            content="I apologize, but I'm having trouble generating a response right now. Could you please try rephrasing your question?",
            quality_score=2.0,
            confidence_score=0.1,
            generation_time=generation_time,
            reasoning_trace=[f"Error: {error_message}"]
        )
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        metrics = self.performance_metrics
        
        return {
            'total_conversations': metrics['total_conversations'],
            'average_quality_score': f"{metrics['average_quality_score']:.1f}/10",
            'average_response_time': f"{metrics['average_response_time']:.3f}s",
            'quality_target': f"{metrics['target_quality']}/10",
            'time_target': f"{metrics['target_response_time']}s",
            'quality_status': self._get_quality_status(),
            'time_status': self._get_time_status(),
            'overall_performance': self._get_overall_status()
        }
    
    def _get_quality_status(self) -> str:
        """Get quality performance status"""
        avg_quality = self.performance_metrics['average_quality_score']
        target = self.performance_metrics['target_quality']
        
        if avg_quality >= target:
            return f"🏆 Excellent - {avg_quality:.1f}/10 (target: {target}/10)"
        elif avg_quality >= target - 0.5:
            return f"✅ Good - {avg_quality:.1f}/10 (target: {target}/10)"
        else:
            return f"⚠️ Below target - {avg_quality:.1f}/10 (target: {target}/10)"
    
    def _get_time_status(self) -> str:
        """Get response time performance status"""
        avg_time = self.performance_metrics['average_response_time']
        target = self.performance_metrics['target_response_time']
        
        if avg_time <= target:
            return f"🏆 Excellent - {avg_time:.3f}s (target: {target}s)"
        elif avg_time <= target + 0.2:
            return f"✅ Good - {avg_time:.3f}s (target: {target}s)"
        else:
            return f"⚠️ Slow - {avg_time:.3f}s (target: {target}s)"
    
    def _get_overall_status(self) -> str:
        """Get overall performance status"""
        avg_quality = self.performance_metrics['average_quality_score']
        avg_time = self.performance_metrics['average_response_time']
        
        quality_good = avg_quality >= 8.0
        time_good = avg_time <= 0.7
        
        if quality_good and time_good:
            return "🏆 Production Ready - Claude-like quality achieved!"
        elif quality_good or time_good:
            return "✅ Good Performance - One metric needs improvement"
        else:
            return "⚠️ Needs Optimization - Both metrics below target"


class ClaudeChatbotDemo:
    """
    Interactive demo for the Claude-like chatbot
    Implements the interface expected by the test suite
    """
    
    def __init__(self):
        self.engine = ClaudeLikeConversationEngine()
        self.conversation_history = []
        
    async def run_demo(self):
        """Run interactive demo"""
        print("🤖 Claude-like Chatbot Demo for Sona v0.8.2")
        print("=" * 50)
        print("💡 Experience Claude-like conversation patterns!")
        print("🚀 Powered by optimized GPT-2 CUDA infrastructure")
        print()
        print("Commands: 'quit', 'stats', 'clear', 'help'")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'stats':
                    self.display_performance_metrics()
                    continue
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("🧹 Conversation cleared!")
                    continue
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif not user_input:
                    continue
                
                # Generate response
                print("Claude: ", end="", flush=True)
                response = await self.engine.generate_response(
                    user_input=user_input,
                    conversation_history=self.conversation_history
                )
                
                print(response.content)
                print(f"📊 Quality: {response.quality_score:.1f}/10 | "
                      f"Time: {response.generation_time:.3f}s")
                print()
                
                # Update history
                self.conversation_history.append({
                    'user_input': user_input,
                    'bot_response': response.content,
                    'timestamp': time.time()
                })
                
            except KeyboardInterrupt:
                print("\n👋 Demo ended")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def display_performance_metrics(self):
        """Display current performance metrics"""
        report = self.engine.get_performance_report()
        print("\n📊 Performance Metrics:")
        print("-" * 30)
        for key, value in report.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print()
    
    def _show_help(self):
        """Show help information"""
        print("\n🤖 Claude-like Chatbot Help")
        print("-" * 30)
        print("This chatbot delivers Claude-like conversation patterns:")
        print("• Thoughtful, step-by-step reasoning")
        print("• Clear explanations with examples")
        print("• Helpful follow-up questions")
        print("• Empathetic and supportive responses")
        print("• Integration with Sona's cognitive features")
        print()


# Main execution for testing
async def main():
    """Main function for testing the conversation engine"""
    demo = ClaudeChatbotDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
