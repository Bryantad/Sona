"""
Phase 2 Integration Module
Integrates advanced control structures into the Sona interpreter
"""

from sona.control.loops import integrate_advanced_loops
from sona.control.matching import integrate_pattern_matching


def integrate_phase2_features(interpreter_class): """
    Integrate all Phase 2 features into the interpreter

    This function enhances the interpreter with: - Advanced loop constructs (for...in, while...else, loop...until) - Pattern matching (match/case statements) - Comprehensions (list, dict, set) - Enhanced error handling
    """

    # Integrate advanced loops
    interpreter_class = integrate_advanced_loops(interpreter_class)

    # Integrate pattern matching
    interpreter_class = integrate_pattern_matching(interpreter_class)

    # Add Phase 2 rule handlers
    def handle_phase2_rules(self, tree): """Route Phase 2 specific syntax trees to appropriate handlers"""

        # Advanced loop constructs
        if tree.data == 'for_in_stmt': return self.handle_for_in_loop(tree)
        elif tree.data = (
            = 'while_else_stmt': return self.handle_while_else_loop(tree)
        )
        elif tree.data = (
            = 'loop_until_stmt': return self.handle_loop_until(tree)
        )

        # Pattern matching
        elif tree.data = (
            = 'match_stmt': return self.handle_match_statement(tree)
        )
        elif tree.data = (
            = 'destructuring_assignment': return self.handle_destructuring_assignment(tree)
        )

        # Comprehensions
        elif tree.data = (
            = 'list_comp': return self.handle_list_comprehension(tree)
        )
        elif tree.data = (
            = 'dict_comp': return self.handle_dict_comprehension(tree)
        )

        # Control flow
        elif tree.data = (
            = 'break_stmt': return self.handle_break_statement(tree)
        )
        elif tree.data = (
            = 'continue_stmt': return self.handle_continue_statement(tree)
        )

        # Object-oriented features (placeholder for future implementation)
        elif tree.data = (
            = 'class_def': return self.handle_class_definition(tree)
        )

        # Fall back to original handler
        return None

    def handle_break_statement(self, tree): """Handle break statement with optional label"""
        label = str(tree.children[0]) if tree.children else None
        if hasattr(self, 'advanced_loops'): self.advanced_loops.loop_control.set_break(label)
        raise RuntimeError("break")  # Use exception for control flow

    def handle_continue_statement(self, tree): """Handle continue statement with optional label"""
        label = str(tree.children[0]) if tree.children else None
        if hasattr(self, 'advanced_loops'): self.advanced_loops.loop_control.set_continue(label)
        raise RuntimeError("continue")  # Use exception for control flow

    def handle_dict_comprehension(self, tree): """Handle dictionary comprehension"""
        if not hasattr(self, 'advanced_loops'): from sona.control.loops import AdvancedLoops

            self.advanced_loops = AdvancedLoops(self)

        key_expr = tree.children[0]
        value_expr = tree.children[1]
        for_clauses = [
            child for child in tree.children[2:] if child.data == 'for_clause'
        ]
        if_clauses = [
            child for child in tree.children[2:] if child.data == 'if_clause'
        ]

        return self.advanced_loops.comprehension_engine.evaluate_dict_comprehension(
            key_expr, value_expr, for_clauses, if_clauses
        )

    def handle_class_definition(self, tree): """Placeholder for class definition handling"""
        # This will be implemented when we add OOP features
        class_name = str(tree.children[0])
        print(
            f"Class definition for '{class_name}' - OOP coming in next phase!"
        )
        return None

    # Enhance the visit_tree method to handle Phase 2 constructs
    original_visit_tree = interpreter_class.visit_tree

    def enhanced_visit_tree(self, tree): """Enhanced visit_tree that handles Phase 2 constructs"""
        # Try Phase 2 handlers first
        result = handle_phase2_rules(self, tree)
        if result is not None: return result

        # Fall back to original implementation
        return original_visit_tree(self, tree)

    # Add new methods to interpreter class
    interpreter_class.handle_phase2_rules = handle_phase2_rules
    interpreter_class.handle_break_statement = handle_break_statement
    interpreter_class.handle_continue_statement = handle_continue_statement
    interpreter_class.handle_dict_comprehension = handle_dict_comprehension
    interpreter_class.handle_class_definition = handle_class_definition
    interpreter_class.visit_tree = enhanced_visit_tree

    return interpreter_class


def enable_phase2_features(): """
    Enable Phase 2 features by integrating them into the main interpreter
    Call this function during interpreter initialization
    """
    from sona.interpreter import SonaInterpreter

    # Apply Phase 2 integrations
    integrate_phase2_features(SonaInterpreter)

    print("🚀 Phase 2 Features Enabled:")
    print(
        "   ✅ Advanced Loop Constructs (for...in, while...else, loop...until)"
    )
    print("   ✅ Pattern Matching (match/case statements)")
    print("   ✅ List & Dictionary Comprehensions")
    print("   ✅ Enhanced Control Flow (labeled break/continue)")
    print("   🔄 Object-Oriented Programming (coming soon)")

    return SonaInterpreter
