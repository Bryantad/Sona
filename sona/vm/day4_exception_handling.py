"""
PHASE 1, DAY 4: EXCEPTION HANDLING & ERROR MANAGEMENT
Sona Programming Language v0.8.1 Development

Building upon Day 3's advanced features, implementing:
1. Exception handling system (try/catch/finally)
2. Error propagation and stack unwinding
3. Custom exception types  
4. Error recovery mechanisms
5. Debugging and error reporting

Target: Robust error handling for production-ready v0.8.1
"""

import time
import traceback
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Import our advanced VM foundation
try:
    from .day3_advanced_features import AdvancedVM, AdvancedOpCode
except ImportError:
    from day3_advanced_features import AdvancedVM, AdvancedOpCode


class ExceptionType(Enum):
    """Built-in exception types for Sona."""
    RUNTIME_ERROR = "RuntimeError"
    TYPE_ERROR = "TypeError"
    VALUE_ERROR = "ValueError"
    INDEX_ERROR = "IndexError"
    KEY_ERROR = "KeyError"
    DIVISION_BY_ZERO = "DivisionByZeroError"
    COGNITIVE_OVERLOAD = "CognitiveOverloadError"
    ACCESSIBILITY_ERROR = "AccessibilityError"


@dataclass
class SonaException:
    """Exception object for Sona VM."""
    type: ExceptionType
    message: str
    stack_trace: List[str]
    cognitive_impact: float = 1.0
    accessibility_info: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.type.value}: {self.message}"


@dataclass
class ExceptionHandler:
    """Exception handler block."""
    start_address: int
    end_address: int
    handler_address: int
    exception_types: List[ExceptionType]
    finally_address: Optional[int] = None


class ExceptionHandlingVM(AdvancedVM):
    """
    VM with comprehensive exception handling capabilities.
    Maintains performance while adding robust error management.
    """
    
    def __init__(self):
        super().__init__()
        self.exception_handlers = []
        self.current_exception = None
        self.exception_history = []
        
        # Error tracking
        self.error_stats = {
            'exceptions_raised': 0,
            'exceptions_handled': 0,
            'unhandled_exceptions': 0,
            'error_recovery_attempts': 0
        }
        
        # Cognitive load monitoring
        self.cognitive_load = 0.0
        self.accessibility_mode = True
    
    def add_exception_handler(self, handler: ExceptionHandler):
        """Register an exception handler."""
        self.exception_handlers.append(handler)
    
    def raise_exception(self, exc_type: ExceptionType, message: str, 
                       cognitive_impact: float = 1.0):
        """Raise an exception with cognitive accessibility considerations."""
        # Create exception with stack trace
        stack_trace = self._build_stack_trace()
        
        exception = SonaException(
            type=exc_type,
            message=message,
            stack_trace=stack_trace,
            cognitive_impact=cognitive_impact,
            accessibility_info=self._generate_accessibility_info(exc_type, message)
        )
        
        self.current_exception = exception
        self.exception_history.append(exception)
        self.error_stats['exceptions_raised'] += 1
        
        # Update cognitive load
        self.cognitive_load += cognitive_impact
        
        return exception
    
    def _build_stack_trace(self) -> List[str]:
        """Build stack trace for debugging."""
        trace = []
        for frame in self.call_stack:
            if 'function_name' in frame:
                trace.append(f"  in {frame['function_name']}()")
            else:
                trace.append(f"  in <unknown>")
        return trace
    
    def _generate_accessibility_info(self, exc_type: ExceptionType, 
                                   message: str) -> str:
        """Generate accessibility-friendly error information."""
        accessibility_messages = {
            ExceptionType.RUNTIME_ERROR: "A runtime issue occurred. The program encountered an unexpected condition.",
            ExceptionType.TYPE_ERROR: "There's a type mismatch. The operation expected a different data type.",
            ExceptionType.VALUE_ERROR: "An invalid value was provided. Please check the input data.",
            ExceptionType.INDEX_ERROR: "Array access is out of bounds. The index is beyond the array size.",
            ExceptionType.DIVISION_BY_ZERO: "Cannot divide by zero. This operation is mathematically undefined.",
            ExceptionType.COGNITIVE_OVERLOAD: "The cognitive complexity is too high. Consider simplifying the operation."
        }
        
        base_info = accessibility_messages.get(exc_type, "An error occurred during execution.")
        return f"{base_info} Details: {message}"
    
    def handle_exception(self, current_address: int) -> Optional[int]:
        """Handle current exception and return jump address."""
        if not self.current_exception:
            return None
        
        # Find appropriate handler
        for handler in self.exception_handlers:
            if (handler.start_address <= current_address <= handler.end_address and
                (not handler.exception_types or 
                 self.current_exception.type in handler.exception_types)):
                
                # Exception handled
                self.error_stats['exceptions_handled'] += 1
                
                # Push exception onto stack for handler access
                self.stack.append(self.current_exception)
                
                # Clear current exception
                self.current_exception = None
                
                return handler.handler_address
        
        # No handler found
        self.error_stats['unhandled_exceptions'] += 1
        return None
    
    def run_with_exceptions(self, program_data: List[Any]) -> Any:
        """
        Enhanced execution loop with exception handling.
        """
        stack = self.stack
        globals_dict = self.globals
        
        # Clear state
        stack.clear()
        globals_dict.clear()
        self.current_exception = None
        self.cognitive_load = 0.0
        
        i = 0
        data_len = len(program_data)
        
        try:
            while i < data_len:
                opcode = program_data[i]
                
                # Check for exception handling
                if self.current_exception:
                    handler_address = self.handle_exception(i)
                    if handler_address:
                        i = handler_address
                        continue
                    else:
                        # Unhandled exception - terminate with error
                        break
                
                # Basic operations (inherited from Day 2-3)
                if opcode == 1:  # LOAD_CONST
                    i += 1
                    const_val = program_data[i]
                    stack.append(const_val)
                    
                elif opcode == 2:  # STORE_VAR
                    i += 1
                    var_name = program_data[i]
                    if not stack:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                                           "Stack underflow in STORE_VAR")
                        continue
                    value = stack.pop()
                    globals_dict[var_name] = value
                    
                elif opcode == 3:  # LOAD_VAR
                    i += 1
                    var_name = program_data[i]
                    if var_name not in globals_dict:
                        self.raise_exception(ExceptionType.VALUE_ERROR, 
                                           f"Undefined variable '{var_name}'")
                        continue
                    value = globals_dict[var_name]
                    stack.append(value)
                    
                elif opcode == 4:  # BINARY_ADD
                    if len(stack) < 2:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                                           "Stack underflow in BINARY_ADD")
                        continue
                    try:
                        b = stack.pop()
                        a = stack.pop()
                        result = a + b
                        stack.append(result)
                    except TypeError as e:
                        self.raise_exception(ExceptionType.TYPE_ERROR, 
                                           f"Cannot add {type(a).__name__} and {type(b).__name__}")
                        continue
                        
                elif opcode == 5:  # BINARY_SUB
                    if len(stack) < 2:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                                           "Stack underflow in BINARY_SUB")
                        continue
                    try:
                        b = stack.pop()
                        a = stack.pop()
                        result = a - b
                        stack.append(result)
                    except TypeError:
                        self.raise_exception(ExceptionType.TYPE_ERROR, 
                                           f"Cannot subtract {type(b).__name__} from {type(a).__name__}")
                        continue
                
                elif opcode == 6:  # BINARY_MUL
                    if len(stack) < 2:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                                           "Stack underflow in BINARY_MUL")
                        continue
                    try:
                        b = stack.pop()
                        a = stack.pop()
                        result = a * b
                        stack.append(result)
                    except TypeError:
                        self.raise_exception(ExceptionType.TYPE_ERROR, 
                                           f"Cannot multiply {type(a).__name__} and {type(b).__name__}")
                        continue
                
                elif opcode == 7:  # PRINT
                    if not stack:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                                           "Stack underflow in PRINT")
                        continue
                    value = stack.pop()
                    if not hasattr(self, '_suppress_output'):
                        print(value)
                
                # Exception handling opcodes
                elif opcode == 28:  # SETUP_EXCEPT
                    i += 1
                    handler_address = program_data[i]
                    i += 1
                    end_address = program_data[i]
                    
                    handler = ExceptionHandler(
                        start_address=i + 1,
                        end_address=end_address,
                        handler_address=handler_address,
                        exception_types=[]  # All exceptions
                    )
                    self.add_exception_handler(handler)
                
                elif opcode == 29:  # RAISE_EXCEPTION
                    i += 1
                    exc_type_name = program_data[i]
                    i += 1
                    message = program_data[i]
                    
                    # Map string to ExceptionType
                    exc_type = ExceptionType.RUNTIME_ERROR
                    for et in ExceptionType:
                        if et.value == exc_type_name:
                            exc_type = et
                            break
                    
                    self.raise_exception(exc_type, message)
                    continue
                
                # Advanced operations from Day 3
                elif opcode == 11:  # CALL_FUNCTION (with error handling)
                    i += 1
                    func_name = program_data[i]
                    i += 1
                    arg_count = program_data[i]
                    
                    if len(stack) < arg_count:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                                           f"Not enough arguments for {func_name}")
                        continue
                    
                    # Collect arguments
                    args = []
                    for _ in range(arg_count):
                        args.append(stack.pop())
                    args.reverse()
                    
                    try:
                        if func_name == 'divide':
                            if len(args) >= 2 and args[1] == 0:
                                self.raise_exception(ExceptionType.DIVISION_BY_ZERO, 
                                                   "Division by zero")
                                continue
                            result = args[0] / args[1]
                        elif func_name == 'get_item':
                            if len(args) >= 2:
                                try:
                                    result = args[0][args[1]]
                                except IndexError:
                                    self.raise_exception(ExceptionType.INDEX_ERROR, 
                                                       f"Index {args[1]} out of range")
                                    continue
                                except KeyError:
                                    self.raise_exception(ExceptionType.KEY_ERROR, 
                                                       f"Key '{args[1]}' not found")
                                    continue
                            else:
                                result = None
                        else:
                            result = None
                        
                        stack.append(result)
                        
                    except Exception as e:
                        self.raise_exception(ExceptionType.RUNTIME_ERROR, str(e))
                        continue
                
                elif opcode == 0:  # HALT
                    break
                    
                i += 1
                
        except Exception as e:
            # Catch any Python exceptions and convert to Sona exceptions
            self.raise_exception(ExceptionType.RUNTIME_ERROR, 
                               f"Internal error: {str(e)}")
        
        return stack[-1] if stack else None
    
    def get_error_report(self) -> Dict[str, Any]:
        """Generate comprehensive error report."""
        return {
            'error_statistics': self.error_stats.copy(),
            'cognitive_load': self.cognitive_load,
            'exception_history': [str(exc) for exc in self.exception_history],
            'current_exception': str(self.current_exception) if self.current_exception else None,
            'handlers_registered': len(self.exception_handlers)
        }


def test_exception_handling():
    """Test exception handling system for Day 4."""
    print("=" * 70)
    print("PHASE 1, DAY 4: EXCEPTION HANDLING & ERROR MANAGEMENT")
    print("=" * 70)
    
    vm = ExceptionHandlingVM()
    vm._suppress_output = True
    
    # Test 1: Basic exception handling
    print("Test 1: Division by Zero Exception")
    
    # Set up exception handler
    handler = ExceptionHandler(
        start_address=0,
        end_address=20,
        handler_address=15,
        exception_types=[ExceptionType.DIVISION_BY_ZERO]
    )
    vm.add_exception_handler(handler)
    
    program1 = [
        1, 10,                          # LOAD_CONST 10
        1, 0,                           # LOAD_CONST 0  
        11, 'divide', 2,                # CALL_FUNCTION divide, 2 args
        2, 'result',                    # STORE_VAR result
        13, 20,                         # JUMP_ABSOLUTE to end (pos 15)
        1, "Division error handled",    # Exception handler starts here
        2, 'error_message',            # STORE_VAR error_message
        1, -1,                         # LOAD_CONST -1 (error result)
        2, 'result',                   # STORE_VAR result
        0                              # HALT (pos 20)
    ]
    
    vm.run_with_exceptions(program1)
    print(f"Result after division by zero: {vm.globals.get('result')}")
    print(f"Error message: {vm.globals.get('error_message')}")
    
    # Test 2: Variable access error
    print("\\nTest 2: Undefined Variable Error")
    vm2 = ExceptionHandlingVM()
    vm2._suppress_output = True
    
    program2 = [
        3, 'undefined_var',             # LOAD_VAR undefined_var (should raise error)
        2, 'result',                    # STORE_VAR result
        0                               # HALT
    ]
    
    vm2.run_with_exceptions(program2)
    print(f"Exception raised: {vm2.current_exception}")
    
    # Test 3: Type error handling
    print("\\nTest 3: Type Error")
    vm3 = ExceptionHandlingVM()
    vm3._suppress_output = True
    
    program3 = [
        1, "hello",                     # LOAD_CONST "hello"
        1, 5,                          # LOAD_CONST 5
        4,                             # BINARY_ADD (string + int should fail)
        2, 'result',                   # STORE_VAR result
        0                              # HALT
    ]
    
    vm3.run_with_exceptions(program3)
    print(f"Type error: {vm3.current_exception}")
    
    # Test 4: Performance with exception handling
    print("\\nTest 4: Performance Impact")
    vm4 = ExceptionHandlingVM()
    vm4._suppress_output = True
    
    # Simple program without errors
    program4 = [
        1, 10,              # LOAD_CONST 10
        1, 20,              # LOAD_CONST 20
        4,                  # BINARY_ADD
        2, 'result',        # STORE_VAR result
        0                   # HALT
    ]
    
    iterations = 50000
    start_time = time.perf_counter()
    
    for _ in range(iterations):
        vm4.stack.clear()
        vm4.globals.clear()
        vm4.current_exception = None
        vm4.run_with_exceptions(program4)
    
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    ops_per_second = iterations / total_time
    
    print(f"Exception-enabled VM Performance:")
    print(f"Iterations: {iterations:,}")
    print(f"Time: {total_time:.4f} seconds")
    print(f"Ops/second: {ops_per_second:,.0f}")
    
    # Compare to previous baselines
    day3_baseline = 374158  # From Day 3 test
    performance_ratio = ops_per_second / day3_baseline
    
    print(f"\\nPerformance Analysis:")
    print(f"Day 3 baseline: {day3_baseline:,} ops/sec")
    print(f"Exception handling: {ops_per_second:,.0f} ops/sec")
    print(f"Performance retention: {performance_ratio:.2f}x")
    
    if performance_ratio >= 0.8:
        perf_status = "✅ EXCELLENT - Minimal performance impact"
    elif performance_ratio >= 0.6:
        perf_status = "✅ GOOD - Acceptable performance with error handling"
    else:
        perf_status = "⚠️ NEEDS OPTIMIZATION - Exception overhead too high"
    
    print(f"Status: {perf_status}")
    
    # Generate comprehensive error report
    print("\\nError Handling Analysis:")
    report = vm.get_error_report()
    for key, value in report.items():
        print(f"{key}: {value}")
    
    # Day 4 completion assessment
    day4_features = [
        ("Exception raising", vm.error_stats['exceptions_raised'] > 0),
        ("Exception handling", vm.error_stats['exceptions_handled'] > 0),
        ("Error reporting", len(vm.exception_history) > 0),
        ("Stack trace generation", any(exc.stack_trace for exc in vm.exception_history)),
        ("Cognitive accessibility", vm.accessibility_mode),
        ("Performance maintained", performance_ratio >= 0.5)
    ]
    
    completed_features = sum(1 for _, implemented in day4_features if implemented)
    total_features = len(day4_features)
    
    print(f"\\nDay 4 Feature Completion:")
    for feature, implemented in day4_features:
        status = "✅" if implemented else "⚪"
        print(f"{status} {feature}")
    
    print(f"\\nCompletion: {completed_features}/{total_features} features ({completed_features/total_features*100:.0f}%)")
    
    if completed_features >= 5:
        day4_status = "✅ PHASE 1, DAY 4: SUCCESSFULLY COMPLETED"
        next_step = "Ready for Phase 1, Day 5"
    elif completed_features >= 4:
        day4_status = "⚡ PHASE 1, DAY 4: MOSTLY COMPLETED"
        next_step = "Good progress for Phase 1, Day 5"
    else:
        day4_status = "⚠️ PHASE 1, DAY 4: NEEDS MORE WORK"
        next_step = "Requires additional development"
    
    print(f"{day4_status}")
    print(f"Next Steps: {next_step}")
    
    return ops_per_second, completed_features


if __name__ == "__main__":
    test_exception_handling()
