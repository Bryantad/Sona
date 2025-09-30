"""
SONA 0.9.0 - Cognitive Runtime Environment
Real-time cognitive monitoring and adaptation during program execution

This module provides the runtime environment that actively monitors
cognitive load, adapts to cognitive profiles, and manages flow states
during program execution.

Author: Sona Development Team
Version: 0.9.0
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .cognitive_core import CognitiveProfile, CognitiveStyle, FlowStateManager
from .cognitive_parser import CognitiveAST
from .utils.debug import debug, warn
from .working_memory import CognitiveLoadMonitor, WorkingMemoryManager


@dataclass
class RuntimeCognitiveState: """Current cognitive state during program execution"""

    current_load: float = 0.0
    flow_state: str = "normal"  # normal, focused, hyperfocus, overwhelmed
    attention_level: float = 0.7
    working_memory_usage: float = 0.0
    break_recommended: bool = False
    last_break_time: Optional[datetime] = None
    session_duration: int = 0  # minutes
    cognitive_events: List[Dict] = field(default_factory = list)


@dataclass
class CognitiveMetrics: """Metrics collected during runtime"""

    execution_time: float = 0.0
    cognitive_load_samples: List[float] = field(default_factory = list)
    flow_state_changes: int = 0
    working_memory_peak: float = 0.0
    break_recommendations: int = 0
    attention_drops: int = 0
    hyperfocus_incidents: int = 0


class CognitiveRuntime: """Runtime environment with cognitive monitoring and adaptation"""

    def __init__(self, cognitive_profile: CognitiveProfile): self.cognitive_profile = (
        cognitive_profile
    )
        self.state = RuntimeCognitiveState()
        self.metrics = CognitiveMetrics()

        # Initialize cognitive systems
        self.flow_manager = FlowStateManager(cognitive_profile)
        self.working_memory = WorkingMemoryManager(cognitive_profile)
        self.load_monitor = CognitiveLoadMonitor(self.working_memory)

        # Runtime control
        self.monitoring_enabled = True
        self.monitoring_thread = None
        self.session_start_time = datetime.now()

        # Adaptation settings
        self.adaptation_settings = self._initialize_adaptation_settings()

        # Event callbacks
        self.event_callbacks = {
            'cognitive_overload': [],
            'flow_state_change': [],
            'break_recommendation': [],
            'hyperfocus_detected': [],
            'attention_drop': [],
        }

        debug(
            f"Cognitive runtime initialized for profile: {cognitive_profile.cognitive_styles}"
        )

    def _initialize_adaptation_settings(self) -> Dict[str, Any]: """Initialize adaptation settings based on cognitive profile"""
        settings = {
            'load_threshold': 0.8,
            'break_interval': 25,  # minutes
            'hyperfocus_limit': 120,  # minutes
            'attention_monitoring': True,
            'real_time_adaptation': True,
        }

        # Adapt based on cognitive styles
        for style in self.cognitive_profile.cognitive_styles: if style = (
            = CognitiveStyle.ADHD_COMBINED: settings['break_interval'] = 15
        )
                settings['hyperfocus_limit'] = 90
                settings['attention_monitoring'] = True
            elif style = (
                = CognitiveStyle.AUTISM_DETAIL_FOCUSED: settings['break_interval'] = 45
            )
                settings['hyperfocus_limit'] = 180
                settings['load_threshold'] = 0.9
            elif style = (
                = CognitiveStyle.WORKING_MEMORY_CHALLENGES: settings['load_threshold'] = 0.6
            )
                settings['break_interval'] = 20

        return settings

    def start_monitoring(self): """Start real-time cognitive monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive(): return

        self.monitoring_enabled = True
        self.monitoring_thread = threading.Thread(
            target = self._monitoring_loop, daemon = True
        )
        self.monitoring_thread.start()
        debug("Cognitive monitoring started")

    def stop_monitoring(self): """Stop cognitive monitoring"""
        self.monitoring_enabled = False
        if self.monitoring_thread: self.monitoring_thread.join(timeout = 1.0)
        debug("Cognitive monitoring stopped")

    def _monitoring_loop(self): """Main monitoring loop"""
        while self.monitoring_enabled: try: self._update_cognitive_state()
                self._check_adaptations()
                self._emit_events()
                time.sleep(1.0)  # Update every second
            except Exception as e: warn(f"Error in cognitive monitoring loop: {e}")
                time.sleep(5.0)  # Wait longer on error

    def _update_cognitive_state(self): """Update current cognitive state"""
        # Update session duration
        self.state.session_duration = int(
            (datetime.now() - self.session_start_time).total_seconds() / 60
        )

        # Update cognitive load
        load_status = self.load_monitor.check_load()
        self.state.current_load = load_status['current_load']
        self.metrics.cognitive_load_samples.append(self.state.current_load)

        # Update working memory usage
        capacity_status = self.working_memory.get_capacity_status()
        self.state.working_memory_usage = capacity_status['utilization']
        self.metrics.working_memory_peak = max(
            self.metrics.working_memory_peak, self.state.working_memory_usage
        )

        # Update flow state
        self._update_flow_state()

        # Update attention level
        self._update_attention_level()

    def _update_flow_state(self): """Update flow state based on current conditions"""
        old_state = self.state.flow_state

        if self.state.current_load > 0.9: self.state.flow_state = "overwhelmed"
        elif (
            self.state.current_load > 0.7 and self.state.attention_level > 0.8
        ): self.state.flow_state = "hyperfocus"
        elif (
            self.state.current_load > 0.5 and self.state.attention_level > 0.7
        ): self.state.flow_state = "focused"
        else: self.state.flow_state = "normal"

        if old_state ! = (
            self.state.flow_state: self.metrics.flow_state_changes + = 1
        )
            self._record_event(
                'flow_state_change',
                {
                    'old_state': old_state,
                    'new_state': self.state.flow_state,
                    'timestamp': datetime.now().isoformat(),
                },
            )

    def _update_attention_level(self): """Update attention level based on various factors"""
        # Base attention level
        base_attention = 0.7

        # Adjust based on cognitive load
        if self.state.current_load > 0.8: base_attention - = 0.2
        elif self.state.current_load < 0.3: base_attention - = 0.1

        # Adjust based on session duration
        if (
            self.state.session_duration
            > self.adaptation_settings['break_interval']
        ): base_attention - = 0.1

        # Adjust based on time since last break
        if self.state.last_break_time: time_since_break = (
                datetime.now() - self.state.last_break_time
            ).total_seconds() / 60
            if time_since_break > self.adaptation_settings['break_interval']: base_attention - = (
                0.15
            )

        old_attention = self.state.attention_level
        self.state.attention_level = max(0.1, min(1.0, base_attention))

        # Detect attention drops
        if old_attention - self.state.attention_level > 0.2: self.metrics.attention_drops + = (
            1
        )
            self._record_event(
                'attention_drop',
                {
                    'old_level': old_attention,
                    'new_level': self.state.attention_level,
                    'timestamp': datetime.now().isoformat(),
                },
            )

    def _check_adaptations(self): """Check if adaptations are needed"""
        # Check for cognitive overload
        if (
            self.state.current_load
            > self.adaptation_settings['load_threshold']
        ): self._trigger_event(
                'cognitive_overload',
                {
                    'load': self.state.current_load,
                    'threshold': self.adaptation_settings['load_threshold'],
                },
            )

        # Check for break recommendation
        if self._should_recommend_break(): self.state.break_recommended = True
            self.metrics.break_recommendations + = 1
            self._trigger_event(
                'break_recommendation',
                {
                    'reason': 'time_based',
                    'session_duration': self.state.session_duration,
                },
            )

        # Check for hyperfocus
        if self._is_hyperfocus_detected(): self.metrics.hyperfocus_incidents + = (
            1
        )
            self._trigger_event(
                'hyperfocus_detected',
                {
                    'duration': self.state.session_duration,
                    'load': self.state.current_load,
                },
            )

    def _should_recommend_break(self) -> bool: """Check if a break should be recommended"""
        # Time-based break
        if (
            self.state.session_duration
            >= self.adaptation_settings['break_interval']
        ): return True

        # Load-based break
        if self.state.current_load > 0.9: return True

        # Attention-based break
        if self.state.attention_level < 0.4: return True

        return False

    def _is_hyperfocus_detected(self) -> bool: """Check if hyperfocus is detected"""
        return (
            self.state.flow_state == "hyperfocus"
            and self.state.session_duration
            > self.adaptation_settings['hyperfocus_limit']
        )

    def _record_event(self, event_type: str, data: Dict[str, Any]): """Record a cognitive event"""
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data,
        }
        self.state.cognitive_events.append(event)

        # Keep only last 100 events
        if len(self.state.cognitive_events) > 100: self.state.cognitive_events.pop(0)

    def _trigger_event(self, event_type: str, data: Dict[str, Any]): """Trigger event callbacks"""
        self._record_event(event_type, data)

        for callback in self.event_callbacks.get(event_type, []): try: callback(data)
            except Exception as e: warn(f"Error in event callback: {e}")

    def _emit_events(self): """Emit periodic events for monitoring"""
        # This could be used for external monitoring systems
        pass

    def register_event_callback(self, event_type: str, callback: Callable): """Register a callback for cognitive events"""
        if event_type in self.event_callbacks: self.event_callbacks[event_type].append(callback)
        else: warn(f"Unknown event type: {event_type}")

    def take_break(self, duration_minutes: int = (
        5): """Record a break taken by the user"""
    )
        self.state.last_break_time = datetime.now()
        self.state.break_recommended = False
        self.state.session_duration = 0
        self.session_start_time = datetime.now()

        self._record_event(
            'break_taken',
            {
                'duration': duration_minutes,
                'timestamp': datetime.now().isoformat(),
            },
        )

        debug(f"Break recorded: {duration_minutes} minutes")

    def get_current_state(self) -> Dict[str, Any]: """Get current cognitive state"""
        return {
            'cognitive_load': self.state.current_load,
            'flow_state': self.state.flow_state,
            'attention_level': self.state.attention_level,
            'working_memory_usage': self.state.working_memory_usage,
            'break_recommended': self.state.break_recommended,
            'session_duration': self.state.session_duration,
            'adaptation_active': self.monitoring_enabled,
        }

    def get_metrics(self) -> Dict[str, Any]: """Get collected metrics"""
        return {
            'execution_time': self.metrics.execution_time,
            'average_cognitive_load': (
                sum(self.metrics.cognitive_load_samples) / len(self.metrics.cognitive_load_samples)
                if self.metrics.cognitive_load_samples
                else 0.0
            ),
            'peak_cognitive_load': (
                max(self.metrics.cognitive_load_samples)
                if self.metrics.cognitive_load_samples
                else 0.0
            ),
            'flow_state_changes': self.metrics.flow_state_changes,
            'working_memory_peak': self.metrics.working_memory_peak,
            'break_recommendations': self.metrics.break_recommendations,
            'attention_drops': self.metrics.attention_drops,
            'hyperfocus_incidents': self.metrics.hyperfocus_incidents,
        }

    def adapt_to_profile(self, new_profile: CognitiveProfile): """Adapt runtime to a new cognitive profile"""
        old_profile = self.cognitive_profile
        self.cognitive_profile = new_profile

        # Update adaptation settings
        self.adaptation_settings = self._initialize_adaptation_settings()

        # Update cognitive systems
        self.flow_manager = FlowStateManager(new_profile)
        self.working_memory = WorkingMemoryManager(new_profile)
        self.load_monitor = CognitiveLoadMonitor(self.working_memory)

        self._record_event(
            'profile_change',
            {
                'old_profile': [
                    style.value for style in old_profile.cognitive_styles
                ],
                'new_profile': [
                    style.value for style in new_profile.cognitive_styles
                ],
                'timestamp': datetime.now().isoformat(),
            },
        )

        debug(
            f"Runtime adapted to new profile: {new_profile.cognitive_styles}"
        )

    def execute_with_monitoring(
        self, code_ast: CognitiveAST, execution_function: Callable
    ): """Execute code with cognitive monitoring"""
        execution_start = time.time()

        # Pre-execution setup
        self.start_monitoring()

        # Add working memory items from AST
        for block in code_ast.cognitive_blocks: self.working_memory.add_item(
                content = f"Thinking: {block.title}",
                item_type = "thinking",
                priority = block.complexity_level,
                context = "execution",
            )

        for concept_name, concept in code_ast.concepts.items(): self.working_memory.add_item(
                content = f"Concept: {concept_name}",
                item_type = "concept",
                priority = concept.complexity_level,
                context = "execution",
            )

        try: # Execute the code
            result = execution_function()

            # Post-execution
            self.metrics.execution_time = time.time() - execution_start

            self._record_event(
                'execution_complete',
                {
                    'duration': self.metrics.execution_time,
                    'cognitive_load': self.state.current_load,
                    'working_memory_usage': self.state.working_memory_usage,
                },
            )

            return result

        except Exception as e: self._record_event(
                'execution_error',
                {
                    'error': str(e),
                    'duration': time.time() - execution_start,
                    'cognitive_load': self.state.current_load,
                },
            )
            raise

        finally: self.stop_monitoring()

    def persist_state(self, filepath: str): """Persist cognitive state to file"""
        state_data = {
            'profile': {
                'cognitive_styles': [
                    style.value
                    for style in self.cognitive_profile.cognitive_styles
                ],
                'working_memory_capacity': self.cognitive_profile.working_memory_capacity,
            },
            'state': {
                'current_load': self.state.current_load,
                'flow_state': self.state.flow_state,
                'attention_level': self.state.attention_level,
                'session_duration': self.state.session_duration,
            },
            'metrics': self.get_metrics(),
            'working_memory': self.working_memory.export_state(),
            'timestamp': datetime.now().isoformat(),
        }

        with open(filepath, 'w') as f: json.dump(state_data, f, indent = 2)

        debug(f"Cognitive state persisted to {filepath}")

    def load_state(self, filepath: str): """Load cognitive state from file"""
        try: with open(filepath, 'r') as f: state_data = json.load(f)

            # Restore working memory
            self.working_memory.import_state(state_data['working_memory'])

            # Restore basic state
            self.state.current_load = state_data['state']['current_load']
            self.state.flow_state = state_data['state']['flow_state']
            self.state.attention_level = state_data['state']['attention_level']

            debug(f"Cognitive state loaded from {filepath}")

        except Exception as e: warn(f"Failed to load cognitive state: {e}")


def create_cognitive_runtime(profile: CognitiveProfile) -> CognitiveRuntime: """Factory function to create a cognitive runtime"""
    return CognitiveRuntime(profile)
