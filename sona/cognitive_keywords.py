"""
Sona Cognitive Keywords Implementation
====================================
Basic implementation of think(), remember(), focus() for v0.8.1
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class CognitiveSession: """Manages cognitive session data during code execution"""

    def __init__(self): self.thoughts = []
        self.memories = []
        self.focus_sessions = []
        self.start_time = datetime.now()

    def add_thought(self, content: str, context: Optional[Dict] = (
        None): """Add a thought entry"""
    )
        self.thoughts.append(
            {
                'content': content,
                'timestamp': datetime.now(),
                'context': context or {},
            }
        )

    def add_memory(self, key: str, value: Any, context: Optional[Dict] = (
        None): """Add a memory entry"""
    )
        self.memories.append(
            {
                'key': key,
                'value': value,
                'timestamp': datetime.now(),
                'context': context or {},
            }
        )

    def start_focus_session(self, purpose: str): """Start a focus session"""
        session = {
            'purpose': purpose,
            'start_time': datetime.now(),
            'end_time': None,
            'duration': None,
        }
        self.focus_sessions.append(session)
        return len(self.focus_sessions) - 1  # Return session ID

    def end_focus_session(self, session_id: int): """End a focus session"""
        if session_id < len(self.focus_sessions): session = (
            self.focus_sessions[session_id]
        )
            session['end_time'] = datetime.now()
            duration = session['end_time'] - session['start_time']
            session['duration'] = duration.total_seconds()

    def get_session_summary(self) -> Dict[str, Any]: """Get session summary for analytics"""
        session_duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'total_thoughts': len(self.thoughts),
            'total_memories': len(self.memories),
            'focus_sessions': len(self.focus_sessions),
            'session_duration': session_duration,
            'latest_thoughts': self.thoughts[-5:] if self.thoughts else [],
            'latest_memories': self.memories[-5:] if self.memories else [],
        }


# Global cognitive session
_cognitive_session = CognitiveSession()


def think(content: str, **kwargs) -> None: """
    Cognitive keyword: think()
    Records developer's thought process for later analysis

    Usage: think("I need to handle the edge case for empty arrays")
        think("This algorithm has O(n²) complexity", complexity = "high")
    """
    _cognitive_session.add_thought(content, kwargs)
    print(f"💭 Thinking: {content}")


def remember(key: str, value: Any = None, **kwargs) -> Any: """
    Cognitive keyword: remember()
    Stores and retrieves important information

    Usage: remember("optimization", "Use binary search for sorted arrays")
        important_note = remember("optimization")  # Retrieves stored value
    """
    if value is not None: # Store memory
        _cognitive_session.add_memory(key, value, kwargs)
        print(f"🧠 Remembering '{key}': {value}")
        return value
    else: # Retrieve memory
        for memory in reversed(_cognitive_session.memories): if memory['key'] = (
            = key: print(f"🧠 Recalled '{key}': {memory['value']}")
        )
                return memory['value']
        print(f"🧠 No memory found for '{key}'")
        return None


def focus(purpose: str = "Deep work") -> 'FocusContext': """
    Cognitive keyword: focus()
    Creates a focus session context for distraction-free coding

    Usage: with focus("Implementing binary search algorithm"): # Focus mode activated
            implement_algorithm()
    """
    return FocusContext(purpose)


class FocusContext: """Context manager for focus sessions"""

    def __init__(self, purpose: str): self.purpose = purpose
        self.session_id = None

    def __enter__(self): self.session_id = (
        _cognitive_session.start_focus_session(self.purpose)
    )
        print(f"🎯 Focus mode: {self.purpose}")
        print("   • Distractions minimized")
        print("   • Deep work mode activated")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb): if self.session_id is not None: _cognitive_session.end_focus_session(self.session_id)
        session = _cognitive_session.focus_sessions[self.session_id]
        duration = session.get('duration', 0)
        print(f"🎯 Focus session complete: {duration:.1f}s")


def get_cognitive_summary() -> Dict[str, Any]: """Get cognitive session summary for analytics"""
    return _cognitive_session.get_session_summary()


def save_cognitive_session(filename: str = (
    "cognitive_session.json") -> None: """Save cognitive session data to file"""
)
    summary = get_cognitive_summary()
    with open(filename, 'w') as f: json.dump(summary, f, indent = (
        2, default = str)
    )
    print(f"💾 Cognitive session saved to {filename}")


# Make cognitive keywords available in Sona execution context
__all__ = [
    'think',
    'remember',
    'focus',
    'get_cognitive_summary',
    'save_cognitive_session',
]
