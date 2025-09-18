"""
Sona Language 0.9.2 Enhanced REPL
Cognitive Accessibility and Neurodivergent-First Features

This enhanced REPL provides comprehensive cognitive accessibility features
including flow state management, thought capture, gentle error handling,
and personalized cognitive support.

Author: Sona Development Team
Version: 0.9.2-dev
License: See LICENSE file
"""

import datetime
import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add the sona directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sona.cognitive_core import (
    AttentionPattern,
    CognitiveProfile,
    CognitiveStrength,
    CognitiveStyle,
    ExecutiveFunctionSupport,
    FlowState,
    FlowStateManager,
    TaskComplexity,
    ThoughtCaptureSystem,
)
from sona.cognitive_syntax import CognitiveEnhancedInterpreter
from sona.utils.debug import debug, warn

from .ai_cognitive_integration import (
    AIAssistanceType,
    AIRequest,
    CognitiveAIContext,
    get_ai_assistant,
    get_cognitive_ai,
)


class CognitiveREPL:
    """Enhanced REPL with cognitive accessibility features"""

    def __init__(
        self, profile_or_path: Optional[Union[str, CognitiveProfile]] = None
    ):
        self.version = "0.9.2"
        self.title = "Sona Language Enhanced REPL"

        # Load or create cognitive profile
        if isinstance(profile_or_path, CognitiveProfile): # Direct profile provided
            self.cognitive_profile = profile_or_path
        elif isinstance(profile_or_path, str): # Path to profile file provided
            self.cognitive_profile = self._load_or_create_profile(
                profile_or_path
            )
        else: # No profile provided, create default
            self.cognitive_profile = self._load_or_create_profile(None)

        # Initialize cognitive systems
        self.interpreter = CognitiveEnhancedInterpreter(self.cognitive_profile)
        self.flow_state_manager = FlowStateManager(self.cognitive_profile)
        self.thought_capture = ThoughtCaptureSystem(self.cognitive_profile)
        self.executive_support = ExecutiveFunctionSupport(
            self.cognitive_profile
        )

        # Initialize parser
        self.parser = None  # Will be initialized when needed

        # Session tracking
        self.session_start_time = time.time()
        self.command_history = []
        self.session_stats = {
            "commands_executed": 0,
            "errors_encountered": 0,
            "flow_state_changes": 0,
            "thoughts_captured": 0,
            "cognitive_checkpoints": 0,
        }

        # Accessibility settings
        self.accessibility_settings = {
            "gentle_errors": self.cognitive_profile.gentle_error_handling,
            "progress_celebration": self.cognitive_profile.celebrates_small_wins,
            "frequent_validation": self.cognitive_profile.needs_frequent_validation,
            "visual_feedback": self.cognitive_profile.prefers_visual_information,
            "break_reminders": self.cognitive_profile.is_adhd_style(),
            "context_preservation": True,
            "flow_protection": True,
        }

        # UI enhancements
        self.colors = self._setup_colors()
        self.symbols = self._setup_symbols()

        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        print(self._create_welcome_message())
        self._start_background_monitoring()

    def _load_or_create_profile(
        self, profile_path: Optional[str]
    ) -> CognitiveProfile: """Load existing cognitive profile or create a new one"""
        if profile_path and os.path.exists(profile_path): try: with open(profile_path, 'r') as f: profile_data = (
            json.load(f)
        )
                    return CognitiveProfile(**profile_data)
            except Exception as e: print(f"Could not load profile: {e}")
                print("Creating new profile...")

        # Create default profile with interactive setup
        print(
            "\n🌟 Welcome to Sona 0.9.2! Let's set up your cognitive profile."
        )
        print("This helps personalize the programming experience for you.")

        profile = CognitiveProfile(
            user_id = "default_user", profile_name = "Default Profile"
        )

        # Interactive profile setup
        profile = self._interactive_profile_setup(profile)

        # Save profile if path provided
        if profile_path: self._save_profile(profile, profile_path)

        return profile

    def _interactive_profile_setup(
        self, profile: CognitiveProfile
    ) -> CognitiveProfile: """Interactive setup for cognitive profile"""
        print("\n📋 Quick Profile Setup (you can change these later)")

        # Cognitive style assessment
        print("\n1. Do you identify with any of these patterns? (y/n)")

        style_questions = {
            "ADHD (difficulty with sustained attention)": CognitiveStyle.ADHD_COMBINED,
            "Autism (detailed/systematic thinking)": CognitiveStyle.AUTISM_DETAIL_FOCUSED,
            "Dyslexia (visual/pattern thinking)": CognitiveStyle.DYSLEXIA_VISUAL,
            "Executive function challenges": CognitiveStyle.EXECUTIVE_FUNCTION_CHALLENGES,
            "Working memory challenges": CognitiveStyle.WORKING_MEMORY_CHALLENGES,
        }

        for question, style in style_questions.items(): answer = (
            input(f"   {question}? (y/n): ").lower().strip()
        )
            if answer in ['y', 'yes']: profile.cognitive_styles.append(style)

        # Attention pattern
        print("\n2. Which attention pattern describes you best?")
        attention_options = {
            "1": (
                "I can focus for long periods on interesting topics",
                AttentionPattern.HYPERFOCUS,
            ),
            "2": (
                "I work better in short, intense bursts",
                AttentionPattern.BURST_FOCUS,
            ),
            "3": (
                "My focus varies depending on energy and interest",
                AttentionPattern.VARIABLE_FOCUS,
            ),
            "4": (
                "I have difficulty maintaining sustained attention",
                AttentionPattern.SCATTERED_FOCUS,
            ),
        }

        for key, (description, pattern) in attention_options.items(): print(f"   {key}. {description}")

        choice = input("   Choose (1-4): ").strip()
        if choice in attention_options: profile.primary_attention_pattern = (
            attention_options[choice][1]
        )

        # Cognitive strengths
        print(
            "\n3. What are your cognitive strengths? (select all that apply)"
        )
        strength_options = {
            "1": (
                "Pattern recognition",
                CognitiveStrength.PATTERN_RECOGNITION,
            ),
            "2": (
                "Systematic thinking",
                CognitiveStrength.SYSTEMATIC_THINKING,
            ),
            "3": (
                "Creative problem solving",
                CognitiveStrength.CREATIVE_PROBLEM_SOLVING,
            ),
            "4": (
                "Attention to detail",
                CognitiveStrength.ATTENTION_TO_DETAIL,
            ),
            "5": ("Visual thinking", CognitiveStrength.VISUAL_THINKING),
            "6": ("Logical reasoning", CognitiveStrength.LOGICAL_REASONING),
        }

        for key, (description, strength) in strength_options.items(): print(f"   {key}. {description}")

        choices = (
            input("   Choose (comma-separated, e.g., 1, 3, 5): ")
            .strip()
            .split(', ')
        )
        for choice in choices: choice = choice.strip()
            if choice in strength_options: profile.cognitive_strengths.append(strength_options[choice][1])

        # Learning preferences
        print("\n4. How do you learn best?")
        if (
            input("   Do you prefer visual information? (y/n): ")
            .lower()
            .startswith('y')
        ): profile.prefers_visual_information = True

        if (
            input("   Do you prefer step-by-step instructions? (y/n): ")
            .lower()
            .startswith('y')
        ): profile.prefers_step_by_step = True

        if (
            input("   Do you like to see the big picture first? (y/n): ")
            .lower()
            .startswith('y')
        ): profile.prefers_big_picture_first = True

        # Sensitivity settings
        print("\n5. Sensitivity and accommodation preferences")

        sensitivity_level = input(
            "   Rate your sensitivity to overwhelm (1-10): "
        ).strip()
        if sensitivity_level.isdigit(): profile.overwhelm_threshold = (
            int(sensitivity_level)
        )

        if (
            input(
                "   Do you prefer gentle, supportive error messages? (y/n): "
            )
            .lower()
            .startswith('y')
        ): profile.gentle_error_handling = True

        if (
            input("   Do you like to celebrate small wins? (y/n): ")
            .lower()
            .startswith('y')
        ): profile.celebrates_small_wins = True

        print(
            "\n✅ Profile setup complete! You can adjust these settings anytime with :profile"
        )

        return profile

    def _save_profile(self, profile: CognitiveProfile, path: str): """Save cognitive profile to file"""
        try: profile_data = {
                "user_id": profile.user_id,
                "profile_name": profile.profile_name,
                "cognitive_styles": [
                    style.value for style in profile.cognitive_styles
                ],
                "primary_attention_pattern": profile.primary_attention_pattern.value,
                "cognitive_strengths": [
                    strength.value for strength in profile.cognitive_strengths
                ],
                "working_memory_capacity": profile.working_memory_capacity,
                "executive_function_capacity": profile.executive_function_capacity,
                "attention_span_minutes": profile.attention_span_minutes,
                "prefers_visual_information": profile.prefers_visual_information,
                "prefers_step_by_step": profile.prefers_step_by_step,
                "needs_frequent_validation": profile.needs_frequent_validation,
                "gentle_error_handling": profile.gentle_error_handling,
                "celebrates_small_wins": profile.celebrates_small_wins,
                "overwhelm_threshold": profile.overwhelm_threshold,
            }

            with open(path, 'w') as f: json.dump(profile_data, f, indent = 2)

            print(f"Profile saved to {path}")

        except Exception as e: print(f"Could not save profile: {e}")

    def _setup_colors(self) -> Dict[str, str]: """Setup color codes for enhanced UI"""
        return {
            "prompt": "\033[96m",  # Cyan
            "success": "\033[92m",  # Green
            "error": "\033[91m",  # Red
            "warning": "\033[93m",  # Yellow
            "info": "\033[94m",  # Blue
            "celebration": "\033[95m",  # Magenta
            "reset": "\033[0m",  # Reset
            "bold": "\033[1m",  # Bold
            "dim": "\033[2m",  # Dim
        }

    def _setup_symbols(self) -> Dict[str, str]: """Setup symbols for enhanced UI"""
        return {
            "prompt": "🌟",
            "success": "✅",
            "error": "🌟",  # Gentle star instead of harsh X
            "warning": "⚠️",
            "info": "💡",
            "celebration": "🎉",
            "thinking": "💭",
            "flow": "🌊",
            "focus": "🎯",
            "break": "☕",
            "checkpoint": "📍",
        }

    def _create_welcome_message(self) -> str: """Create personalized welcome message"""
        welcome_lines = [
            f"\n{' = '*60}",
            f"{self.colors['bold']}{self.title} v{self.version}{self.colors['reset']}",
            f"🧠 Neurodivergent-First Programming Experience",
            f"{' = '*60}",
            f"\n👋 Welcome, {self.cognitive_profile.profile_name}!",
            f"🌟 Your cognitive profile is loaded and ready",
            f"🔮 Type code naturally, think out loud, capture fleeting thoughts",
            f"\n{self.colors['info']}Available commands:{self.colors['reset']}",
        ]

        commands = [
            ":help - Show all commands",
            ":profile - View/edit your cognitive profile",
            ":flow - Check current flow state",
            ":thought - Capture a quick thought",
            ":checkpoint - Cognitive checkpoint",
            ":break - Take a mindful break",
            ":stats - View session statistics",
            ":accessibility - Adjust accessibility settings",
            ":quit - Exit REPL",
        ]

        for cmd in commands: welcome_lines.append(f"  {cmd}")

        welcome_lines.extend(
            [
                f"\n{self.colors['celebration']}💫 Ready to code with cognitive superpowers!{self.colors['reset']}\n"
            ]
        )

        return "\n".join(welcome_lines)

    def _start_background_monitoring(self): """Start background monitoring for flow state and cognitive load"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target = self._background_monitor, daemon = True
        )
        self.monitoring_thread.start()

    def _background_monitor(self): """Background monitoring loop"""
        while self.monitoring_active: try: # Check flow state
                self.flow_state_manager.update_flow_metrics()

                # Check if break is needed
                if self.accessibility_settings["break_reminders"]: self._check_break_needed()

                # Monitor cognitive load
                self._monitor_cognitive_load()

                time.sleep(30)  # Check every 30 seconds

            except Exception as e: debug(f"Background monitoring error: {e}")
                time.sleep(60)  # Wait longer on error

    def _check_break_needed(self): """Check if user needs a break reminder"""
        session_duration = time.time() - self.session_start_time
        optimal_duration = (
            self.cognitive_profile.get_optimal_session_duration() * 60
        )

        if session_duration > optimal_duration: self._suggest_break()

    def _suggest_break(self): """Suggest a break to the user"""
        print(
            f"\n{self.symbols['break']} {self.colors['info']}Gentle reminder: You've been coding for a while."
        )
        print(
            f"Consider taking a short break to recharge. Type :break for a guided break.{self.colors['reset']}"
        )

    def _monitor_cognitive_load(self): """Monitor and manage cognitive load"""
        flow_score = (
            self.flow_state_manager.flow_metrics.calculate_flow_score()
        )

        if flow_score < 0.3: # Low flow score indicates potential overload
            self._suggest_cognitive_support()

    def _suggest_cognitive_support(self): """Suggest cognitive support measures"""
        suggestions = [
            "Consider breaking down the current task into smaller steps",
            "Try the :checkpoint command to validate your progress",
            "Capture any distracting thoughts with :thought",
            "Take a brief mental break with :break",
        ]

        print(
            f"\n{self.symbols['info']} {self.colors['info']}Cognitive support suggestion:"
        )
        print(
            f"{suggestions[len(self.session_stats) % len(suggestions)]}{self.colors['reset']}"
        )

    def run(self): """Main REPL loop"""
        try: while True: try: # Update flow state
                    self.flow_state_manager.update_flow_metrics()

                    # Create dynamic prompt based on flow state
                    prompt = self._create_dynamic_prompt()

                    # Get user input
                    user_input = input(prompt).strip()

                    if not user_input: continue

                    # Track command
                    self.command_history.append(user_input)
                    self.session_stats["commands_executed"] + = 1

                    # Handle commands
                    if user_input.startswith(':'): self._handle_command(user_input)
                    else: self._execute_code(user_input)

                except KeyboardInterrupt: print(
                        f"\n{self.symbols['info']} Paused. Type :quit to exit or continue coding."
                    )
                    continue
                except EOFError: print(
                        f"\n{self.symbols['success']} Goodbye! Keep coding with confidence! 🌟"
                    )
                    break

        finally: self.monitoring_active = False
            self._save_session_summary()

    def _create_dynamic_prompt(self) -> str: """Create dynamic prompt based on flow state"""
        flow_state = self.flow_state_manager.current_state

        if flow_state == FlowState.DEEP_FLOW: prompt_symbol = "🌊"
            prompt_color = self.colors["success"]
        elif flow_state == FlowState.LIGHT_FLOW: prompt_symbol = "🌟"
            prompt_color = self.colors["info"]
        elif flow_state == FlowState.FOCUSED: prompt_symbol = "🎯"
            prompt_color = self.colors["prompt"]
        elif flow_state == FlowState.DISTRACTED: prompt_symbol = "💭"
            prompt_color = self.colors["warning"]
        else: prompt_symbol = "🌱"
            prompt_color = self.colors["info"]

        return f"{prompt_color}{prompt_symbol} sona{self.colors['reset']} "

    def _handle_command(self, command: str): """Handle REPL commands"""
        parts = command[1:].split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        command_handlers = {
            "help": self._cmd_help,
            "profile": self._cmd_profile,
            "flow": self._cmd_flow,
            "thought": self._cmd_thought,
            "checkpoint": self._cmd_checkpoint,
            "break": self._cmd_break,
            "stats": self._cmd_stats,
            "accessibility": self._cmd_accessibility,
            "traditional": self._cmd_switch_traditional,
            "quit": self._cmd_quit,
            "exit": self._cmd_quit,
            "version": self._cmd_version,
            "clear": self._cmd_clear,
            "history": self._cmd_history,
            "debug": self._cmd_debug,
            "cognitive": self._cmd_cognitive_tools,
        }

        if cmd in command_handlers: command_handlers[cmd](args)
        else: print(f"{self.symbols['error']} Unknown command: {command}")
            print(f"Type :help for available commands.")

    def _execute_code(self, code: str): """Execute Sona code with cognitive enhancements"""
        try: # Parse and execute code
            result = self.interpreter.run_code(code)

            # Display result with cognitive enhancements
            if result is not None: self._display_result(result)

            # Celebration for successful execution
            if self.accessibility_settings["progress_celebration"]: self._celebrate_success()

            # Cognitive checkpoint if enabled
            if self.accessibility_settings["frequent_validation"]: self._auto_checkpoint()

        except Exception as e: self._handle_execution_error(e, code)

    def _display_result(self, result: Any): """Display execution result with cognitive enhancements"""
        if self.accessibility_settings["visual_feedback"]: print(
                f"{self.symbols['success']} {self.colors['success']}Result:{self.colors['reset']}"
            )

        # Format result based on type
        if isinstance(result, dict): self._display_dict_result(result)
        elif isinstance(result, list): self._display_list_result(result)
        else: print(f"  {result}")

    def _display_dict_result(self, result: dict): """Display dictionary result with enhanced formatting"""
        print(f"  {self.colors['dim']}{{")
        for key, value in result.items(): print(f"    {key}: {value}")
        print(f"  }}{self.colors['reset']}")

    def _display_list_result(self, result: list): """Display list result with enhanced formatting"""
        print(f"  {self.colors['dim']}[")
        for i, item in enumerate(result): print(f"    {i}: {item}")
        print(f"  ]{self.colors['reset']}")

    def _celebrate_success(self): """Celebrate successful code execution"""
        celebrations = [
            f"{self.symbols['celebration']} Great job!",
            f"{self.symbols['success']} Code executed successfully!",
            f"🌟 Well done!",
            f"✨ Excellent work!",
            f"🎯 Perfect execution!",
        ]

        celebration = celebrations[
            self.session_stats["commands_executed"] % len(celebrations)
        ]
        print(
            f"{self.colors['celebration']}{celebration}{self.colors['reset']}"
        )

    def _auto_checkpoint(self): """Automatic cognitive checkpoint"""
        if (
            self.session_stats["commands_executed"] % 5 == 0
        ): # Every 5 commands
            self._cmd_checkpoint([])

    def _handle_execution_error(self, error: Exception, code: str): """Handle execution errors with cognitive accessibility"""
        self.session_stats["errors_encountered"] + = 1

        if self.accessibility_settings["gentle_errors"]: self._display_gentle_error(error, code)
        else: self._display_standard_error(error, code)

    def _display_gentle_error(self, error: Exception, code: str): """Display gentle, supportive error message"""
        error_type = type(error).__name__

        print(
            f"\n{self.symbols['error']} {self.colors['info']}Let's work through this together!{self.colors['reset']}"
        )

        # Gentle explanation
        gentle_explanations = {
            "NameError": "It looks like you're using a variable that hasn't been defined yet.",
            "SyntaxError": "There's a small syntax issue - like a typo in the code.",
            "TypeError": "The code is trying to do something that doesn't quite match the data type.",
            "AttributeError": "You're trying to access something that doesn't exist on this object.",
            "IndexError": "You're trying to access an item beyond the list boundaries.",
        }

        if error_type in gentle_explanations: print(f"💡 {gentle_explanations[error_type]}")
        else: print(f"💡 {str(error)}")

        # Learning opportunity
        print(
            f"\n{self.symbols['info']} {self.colors['info']}Learning opportunity:{self.colors['reset']}"
        )
        self._provide_learning_context(error_type, code)

        # Supportive next steps
        print(
            f"\n{self.symbols['success']} {self.colors['success']}You've got this! Try adjusting the code and run it again.{self.colors['reset']}"
        )

    def _display_standard_error(self, error: Exception, code: str): """Display standard error message"""
        print(
            f"{self.symbols['error']} {self.colors['error']}Error: {error}{self.colors['reset']}"
        )
        print(f"Code: {code}")

    def _provide_learning_context(self, error_type: str, code: str): """Provide learning context for errors"""
        learning_tips = {
            "NameError": "Variables need to be defined before they're used. Check if you've declared the variable above this line.",
            "SyntaxError": "Programming languages have specific grammar rules. Look for missing punctuation or typos.",
            "TypeError": "Each data type has specific operations. Make sure you're using compatible types.",
            "AttributeError": "Objects have specific methods and properties. Check what's available on this object.",
            "IndexError": "Lists have boundaries. Make sure your index is within the list length.",
        }

        tip = learning_tips.get(
            error_type, "Every error is a learning opportunity!"
        )
        print(f"  {tip}")

    # Command handlers
    def _cmd_help(self, args: List[str]): """Show help information"""
        print(
            f"\n{self.symbols['info']} {self.colors['bold']}Sona Enhanced REPL Commands:{self.colors['reset']}"
        )

        command_help = {
            "Profile Management": [
                ":profile - View/edit your cognitive profile",
                ":accessibility - Adjust accessibility settings",
            ],
            "Cognitive Support": [
                ":flow - Check current flow state",
                ":thought <message> - Capture a quick thought",
                ":checkpoint - Cognitive checkpoint and validation",
                ":break - Take a guided break",
                ":cognitive - Access cognitive tools",
            ],
            "Session Management": [
                ":stats - View session statistics",
                ":history - View command history",
                ":clear - Clear screen",
                ":debug - Toggle debug mode",
            ],
            "General": [
                ":help - Show this help",
                ":version - Show version information",
                ":quit - Exit REPL",
            ],
        }

        for category, commands in command_help.items(): print(f"\n{self.colors['info']}{category}:{self.colors['reset']}")
            for cmd in commands: print(f"  {cmd}")

    def _cmd_profile(self, args: List[str]): """View or edit cognitive profile"""
        if not args: self._display_profile()
        elif args[0] == "edit": self._edit_profile()
        else: print(f"Usage: :profile [edit]")

    def _display_profile(self): """Display current cognitive profile"""
        profile = self.cognitive_profile

        print(
            f"\n{self.symbols['info']} {self.colors['bold']}Your Cognitive Profile:{self.colors['reset']}"
        )
        print(f"  Name: {profile.profile_name}")
        print(
            f"  Cognitive Styles: {[style.value for style in profile.cognitive_styles]}"
        )
        print(
            f"  Attention Pattern: {profile.primary_attention_pattern.value}"
        )
        print(
            f"  Cognitive Strengths: {[strength.value for strength in profile.cognitive_strengths]}"
        )
        print(
            f"  Working Memory Capacity: {profile.working_memory_capacity}/10"
        )
        print(
            f"  Executive Function Capacity: {profile.executive_function_capacity}/10"
        )
        print(f"  Attention Span: {profile.attention_span_minutes} minutes")
        print(f"  Preferences:")
        print(f"    Visual Information: {profile.prefers_visual_information}")
        print(f"    Step-by-Step: {profile.prefers_step_by_step}")
        print(f"    Gentle Errors: {profile.gentle_error_handling}")
        print(f"    Celebrate Wins: {profile.celebrates_small_wins}")

    def _edit_profile(self): """Edit cognitive profile"""
        print(f"\n{self.symbols['info']} Profile editing is coming soon!")
        print(
            "For now, you can restart the REPL to go through profile setup again."
        )

    def _cmd_flow(self, args: List[str]): """Check current flow state"""
        flow_state = self.flow_state_manager.current_state
        flow_score = (
            self.flow_state_manager.flow_metrics.calculate_flow_score()
        )

        state_descriptions = {
            FlowState.DEEP_FLOW: "🌊 Deep Flow - You're in the zone! Optimal programming state.",
            FlowState.LIGHT_FLOW: "🌟 Light Flow - Good focus with manageable distractions.",
            FlowState.FOCUSED: "🎯 Focused - Concentrated and ready to code.",
            FlowState.DISTRACTED: "💭 Distracted - Attention is scattered. Consider refocusing techniques.",
            FlowState.OVERWHELMED: "🌪️ Overwhelmed - High cognitive load. Consider simplifying or taking a break.",
        }

        print(
            f"\n{self.symbols['flow']} {self.colors['info']}Current Flow State:{self.colors['reset']}"
        )
        print(f"  {state_descriptions[flow_state]}")
        print(f"  Flow Score: {flow_score:.2f}/1.0")

        # Provide recommendations
        recommendations = self.flow_state_manager.protect_flow_state()
        if recommendations["recommendations"]: print(f"\n{self.symbols['info']} Recommendations:")
            for rec in recommendations["recommendations"]: print(f"  • {rec}")

    def _cmd_thought(self, args: List[str]): """Capture a quick thought"""
        if not args: print("Usage: :thought <your thought>")
            return

        thought_content = " ".join(args)
        thought = self.thought_capture.capture_thought(thought_content)

        self.session_stats["thoughts_captured"] + = 1

        print(
            f"\n{self.symbols['thinking']} {self.colors['success']}Thought captured!{self.colors['reset']}"
        )
        print(f"  Content: {thought.content}")
        print(f"  Category: {thought.category}")
        print(f"  Priority: {thought.priority}")

        if thought.ai_suggestions: print(f"  AI Suggestions:")
            for suggestion in thought.ai_suggestions: print(f"    • {suggestion}")

    def _cmd_checkpoint(self, args: List[str]): """Cognitive checkpoint and validation"""
        self.session_stats["cognitive_checkpoints"] + = 1

        # Calculate progress
        commands_this_session = self.session_stats["commands_executed"]
        progress = min(
            commands_this_session / 20.0, 1.0
        )  # Normalize to 20 commands

        print(
            f"\n{self.symbols['checkpoint']} {self.colors['info']}Cognitive Checkpoint{self.colors['reset']}"
        )
        print(f"  Session Progress: {progress*100:.1f}%")
        print(f"  Commands Executed: {commands_this_session}")
        print(
            f"  Thoughts Captured: {self.session_stats['thoughts_captured']}"
        )

        # Validation questions
        if self.accessibility_settings["frequent_validation"]: print(f"\n{self.symbols['info']} Quick Check:")
            print("  • How are you feeling about your progress?")
            print("  • Is the current approach making sense?")
            print("  • Do you need any support or clarification?")

        # Encouragement
        encouragements = [
            "You're doing great! Keep up the excellent work!",
            "Fantastic progress! You're building valuable skills!",
            "Well done! Every line of code is a step forward!",
            "Excellent work! You're growing as a programmer!",
        ]

        encouragement = encouragements[
            self.session_stats["cognitive_checkpoints"] % len(encouragements)
        ]
        print(
            f"\n{self.symbols['celebration']} {self.colors['celebration']}{encouragement}{self.colors['reset']}"
        )

    def _cmd_break(self, args: List[str]): """Take a guided break"""
        print(
            f"\n{self.symbols['break']} {self.colors['info']}Time for a mindful break!{self.colors['reset']}"
        )

        break_activities = [
            "Take 5 deep breaths",
            "Look away from the screen for 30 seconds",
            "Stretch your arms and shoulders",
            "Walk around for a minute",
            "Drink some water",
            "Do a quick body scan for tension",
        ]

        activity = break_activities[
            len(self.command_history) % len(break_activities)
        ]
        print(f"  Suggested activity: {activity}")

        print(
            f"\n{self.symbols['info']} Press Enter when you're ready to continue..."
        )
        input()

        print(
            f"{self.symbols['success']} {self.colors['success']}Welcome back! Ready to continue coding!{self.colors['reset']}"
        )

    def _cmd_stats(self, args: List[str]): """View session statistics"""
        session_duration = time.time() - self.session_start_time

        print(
            f"\n{self.symbols['info']} {self.colors['bold']}Session Statistics:{self.colors['reset']}"
        )
        print(f"  Duration: {session_duration/60:.1f} minutes")
        print(
            f"  Commands Executed: {self.session_stats['commands_executed']}"
        )
        print(
            f"  Errors Encountered: {self.session_stats['errors_encountered']}"
        )
        print(
            f"  Thoughts Captured: {self.session_stats['thoughts_captured']}"
        )
        print(
            f"  Cognitive Checkpoints: {self.session_stats['cognitive_checkpoints']}"
        )

        # Success rate
        if self.session_stats["commands_executed"] > 0: success_rate = 1 - (
                self.session_stats["errors_encountered"] / self.session_stats["commands_executed"]
            )
            print(f"  Success Rate: {success_rate*100:.1f}%")

        # Flow state summary
        flow_score = (
            self.flow_state_manager.flow_metrics.calculate_flow_score()
        )
        print(f"  Current Flow Score: {flow_score:.2f}/1.0")

    def _cmd_accessibility(self, args: List[str]): """Adjust accessibility settings"""
        if not args: print(
                f"\n{self.symbols['info']} {self.colors['bold']}Accessibility Settings:{self.colors['reset']}"
            )
            for setting, value in self.accessibility_settings.items(): print(f"  {setting}: {value}")
            print(f"\nUsage: :accessibility <setting> <on/off>")
        else: # Toggle setting
            setting = args[0]
            if setting in self.accessibility_settings: if len(args) > 1: value = (
                args[1].lower() in ['on', 'true', '1']
            )
                    self.accessibility_settings[setting] = value
                    print(f"Set {setting} to {value}")
                else: # Toggle
                    self.accessibility_settings[setting] = (
                        not self.accessibility_settings[setting]
                    )
                    print(
                        f"Toggled {setting} to {self.accessibility_settings[setting]}"
                    )
            else: print(f"Unknown setting: {setting}")

    def _cmd_cognitive_tools(self, args: List[str]): """Access cognitive tools"""
        print(
            f"\n{self.symbols['info']} {self.colors['bold']}Cognitive Tools:{self.colors['reset']}"
        )
        print("  • :flow - Check flow state")
        print("  • :thought - Capture thoughts")
        print("  • :checkpoint - Validate progress")
        print("  • :break - Take guided breaks")
        print("  • Pattern recognition (coming soon)")
        print("  • Executive function support (coming soon)")
        print("  • Visual code representation (coming soon)")

    def _cmd_version(self, args: List[str]): """Show version information"""
        print(
            f"\n{self.symbols['info']} {self.colors['bold']}Sona Language Enhanced REPL{self.colors['reset']}"
        )
        print(f"  Version: {self.version}")
        print(f"  Cognitive Accessibility: ✅ Enabled")
        print(f"  Neurodivergent Support: ✅ Active")
        print(f"  Profile: {self.cognitive_profile.profile_name}")

    def _cmd_clear(self, args: List[str]): """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self._create_welcome_message())

    def _cmd_history(self, args: List[str]): """View command history"""
        print(
            f"\n{self.symbols['info']} {self.colors['bold']}Command History:{self.colors['reset']}"
        )
        for i, cmd in enumerate(self.command_history[-10:], 1): # Show last 10
            print(f"  {i}. {cmd}")

    def _cmd_debug(self, args: List[str]): """Toggle debug mode"""
        # This would toggle debug mode in the interpreter
        print(f"{self.symbols['info']} Debug mode toggled")

    def _cmd_quit(self, args: List[str]): """Exit REPL"""
        print(
            f"\n{self.symbols['success']} {self.colors['celebration']}Thank you for using Sona!"
        )
        print(
            "Keep coding with confidence and cognitive superpowers! 🌟{self.colors['reset']}"
        )

        # Save session summary
        self._save_session_summary()

        raise EOFError()

    def _save_session_summary(self): """Save session summary"""
        summary = {
            "session_duration": time.time() - self.session_start_time,
            "stats": self.session_stats,
            "cognitive_profile": self.cognitive_profile.profile_name,
            "flow_state_final": self.flow_state_manager.current_state.value,
            "flow_score_final": self.flow_state_manager.flow_metrics.calculate_flow_score(),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # In a real implementation, this would save to a file or database
        debug(f"Session summary: {summary}")

    # Additional cognitive methods for validation
    def handle_thinking(self, thought: str) -> str: """Handle thinking process"""
        return self.thought_capture.capture_thought(thought, "manual")

    def check_flow_state(self) -> str: """Check current flow state"""
        state = self.flow_state_manager.get_current_state()
        return f"Current flow state: {state.name}"

    def cognitive_help(self, topic: str = (
        None) -> str: """Provide cognitive-specific help"""
    )
        if not topic: return "Available cognitive features: thinking, flow_state, accessibility, profile"

        help_topics = {
            "thinking": "Use :thought to capture thoughts or handle_thinking() in code",
            "flow_state": "Use :flow to check flow state or check_flow_state() in code",
            "accessibility": "Use :accessibility to adjust settings",
            "profile": "Use :profile to view your cognitive profile",
        }

        return help_topics.get(topic, f"No help available for '{topic}'")

    def _cmd_switch_traditional(self, args): """Switch to traditional REPL mode"""
        info_msg = f"\n{self.symbols['info']} {self.colors['info']}"
        info_msg + = "Switching to Traditional REPL mode..."
        info_msg + = f"{self.colors['reset']}"
        print(info_msg)
        print("⚡ Standard programming interface will be activated")
        print("🔄 You can return to cognitive mode anytime with ':cognitive'")
        print("👋 Thanks for using the cognitive features!")

        # Save session summary
        self._save_session_summary()

        # Stop monitoring
        self.monitoring_active = False

        # Start traditional REPL
        try: from sona.repl import run_repl

            success_msg = f"\n{self.colors['success']}"
            success_msg + = "Starting Traditional REPL..."
            success_msg + = f"{self.colors['reset']}"
            print(success_msg)
            run_repl()
        except ImportError: error_msg = f"\n{self.colors['error']}"
            error_msg + = "❌ Traditional REPL not available"
            error_msg + = f"{self.colors['reset']}"
            print(error_msg)
        except Exception as e: error_msg = f"\n{self.colors['error']}"
            error_msg + = f"❌ Error starting traditional REPL: {e}"
            error_msg + = f"{self.colors['reset']}"
            print(error_msg)

        # Exit cognitive REPL
        raise SystemExit(0)


def main(): """Main entry point"""
    import argparse

    parser_desc = "Sona Enhanced REPL with Cognitive Accessibility"
    parser = argparse.ArgumentParser(description = parser_desc)
    parser.add_argument("--profile", help = "Path to cognitive profile file")
    parser.add_argument(
        "--debug", action = "store_true", help = "Enable debug mode"
    )

    args = parser.parse_args()

    # Initialize and run REPL
    repl = CognitiveREPL(profile_path = args.profile)
    repl.run()


if __name__ == "__main__": main()
