"""
Enhanced CLI Commands for Sona v0.10.1

Implements the new AI-powered CLI commands including profile, benchmark,
suggest, and explain with cognitive assistance features.
"""

import time
from pathlib import Path
from typing import Any, Dict, List

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


_AI_MODULES: dict[str, Any] | bool | None = None
_AI_LOAD_ERROR: str | None = None


def _load_ai_modules() -> dict[str, Any] | None:
    global _AI_MODULES, _AI_LOAD_ERROR
    if isinstance(_AI_MODULES, dict):
        return _AI_MODULES
    if _AI_MODULES is False:
        return None
    try:
        from sona.ai.code_completion import CodeCompletion
        from sona.ai.cognitive_assistant import CognitiveAssistant
        from sona.ai.ai_backend import get_ai_backend
        from sona.ai.natural_language import NaturalLanguageProcessor
        _AI_MODULES = {
            'CodeCompletion': CodeCompletion,
            'CognitiveAssistant': CognitiveAssistant,
            'get_ai_backend': get_ai_backend,
            'NaturalLanguageProcessor': NaturalLanguageProcessor,
        }
        return _AI_MODULES
    except Exception as exc:
        _AI_MODULES = False
        _AI_LOAD_ERROR = str(exc)
        return None


def _require_ai() -> dict[str, Any] | None:
    modules = _load_ai_modules()
    if modules is None:
        detail = _AI_LOAD_ERROR or "missing dependencies"
        print(f"[ERROR] AI features not available: {detail}")
        print("        Install transformers/torch, or set SONA_AI_BACKEND=ollama and start Ollama.")
        return None
    return modules


def _memory_mb() -> float | None:
    if psutil is None:
        return None
    try:
        return psutil.Process().memory_info().rss / 1024 / 1024
    except Exception:
        return None


def profile_command(args: list[str]) -> int:
    """Sona profile command - AI-powered execution profiling"""
    if not args:
        print("Usage: sona profile <file.sona> [--ai-insights]")
        return 1

    file_path = args[0]
    ai_insights = "--ai-insights" in args

    if not Path(file_path).exists():
        print(f"[ERROR] File not found: {file_path}")
        return 1

    print(f"[INFO] Profiling Sona execution: {file_path}")
    print("=" * 50)

    # Start profiling
    start_time = time.time()
    start_memory = _memory_mb()

    try:
        # Read and analyze the code
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()

        # Basic code analysis
        analysis = analyze_code_structure(code_content)

        # Simulate execution (replace with actual VM execution)
        execution_time = simulate_execution(code_content)

        end_time = time.time()
        end_memory = _memory_mb()

        memory_used = None
        if start_memory is not None and end_memory is not None:
            memory_used = max(0.0, end_memory - start_memory)

        # Display profiling results
        display_profile_results({
            'file': file_path,
            'execution_time': execution_time,
            'total_time': end_time - start_time,
            'memory_used': memory_used,
            'code_analysis': analysis,
            'ai_insights_enabled': ai_insights,
        })

        # Generate AI insights if requested
        if ai_insights:
            modules = _load_ai_modules()
            if modules is None:
                print("[WARN] AI insights unavailable (missing dependencies).")
            else:
                gpt2 = modules['get_ai_backend']()
                generate_ai_insights(code_content, analysis, gpt2)

        return 0

    except Exception as e:
        print(f"[ERROR] Profiling failed: {e}")
        return 1


def benchmark_command(args: list[str]) -> int:
    """Sona benchmark command - Performance testing with AI recommendations"""
    if not args:
        print("Usage: sona benchmark <file.sona> [--compare-versions] [--ai-recommendations]")
        return 1

    file_path = args[0]
    compare_versions = "--compare-versions" in args
    ai_recommendations = "--ai-recommendations" in args

    if not Path(file_path).exists():
        print(f"[ERROR] File not found: {file_path}")
        return 1

    print(f"[INFO] Benchmarking Sona performance: {file_path}")
    print("=" * 50)

    try:
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()

        # Run multiple benchmark iterations
        results = run_benchmark_iterations(code_content, iterations=5)

        # Display benchmark results
        display_benchmark_results(results)

        # Compare with previous versions if requested
        if compare_versions:
            compare_with_previous_versions(results)

        # Generate AI recommendations if requested
        if ai_recommendations:
            modules = _load_ai_modules()
            if modules is None:
                print("[WARN] AI recommendations unavailable (missing dependencies).")
            else:
                gpt2 = modules['get_ai_backend']()
                generate_performance_recommendations(code_content, results, gpt2)

        return 0

    except Exception as e:
        print(f"[ERROR] Benchmarking failed: {e}")
        return 1


def suggest_command(args: list[str]) -> int:
    """Sona suggest command - AI-powered code suggestions"""
    if not args:
        print("Usage: sona suggest <file.sona> [--cognitive] [--performance] [--accessibility]")
        return 1

    file_path = args[0]
    cognitive = "--cognitive" in args
    performance = "--performance" in args
    accessibility = "--accessibility" in args

    if not Path(file_path).exists():
        print(f"[ERROR] File not found: {file_path}")
        return 1

    modules = _require_ai()
    if modules is None:
        return 1

    print(f"[INFO] Generating AI suggestions for: {file_path}")
    print("=" * 50)

    try:
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()

        # Initialize AI components
        gpt2 = modules['get_ai_backend']()
        cognitive_assistant = modules['CognitiveAssistant']()
        code_completion = modules['CodeCompletion']()

        # Generate different types of suggestions
        suggestions = {}

        if cognitive or not any([performance, accessibility]):
            suggestions['cognitive'] = generate_cognitive_suggestions(
                code_content, cognitive_assistant
            )

        if performance or not any([cognitive, accessibility]):
            suggestions['performance'] = generate_performance_suggestions(
                code_content, gpt2
            )

        if accessibility or not any([cognitive, performance]):
            suggestions['accessibility'] = generate_accessibility_suggestions(
                code_content, code_completion
            )

        # Display suggestions
        display_suggestions(suggestions)

        return 0

    except Exception as e:
        print(f"[ERROR] Suggestion generation failed: {e}")
        return 1


def explain_command(args: list[str]) -> int:
    """Sona explain command - AI code explanation"""
    if not args:
        print("Usage: sona explain <file.sona> [--style simple|detailed|cognitive]")
        return 1

    file_path = args[0]
    style = "simple"

    # Parse style argument
    for i, arg in enumerate(args):
        if arg == "--style" and i + 1 < len(args):
            style = args[i + 1]
            break

    if not Path(file_path).exists():
        print(f"[ERROR] File not found: {file_path}")
        return 1

    modules = _require_ai()
    if modules is None:
        return 1

    print(f"[INFO] Explaining code: {file_path}")
    print(f"Style: {style}")
    print("=" * 50)

    try:
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()

        # Initialize NLP processor
        nlp = modules['NaturalLanguageProcessor']()

        # Generate explanation
        explanation = nlp.explain_code(code_content, style)

        print(explanation)

        # Add cognitive insights for cognitive style
        if style == "cognitive":
            cognitive_assistant = modules['CognitiveAssistant']()
            analysis = cognitive_assistant.analyze_working_memory("explaining code", code_content)

            print("\n[COGNITIVE] Cognitive Analysis:")
            print(f"   Complexity: {analysis['cognitive_load']}")
            print(f"   Suggestions: {', '.join(analysis['suggestions'][:2])}")

        return 0

    except Exception as e:
        print(f"[ERROR] Code explanation failed: {e}")
        return 1


# Helper functions

def analyze_code_structure(code: str) -> dict[str, Any]:
    """Analyze basic code structure"""
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    return {
        'total_lines': len(lines),
        'code_lines': len(non_empty_lines),
        'functions': code.count('function ') + code.count('def '),
        'classes': code.count('class '),
        'loops': code.count('for ') + code.count('while '),
        'conditionals': code.count('if ') + code.count('elif '),
        'comments': code.count('//') + code.count('#'),
        'cognitive_keywords': (
            code.count('think(')
            + code.count('remember(')
            + code.count('focus(')
        ),
    }


def simulate_execution(code: str) -> float:
    """Simulate code execution and return time"""
    # Simulate execution time based on code complexity
    complexity = len(code) * 0.001 + code.count('for ') * 0.01
    return complexity


def display_profile_results(results: dict[str, Any]) -> None:
    """Display profiling results"""
    print("[RESULTS] Profiling Results")
    print(f"   File: {results['file']}")
    print(f"   Execution Time: {results['execution_time']:.4f}s")
    print(f"   Total Time: {results['total_time']:.4f}s")

    memory_used = results.get('memory_used')
    if memory_used is None:
        print("   Memory Used: N/A")
    else:
        print(f"   Memory Used: {memory_used:.2f} MB")

    analysis = results['code_analysis']
    print("\n[ANALYSIS] Code Analysis:")
    print(f"   Lines of Code: {analysis['code_lines']}")
    print(f"   Functions: {analysis['functions']}")
    print(f"   Classes: {analysis['classes']}")
    print(f"   Loops: {analysis['loops']}")
    print(f"   Conditionals: {analysis['conditionals']}")
    print(f"   Cognitive Keywords: {analysis['cognitive_keywords']}")


def generate_ai_insights(code: str, analysis: dict[str, Any], gpt2) -> None:
    """Generate AI-powered insights"""
    try:
        print("\n[AI] Insights:")

        # Generate performance suggestions
        suggestions = gpt2.suggest_improvements(code)
        if suggestions:
            print(f"   Performance: {suggestions[:100]}...")

        # Cognitive load analysis
        if analysis['cognitive_keywords'] > 0:
            print("   [OK] Good use of cognitive programming patterns")
        else:
            print("   [SUGGEST] Consider adding cognitive keywords for accessibility")

    except Exception as e:
        print(f"   [WARN] AI insights unavailable: {e}")


def run_benchmark_iterations(code: str, iterations: int = 5) -> dict[str, Any]:
    """Run multiple benchmark iterations"""
    times = []

    for _ in range(iterations):
        start_time = time.time()
        simulate_execution(code)
        end_time = time.time()
        times.append(end_time - start_time)

    return {
        'times': times,
        'average': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'iterations': iterations,
    }


def display_benchmark_results(results: dict[str, Any]) -> None:
    """Display benchmark results"""
    print(f"[RESULTS] Benchmark Results ({results['iterations']} iterations):")
    print(f"   Average Time: {results['average']:.4f}s")
    print(f"   Min Time: {results['min']:.4f}s")
    print(f"   Max Time: {results['max']:.4f}s")
    print(
        "   Consistency: "
        f"{((1 - (results['max'] - results['min']) / results['average']) * 100):.1f}%"
    )


def compare_with_previous_versions(_results: dict[str, Any]) -> None:
    """Compare with previous version performance"""
    print("\n[INFO] Version Comparison:")
    print("   v0.8.1: Current results")
    print("   v0.8.0: ~15% slower (simulated)")
    print("   v0.7.2: ~30% slower (simulated)")


def generate_performance_recommendations(code: str, _results: dict[str, Any], gpt2) -> None:
    """Generate AI performance recommendations"""
    try:
        recommendations = gpt2.suggest_improvements(code)

        print("\n[AI] Performance Recommendations:")
        if recommendations:
            print(f"   {recommendations}")
        else:
            print("   Code appears to be well-optimized")

    except Exception as e:
        print(f"   [WARN] AI recommendations unavailable: {e}")


def generate_cognitive_suggestions(code: str, cognitive_assistant) -> list[str]:
    """Generate cognitive programming suggestions"""
    analysis = cognitive_assistant.analyze_working_memory("code review", code)
    return analysis['suggestions']


def generate_performance_suggestions(code: str, gpt2) -> list[str]:
    """Generate performance suggestions"""
    try:
        suggestions = gpt2.suggest_improvements(code)
        return [suggestions] if suggestions else []
    except Exception:
        return ["Performance analysis unavailable"]


def generate_accessibility_suggestions(code: str, code_completion) -> list[str]:
    """Generate accessibility suggestions"""
    return code_completion.get_cognitive_suggestions(code)


def display_suggestions(suggestions: dict[str, list[str]]) -> None:
    """Display all suggestions"""
    has_any = False
    for category, suggestion_list in suggestions.items():
        if suggestion_list:
            has_any = True
            print(f"\n[SUGGEST] {category.title()} Suggestions:")
            for i, suggestion in enumerate(suggestion_list[:3], 1):
                print(f"   {i}. {suggestion}")
    if not has_any:
        print("[INFO] No suggestions generated.")


# Command mapping for easy access
ENHANCED_COMMANDS = {
    'profile': profile_command,
    'benchmark': benchmark_command,
    'suggest': suggest_command,
    'explain': explain_command,
}
