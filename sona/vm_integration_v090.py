"""
Sona v0.9.0 - VM Integration Module for Enhanced Features
========================================================

This module provides seamless integration between the Sona VM and the new
v0.9.0 features including enhanced control flow, module system, and AI integration.

The integration ensures backward compatibility while providing advanced features
for developers who want to leverage the full power of Sona v0.9.0.

Author: Sona Development Team
Version: 0.9.0
Date: August 2025
"""

import traceback
from pathlib import Path
from typing import Any


# Import the enhanced components
try:
    from .control_flow_v090 import EnhancedControlFlow
    # Note: ast_nodes_v090 will be imported when needed to avoid circular imports
except ImportError:
    # Fallback for when modules aren't available
    EnhancedControlFlow = None

class SonaVMv090Integration:
    """
    Integration layer for Sona VM v0.9.0 enhanced features
    
    This class provides a bridge between the existing Sona VM and the new
    v0.9.0 features, ensuring smooth operation and backward compatibility.
    """
    
    def __init__(self, vm_instance):
        """Initialize the integration with a VM instance"""
        self.vm = vm_instance
        self.control_flow = EnhancedControlFlow()
        self.module_cache = {}
        self.ai_assistant = None
        self.cognitive_monitor = None
        
        # Feature flags for conditional functionality
        self.features_enabled = {
            'enhanced_control_flow': True,
            'module_system': True,
            'ai_integration': False,  # Disabled by default until AI backend is configured
            'cognitive_programming': True,
            'enhanced_debugging': True
        }
        
        # Initialize components
        self._initialize_integration()
    
    def _initialize_integration(self):
        """Initialize the integration components"""
        try:
            # Add v0.9.0 methods to the VM instance
            self.vm.control_flow_integration = self
            
            # Initialize module search paths
            self.module_search_paths = [
                Path.cwd(),
                Path.cwd() / "modules",
                Path.cwd() / "lib",
                Path(__file__).parent / "stdlib"
            ]
            
            # Initialize AI assistant if available
            self._initialize_ai_assistant()
            
            # Initialize cognitive monitor
            self._initialize_cognitive_monitor()
            
            print("✅ Sona v0.9.0 VM Integration initialized successfully")
            
        except Exception as e:  # B904
            print(
                f"⚠️  Warning: Some v0.9.0 features may not be available: {e}"
            )
    
    def _initialize_ai_assistant(self):
        """Initialize the AI assistant if available"""
        try:
            # This would connect to the actual AI backend
            # For now, we'll create a mock assistant
            self.ai_assistant = MockAIAssistant()
            self.features_enabled['ai_integration'] = True
        except Exception as e:  # B904
            print(f"ℹ️  AI integration not available: {e}")
            self.features_enabled['ai_integration'] = False
    
    def _initialize_cognitive_monitor(self):
        """Initialize the cognitive programming monitor"""
        try:
            self.cognitive_monitor = CognitiveMonitor()
            print("🧠 Cognitive programming features activated")
        except Exception as e:  # B904
            print(f"ℹ️  Cognitive programming not available: {e}")
            self.features_enabled['cognitive_programming'] = False
    
    # ========================================================================
    # ENHANCED CONTROL FLOW INTEGRATION
    # ========================================================================
    
    def execute_enhanced_if(self, if_statement):
        """Execute enhanced if statement with full feature support"""
        if not self.features_enabled['enhanced_control_flow']:
            return if_statement._basic_execute(self.vm)
        
        try:
            # Use the enhanced control flow engine
            return self.control_flow.execute_if_statement(
                if_statement, self.vm.current_scope, self.vm
            )
        except Exception as e:
            self._handle_control_flow_error(e, "if statement")
            return if_statement._basic_execute(self.vm)
    
    def execute_enhanced_for(self, for_loop):
        """Execute enhanced for loop with break/continue support"""
        if not self.features_enabled['enhanced_control_flow']:
            return for_loop._basic_execute(self.vm)
        
        try:
            return self.control_flow.execute_for_loop(
                for_loop, self.vm.current_scope, self.vm
            )
        except Exception as e:
            self._handle_control_flow_error(e, "for loop")
            return for_loop._basic_execute(self.vm)
    
    def execute_enhanced_while(self, while_loop):
        """Execute enhanced while loop with break/continue support"""
        if not self.features_enabled['enhanced_control_flow']:
            return while_loop._basic_execute(self.vm)
        
        try:
            return self.control_flow.execute_while_loop(
                while_loop, self.vm.current_scope, self.vm
            )
        except Exception as e:
            self._handle_control_flow_error(e, "while loop")
            return while_loop._basic_execute(self.vm)
    
    def execute_enhanced_try(self, try_statement):
        """Execute enhanced try statement with comprehensive exception handling"""
        if not self.features_enabled['enhanced_control_flow']:
            return try_statement._basic_execute(self.vm)
        
        try:
            return self.control_flow.execute_try_statement(
                try_statement, self.vm.current_scope, self.vm
            )
        except Exception as e:
            self._handle_control_flow_error(e, "try statement")
            return try_statement._basic_execute(self.vm)
    
    def execute_break(self):
        """Execute break statement"""
        return self.control_flow.execute_break()
    
    def execute_continue(self):
        """Execute continue statement"""
        return self.control_flow.execute_continue()
    
    def _handle_control_flow_error(self, error, context):
        """Handle errors in control flow execution"""
        if self.features_enabled['enhanced_debugging']:
            print(f"🔧 Enhanced debugging: Error in {context}")
            print(f"   Error type: {type(error).__name__}")
            print(f"   Error message: {str(error)}")
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                suggestion = self.ai_assistant.debug_assistance(error)
                if suggestion:
                    print(f"💡 AI Suggestion: {suggestion}")
    
    # ========================================================================
    # MODULE SYSTEM INTEGRATION
    # ========================================================================
    
    def import_module(self, module_path: str, alias: str | None = None):
        """Import a module using the enhanced module system"""
        if not self.features_enabled['module_system']:
            raise RuntimeError("Module system not available")
        
        try:
            # Check cache first
            if module_path in self.module_cache:
                module = self.module_cache[module_path]
            else:
                module = self._load_module(module_path)
                self.module_cache[module_path] = module
            
            # Add to current scope
            module_name = alias if alias else module_path.split('.')[-1]
            self.vm.current_scope[module_name] = module
            
            return module
            
        except Exception as e:  # B904
            raise RuntimeError(
                f"Failed to import module '{module_path}': {e}"
            ) from e
    
    def import_from_module(self, module_path: str, import_list: list[str]):
        """Import specific items from a module"""
        if not self.features_enabled['module_system']:
            raise RuntimeError("Module system not available")
        
        try:
            # Load the module
            if module_path in self.module_cache:
                module = self.module_cache[module_path]
            else:
                module = self._load_module(module_path)
                self.module_cache[module_path] = module
            
            # Import specific items
            for item_name in import_list:
                if hasattr(module, item_name):
                    self.vm.current_scope[item_name] = getattr(module, item_name)
                else:
                    raise RuntimeError(f"Module '{module_path}' has no attribute '{item_name}'")
            
            return True
            
        except Exception as e:  # B904
            raise RuntimeError(
                f"Failed to import from module '{module_path}': {e}"
            ) from e
    
    def _load_module(self, module_path: str):
        """Load a module from the filesystem"""
        # Try to find the module file
        for search_path in self.module_search_paths:
            module_file = search_path / f"{module_path}.sona"
            if module_file.exists():
                return self._execute_module_file(module_file)
        
        # Try Python modules as fallback
        try:
            import importlib
            return importlib.import_module(module_path)
        except ImportError:  # pragma: no cover
            pass
        
        raise RuntimeError(
            f"Module '{module_path}' not found"
        )
    
    def _execute_module_file(self, module_file: Path):
        """Execute a Sona module file and return its exports"""
        # This would parse and execute the module file
        # For now, return a mock module object
        class MockModule:
            def __init__(self, name):
                self.name = name
                self.exports = {}
        
        return MockModule(module_file.stem)
    
    def register_export(self, exported_item, value):
        """Register an item for export from the current module"""
        # This would be implemented when module compilation is ready
        pass
    
    # ========================================================================
    # AI INTEGRATION
    # ========================================================================
    
    def execute_ai_complete(self, statement):
        """Execute AI code completion"""
        if (
            not self.features_enabled['ai_integration']
            or not self.ai_assistant
        ):
            print("ℹ️  AI integration not available")
            return None
        
        return self.ai_assistant.complete_code(statement.prompt)
    
    def execute_ai_explain(self, statement):
        """Execute AI code explanation"""
        if (
            not self.features_enabled['ai_integration']
            or not self.ai_assistant
        ):
            print("ℹ️  AI integration not available")
            return None
        
        target_value = statement.target.evaluate(self.vm.current_scope)
        return self.ai_assistant.explain_code(target_value)
    
    def execute_ai_debug(self, statement):
        """Execute AI debugging assistance"""
        if (
            not self.features_enabled['ai_integration']
            or not self.ai_assistant
        ):
            print("ℹ️  AI integration not available")
            return None
        
        context_value = None
        if statement.context:
            context_value = statement.context.evaluate(self.vm.current_scope)
        
        return self.ai_assistant.debug_assistance(context_value)
    
    def execute_ai_optimize(self, statement):
        """Execute AI optimization suggestions"""
        if (
            not self.features_enabled['ai_integration']
            or not self.ai_assistant
        ):
            print("ℹ️  AI integration not available")
            return None
        
        target_value = statement.target.evaluate(self.vm.current_scope)
        return self.ai_assistant.suggest_optimization(target_value)
    
    # ========================================================================
    # COGNITIVE PROGRAMMING INTEGRATION
    # ========================================================================
    
    def execute_cognitive_check(self, statement):
        """Execute cognitive load check"""
        if (
            not self.features_enabled['cognitive_programming']
            or not self.cognitive_monitor
        ):
            # Basic execution without cognitive features
            for key, expr in statement.body.items():
                self.vm.current_scope[key] = expr.evaluate(
                    self.vm.current_scope
                )
            return None
        
        # Evaluate all body expressions
        evaluated_body = {}
        for key, expr in statement.body.items():
            evaluated_body[key] = expr.evaluate(self.vm.current_scope)
        
        return self.cognitive_monitor.check_cognitive_load(evaluated_body)
    
    def execute_focus_mode(self, statement):
        """Execute focus mode configuration"""
        if (
            not self.features_enabled['cognitive_programming']
            or not self.cognitive_monitor
        ):
            # Basic execution without cognitive features
            for key, expr in statement.body.items():
                self.vm.current_scope[key] = expr.evaluate(
                    self.vm.current_scope
                )
            return None
        
        # Evaluate all body expressions
        evaluated_body = {}
        for key, expr in statement.body.items():
            evaluated_body[key] = expr.evaluate(self.vm.current_scope)
        
        return self.cognitive_monitor.configure_focus_mode(evaluated_body)
    
    def execute_working_memory(self, statement):
        """Execute working memory management"""
        if (
            not self.features_enabled['cognitive_programming']
            or not self.cognitive_monitor
        ):
            # Basic execution without cognitive features
            for key, expr in statement.body.items():
                self.vm.current_scope[key] = expr.evaluate(
                    self.vm.current_scope
                )
            return None
        
        # Evaluate all body expressions
        evaluated_body = {}
        for key, expr in statement.body.items():
            evaluated_body[key] = expr.evaluate(self.vm.current_scope)
        
        return self.cognitive_monitor.manage_working_memory(evaluated_body)
    
    # ========================================================================
    # ENHANCED DEBUGGING INTEGRATION
    # ========================================================================
    
    def enhanced_error_reporting(self, error, context=None):
        """Provide enhanced error reporting with AI assistance"""
        if not self.features_enabled['enhanced_debugging']:
            return str(error)
        
        # Build comprehensive error report
        error_report = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'scope_variables': dict(self.vm.current_scope),
            'suggestions': []
        }
        
        # Add AI suggestions if available
        if self.features_enabled['ai_integration'] and self.ai_assistant:
            ai_suggestion = self.ai_assistant.debug_assistance(error_report)
            if ai_suggestion:
                error_report['suggestions'].append(f"AI: {ai_suggestion}")
        
        # Add cognitive programming insights
        if (
            self.features_enabled['cognitive_programming']
            and self.cognitive_monitor
        ):
            cognitive_insight = self.cognitive_monitor.analyze_error(
                error_report
            )
            if cognitive_insight:
                error_report['suggestions'].append(
                    f"Cognitive: {cognitive_insight}"
                )
        
        return error_report
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_feature_status(self) -> dict[str, bool]:
        """Get the status of all v0.9.0 features"""
        return self.features_enabled.copy()
    
    def enable_feature(self, feature_name: str) -> bool:
        """Enable a specific feature"""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = True
            return True
        return False
    
    def disable_feature(self, feature_name: str) -> bool:
        """Disable a specific feature"""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = False
            return True
        return False
    
    def get_version_info(self) -> dict[str, Any]:
        """Get comprehensive version and feature information"""
        return {
            'sona_version': '0.9.0',
            'vm_integration_version': '0.9.0',
            'features_enabled': self.features_enabled,
            'module_search_paths': [str(p) for p in self.module_search_paths],
            'cached_modules': list(self.module_cache.keys()),
            'ai_assistant_available': self.ai_assistant is not None,
            'cognitive_monitor_available': self.cognitive_monitor is not None
        }


# ========================================================================
# SUPPORT CLASSES
# ========================================================================

class MockAIAssistant:
    """Mock AI assistant for testing and development"""
    
    def complete_code(self, prompt: str) -> str:
        """Mock code completion"""
        return f"# AI completion for: {prompt}\n# (Mock implementation)"
    
    def explain_code(self, code) -> str:
        """Mock code explanation"""
        return (
            f"This code appears to be: {type(code).__name__} "
            "(Mock explanation)"
        )
    
    def debug_assistance(self, context) -> str:
        """Mock debugging assistance"""
        if isinstance(context, Exception):
            return f"Consider checking for {type(context).__name__} errors"
        return "General debugging suggestion: Check variable names and syntax"
    
    def suggest_optimization(self, code) -> str:
        """Mock optimization suggestions"""
        return "Consider using more efficient algorithms or data structures"


class CognitiveMonitor:
    """Cognitive programming monitor for neurodivergent developer support"""
    
    def __init__(self):
        self.current_cognitive_load = 0
        self.focus_mode_active = False
        self.working_memory_items = []
        self.max_working_memory = 7  # Miller's rule
    
    def check_cognitive_load(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check and report cognitive load"""
        # Calculate cognitive load based on context complexity
        load_factors = {
            'variable_count': len(context),
            'nesting_depth': self._calculate_nesting_depth(context),
            'concept_complexity': self._assess_concept_complexity(context)
        }
        
        total_load = sum(load_factors.values())
        self.current_cognitive_load = min(total_load, 10)  # Scale 0-10
        
        return {
            'cognitive_load': self.current_cognitive_load,
            'load_factors': load_factors,
            'recommendations': self._get_load_recommendations()
        }
    
    def configure_focus_mode(self, config: dict[str, Any]) -> dict[str, Any]:
        """Configure focus mode for better concentration"""
        self.focus_mode_active = config.get('enabled', False)
        
        if self.focus_mode_active:
            return {
                'focus_mode': 'activated',
                'distractions_filtered': True,
                'simplification_enabled': True,
                'break_reminders': True
            }
        else:
            return {'focus_mode': 'deactivated'}
    
    def manage_working_memory(self, items: dict[str, Any]) -> dict[str, Any]:
        """Manage working memory load"""
        self.working_memory_items = list(items.keys())
        
        if len(self.working_memory_items) > self.max_working_memory:
            return {
                'warning': 'Working memory overload detected',
                'current_items': len(self.working_memory_items),
                'recommended_max': self.max_working_memory,
                'suggestion': 'Consider breaking this into smaller functions'
            }
        
        return {
            'working_memory_status': 'optimal',
            'items_tracked': len(self.working_memory_items),
            'capacity_remaining': (
                self.max_working_memory - len(self.working_memory_items)
            )
        }
    
    def analyze_error(self, error_context: dict[str, Any]) -> str:
        """Provide cognitive-aware error analysis"""
        if self.current_cognitive_load > 7:
            return (
                "High cognitive load detected. Consider taking a break "
                "and simplifying the problem."
            )
        elif len(self.working_memory_items) > 5:
            return (
                "Working memory overload may be contributing to this error. "
                "Try focusing on one concept at a time."
            )
        else:
            return (
                "Error may be due to syntax or logic issues. Review step by "
                "step."
            )
    
    def _calculate_nesting_depth(self, context: dict[str, Any]) -> int:
        """Calculate the depth of nested structures"""
        max_depth = 0
        for value in context.values():
            if isinstance(value, (dict, list)):
                depth = self._get_depth(value)
                max_depth = max(max_depth, depth)
        return max_depth
    
    def _get_depth(self, obj, current_depth=1) -> int:
        """Recursively calculate depth of nested object"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                self._get_depth(v, current_depth + 1)
                for v in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                self._get_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth
    
    def _assess_concept_complexity(self, context: dict[str, Any]) -> int:
        """Assess the conceptual complexity of the context"""
        complexity_score = 0
        
        # Count different data types
        types_present = set(type(v).__name__ for v in context.values())
        complexity_score += len(types_present)
        
        # Count function-like objects
        for value in context.values():
            if callable(value):
                complexity_score += 2
        
        return min(complexity_score, 5)  # Cap at 5
    
    def _get_load_recommendations(self) -> list[str]:
        """Get recommendations based on current cognitive load"""
        if self.current_cognitive_load > 8:
            return [
                "Consider taking a break",
                "Simplify the current problem",
                "Break down into smaller steps"
            ]
        elif self.current_cognitive_load > 6:
            return [
                "Consider using simpler variable names",
                "Add more comments for clarity",
                "Focus on one concept at a time"
            ]
        else:
            return ["Cognitive load is manageable"]


# ========================================================================
# INTEGRATION HELPERS
# ========================================================================

def integrate_with_existing_vm(vm_instance):
    """
    Integrate v0.9.0 features with an existing VM instance
    
    This function adds v0.9.0 capabilities to any existing Sona VM
    without breaking existing functionality.
    """
    try:
        integration = SonaVMv090Integration(vm_instance)
        return integration
    except Exception as e:
        print(f"❌ Failed to integrate v0.9.0 features: {e}")
        return None

 
def check_v090_compatibility(vm_instance) -> bool:
    """Check if a VM instance is compatible with v0.9.0 features"""
    required_methods = ['execute_statements', 'current_scope']
    
    return all(hasattr(vm_instance, method) for method in required_methods)

 
def upgrade_vm_to_v090(vm_instance):
    """Upgrade an existing VM to support v0.9.0 features"""
    if not check_v090_compatibility(vm_instance):
        raise RuntimeError(
            "VM instance is not compatible with v0.9.0 features"
        )
    
    integration = integrate_with_existing_vm(vm_instance)
    if integration:
        print("✅ VM successfully upgraded to support Sona v0.9.0 features")
        return integration
    raise RuntimeError("Failed to upgrade VM to v0.9.0")


# ========================================================================
# EXAMPLE USAGE
# ========================================================================

if __name__ == "__main__":
    # Example of how to use the integration
    print("Sona v0.9.0 VM Integration Example")
    print("=" * 50)
    
    # Mock VM class for demonstration
    class MockVM:
        def __init__(self):
            self.current_scope = {}
        
        def execute_statements(self, statements):
            return f"Executed {len(statements)} statements"
    
    # Create and integrate
    vm = MockVM()
    integration = integrate_with_existing_vm(vm)
    
    if integration:
        print("Feature Status:")
        for feature, enabled in integration.get_feature_status().items():
            status = "✅" if enabled else "❌"
            print(f"  {status} {feature}")
        
        print("\nVersion Info:")
        version_info = integration.get_version_info()
        for key, value in version_info.items():
            print(f"  {key}: {value}")
    else:
        print("Integration failed - using basic functionality only")
