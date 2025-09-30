"""
Sona 0.9.0 AI Integration Module
Integrates the trained SonaCore model (sona_70m_massive_20250704_181305)
into the cognitive programming environment.

This module provides:
- Real-time AI code assistance
- Cognitive-aware AI responses
- Intelligent error recovery with AI explanations
- Pattern recognition for neurodivergent coding strengths
- Multi-modal AI programming support

Model: sona_70m_massive_20250704_181305/checkpoint-10000 (70M parameters)
Training: Completed July 4, 2025 - 10, 000 steps over 12.78 epochs
"""

import json
import os
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from .cognitive_core import CognitiveProfile, FlowState, FlowStateManager
from .utils.debug import debug, warn

# Model configuration
TRAINED_MODEL_PATH = (
    r"F:\SfM1+\SfM-2-Core\training\retrained_model\sona_70m_massive_20250704_181305\checkpoint-10000"
)


class AIAssistanceType(Enum): """Types of AI assistance available"""

    CODE_COMPLETION = "code_completion"
    ERROR_EXPLANATION = "error_explanation"
    CONCEPT_EXPLANATION = "concept_explanation"
    DEBUGGING_HELP = "debugging_help"
    PATTERN_RECOGNITION = "pattern_recognition"
    COGNITIVE_SCAFFOLDING = "cognitive_scaffolding"
    WORKING_MEMORY_SUPPORT = "working_memory_support"


class CognitiveAIContext(Enum): """AI context aware of cognitive needs"""

    HYPERFOCUS_MODE = "hyperfocus"
    GENTLE_LEARNING = "gentle_learning"
    VISUAL_EXPLANATION = "visual_explanation"
    STEP_BY_STEP = "step_by_step"
    PATTERN_EXPLORATION = "pattern_exploration"
    EXECUTIVE_FUNCTION_SUPPORT = "executive_function"


@dataclass
class AIRequest: """Structured AI assistance request"""

    request_type: AIAssistanceType
    context: str
    cognitive_profile: Optional[CognitiveProfile] = None
    cognitive_context: Optional[CognitiveAIContext] = None
    max_length: int = 150
    temperature: float = 0.7
    priority: str = "normal"  # "low", "normal", "high", "urgent"


@dataclass
class AIResponse: """Structured AI response with cognitive enhancements"""

    generated_text: str
    confidence: float
    cognitive_adaptations: List[str]
    assistance_type: AIAssistanceType
    processing_time_ms: int
    model_used: str
    suggestions: List[str] = None
    visual_metaphors: List[str] = None
    next_steps: List[str] = None


class SonaAIAssistant: """Advanced AI assistant integrated with cognitive accessibility features"""

    def __init__(self, model_path: str = (
        TRAINED_MODEL_PATH): """Initialize the Sona AI Assistant with the trained model"""
    )
        self.model_path = Path(model_path)
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # Model components
        self.model = None
        self.tokenizer = None
        self.model_loaded = False

        # Performance tracking
        self.request_count = 0
        self.total_processing_time = 0
        self.cache = {}

        # Cognitive adaptations
        self.cognitive_patterns = {
            "adhd_hyperactive": {
                "max_length": 100,
                "temperature": 0.8,
                "emphasis": "quick_wins",
                "break_intervals": True,
            },
            "adhd_inattentive": {
                "max_length": 80,
                "temperature": 0.6,
                "emphasis": "step_by_step",
                "gentle_reminders": True,
            },
            "autism_detail_focused": {
                "max_length": 200,
                "temperature": 0.5,
                "emphasis": "comprehensive",
                "pattern_highlights": True,
            },
            "dyslexia_visual": {
                "max_length": 120,
                "temperature": 0.7,
                "emphasis": "visual_metaphors",
                "simplified_language": True,
            },
        }

        # Load the model
        self._load_model()

        debug(f"✅ SonaAI Assistant initialized with {self.model_path}")

    def _load_model(self): """Load the trained SonaCore model"""
        try: start_time = time.time()

            # Load tokenizer
            debug("Loading SonaCore tokenizer...")
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_path)

            if self.tokenizer.pad_token is None: self.tokenizer.pad_token = (
                self.tokenizer.eos_token
            )

            # Load model
            debug("Loading SonaCore model...")
            self.model = GPT2LMHeadModel.from_pretrained(
                self.model_path,
                torch_dtype = (
                    torch.float16
                    if torch.cuda.is_available()
                    else torch.float32
                ),
            )

            self.model.to(self.device)
            self.model.eval()

            load_time = time.time() - start_time
            self.model_loaded = True

            # Load model info if available
            config_path = self.model_path / "config.json"
            if config_path.exists(): with open(config_path, 'r') as f: config = (
                json.load(f)
            )
                    debug(
                        f"Model config: {config.get('model_type', 'Unknown')} - {config.get('n_layer', 'Unknown')} layers"
                    )

            debug(
                f"✅ SonaCore model loaded in {load_time:.2f}s on {self.device}"
            )

        except Exception as e: warn(f"Failed to load SonaCore model: {e}")
            self.model_loaded = False
            raise

    def generate_assistance(self, request: AIRequest) -> AIResponse: """Generate AI assistance response adapted to cognitive profile"""
        if not self.model_loaded: return self._fallback_response(request)

        start_time = time.time()

        try: # Adapt request based on cognitive profile
            adapted_request = self._adapt_request_for_cognition(request)

            # Generate response
            generated_text = self._generate_text(
                adapted_request.context,
                max_length = adapted_request.max_length,
                temperature = adapted_request.temperature,
            )

            # Post-process for cognitive accessibility
            processed_response = self._post_process_for_cognition(
                generated_text,
                request.cognitive_profile,
                request.cognitive_context,
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Create structured response
            response = AIResponse(
                generated_text = processed_response["text"],
                confidence = processed_response["confidence"],
                cognitive_adaptations = processed_response["adaptations"],
                assistance_type = request.request_type,
                processing_time_ms = processing_time,
                model_used = "sona_70m_massive_20250704_181305",
                suggestions = processed_response.get("suggestions", []),
                visual_metaphors = processed_response.get(
                    "visual_metaphors", []
                ),
                next_steps = processed_response.get("next_steps", []),
            )

            # Update statistics
            self.request_count + = 1
            self.total_processing_time + = processing_time

            return response

        except Exception as e: warn(f"AI generation failed: {e}")
            return self._fallback_response(request)

    def _generate_text(
        self, prompt: str, max_length: int = 150, temperature: float = 0.7
    ) -> str: """Generate text using the trained model"""
        # Tokenize input with attention mask
        encoded = self.tokenizer(
            prompt, return_tensors = "pt", padding = True, truncation = True
        )
        inputs = encoded['input_ids'].to(self.device)
        attention_mask = encoded['attention_mask'].to(self.device)

        # Generate with proper attention mask
        with torch.no_grad(): outputs = self.model.generate(
                inputs,
                attention_mask = attention_mask,
                max_length = len(inputs[0]) + max_length,
                temperature = temperature,
                top_p = 0.9,
                do_sample = True,
                pad_token_id = self.tokenizer.eos_token_id,
                eos_token_id = self.tokenizer.eos_token_id,
                no_repeat_ngram_size = 2,
            )

        # Decode response
        full_response = self.tokenizer.decode(
            outputs[0], skip_special_tokens = True
        )

        # Extract only the generated part
        generated_part = full_response[len(prompt) :].strip()

        return generated_part

    def _adapt_request_for_cognition(self, request: AIRequest) -> AIRequest: """Adapt AI request based on cognitive profile"""
        if not request.cognitive_profile: return request

        # Get cognitive pattern adaptations
        profile_key = (
            request.cognitive_profile.cognitive_styles[0].value
            if request.cognitive_profile.cognitive_styles
            else "default"
        )
        adaptations = self.cognitive_patterns.get(profile_key, {})

        # Create adapted request
        adapted = AIRequest(
            request_type = request.request_type,
            context = self._adapt_context_for_cognition(
                request.context, request.cognitive_profile
            ),
            cognitive_profile = request.cognitive_profile,
            cognitive_context = request.cognitive_context,
            max_length = adaptations.get("max_length", request.max_length),
            temperature = adaptations.get("temperature", request.temperature),
            priority = request.priority,
        )

        return adapted

    def _adapt_context_for_cognition(
        self, context: str, profile: CognitiveProfile
    ) -> str: """Adapt context prompt based on cognitive needs"""
        adaptations = []

        if profile.needs_gentle_language: adaptations.append("Please use gentle, supportive language.")

        if profile.prefers_step_by_step: adaptations.append("Break this down into clear, manageable steps.")

        if profile.prefers_visual_information: adaptations.append(
                "Include visual metaphors or analogies when helpful."
            )

        if profile.learns_by_example: adaptations.append("Provide concrete examples when possible.")

        if profile.needs_frequent_validation: adaptations.append("Include encouraging validation.")

        if adaptations: adapted_context = (
                f"{context}\n\nCognitive adaptations: {' '.join(adaptations)}"
            )
            return adapted_context

        return context

    def _post_process_for_cognition(
        self,
        text: str,
        profile: Optional[CognitiveProfile],
        context: Optional[CognitiveAIContext],
    ) -> Dict[str, Any]: """Post-process AI response for cognitive accessibility"""
        processed = {
            "text": text,
            "confidence": 0.85,  # Base confidence
            "adaptations": [],
            "suggestions": [],
            "visual_metaphors": [],
            "next_steps": [],
        }

        if not profile: return processed

        # Apply cognitive adaptations
        if profile.needs_gentle_language: processed["text"] = (
            self._make_language_gentle(text)
        )
            processed["adaptations"].append("gentle_language")

        if (
            profile.prefers_visual_information
            and context == CognitiveAIContext.VISUAL_EXPLANATION
        ): visual_metaphors = self._extract_or_add_metaphors(text)
            processed["visual_metaphors"] = visual_metaphors
            processed["adaptations"].append("visual_metaphors")

        if profile.prefers_step_by_step: next_steps = (
            self._extract_or_add_steps(text)
        )
            processed["next_steps"] = next_steps
            processed["adaptations"].append("step_by_step")

        if profile.learns_by_example: suggestions = (
            self._extract_or_add_examples(text)
        )
            processed["suggestions"] = suggestions
            processed["adaptations"].append("examples")

        return processed

    def _make_language_gentle(self, text: str) -> str: """Make language more gentle and supportive"""
        # Replace harsh language with gentle alternatives
        gentle_replacements = {
            "error": "something to adjust",
            "wrong": "needs a small change",
            "failed": "needs another try",
            "invalid": "could be refined",
            "bad": "could be improved",
            "incorrect": "close, but needs adjustment",
        }

        gentle_text = text
        for harsh, gentle in gentle_replacements.items(): gentle_text = (
            gentle_text.replace(harsh, gentle)
        )

        return gentle_text

    def _extract_or_add_metaphors(self, text: str) -> List[str]: """Extract or add visual metaphors"""
        metaphors = []

        # Look for existing metaphors
        if "like" in text.lower(): sentences = text.split('.')
            for sentence in sentences: if "like" in sentence.lower(): metaphors.append(sentence.strip())

        # Add programming metaphors if none found
        if not metaphors: metaphors = [
                "Think of variables like labeled boxes that store things",
                "Functions are like recipes - they take ingredients and create something new",
                "Loops are like doing the same dance move multiple times",
            ]

        return metaphors[:3]  # Limit to 3 metaphors

    def _extract_or_add_steps(self, text: str) -> List[str]: """Extract or add step-by-step guidance"""
        steps = []

        # Look for numbered steps
        lines = text.split('\n')
        for line in lines: line = line.strip()
            if line.startswith(
                ('1.', '2.', '3.', '4.', '5.')
            ) or line.startswith(('First', 'Next', 'Then', 'Finally')): steps.append(line)

        # Add generic next steps if none found
        if not steps: steps = [
                "Start with understanding the problem",
                "Break it into smaller pieces",
                "Try one piece at a time",
                "Test as you go",
            ]

        return steps[:4]  # Limit to 4 steps

    def _extract_or_add_examples(self, text: str) -> List[str]: """Extract or add concrete examples"""
        examples = []

        # Look for code examples or "for example" phrases
        if "example" in text.lower() or "```" in text: parts = (
            text.split("example")
        )
            if len(parts) > 1: examples.append(f"Example: {parts[1][:100]}...")

        # Add generic examples if none found
        if not examples: examples = [
                "Try starting with a simple version first",
                "Practice with familiar data",
                "Look at similar working code",
            ]

        return examples[:3]  # Limit to 3 examples

    def _fallback_response(self, request: AIRequest) -> AIResponse: """Provide fallback response when AI model unavailable"""
        fallback_responses = {
            AIAssistanceType.CODE_COMPLETION: "// AI code completion temporarily unavailable",
            AIAssistanceType.ERROR_EXPLANATION: "This error needs attention. Let's work through it step by step.",
            AIAssistanceType.CONCEPT_EXPLANATION: "This concept involves understanding the relationship between different parts.",
            AIAssistanceType.DEBUGGING_HELP: "For debugging, try checking each step carefully and testing small parts.",
            AIAssistanceType.PATTERN_RECOGNITION: "Look for repeating patterns or familiar structures in your code.",
            AIAssistanceType.COGNITIVE_SCAFFOLDING: "Break this down into smaller, manageable pieces.",
            AIAssistanceType.WORKING_MEMORY_SUPPORT: "Focus on one piece at a time and save your progress frequently.",
        }

        return AIResponse(
            generated_text = fallback_responses.get(
                request.request_type, "AI assistance temporarily unavailable"
            ),
            confidence = 0.3,
            cognitive_adaptations = ["fallback_mode"],
            assistance_type = request.request_type,
            processing_time_ms = 10,
            model_used = "fallback",
            suggestions = [
                "Try the operation again",
                "Check your cognitive profile settings",
            ],
            visual_metaphors = [],
            next_steps = (
                ["Verify AI model is loaded", "Check system resources"],
            )
        )

    def get_statistics(self) -> Dict[str, Any]: """Get AI assistant performance statistics"""
        avg_processing_time = self.total_processing_time / max(
            self.request_count, 1
        )

        return {
            "model_loaded": self.model_loaded,
            "model_path": str(self.model_path),
            "device": str(self.device),
            "request_count": self.request_count,
            "total_processing_time_ms": self.total_processing_time,
            "average_processing_time_ms": avg_processing_time,
            "cache_size": len(self.cache),
            "supported_assistance_types": [t.value for t in AIAssistanceType],
            "cognitive_patterns_loaded": len(self.cognitive_patterns),
        }


class CognitiveAIIntegration: """High-level integration of AI assistance with cognitive programming"""

    def __init__(self, cognitive_profile: CognitiveProfile): self.cognitive_profile = (
        cognitive_profile
    )
        self.ai_assistant = SonaAIAssistant()
        self.flow_state_manager = FlowStateManager(cognitive_profile)

        # Context tracking
        self.current_context = []
        self.recent_errors = []
        self.learning_patterns = {}

        debug("✅ Cognitive AI Integration initialized")

    def request_code_completion(
        self, code_context: str, cursor_position: int = None
    ) -> str: """Request AI code completion adapted to cognitive profile"""
        # Determine cognitive context based on flow state
        cognitive_context = self._determine_cognitive_context()

        request = AIRequest(
            request_type = AIAssistanceType.CODE_COMPLETION,
            context = f"Complete this Sona code: {code_context}",
            cognitive_profile = self.cognitive_profile,
            cognitive_context = cognitive_context,
            max_length = 100,
        )

        response = self.ai_assistant.generate_assistance(request)

        # Track usage patterns
        self._update_learning_patterns("code_completion", response)

        return response.generated_text

    def explain_error(
        self, error_message: str, code_context: str = ""
    ) -> Dict[str, Any]: """Get AI explanation of error adapted to cognitive needs"""
        cognitive_context = CognitiveAIContext.GENTLE_LEARNING

        if self.cognitive_profile.prefers_step_by_step: cognitive_context = (
            CognitiveAIContext.STEP_BY_STEP
        )
        elif self.cognitive_profile.prefers_visual_information: cognitive_context = (
            CognitiveAIContext.VISUAL_EXPLANATION
        )

        request = AIRequest(
            request_type = AIAssistanceType.ERROR_EXPLANATION,
            context = (
                f"Explain this error gently: {error_message}\nCode context: {code_context}",
            )
            cognitive_profile = self.cognitive_profile,
            cognitive_context = cognitive_context,
            max_length = 150,
        )

        response = self.ai_assistant.generate_assistance(request)

        # Store error for pattern recognition
        self.recent_errors.append(
            {
                "error": error_message,
                "explanation": response.generated_text,
                "timestamp": time.time(),
            }
        )

        return {
            "explanation": response.generated_text,
            "suggestions": response.suggestions,
            "next_steps": response.next_steps,
            "visual_metaphors": response.visual_metaphors,
            "confidence": response.confidence,
        }

    def provide_concept_help(
        self, concept: str, learning_context: str = ""
    ) -> Dict[str, Any]: """Provide AI-powered concept explanation"""
        cognitive_context = CognitiveAIContext.GENTLE_LEARNING

        if self.cognitive_profile.prefers_visual_information: cognitive_context = (
            CognitiveAIContext.VISUAL_EXPLANATION
        )
        elif self.cognitive_profile.learns_by_example: cognitive_context = (
            CognitiveAIContext.PATTERN_EXPLORATION
        )

        request = AIRequest(
            request_type = AIAssistanceType.CONCEPT_EXPLANATION,
            context = (
                f"Explain the concept '{concept}' in programming. Context: {learning_context}",
            )
            cognitive_profile = self.cognitive_profile,
            cognitive_context = cognitive_context,
            max_length = 200,
        )

        response = self.ai_assistant.generate_assistance(request)

        return {
            "explanation": response.generated_text,
            "visual_metaphors": response.visual_metaphors,
            "examples": response.suggestions,
            "learning_path": response.next_steps,
        }

    def _determine_cognitive_context(self) -> CognitiveAIContext: """Determine appropriate cognitive context based on current state"""
        flow_state = self.flow_state_manager.current_state
        flow_metrics = self.flow_state_manager.flow_metrics

        if (
            flow_metrics.calculate_flow_score() < 0.3
        ): # Low flow indicates overwhelm
            return CognitiveAIContext.GENTLE_LEARNING
        elif flow_state = (
            = FlowState.DEEP_FLOW: return CognitiveAIContext.HYPERFOCUS_MODE
        )
        elif self.cognitive_profile.prefers_visual_information: return CognitiveAIContext.VISUAL_EXPLANATION
        elif self.cognitive_profile.prefers_step_by_step: return CognitiveAIContext.STEP_BY_STEP
        else: return CognitiveAIContext.GENTLE_LEARNING

    def _update_learning_patterns(
        self, interaction_type: str, response: AIResponse
    ): """Update learning patterns based on AI interactions"""
        if interaction_type not in self.learning_patterns: self.learning_patterns[interaction_type] = (
            {
        )
                "count": 0,
                "avg_confidence": 0.0,
                "preferred_adaptations": [],
            }

        pattern = self.learning_patterns[interaction_type]
        pattern["count"] + = 1
        pattern["avg_confidence"] = (
            pattern["avg_confidence"] + response.confidence
        ) / 2

        # Track preferred adaptations
        for adaptation in response.cognitive_adaptations: if adaptation not in pattern["preferred_adaptations"]: pattern["preferred_adaptations"].append(adaptation)

    def get_ai_health_status(self) -> Dict[str, Any]: """Get comprehensive AI integration health status"""
        ai_stats = self.ai_assistant.get_statistics()
        flow_state = self.flow_state_manager.current_state

        return {
            "ai_model_status": (
                "healthy" if ai_stats["model_loaded"] else "unavailable"
            ),
            "cognitive_profile": (
                self.cognitive_profile.cognitive_styles[0].value
                if self.cognitive_profile.cognitive_styles
                else "default"
            ),
            "flow_state": {
                "state": flow_state.value,
                "flow_score": self.flow_state_manager.flow_metrics.calculate_flow_score(),
                "in_hyperfocus": flow_state.in_hyperfocus,
                "focus_quality": flow_state.focus_quality,
            },
            "ai_performance": {
                "request_count": ai_stats["request_count"],
                "average_response_time": ai_stats[
                    "average_processing_time_ms"
                ],
                "model_device": ai_stats["device"],
            },
            "learning_patterns": self.learning_patterns,
            "recent_error_count": len(self.recent_errors),
        }


# Global instances for easy access
_global_ai_assistant = None
_global_cognitive_ai = None


def get_ai_assistant() -> SonaAIAssistant: """Get global AI assistant instance"""
    global _global_ai_assistant
    if _global_ai_assistant is None: _global_ai_assistant = SonaAIAssistant()
    return _global_ai_assistant


def get_cognitive_ai(
    cognitive_profile: CognitiveProfile,
) -> CognitiveAIIntegration: """Get cognitive AI integration instance"""
    global _global_cognitive_ai
    if _global_cognitive_ai is None: _global_cognitive_ai = (
        CognitiveAIIntegration(cognitive_profile)
    )
    return _global_cognitive_ai


def test_ai_integration(): """Test the AI integration system"""
    print("🧪 Testing Sona AI Integration...")

    try: # Test AI assistant
        assistant = get_ai_assistant()
        print(f"✅ AI Assistant loaded: {assistant.model_loaded}")

        # Test basic generation
        if assistant.model_loaded: request = AIRequest(
                request_type = AIAssistanceType.CODE_COMPLETION,
                context = "let x = ",
                max_length = 50,
            )

            response = assistant.generate_assistance(request)
            print(f"✅ AI Response: {response.generated_text[:50]}...")
            print(f"✅ Processing time: {response.processing_time_ms}ms")

        print("✅ AI Integration test completed successfully")
        return True

    except Exception as e: print(f"❌ AI Integration test failed: {e}")
        return False


# Add alias for validation compatibility
CognitiveAIAssistant = SonaAIAssistant

if __name__ == "__main__": test_ai_integration()
