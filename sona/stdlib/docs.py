"""Documentation and examples for Sona standard library modules"""

MODULE_DOCS = {
    "math": {
        "description": """Math module provides standard mathematical functions and constants.

Available functions:
- add(a, b)      : Add two numbers
- subtract(a, b)  : Subtract b from a
- multiply(a, b)  : Multiply two numbers
- divide(a, b)    : Divide a by b
- pow(x, y)      : Raise x to power y
- sqrt(x)        : Square root of x
- sin(x)         : Sine of x (radians)
- cos(x)         : Cosine of x (radians)
- tan(x)         : Tangent of x (radians)
- log(x)         : Natural logarithm
- exp(x)         : e raised to power x

Constants:
- PI  (π)        : 3.141592653589793
- E   (e)        : 2.718281828459045
- TAU (τ = 2π)   : 6.283185307179586""",
        
        "example": """# Basic arithmetic
print(math.add(5, 3))      # 8
print(math.subtract(5, 3))  # 2
print(math.multiply(4, 3))  # 12
print(math.divide(10, 2))   # 5

# Constants
print(math.PI)  # 3.141592653589793
print(math.E)   # 2.718281828459045
print(math.TAU) # 6.283185307179586

# Advanced math
print(math.sqrt(16))      # 4.0
print(math.pow(2, 3))     # 8.0
print(math.log(math.E))   # 1.0
print(math.sin(math.PI))  # ≈0.0

# Example calculation: area of a circle
let radius = 5
let area = math.multiply(math.PI, math.pow(radius, 2))
print(area)  # ≈78.54
""",
    },
    "greeting": {
        "description": """Greeting module provides friendly greeting functions.

Available functions:
- hi()             : Simple greeting that returns "Hello there!"
- hello(name="")   : Personalized hello greeting for a name (or "World" if none provided)
- greet(name="friend") : Formal greeting with "Greetings, ___!"
- say(message)     : Returns any custom message

Note: In the REPL, you can also call these functions directly without importing the greeting module!""",
        
        "example": """# Import the greeting module
import greeting

# Simple greeting
print(greeting.hi())  # Hello there!

# Personalized greeting
print(greeting.hello("Sona"))  # Hello, Sona!
print(greeting.hello())  # Hello, World!

# Formal greeting
print(greeting.greet("User"))  # Greetings, User!
print(greeting.greet())  # Greetings, friend!

# Custom message
let message = greeting.say("This is a custom message!")
print(message)  # This is a custom message!

# In REPL, you can also use these directly:
# hi()
# hello("Sona")
# greet("User")
# say("Hello!")
""",
    },
    "random": {
        "description": """Random module provides random number generation and related functions.""",
        "example": """# Basic random operations
print(random.random())        # Float in [0.0, 1.0)
print(random.randint(1, 6))  # Integer from 1 to 6

# Advanced operations
items = [1, 2, 3, 4, 5]
print(random.choice(items))   # Pick random item
print(random.shuffle(items))  # Shuffle list
"""
    },
    "string": {
        "description": """String module provides string manipulation functions.""",
        "example": """text = "Hello, World!"
print(string.length(text))      # 13
print(string.upper(text))       # "HELLO, WORLD!"
print(string.lower(text))       # "hello, world!"
print(string.replace(text, "World", "Sona"))  # "Hello, Sona!"
"""
    }
}

def show_module_doc(module_name):
    """Show documentation for a module"""
    if module_name not in MODULE_DOCS:
        print(f"[ERROR] No documentation found for module '{module_name}'")
        return

    doc = MODULE_DOCS[module_name]
    print(f"\n{module_name.upper()} MODULE")
    print("=" * (len(module_name) + 7))
    print(doc["description"])
    
def show_module_example(module_name):
    """Show example code for a module"""
    if module_name not in MODULE_DOCS:
        print(f"[ERROR] No examples found for module '{module_name}'")
        return

    doc = MODULE_DOCS[module_name]
    print(f"\n{module_name.upper()} EXAMPLES")
    print("=" * (len(module_name) + 9))
    print(doc["example"])
