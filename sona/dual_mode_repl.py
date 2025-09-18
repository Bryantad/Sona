#!/usr/bin/env python3
"""
SONA 0.8.0 DUAL-MODE REPL SELECTOR
Allows users to choose between cognitive and traditional REPLs
"""

import os
import sys
from pathlib import Path


class SonaREPLSelector: """Interactive REPL mode selector for Sona 0.8.0"""

    def __init__(self): self.colors = {
            'blue': '\033[94m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'bold': '\033[1m',
            'reset': '\033[0m',
        }

    def display_welcome(self): """Display the welcome screen with mode selection"""
        print(f"{self.colors['bold']}{self.colors['blue']}")
        print("━" * 60)
        print("🧠 SONA 0.8.0 - NEURODIVERGENT-FIRST PROGRAMMING LANGUAGE")
        print("━" * 60)
        print(f"{self.colors['reset']}")
        print()
        print("🌟 Choose your preferred REPL experience:")
        print()
        print(
            f"   {self.colors['green']}1. Cognitive REPL{self.colors['reset']}"
        )
        print("      🧠 Neurodivergent-friendly interface")
        print("      💡 ADHD, Autism, Dyslexia support")
        print("      🎯 Thinking blocks, concepts, gentle errors")
        print("      📚 Interactive learning and guidance")
        print()
        print(
            f"   {self.colors['blue']}2. Traditional REPL{self.colors['reset']}"
        )
        print("      ⚡ Familiar programming interface")
        print("      🔧 Classic command-line experience")
        print("      📝 Standard syntax and error messages")
        print("      🚀 Fast and efficient for experienced users")
        print()
        print(
            f"   {self.colors['yellow']}3. Auto-Detect{self.colors['reset']}"
        )
        print("      🤖 AI-powered cognitive preference detection")
        print("      🔄 Adaptive interface based on usage patterns")
        print("      📊 Learns your preferred interaction style")
        print()

    def get_user_choice(self): """Get user's REPL mode preference"""
        while True: try: print(
                    f"{self.colors['bold']}Choose your REPL mode (1-3):{self.colors['reset']}",
                    end = " ",
                )
                choice = input().strip()

                if choice in ['1', 'cognitive', 'c']: return 'cognitive'
                elif choice in ['2', 'traditional', 't']: return 'traditional'
                elif choice in ['3', 'auto', 'a']: return 'auto'
                elif choice in ['help', 'h', '?']: self.show_help()
                    continue
                elif choice in ['exit', 'quit', 'q']: print("👋 Goodbye!")
                    sys.exit(0)
                else: print(
                        f"{self.colors['red']}Invalid choice. Please enter 1, 2, or 3.{self.colors['reset']}"
                    )
                    continue

            except KeyboardInterrupt: print(
                    f"\n{self.colors['yellow']}👋 Goodbye!{self.colors['reset']}"
                )
                sys.exit(0)
            except EOFError: print(
                    f"\n{self.colors['yellow']}👋 Goodbye!{self.colors['reset']}"
                )
                sys.exit(0)

    def show_help(self): """Show help information"""
        print()
        print(
            f"{self.colors['bold']}SONA REPL MODE HELP:{self.colors['reset']}"
        )
        print()
        print("🧠 COGNITIVE REPL:")
        print("   • Designed for neurodivergent users")
        print("   • Gentle error messages and suggestions")
        print("   • Visual thinking blocks and concepts")
        print("   • Break reminders and focus support")
        print("   • Multi-modal learning examples")
        print()
        print("⚡ TRADITIONAL REPL:")
        print("   • Standard programming interface")
        print("   • Familiar command-line experience")
        print("   • Quick and efficient for experienced users")
        print("   • Traditional error messages and syntax")
        print()
        print("🤖 AUTO-DETECT:")
        print("   • AI analyzes your coding patterns")
        print("   • Adapts interface to your preferences")
        print("   • Learns from your interaction style")
        print("   • Switches modes based on context")
        print()
        print(
            "Commands: 1/cognitive/c, 2/traditional/t, 3/auto/a, help/h, exit/quit/q"
        )
        print()

    def detect_cognitive_preference(self): """Simple cognitive preference detection"""
        print(
            f"{self.colors['yellow']}🤖 Analyzing your preferences...{self.colors['reset']}"
        )
        print()

        # Simple preference detection questions
        questions = [
            {
                'question': "Do you prefer detailed explanations when learning new concepts?",
                'cognitive_answer': ['yes', 'y', 'detailed', 'more'],
                'traditional_answer': ['no', 'n', 'brief', 'less'],
            },
            {
                'question': "Would you like gentle, encouraging error messages?",
                'cognitive_answer': ['yes', 'y', 'gentle', 'encouraging'],
                'traditional_answer': ['no', 'n', 'direct', 'standard'],
            },
            {
                'question': "Do you find visual examples helpful when coding?",
                'cognitive_answer': ['yes', 'y', 'visual', 'examples'],
                'traditional_answer': ['no', 'n', 'text', 'minimal'],
            },
        ]

        cognitive_score = 0
        traditional_score = 0

        for i, q in enumerate(questions, 1): print(f"{i}. {q['question']} (yes/no): ", end = (
            "")
        )
            try: answer = input().strip().lower()

                if answer in q['cognitive_answer']: cognitive_score + = 1
                elif answer in q['traditional_answer']: traditional_score + = 1

            except (KeyboardInterrupt, EOFError): print(
                    f"\n{self.colors['yellow']}Defaulting to cognitive mode...{self.colors['reset']}"
                )
                return 'cognitive'

        print()
        if cognitive_score > traditional_score: print(
                f"{self.colors['green']}🧠 Cognitive REPL recommended based on your preferences!{self.colors['reset']}"
            )
            return 'cognitive'
        elif traditional_score > cognitive_score: print(
                f"{self.colors['blue']}⚡ Traditional REPL recommended based on your preferences!{self.colors['reset']}"
            )
            return 'traditional'
        else: print(
                f"{self.colors['yellow']}🤖 Balanced preferences detected - starting with Cognitive REPL{self.colors['reset']}"
            )
            return 'cognitive'

    def start_cognitive_repl(self): """Start the cognitive REPL"""
        print(
            f"{self.colors['green']}🧠 Starting Cognitive REPL...{self.colors['reset']}"
        )
        print("🌟 Neurodivergent-friendly features enabled")
        print("💡 Type ':help' for cognitive commands")
        print(
            "🔄 You can switch to traditional mode anytime with ':traditional'"
        )
        print()

        try: from sona.cognitive_repl import CognitiveREPL

            cognitive_repl = CognitiveREPL()
            cognitive_repl.run()
        except ImportError: print(
                f"{self.colors['red']}❌ Cognitive REPL not available. Starting traditional REPL...{self.colors['reset']}"
            )
            self.start_traditional_repl()
        except Exception as e: print(
                f"{self.colors['red']}❌ Error starting cognitive REPL: {e}{self.colors['reset']}"
            )
            print("🔄 Falling back to traditional REPL...")
            self.start_traditional_repl()

    def start_traditional_repl(self): """Start the traditional REPL"""
        print(
            f"{self.colors['blue']}⚡ Starting Traditional REPL...{self.colors['reset']}"
        )
        print("🚀 Standard programming interface active")
        print("💻 Type ':help' for commands")
        print("🔄 You can switch to cognitive mode anytime with ':cognitive'")
        print()

        try: # Use custom traditional REPL
            from sona.traditional_repl import TraditionalREPL

            repl = TraditionalREPL()
            repl.run()
        except Exception as e: error_msg = (
            f"{self.colors['red']}❌ Error starting traditional "
        )
            error_msg + = f"REPL: {e}{self.colors['reset']}"
            print(error_msg)
            sys.exit(1)

    def run(self): """Main REPL selector run method"""
        self.display_welcome()

        choice = self.get_user_choice()

        if choice == 'cognitive': self.start_cognitive_repl()
        elif choice == 'traditional': self.start_traditional_repl()
        elif choice = (
            = 'auto': detected_mode = self.detect_cognitive_preference()
        )
            if detected_mode == 'cognitive': self.start_cognitive_repl()
            else: self.start_traditional_repl()


def main(): """Main entry point for dual-mode REPL selector"""
    selector = SonaREPLSelector()
    selector.run()


if __name__ == "__main__": main()
