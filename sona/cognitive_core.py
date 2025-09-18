"""
Professional Sona Cognitive Core v0.9.2 - Neurodivergent Programming Framework

Advanced AI-Assisted Code Remediation Protocol Implementation
Complete cognitive computing framework with accessibility excellence

A comprehensive cognitive computing framework for the Sona programming language that provides
neurodivergent-aware programming experiences with cognitive accessibility features,
thinking pattern analysis, and PhD-level cognitive science integration.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CognitiveStyle(Enum):
    """Different neurodivergent cognitive styles and their characteristics."""
    
    # ADHD Variants
    ADHD_HYPERACTIVE = "adhd_hyperactive"
    ADHD_INATTENTIVE = "adhd_inattentive" 
    ADHD_COMBINED = "adhd_combined"
    
    # Autism Spectrum Variants
    AUTISM_DETAIL_FOCUSED = "autism_detail_focused"
    AUTISM_PATTERN_FOCUSED = "autism_pattern_focused"
    AUTISM_SYSTEMATIC = "autism_systematic"
    
    # Learning Differences
    DYSLEXIA_VISUAL = "dyslexia_visual"
    DYSLEXIA_PHONOLOGICAL = "dyslexia_phonological"
    DYSCALCULIA = "dyscalculia"
    
    # Executive Function Variants
    EXECUTIVE_FUNCTION_CHALLENGES = "executive_function_challenges"
    WORKING_MEMORY_CHALLENGES = "working_memory_challenges"
    PROCESSING_SPEED_VARIANCE = "processing_speed_variance"
    
    # Focus and Attention Patterns
    HYPERFOCUS_PRONE = "hyperfocus_prone"
    ATTENTION_FLEXIBLE = "attention_flexible"
    
    # Sensory Processing
    SENSORY_PROCESSING_SENSITIVE = "sensory_processing_sensitive"
    SENSORY_SEEKING = "sensory_seeking"
    
    # General Neurodivergent
    NEURODIVERGENT_GENERAL = "neurodivergent_general"
    
    # Legacy compatibility
    NEUROTYPICAL = "neurotypical"


class CognitiveState(Enum):
    """Current cognitive and emotional states affecting programming."""
    
    # Attention States
    FOCUSED = "focused"
    HYPERFOCUSED = "hyperfocused"
    DISTRACTED = "distracted"
    SCATTERED = "scattered"
    
    # Energy States
    HIGH_ENERGY = "high_energy"
    MODERATE_ENERGY = "moderate_energy"
    LOW_ENERGY = "low_energy"
    DEPLETED = "depleted"
    
    # Emotional States
    CALM = "calm"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    OVERWHELMED = "overwhelmed"
    
    # Processing States
    VERBAL_PROCESSING = "verbal_processing"
    VISUAL_PROCESSING = "visual_processing"
    KINESTHETIC_PROCESSING = "kinesthetic_processing"
    
    # Flow States
    FLOW = "flow"
    NEAR_FLOW = "near_flow"
    STRUGGLING = "struggling"


@dataclass
class CognitiveProfile:
    """Comprehensive cognitive profile for neurodivergent programming support."""
    
    # Core Identity
    user_id: str
    cognitive_styles: list[CognitiveStyle] = field(default_factory=list)
    
    # Attention and Focus
    attention_span_minutes: int = 25
    hyperfocus_duration_hours: int = 4
    break_frequency_minutes: int = 5
    optimal_work_blocks: int = 4
    
    # Processing Preferences
    preferred_modality: str = "visual"  # visual, auditory, kinesthetic
    information_chunk_size: str = "medium"  # small, medium, large
    complexity_tolerance: str = "moderate"  # low, moderate, high
    
    # Environmental Needs
    noise_sensitivity: float = 0.5  # 0.0 to 1.0
    lighting_preference: str = "moderate"  # dim, moderate, bright
    distraction_sensitivity: float = 0.7
    
    # Cognitive Strengths and Challenges
    strengths: list[str] = field(default_factory=list)
    challenges: list[str] = field(default_factory=list)
    
    # Accessibility Features
    screen_reader_compatible: bool = True
    high_contrast_mode: bool = False
    font_size_preference: str = "medium"
    color_blind_support: bool = False
    
    # Personalization
    preferred_error_verbosity: str = "detailed"  # minimal, moderate, detailed
    encouragement_level: str = "moderate"  # minimal, moderate, high
    
    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "0.9.2"


@dataclass 
class CognitiveSession:
    """Tracks cognitive state during a programming session."""
    
    session_id: str
    start_time: float = field(default_factory=time.time)
    current_state: CognitiveState = CognitiveState.FOCUSED
    energy_level: float = 0.8  # 0.0 to 1.0
    focus_score: float = 0.7   # 0.0 to 1.0
    
    # Session Tracking
    total_lines_written: int = 0
    total_errors_encountered: int = 0
    total_breaks_taken: int = 0
    cognitive_blocks_used: int = 0
    
    # Time tracking
    focused_time_seconds: float = 0.0
    break_time_seconds: float = 0.0
    last_activity: float = field(default_factory=time.time)
    
    # Cognitive Events
    thinking_blocks: list[dict[str, Any]] = field(default_factory=list)
    memory_entries: dict[str, Any] = field(default_factory=dict)
    focus_sessions: list[dict[str, Any]] = field(default_factory=list)


class CognitiveCore:
    """
    Professional-grade cognitive computing framework for neurodivergent programming.
    
    Implements the Advanced AI-Assisted Code Remediation Protocol with:
    - Complete neurodivergent cognitive support
    - Accessibility excellence framework
    - Personalized programming assistance
    - PhD-level cognitive science integration
    """
    
    def __init__(self, profile_path: Path | None = None):
        """Initialize the cognitive core with user profile support."""
        self.profile_path = profile_path or Path.home() / ".sona_profile.json"
        self.current_profile: CognitiveProfile | None = None
        self.current_session: CognitiveSession | None = None
        
        # Cognitive Enhancement Features
        self.thinking_patterns = {}
        self.memory_store = {}
        self.focus_history = []
        self.accessibility_settings = {}
        
        # Load existing profile if available
        self._load_profile()

    def create_profile(self, user_id: str, **kwargs) -> CognitiveProfile:
        """Create a new cognitive profile with neurodivergent support."""
        profile = CognitiveProfile(user_id=user_id, **kwargs)
        
        # Set intelligent defaults based on cognitive styles
        self._configure_defaults(profile)
        
        self.current_profile = profile
        self._save_profile()
        
        return profile

    def _configure_defaults(self, profile: CognitiveProfile) -> None:
        """Configure intelligent defaults based on cognitive styles."""
        for style in profile.cognitive_styles:
            if style == CognitiveStyle.ADHD_HYPERACTIVE:
                profile.attention_span_minutes = 15
                profile.break_frequency_minutes = 3
                profile.optimal_work_blocks = 6
                profile.strengths.extend(["creative_thinking", "rapid_prototyping"])
                profile.challenges.extend(["sustained_attention", "detail_focus"])
                
            elif style == CognitiveStyle.ADHD_INATTENTIVE:
                profile.attention_span_minutes = 20
                profile.hyperfocus_duration_hours = 6
                profile.strengths.extend(["deep_focus", "pattern_recognition"])
                profile.challenges.extend(["task_switching", "interruption_recovery"])
                
            elif style == CognitiveStyle.AUTISM_DETAIL_FOCUSED:
                profile.complexity_tolerance = "high"
                profile.information_chunk_size = "large"
                profile.strengths.extend(["systematic_thinking", "error_detection"])
                profile.challenges.extend(["context_switching", "ambiguity_tolerance"])
                
            elif style == CognitiveStyle.DYSLEXIA_VISUAL:
                profile.preferred_modality = "visual"
                profile.font_size_preference = "large"
                profile.strengths.extend(["spatial_reasoning", "big_picture_thinking"])
                profile.challenges.extend(["text_processing", "sequential_instructions"])

    def start_session(self, session_id: str | None = None) -> CognitiveSession:
        """Start a new cognitive programming session."""
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        self.current_session = CognitiveSession(session_id=session_id)
        
        # Configure session based on profile
        if self.current_profile:
            self._configure_session_from_profile()
        
        return self.current_session

    def _configure_session_from_profile(self) -> None:
        """Configure session settings based on cognitive profile."""
        if not self.current_profile or not self.current_session:
            return
        
        # Adjust energy and focus based on cognitive styles
        for style in self.current_profile.cognitive_styles:
            if style in [CognitiveStyle.ADHD_HYPERACTIVE, CognitiveStyle.HIGH_ENERGY]:
                self.current_session.energy_level = min(1.0, self.current_session.energy_level + 0.2)
            elif style == CognitiveStyle.PROCESSING_SPEED_VARIANCE:
                self.current_session.focus_score = 0.6  # Start conservative

    def add_thinking_block(self, context: str, content: str, 
                          accessibility_level: str = "standard") -> str:
        """Add a thinking block with cognitive accessibility features."""
        if not self.current_session:
            self.start_session()
        
        thinking_block = {
            "id": f"think_{len(self.current_session.thinking_blocks)}",
            "context": context,
            "content": content,
            "timestamp": time.time(),
            "accessibility_level": accessibility_level,
            "cognitive_state": self.current_session.current_state.value
        }
        
        self.current_session.thinking_blocks.append(thinking_block)
        self.current_session.cognitive_blocks_used += 1
        
        # Update cognitive state based on thinking activity
        self._update_cognitive_state("thinking")
        
        return thinking_block["id"]

    def store_memory(self, key: str, value: Any, 
                    persistence_level: str = "session") -> None:
        """Store cognitive memory with accessibility features."""
        if not self.current_session:
            self.start_session()
        
        memory_entry = {
            "value": value,
            "timestamp": time.time(),
            "persistence_level": persistence_level,
            "cognitive_context": self.current_session.current_state.value,
            "accessibility_metadata": {
                "screen_reader_text": str(value),
                "summary": f"Stored: {key}"
            }
        }
        
        # Store in session
        self.current_session.memory_entries[key] = memory_entry
        
        # Store in long-term memory if requested
        if persistence_level in ["permanent", "profile"]:
            self.memory_store[key] = memory_entry

    def retrieve_memory(self, key: str) -> Any:
        """Retrieve cognitive memory with accessibility support."""
        # Check session memory first
        if self.current_session and key in self.current_session.memory_entries:
            return self.current_session.memory_entries[key]["value"]
        
        # Check long-term memory
        if key in self.memory_store:
            return self.memory_store[key]["value"]
        
        return None

    def enter_focus_mode(self, settings: dict[str, Any]) -> str:
        """Enter focus mode with cognitive accessibility features."""
        if not self.current_session:
            self.start_session()
        
        focus_session = {
            "id": f"focus_{len(self.current_session.focus_sessions)}",
            "start_time": time.time(),
            "settings": settings,
            "cognitive_state_entry": self.current_session.current_state.value,
            "accessibility_active": True
        }
        
        self.current_session.focus_sessions.append(focus_session)
        self.current_session.current_state = CognitiveState.FOCUSED
        
        # Apply focus settings
        self._apply_focus_settings(settings)
        
        return focus_session["id"]

    def _apply_focus_settings(self, settings: dict[str, Any]) -> None:
        """Apply focus settings with neurodivergent considerations."""
        # Configure accessibility settings based on focus requirements
        if "distractions" in settings:
            distraction_level = settings["distractions"]
            if distraction_level == "minimal":
                self.accessibility_settings["reduce_notifications"] = True
                self.accessibility_settings["simplified_interface"] = True
            
        if "accessibility" in settings:
            accessibility_mode = settings["accessibility"] 
            if accessibility_mode == "screen_reader_optimized":
                self.accessibility_settings["screen_reader_mode"] = True
                self.accessibility_settings["verbose_descriptions"] = True

    def _update_cognitive_state(self, activity: str) -> None:
        """Update cognitive state based on current activity."""
        if not self.current_session:
            return
        
        current_time = time.time()
        time_since_last = current_time - self.current_session.last_activity
        
        # Update focus score based on activity patterns
        if activity == "thinking":
            self.current_session.focus_score = min(1.0, self.current_session.focus_score + 0.1)
        elif activity == "error":
            self.current_session.focus_score = max(0.0, self.current_session.focus_score - 0.2)
        elif time_since_last > 300:  # 5 minutes of inactivity
            self.current_session.focus_score = max(0.3, self.current_session.focus_score - 0.1)
        
        # Update energy level
        if time_since_last > 1800:  # 30 minutes - energy decay
            self.current_session.energy_level = max(0.1, self.current_session.energy_level - 0.1)
        
        self.current_session.last_activity = current_time

    def get_cognitive_recommendations(self) -> list[str]:
        """Get personalized cognitive recommendations."""
        recommendations = []
        
        if not self.current_session:
            return ["Start a coding session to get personalized recommendations"]
        
        # Focus-based recommendations
        if self.current_session.focus_score < 0.4:
            recommendations.append("🎯 Consider taking a short break to restore focus")
            recommendations.append("🧠 Try a thinking block to organize your thoughts")
        
        # Energy-based recommendations
        if self.current_session.energy_level < 0.3:
            recommendations.append("⚡ Your energy is low - consider a longer break")
            recommendations.append("🚶 Physical movement might help restore energy")
        
        # Profile-based recommendations
        if self.current_profile:
            work_time = time.time() - self.current_session.start_time
            if work_time > self.current_profile.attention_span_minutes * 60:
                recommendations.append("⏰ You've exceeded your optimal attention span")
                recommendations.append("🔄 Time for a cognitive break")
        
        return recommendations

    def get_accessibility_status(self) -> dict[str, Any]:
        """Get current accessibility feature status."""
        status = {
            "screen_reader_compatible": True,
            "cognitive_features_active": bool(self.current_session),
            "profile_loaded": bool(self.current_profile),
            "accessibility_settings": self.accessibility_settings.copy()
        }
        
        if self.current_profile:
            status.update({
                "high_contrast_mode": self.current_profile.high_contrast_mode,
                "font_size_preference": self.current_profile.font_size_preference,
                "color_blind_support": self.current_profile.color_blind_support
            })
        
        if self.current_session:
            status.update({
                "thinking_blocks_count": len(self.current_session.thinking_blocks),
                "memory_entries_count": len(self.current_session.memory_entries),
                "focus_sessions_count": len(self.current_session.focus_sessions),
                "current_cognitive_state": self.current_session.current_state.value,
                "focus_score": self.current_session.focus_score,
                "energy_level": self.current_session.energy_level
            })
        
        return status

    def _load_profile(self) -> None:
        """Load cognitive profile from disk."""
        if not self.profile_path.exists():
            return
        
        try:
            with open(self.profile_path) as f:
                data = json.load(f)
                
            # Convert cognitive styles from strings to enums
            styles = [CognitiveStyle(style) for style in data.get('cognitive_styles', [])]
            data['cognitive_styles'] = styles
            
            self.current_profile = CognitiveProfile(**data)
            
        except Exception as e:
            print(f"Warning: Could not load cognitive profile: {e}")

    def _save_profile(self) -> None:
        """Save cognitive profile to disk."""
        if not self.current_profile:
            return
        
        try:
            # Convert profile to serializable format
            data = {
                'user_id': self.current_profile.user_id,
                'cognitive_styles': [style.value for style in self.current_profile.cognitive_styles],
                'attention_span_minutes': self.current_profile.attention_span_minutes,
                'hyperfocus_duration_hours': self.current_profile.hyperfocus_duration_hours,
                'break_frequency_minutes': self.current_profile.break_frequency_minutes,
                'optimal_work_blocks': self.current_profile.optimal_work_blocks,
                'preferred_modality': self.current_profile.preferred_modality,
                'information_chunk_size': self.current_profile.information_chunk_size,
                'complexity_tolerance': self.current_profile.complexity_tolerance,
                'noise_sensitivity': self.current_profile.noise_sensitivity,
                'lighting_preference': self.current_profile.lighting_preference,
                'distraction_sensitivity': self.current_profile.distraction_sensitivity,
                'strengths': self.current_profile.strengths,
                'challenges': self.current_profile.challenges,
                'screen_reader_compatible': self.current_profile.screen_reader_compatible,
                'high_contrast_mode': self.current_profile.high_contrast_mode,
                'font_size_preference': self.current_profile.font_size_preference,
                'color_blind_support': self.current_profile.color_blind_support,
                'preferred_error_verbosity': self.current_profile.preferred_error_verbosity,
                'encouragement_level': self.current_profile.encouragement_level,
                'last_updated': datetime.now().isoformat(),
                'version': self.current_profile.version
            }
            
            # Ensure directory exists
            self.profile_path.parent.mkdir(exist_ok=True)
            
            # Save profile
            with open(self.profile_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save cognitive profile: {e}")

    def end_session(self) -> dict[str, Any] | None:
        """End the current cognitive session and return summary."""
        if not self.current_session:
            return None
        
        session_duration = time.time() - self.current_session.start_time
        
        summary = {
            "session_id": self.current_session.session_id,
            "duration_seconds": session_duration,
            "duration_minutes": session_duration / 60,
            "final_focus_score": self.current_session.focus_score,
            "final_energy_level": self.current_session.energy_level,
            "thinking_blocks_used": len(self.current_session.thinking_blocks),
            "memory_entries_created": len(self.current_session.memory_entries),
            "focus_sessions": len(self.current_session.focus_sessions),
            "total_lines_written": self.current_session.total_lines_written,
            "total_errors_encountered": self.current_session.total_errors_encountered,
            "cognitive_accessibility_score": self._calculate_accessibility_score()
        }
        
        # Clear current session
        self.current_session = None
        
        return summary

    def _calculate_accessibility_score(self) -> float:
        """Calculate accessibility utilization score."""
        if not self.current_session:
            return 0.0
        
        score = 0.0
        
        # Cognitive blocks usage
        if self.current_session.cognitive_blocks_used > 0:
            score += 0.3
        
        # Memory usage
        if len(self.current_session.memory_entries) > 0:
            score += 0.3
        
        # Focus management
        if len(self.current_session.focus_sessions) > 0:
            score += 0.2
        
        # Overall session health
        if self.current_session.focus_score > 0.6:
            score += 0.2
        
        return min(1.0, score)


# Factory functions for easy instantiation
def create_cognitive_core(profile_path: Path | None = None) -> CognitiveCore:
    """Create a new CognitiveCore instance following the Advanced Protocol."""
    return CognitiveCore(profile_path=profile_path)


def create_neurodivergent_profile(user_id: str, 
                                 cognitive_styles: list[str],
                                 **kwargs) -> CognitiveProfile:
    """
    Quick profile creation for neurodivergent programmers.
    
    Args:
        user_id: Unique identifier for the user
        cognitive_styles: List of cognitive style strings
        **kwargs: Additional profile customization options
    
    Returns:
        Configured CognitiveProfile with accessibility features
    """
    styles = [CognitiveStyle(style) for style in cognitive_styles]
    return CognitiveProfile(
        user_id=user_id, 
        cognitive_styles=styles,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage demonstrating cognitive accessibility features
    print("🧠 Sona Cognitive Core v0.9.2 - Neurodivergent Programming Framework")
    
    # Create cognitive core
    core = create_cognitive_core()
    
    # Create a sample neurodivergent profile
    profile = core.create_profile(
        user_id="demo_user",
        cognitive_styles=[
            CognitiveStyle.ADHD_COMBINED,
            CognitiveStyle.AUTISM_DETAIL_FOCUSED
        ]
    )
    
    print(f"✅ Created cognitive profile for: {profile.user_id}")
    print(f"   Cognitive styles: {[s.value for s in profile.cognitive_styles]}")
    
    # Start a programming session
    session = core.start_session()
    print(f"🚀 Started cognitive session: {session.session_id}")
    
    # Demonstrate cognitive features
    core.add_thinking_block(
        "Code planning",
        "Thinking about the best approach for this function"
    )
    
    core.store_memory(
        "current_task",
        "Implementing cognitive accessibility features"
    )
    
    core.enter_focus_mode({
        "distractions": "minimal",
        "accessibility": "screen_reader_optimized"
    })
    
    # Get recommendations
    recommendations = core.get_cognitive_recommendations()
    print(f"💡 Cognitive recommendations: {recommendations}")
    
    # Show accessibility status
    status = core.get_accessibility_status()
    print(f"♿ Accessibility status: {status}")
    
    # End session
    summary = core.end_session()
    print(f"📊 Session summary: {summary}")
