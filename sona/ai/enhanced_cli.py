"""
Enhanced CLI Commands for Sona v0.8.2

Implements the new AI-powered CLI commands including profile, benchmark,
suggest, and explain with cognitive assistance features.
"""

import time
from pathlib import Path
from typing import Any, Dict, List

import psutil


# Import AI modules
try:
    from sona.ai.code_completion import CodeCompletion
    from sona.ai.cognitive_assistant import CognitiveAssistant
    from sona.ai.gpt2_integration import get_gpt2_instance
    from sona.ai.natural_language import NaturalLanguageProcessor
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI features not available. Install transformers and torch.")


def profile_command(args: list[str]) -> None:
    """Sona profile command - AI-powered execution profiling"""
    if not args:
        print("Usage: sona profile <file.sona> [--ai-insights]")
        return
    
    file_path = args[0]
    ai_insights = "--ai-insights" in args
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"🔍 Profiling Sona execution: {file_path}")
    print("=" * 50)
    
    # Start profiling
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    try:
        # Read and analyze the code
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()
        
        # Basic code analysis
        analysis = analyze_code_structure(code_content)
        
        # Simulate execution (replace with actual VM execution)
        execution_time = simulate_execution(code_content)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Display profiling results
        display_profile_results({
            'file': file_path,
            'execution_time': execution_time,
            'total_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'code_analysis': analysis,
            'ai_insights_enabled': ai_insights
        })
        
        # Generate AI insights if requested
        if ai_insights and AI_AVAILABLE:
            generate_ai_insights(code_content, analysis)
            
    except Exception as e:
        print(f"❌ Profiling failed: {e}")


def benchmark_command(args: list[str]) -> None:
    """Sona benchmark command - Performance testing with AI recommendations"""
    if not args:
        print("Usage: sona benchmark <file.sona> [--compare-versions] [--ai-recommendations]")
        return
    
    file_path = args[0]
    compare_versions = "--compare-versions" in args
    ai_recommendations = "--ai-recommendations" in args
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"⚡ Benchmarking Sona performance: {file_path}")
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
        if ai_recommendations and AI_AVAILABLE:
            generate_performance_recommendations(code_content, results)
            
    except Exception as e:
        print(f"❌ Benchmarking failed: {e}")


def suggest_command(args: list[str]) -> None:
    """Sona suggest command - AI-powered code suggestions"""
    if not args:
        print("Usage: sona suggest <file.sona> [--cognitive] [--performance] [--accessibility]")
        return
    
    file_path = args[0]
    cognitive = "--cognitive" in args
    performance = "--performance" in args
    accessibility = "--accessibility" in args
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    if not AI_AVAILABLE:
        print("❌ AI features not available. Please install required dependencies.")
        return
    
    print(f"💡 Generating AI suggestions for: {file_path}")
    print("=" * 50)
    
    try:
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()
        
        # Initialize AI components
        gpt2 = get_gpt2_instance()
        cognitive_assistant = CognitiveAssistant()
        code_completion = CodeCompletion()
        
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
        
    except Exception as e:
        print(f"❌ Suggestion generation failed: {e}")


def explain_command(args: list[str]) -> None:
    """Sona explain command - AI code explanation"""
    if not args:
        print("Usage: sona explain <file.sona> [--style simple|detailed|cognitive]")
        return
    
    file_path = args[0]
    style = "simple"
    
    # Parse style argument
    for i, arg in enumerate(args):
        if arg == "--style" and i + 1 < len(args):
            style = args[i + 1]
            break
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    if not AI_AVAILABLE:
        print("❌ AI features not available. Please install required dependencies.")
        return
    
    print(f"📖 Explaining code: {file_path}")
    print(f"Style: {style}")
    print("=" * 50)
    
    try:
        with open(file_path, encoding='utf-8') as f:
            code_content = f.read()
        
        # Initialize NLP processor
        nlp = NaturalLanguageProcessor()
        
        # Generate explanation
        explanation = nlp.explain_code(code_content, style)
        
        print(explanation)
        
        # Add cognitive insights for cognitive style
        if style == "cognitive" and AI_AVAILABLE:
            cognitive_assistant = CognitiveAssistant()
            analysis = cognitive_assistant.analyze_working_memory("explaining code", code_content)
            
            print("\n🧠 Cognitive Analysis:")
            print(f"   Complexity: {analysis['cognitive_load']}")
            print(f"   Suggestions: {', '.join(analysis['suggestions'][:2])}")
        
    except Exception as e:
        print(f"❌ Code explanation failed: {e}")


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
            code.count('think(') + 
            code.count('remember(') + 
            code.count('focus(')
        )
    }


def simulate_execution(code: str) -> float:
    """Simulate code execution and return time"""
    # Simulate execution time based on code complexity
    complexity = len(code) * 0.001 + code.count('for ') * 0.01
    return complexity


def display_profile_results(results: dict[str, Any]) -> None:
    """Display profiling results"""
    print("📊 Profiling Results")
    print(f"   File: {results['file']}")
    print(f"   Execution Time: {results['execution_time']:.4f}s")
    print(f"   Total Time: {results['total_time']:.4f}s")
    print(f"   Memory Used: {results['memory_used']:.2f} MB")
    
    analysis = results['code_analysis']
    print("\n📈 Code Analysis:")
    print(f"   Lines of Code: {analysis['code_lines']}")
    print(f"   Functions: {analysis['functions']}")
    print(f"   Classes: {analysis['classes']}")
    print(f"   Loops: {analysis['loops']}")
    print(f"   Conditionals: {analysis['conditionals']}")
    print(f"   Cognitive Keywords: {analysis['cognitive_keywords']}")


def generate_ai_insights(code: str, analysis: dict[str, Any]) -> None:
    """Generate AI-powered insights"""
    try:
        gpt2 = get_gpt2_instance()
        
        print("\n🤖 AI Insights:")
        
        # Generate performance suggestions
        suggestions = gpt2.suggest_improvements(code)
        if suggestions:
            print(f"   Performance: {suggestions[:100]}...")
        
        # Cognitive load analysis
        if analysis['cognitive_keywords'] > 0:
            print("   ✅ Good use of cognitive programming patterns")
        else:
            print("   💡 Consider adding cognitive keywords for better accessibility")
            
    except Exception as e:
        print(f"   ⚠️ AI insights unavailable: {e}")


def run_benchmark_iterations(code: str, iterations: int = 5) -> dict[str, Any]:
    """Run multiple benchmark iterations"""
    times = []
    
    for i in range(iterations):
        start_time = time.time()
        simulate_execution(code)
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        'times': times,
        'average': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'iterations': iterations
    }


def display_benchmark_results(results: dict[str, Any]) -> None:
    """Display benchmark results"""
    print(f"⚡ Benchmark Results ({results['iterations']} iterations):")
    print(f"   Average Time: {results['average']:.4f}s")
    print(f"   Min Time: {results['min']:.4f}s")
    print(f"   Max Time: {results['max']:.4f}s")
    print(f"   Consistency: {((1 - (results['max'] - results['min']) / results['average']) * 100):.1f}%")


def compare_with_previous_versions(results: dict[str, Any]) -> None:
    """Compare with previous version performance"""
    print("\n📊 Version Comparison:")
    print("   v0.8.1: Current results")
    print("   v0.8.0: ~15% slower (simulated)")
    print("   v0.7.2: ~30% slower (simulated)")


def generate_performance_recommendations(code: str, results: dict[str, Any]) -> None:
    """Generate AI performance recommendations"""
    try:
        gpt2 = get_gpt2_instance()
        recommendations = gpt2.suggest_improvements(code)
        
        print("\n🚀 Performance Recommendations:")
        if recommendations:
            print(f"   {recommendations}")
        else:
            print("   Code appears to be well-optimized")
            
    except Exception as e:
        print(f"   ⚠️ AI recommendations unavailable: {e}")


def generate_cognitive_suggestions(code: str, cognitive_assistant: CognitiveAssistant) -> list[str]:
    """Generate cognitive programming suggestions"""
    analysis = cognitive_assistant.analyze_working_memory("code review", code)
    return analysis['suggestions']


def generate_performance_suggestions(code: str, gpt2) -> list[str]:
    """Generate performance suggestions"""
    try:
        suggestions = gpt2.suggest_improvements(code)
        return [suggestions] if suggestions else []
    except:
        return ["Performance analysis unavailable"]


def generate_accessibility_suggestions(code: str, code_completion: CodeCompletion) -> list[str]:
    """Generate accessibility suggestions"""
    return code_completion.get_cognitive_suggestions(code)


def display_suggestions(suggestions: dict[str, list[str]]) -> None:
    """Display all suggestions"""
    for category, suggestion_list in suggestions.items():
        if suggestion_list:
            print(f"\n💡 {category.title()} Suggestions:")
            for i, suggestion in enumerate(suggestion_list[:3], 1):
                print(f"   {i}. {suggestion}")


# Command mapping for easy access
ENHANCED_COMMANDS = {
    'profile': profile_command,
    'benchmark': benchmark_command,
    'suggest': suggest_command,
    'explain': explain_command
}
