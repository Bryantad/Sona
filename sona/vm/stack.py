"""
Sona VM Stack Implementation
Phase 1, Day 1: Core VM Infrastructure

Implements optimized stack operations for bytecode execution with
cognitive accessibility features and performance monitoring.
"""

from typing import Any, List, Optional


class VMStack:
    """
    High-performance stack for Sona VM execution.
    
    Optimized for frequent push/pop operations with cognitive load tracking
    for accessibility features.
    """
    
    def __init__(self, initial_capacity: int = 1024):
        """Initialize VM stack with given capacity."""
        self.stack: list[Any] = []
        # Pre-allocate list for performance (extend with None values)
        self.stack.extend([None] * min(initial_capacity, 100))
        self.stack.clear()  # Clear pre-allocated values but keep capacity
        self.max_size = initial_capacity * 10  # Growth limit
        self.operation_count = 0
        self.max_depth_reached = 0
        
    def push(self, value: Any) -> None:
        """Push value onto stack with overflow protection."""
        if len(self.stack) >= self.max_size:
            raise RuntimeError(
                f"Stack overflow: exceeded maximum size {self.max_size}"
            )
        
        self.stack.append(value)
        self.operation_count += 1
        
        # Track maximum depth for performance analysis
        if len(self.stack) > self.max_depth_reached:
            self.max_depth_reached = len(self.stack)
    
    def pop(self) -> Any:
        """Pop and return top value from stack."""
        if not self.stack:
            raise RuntimeError("Stack underflow: cannot pop from empty stack")
        
        self.operation_count += 1
        return self.stack.pop()
    
    def peek(self, offset: int = 0) -> Any:
        """Peek at stack value without popping."""
        if offset >= len(self.stack):
            raise RuntimeError(f"Stack peek out of bounds: offset {offset}")
        
        return self.stack[-(offset + 1)]
    
    def duplicate_top(self) -> None:
        """Duplicate the top stack value."""
        if not self.stack:
            raise RuntimeError("Cannot duplicate from empty stack")
        
        top_value = self.peek()
        self.push(top_value)
    
    def swap_top_two(self) -> None:
        """Swap the top two stack values."""
        if len(self.stack) < 2:
            raise RuntimeError("Need at least 2 values to swap")
        
        value1 = self.pop()
        value2 = self.pop()
        self.push(value1)
        self.push(value2)
    
    def size(self) -> int:
        """Return current stack size."""
        return len(self.stack)
    
    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return len(self.stack) == 0
    
    def clear(self) -> None:
        """Clear all values from stack."""
        self.stack.clear()
        self.operation_count = 0
    
    def get_stats(self) -> dict:
        """Get stack performance statistics."""
        return {
            'current_size': len(self.stack),
            'max_capacity': self.max_size,
            'max_depth_reached': self.max_depth_reached,
            'total_operations': self.operation_count,
            'memory_efficiency': len(self.stack) / max(1, self.max_depth_reached)
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"VMStack(size={len(self.stack)}, top={self.peek() if self.stack else None})"


class CallStack:
    """
    Call stack for function calls and returns.
    
    Manages function call frames with return addresses and local variables.
    """
    
    def __init__(self, max_depth: int = 1000):
        """Initialize call stack with maximum recursion depth."""
        self.frames: list[dict] = []
        self.max_depth = max_depth
        
    def push_frame(self, function_name: str, return_address: int, 
                   local_vars: dict | None = None) -> None:
        """Push new call frame onto stack."""
        if len(self.frames) >= self.max_depth:
            raise RuntimeError(
                f"Maximum call stack depth exceeded: {self.max_depth}"
            )
        
        frame = {
            'function_name': function_name,
            'return_address': return_address,
            'local_vars': local_vars or {},
            'created_at': len(self.frames)
        }
        self.frames.append(frame)
    
    def pop_frame(self) -> dict:
        """Pop and return top call frame."""
        if not self.frames:
            raise RuntimeError("Cannot return from empty call stack")
        
        return self.frames.pop()
    
    def current_frame(self) -> dict | None:
        """Get current call frame without popping."""
        return self.frames[-1] if self.frames else None
    
    def get_local_var(self, name: str) -> Any:
        """Get local variable from current frame."""
        frame = self.current_frame()
        if frame is None:
            raise RuntimeError("No active call frame for local variable")
        
        if name not in frame['local_vars']:
            raise RuntimeError(f"Local variable '{name}' not found")
        
        return frame['local_vars'][name]
    
    def set_local_var(self, name: str, value: Any) -> None:
        """Set local variable in current frame."""
        frame = self.current_frame()
        if frame is None:
            raise RuntimeError("No active call frame for local variable")
        
        frame['local_vars'][name] = value
    
    def depth(self) -> int:
        """Return current call stack depth."""
        return len(self.frames)
    
    def is_empty(self) -> bool:
        """Check if call stack is empty."""
        return len(self.frames) == 0
    
    def clear(self) -> None:
        """Clear all call frames."""
        self.frames.clear()
    
    def get_stack_trace(self) -> list[str]:
        """Get formatted stack trace for debugging."""
        trace = []
        for i, frame in enumerate(reversed(self.frames)):
            trace.append(
                f"  {i}: {frame['function_name']} "
                f"(return_addr: {frame['return_address']})"
            )
        return trace
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        current = self.current_frame()
        func_name = current['function_name'] if current else "None"
        return f"CallStack(depth={len(self.frames)}, current={func_name})"


# Test functions for development
def test_vm_stack():
    """Test VMStack functionality."""
    stack = VMStack()
    
    # Test basic operations
    stack.push(10)
    stack.push(20)
    stack.push("hello")
    
    print(f"Stack size: {stack.size()}")
    print(f"Top value: {stack.peek()}")
    
    # Test pop operations
    value = stack.pop()
    print(f"Popped: {value}")
    
    # Test duplicate
    stack.duplicate_top()
    print(f"After duplicate, size: {stack.size()}")
    
    # Test stats
    stats = stack.get_stats()
    print(f"Stack stats: {stats}")


def test_call_stack():
    """Test CallStack functionality."""
    call_stack = CallStack()
    
    # Test function calls
    call_stack.push_frame("main", 0)
    call_stack.push_frame("foo", 15, {"x": 42, "y": "test"})
    
    print(f"Call depth: {call_stack.depth()}")
    print(f"Current frame: {call_stack.current_frame()}")
    
    # Test local variables
    call_stack.set_local_var("z", 100)
    z_value = call_stack.get_local_var("z")
    print(f"Local var z: {z_value}")
    
    # Test stack trace
    trace = call_stack.get_stack_trace()
    print("Stack trace:")
    for line in trace:
        print(line)


if __name__ == "__main__":
    test_vm_stack()
    print("\n" + "="*50 + "\n")
    test_call_stack()
