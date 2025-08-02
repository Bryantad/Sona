"""
Main Claude-like Conversation Engine for Sona v0.8.2
===================================================

Production-grade conversational AI engine that leverages Sona's existing
GPT-2 CUDA infrastructure while providing Claude-like conversation patterns.
"""

import asyncio
import time
import logging
from typing import Dict, List
from datetime import datetime

from .gpt2_integration import GPT2Integration
from .cognitive_assistant import CognitiveAssistant
from .claude_like_chatbot import (
    ClaudeStylePromptEngine, ClaudeResponseRefinery,
    ConversationTopic, CognitiveState, UserContext, ConversationResponse
)
from .claude_chatbot_components import (
    AdvancedContextManager, ConversationSafetyFilter, 
    SonaCognitiveIntegration, TopicTracker
)

logger = logging.getLogger(__name__)


class ClaudeLikeConversationEngine:
    """
    Production-grade conversation processor leveraging Sona's GPT-2 CUDA setup
    """
    
    def __init__(self, gpt2_model_path: str = None):
        # Initialize core components
        self.gpt2_model = GPT2Integration(model_path=gpt2_model_path)
        self.cognitive_assistant = CognitiveAssistant()
        
        # Initialize Claude-like components
        self.prompt_engineer = ClaudeStylePromptEngine()
        self.response_refinery = ClaudeResponseRefinery()
        self.context_manager = AdvancedContextManager(max_turns=50)
        self.safety_filter = ConversationSafetyFilter()
        self.cognitive_integration = SonaCognitiveIntegration(self.cognitive_assistant)
        self.topic_tracker = TopicTracker()
        
        # Performance tracking
        self.conversation_metrics = {
            'total_conversations': 0,
            'average_response_time': 0.0,
            'average_quality_score': 0.0,
            'user_satisfaction_scores': []
        }
        
        logger.info("Claude-like Conversation Engine initialized")
        
    async def generate_response(self, 
                              user_input: str, 
                              user_id: str = "default_user",
                              conversation_history: List[Dict] = None) -> ConversationResponse:
        """
        Primary conversation pipeline:
        1. Analyze intent and determine reasoning approach
        2. Engineer Claude-style prompts for GPT-2 model
        3. Generate response using optimized CUDA pipeline
        4. Refine output to match Claude's conversational patterns
        5. Apply safety filters and quality assurance
        """
        
        start_time = time.time()
        
        try:
            # Step 1: Prepare user context
            user_context = await self._prepare_user_context(user_id, user_input, conversation_history)
            
            # Step 2: Identify conversation topic
            topic = self.topic_tracker.identify_topic(user_input)
            logger.info(f"Identified topic: {topic}")
            
            # Step 3: Engineer Claude-style prompt
            engineered_prompt = self.prompt_engineer.engineer_prompt(
                user_input, user_context, topic
            )
            
            # Step 4: Generate response using GPT-2
            raw_response = await self._generate_gpt2_response(engineered_prompt)
            
            # Step 5: Refine response to Claude-like quality
            refined_response = await self.response_refinery.refine_response(
                raw_response, 
                {
                    'user_input': user_input,
                    'topic': topic,
                    'user_context': user_context
                }
            )
            
            # Step 6: Apply safety filters
            safe_response = self.safety_filter.filter_response(refined_response.content)
            refined_response.content = safe_response
            
            # Step 7: Add cognitive programming integration
            enhanced_response = self.cognitive_integration.enhance_response_with_cognitive_awareness(
                refined_response.content, user_context
            )
            refined_response.content = enhanced_response
            
            # Step 8: Update context and metrics
            await self._update_conversation_state(user_input, refined_response, topic, user_context)
            
            # Step 9: Calculate final metrics
            total_time = time.time() - start_time
            refined_response.generation_time = total_time
            
            logger.info(f"Response generated in {total_time:.3f}s with quality {refined_response.quality_score:.1f}/10")
            
            return refined_response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._create_error_response(str(e), time.time() - start_time)
            
    async def _prepare_user_context(self, user_id: str, user_input: str, history: List[Dict]) -> UserContext:
        """Prepare comprehensive user context"""
        return UserContext(
            user_id=user_id,
            conversation_history=history or [],
            current_session_duration=self._calculate_session_duration(history),
            cognitive_state=self._analyze_cognitive_state(user_input, history),
            last_activity=datetime.now()
        )
        
    async def _generate_gpt2_response(self, prompt: str) -> str:
        """Generate response using Sona's optimized GPT-2 model"""
        try:
            # Use your existing GPT-2 integration
            response = self.gpt2_model.generate_completion(
                prompt=prompt,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True
            )
            
            # Extract just the response part (after "Claude:")
            if "Claude:" in response:
                response = response.split("Claude:")[-1].strip()
                
            return response
            
        except Exception as e:
            logger.error(f"GPT-2 generation error: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now. Could you please try again?"
            
    def _calculate_session_duration(self, history: List[Dict]) -> float:
        """Calculate current session duration"""
        if not history:
            return 0.0
            
        first_timestamp = history[0].get('timestamp', time.time())
        return time.time() - first_timestamp
        
    def _analyze_cognitive_state(self, user_input: str, history: List[Dict]) -> CognitiveState:
        """Analyze user's cognitive state from input patterns"""
        input_lower = user_input.lower()
        
        # Detect overwhelm
        if any(word in input_lower for word in ['overwhelmed', 'confused', 'too much', 'stuck']):
            return CognitiveState.OVERWHELMED
            
        # Detect distraction
        if any(word in input_lower for word in ['unfocused', 'distracted', 'can\'t concentrate']):
            return CognitiveState.DISTRACTED
            
        # Detect hyperfocus
        if len(user_input) > 500 or (history and len(history) > 10):
            return CognitiveState.HYPERFOCUS
            
        # Detect focused state
        if any(word in input_lower for word in ['focused', 'clear', 'understand', 'working on']):
            return CognitiveState.FOCUSED
            
        return CognitiveState.NORMAL
        
    async def _update_conversation_state(self, user_input: str, response: ConversationResponse, 
                                       topic: ConversationTopic, user_context: UserContext):
        """Update conversation state and metrics"""
        
        # Update context manager
        self.context_manager.update_context(user_input, response.content, topic)
        
        # Update topic tracker
        self.topic_tracker.update({
            'user_input': user_input,
            'timestamp': time.time()
        })
        
        # Update metrics
        self.conversation_metrics['total_conversations'] += 1
        self._update_performance_metrics(response)
        
    def _update_performance_metrics(self, response: ConversationResponse):
        """Update running performance metrics"""
        total = self.conversation_metrics['total_conversations']
        
        # Update average response time
        current_avg_time = self.conversation_metrics['average_response_time']
        new_avg_time = ((current_avg_time * (total - 1)) + response.generation_time) / total
        self.conversation_metrics['average_response_time'] = new_avg_time
        
        # Update average quality score
        current_avg_quality = self.conversation_metrics['average_quality_score']
        new_avg_quality = ((current_avg_quality * (total - 1)) + response.quality_score) / total
        self.conversation_metrics['average_quality_score'] = new_avg_quality
        
    def _create_error_response(self, error_message: str, generation_time: float) -> ConversationResponse:
        """Create error response in ConversationResponse format"""
        return ConversationResponse(
            content="I apologize, but I encountered an issue while processing your request. Please try again.",
            confidence_score=0.1,
            reasoning_trace=[f"Error: {error_message}"],
            context_used={},
            generation_time=generation_time,
            safety_flags=["error_response"],
            quality_score=2.0,
            engagement_level=0.3
        )
        
    def get_performance_report(self) -> Dict:
        """Get current performance metrics"""
        return {
            'total_conversations': self.conversation_metrics['total_conversations'],
            'average_response_time': f"{self.conversation_metrics['average_response_time']:.3f}s",
            'average_quality_score': f"{self.conversation_metrics['average_quality_score']:.1f}/10",
            'target_response_time': "0.5s",
            'target_quality_score': "8.5/10",
            'performance_status': self._get_performance_status()
        }
        
    def _get_performance_status(self) -> str:
        """Determine overall performance status"""
        avg_time = self.conversation_metrics['average_response_time']
        avg_quality = self.conversation_metrics['average_quality_score']
        
        if avg_time <= 0.5 and avg_quality >= 8.5:
            return "🏆 Excellent - Exceeding all targets"
        elif avg_time <= 0.7 and avg_quality >= 7.5:
            return "✅ Good - Meeting performance standards"
        elif avg_time <= 1.0 and avg_quality >= 6.5:
            return "⚠️ Acceptable - Below optimal performance"
        else:
            return "❌ Needs Improvement - Performance issues detected"


class ClaudeChatbotDemo:
    """Demo interface for testing the Claude-like chatbot"""
    
    def __init__(self):
        self.engine = ClaudeLikeConversationEngine()
        self.conversation_history = []
        
    async def interactive_demo(self):
        """Run interactive demo session"""
        print("🤖 Claude-like Chatbot Demo for Sona v0.8.2")
        print("=" * 50)
        print("Type 'quit' to exit, 'stats' for performance metrics")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'stats':
                    self._show_performance_stats()
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
                print(f"📊 Quality: {response.quality_score:.1f}/10 | Time: {response.generation_time:.3f}s")
                print()
                
                # Update history
                self.conversation_history.append({
                    'user_input': user_input,
                    'bot_response': response.content,
                    'timestamp': time.time()
                })
                
            except KeyboardInterrupt:
                print("\n👋 Demo ended by user")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
        self._show_final_report()
        
    def _show_performance_stats(self):
        """Display current performance statistics"""
        stats = self.engine.get_performance_report()
        print("\n📊 Performance Statistics:")
        print("-" * 30)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print()
        
    def _show_final_report(self):
        """Show final session report"""
        print("\n📋 Final Session Report:")
        print("=" * 30)
        stats = self.engine.get_performance_report()
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("\n🎯 Thank you for testing the Claude-like chatbot!")


async def main():
    """Main demo function"""
    demo = ClaudeChatbotDemo()
    await demo.interactive_demo()


if __name__ == "__main__":
    asyncio.run(main())
