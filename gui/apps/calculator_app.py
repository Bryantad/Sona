#!/usr/bin/env python3
"""
Sona Calculator Application - Advanced Scientific Calculator
Part of the Sona Application Platform
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import re
from typing import Optional, List, Dict, Any


class CalculatorApp:
    """Advanced scientific calculator with graphing capabilities"""
    
    def __init__(self, container: tk.Widget, instance, framework):
        self.container = container
        self.instance = instance
        self.framework = framework
        
        # Calculator state
        self.display_var = tk.StringVar(value="0")
        self.memory = 0.0
        self.history = []
        self.current_expression = ""
        self.result_displayed = True
        
        # UI components
        self.create_interface()
        self.setup_keyboard_bindings()
        
        # Update framework heartbeat
        self.update_heartbeat()
    
    def create_interface(self):
        """Create the calculator interface"""
        # Main container
        main_frame = ttk.Frame(self.container, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu if supported
        if self.instance.capabilities.has_menu:
            self.create_menu()
        
        # Display area
        self.create_display_area(main_frame)
        
        # Button area
        self.create_button_area(main_frame)
        
        # History panel (collapsible)
        self.create_history_panel(main_frame)
        
        # Memory panel
        self.create_memory_panel(main_frame)
        
        # Status bar if supported
        if self.instance.capabilities.has_statusbar:
            self.create_status_bar(main_frame)
    
    def create_menu(self):
        """Create calculator menu"""
        # This would integrate with the parent window's menu
        pass
    
    def create_display_area(self, parent):
        """Create the calculator display"""
        display_frame = ttk.LabelFrame(parent, text="Display", padding=5)
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Expression display (shows what's being typed)
        self.expression_var = tk.StringVar()
        expression_label = ttk.Label(display_frame, textvariable=self.expression_var,
                                   font=('Consolas', 10), foreground='gray')
        expression_label.pack(fill=tk.X)
        
        # Main display
        display_entry = ttk.Entry(display_frame, textvariable=self.display_var,
                                font=('Consolas', 16, 'bold'), justify='right',
                                state='readonly')
        display_entry.pack(fill=tk.X, pady=(5, 0))
    
    def create_button_area(self, parent):
        """Create calculator buttons"""
        button_frame = ttk.LabelFrame(parent, text="Calculator", padding=5)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Configure grid weights
        for i in range(6):
            button_frame.columnconfigure(i, weight=1)
        
        # Button definitions (text, row, col, colspan, command)
        buttons = [
            # Row 0 - Memory and advanced functions
            ('MC', 0, 0, 1, self.memory_clear),
            ('MR', 0, 1, 1, self.memory_recall),
            ('M+', 0, 2, 1, self.memory_add),
            ('M-', 0, 3, 1, self.memory_subtract),
            ('MS', 0, 4, 1, self.memory_store),
            ('C', 0, 5, 1, self.clear_all),
            
            # Row 1 - Scientific functions
            ('sin', 1, 0, 1, lambda: self.apply_function('sin')),
            ('cos', 1, 1, 1, lambda: self.apply_function('cos')),
            ('tan', 1, 2, 1, lambda: self.apply_function('tan')),
            ('log', 1, 3, 1, lambda: self.apply_function('log')),
            ('ln', 1, 4, 1, lambda: self.apply_function('ln')),
            ('CE', 1, 5, 1, self.clear_entry),
            
            # Row 2 - More functions and numbers
            ('π', 2, 0, 1, lambda: self.input_constant('π')),
            ('e', 2, 1, 1, lambda: self.input_constant('e')),
            ('x²', 2, 2, 1, lambda: self.apply_function('square')),
            ('√', 2, 3, 1, lambda: self.apply_function('sqrt')),
            ('1/x', 2, 4, 1, lambda: self.apply_function('reciprocal')),
            ('⌫', 2, 5, 1, self.backspace),
            
            # Row 3 - Numbers and operations
            ('7', 3, 0, 1, lambda: self.input_digit('7')),
            ('8', 3, 1, 1, lambda: self.input_digit('8')),
            ('9', 3, 2, 1, lambda: self.input_digit('9')),
            ('/', 3, 3, 1, lambda: self.input_operator('/')),
            ('(', 3, 4, 1, lambda: self.input_operator('(')),
            (')', 3, 5, 1, lambda: self.input_operator(')')),
            
            # Row 4
            ('4', 4, 0, 1, lambda: self.input_digit('4')),
            ('5', 4, 1, 1, lambda: self.input_digit('5')),
            ('6', 4, 2, 1, lambda: self.input_digit('6')),
            ('*', 4, 3, 1, lambda: self.input_operator('*')),
            ('x^y', 4, 4, 1, lambda: self.input_operator('**')),
            ('±', 4, 5, 1, self.toggle_sign),
            
            # Row 5
            ('1', 5, 0, 1, lambda: self.input_digit('1')),
            ('2', 5, 1, 1, lambda: self.input_digit('2')),
            ('3', 5, 2, 1, lambda: self.input_digit('3')),
            ('-', 5, 3, 1, lambda: self.input_operator('-')),
            ('mod', 5, 4, 1, lambda: self.input_operator('%')),
            ('=', 5, 5, 1, self.calculate),
            
            # Row 6
            ('0', 6, 0, 2, lambda: self.input_digit('0')),
            ('.', 6, 2, 1, lambda: self.input_digit('.')),
            ('+', 6, 3, 1, lambda: self.input_operator('+')),
            ('Ans', 6, 4, 1, self.input_last_answer),
            ('=', 6, 5, 1, self.calculate),
        ]
        
        # Create buttons
        self.buttons = {}
        for text, row, col, colspan, command in buttons:
            if text in ['='] and row == 6:  # Skip duplicate equals
                continue
                
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=row, column=col, columnspan=colspan, 
                    sticky='nsew', padx=1, pady=1)
            self.buttons[text] = btn
            
            # Make equals button prominent
            if text == '=':
                btn.configure(style='Accent.TButton')
    
    def create_history_panel(self, parent):
        """Create calculation history panel"""
        history_frame = ttk.LabelFrame(parent, text="History", padding=5)
        history_frame.pack(fill=tk.X, pady=(0, 10))
        
        # History listbox with scrollbar
        history_container = ttk.Frame(history_frame)
        history_container.pack(fill=tk.X)
        
        self.history_listbox = tk.Listbox(history_container, height=4,
                                        font=('Consolas', 9))
        history_scrollbar = ttk.Scrollbar(history_container, orient="vertical",
                                        command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_listbox.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        
        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(history_controls, text="Clear History",
                  command=self.clear_history).pack(side=tk.LEFT)
        ttk.Button(history_controls, text="Use Selected",
                  command=self.use_history_item).pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind double-click to use history item
        self.history_listbox.bind('<Double-Button-1>', 
                                lambda e: self.use_history_item())
    
    def create_memory_panel(self, parent):
        """Create memory panel"""
        memory_frame = ttk.LabelFrame(parent, text="Memory", padding=5)
        memory_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.memory_var = tk.StringVar(value="Memory: 0")
        ttk.Label(memory_frame, textvariable=self.memory_var).pack()
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Calculator mode indicator
        ttk.Label(status_frame, text="Scientific Mode").pack(side=tk.RIGHT)
    
    def setup_keyboard_bindings(self):
        """Setup keyboard shortcuts"""
        # Bind to container's parent for keyboard events
        widget = self.container
        while widget.master:
            widget = widget.master
        
        # Number keys
        for i in range(10):
            widget.bind(f'<Key-{i}>', lambda e, digit=str(i): self.input_digit(digit))
        
        # Operators
        widget.bind('<Key-plus>', lambda e: self.input_operator('+'))
        widget.bind('<Key-minus>', lambda e: self.input_operator('-'))
        widget.bind('<Key-asterisk>', lambda e: self.input_operator('*'))
        widget.bind('<Key-slash>', lambda e: self.input_operator('/'))
        widget.bind('<Key-percent>', lambda e: self.input_operator('%'))
        
        # Other keys
        widget.bind('<Key-period>', lambda e: self.input_digit('.'))
        widget.bind('<Key-Return>', lambda e: self.calculate())
        widget.bind('<Key-KP_Enter>', lambda e: self.calculate())
        widget.bind('<Key-Escape>', lambda e: self.clear_all())
        widget.bind('<Key-BackSpace>', lambda e: self.backspace())
        widget.bind('<Key-Delete>', lambda e: self.clear_entry())
    
    def input_digit(self, digit: str):
        """Input a digit"""
        if self.result_displayed:
            self.current_expression = ""
            self.result_displayed = False
        
        if digit == '.' and '.' in self.get_current_number():
            return  # Don't allow multiple decimal points
        
        self.current_expression += digit
        self.update_display()
        self.update_heartbeat()
    
    def input_operator(self, operator: str):
        """Input an operator"""
        if self.current_expression and not self.result_displayed:
            # Check if last character is already an operator
            if self.current_expression[-1] in '+-*/()%**':
                self.current_expression = self.current_expression[:-1]
        
        self.current_expression += operator
        self.result_displayed = False
        self.update_display()
        self.update_heartbeat()
    
    def input_constant(self, constant: str):
        """Input a mathematical constant"""
        value = {'π': str(math.pi), 'e': str(math.e)}[constant]
        
        if self.result_displayed:
            self.current_expression = ""
            self.result_displayed = False
        
        self.current_expression += value
        self.update_display()
        self.update_heartbeat()
    
    def input_last_answer(self):
        """Input the last calculated answer"""
        if self.history:
            last_result = self.history[-1].split(' = ')[-1]
            
            if self.result_displayed:
                self.current_expression = ""
                self.result_displayed = False
            
            self.current_expression += last_result
            self.update_display()
        self.update_heartbeat()
    
    def apply_function(self, function: str):
        """Apply a mathematical function"""
        current_number = self.get_current_number()
        if not current_number:
            return
        
        try:
            value = float(current_number)
            
            if function == 'sin':
                result = math.sin(math.radians(value))
            elif function == 'cos':
                result = math.cos(math.radians(value))
            elif function == 'tan':
                result = math.tan(math.radians(value))
            elif function == 'log':
                result = math.log10(value)
            elif function == 'ln':
                result = math.log(value)
            elif function == 'sqrt':
                result = math.sqrt(value)
            elif function == 'square':
                result = value ** 2
            elif function == 'reciprocal':
                result = 1 / value
            else:
                return
            
            # Replace current number with result
            self.replace_current_number(str(result))
            self.update_display()
            
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            self.show_error(str(e))
        
        self.update_heartbeat()
    
    def calculate(self):
        """Perform calculation"""
        if not self.current_expression:
            return
        
        try:
            # Prepare expression for evaluation
            expression = self.current_expression.replace('**', '^')
            
            # Evaluate the expression
            result = self.safe_eval(self.current_expression)
            
            # Add to history
            history_item = f"{expression} = {result}"
            self.history.append(history_item)
            self.history_listbox.insert(tk.END, history_item)
            self.history_listbox.see(tk.END)
            
            # Update display
            self.display_var.set(str(result))
            self.current_expression = str(result)
            self.result_displayed = True
            
            self.status_var.set("Calculation completed")
            
        except Exception as e:
            self.show_error(str(e))
        
        self.update_heartbeat()
    
    def safe_eval(self, expression: str) -> float:
        """Safely evaluate a mathematical expression"""
        # Replace operators for Python evaluation
        expression = expression.replace('^', '**')
        
        # Allowed functions and constants
        allowed_names = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log10,
            'ln': math.log,
            'sqrt': math.sqrt,
            'pi': math.pi,
            'e': math.e,
        }
        
        # Compile and evaluate
        code = compile(expression, '<string>', 'eval')
        
        # Check for forbidden operations
        for name in code.co_names:
            if name not in allowed_names:
                raise ValueError(f"Unknown function: {name}")
        
        return eval(code, {"__builtins__": {}}, allowed_names)
    
    def get_current_number(self) -> str:
        """Get the current number being entered"""
        if not self.current_expression:
            return ""
        
        # Find the last number in the expression
        numbers = re.findall(r'[\d.]+', self.current_expression)
        return numbers[-1] if numbers else ""
    
    def replace_current_number(self, new_number: str):
        """Replace the current number in the expression"""
        current = self.get_current_number()
        if current:
            self.current_expression = self.current_expression.rsplit(current, 1)[0] + new_number
    
    def toggle_sign(self):
        """Toggle the sign of the current number"""
        current = self.get_current_number()
        if current:
            if current.startswith('-'):
                new_number = current[1:]
            else:
                new_number = '-' + current
            self.replace_current_number(new_number)
            self.update_display()
        self.update_heartbeat()
    
    def backspace(self):
        """Remove last character"""
        if self.current_expression and not self.result_displayed:
            self.current_expression = self.current_expression[:-1]
            self.update_display()
        self.update_heartbeat()
    
    def clear_entry(self):
        """Clear current entry"""
        self.current_expression = ""
        self.display_var.set("0")
        self.expression_var.set("")
        self.result_displayed = True
        self.update_heartbeat()
    
    def clear_all(self):
        """Clear everything"""
        self.clear_entry()
        self.memory = 0.0
        self.update_memory_display()
        self.status_var.set("All cleared")
        self.update_heartbeat()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()
        self.history_listbox.delete(0, tk.END)
        self.status_var.set("History cleared")
        self.update_heartbeat()
    
    def use_history_item(self):
        """Use selected history item"""
        selection = self.history_listbox.curselection()
        if selection:
            item = self.history_listbox.get(selection[0])
            result = item.split(' = ')[-1]
            self.current_expression = result
            self.display_var.set(result)
            self.result_displayed = True
        self.update_heartbeat()
    
    # Memory operations
    def memory_clear(self):
        """Clear memory"""
        self.memory = 0.0
        self.update_memory_display()
        self.status_var.set("Memory cleared")
        self.update_heartbeat()
    
    def memory_recall(self):
        """Recall from memory"""
        if self.result_displayed:
            self.current_expression = ""
            self.result_displayed = False
        
        self.current_expression += str(self.memory)
        self.update_display()
        self.status_var.set("Memory recalled")
        self.update_heartbeat()
    
    def memory_store(self):
        """Store current value in memory"""
        try:
            current = self.display_var.get()
            self.memory = float(current)
            self.update_memory_display()
            self.status_var.set("Value stored in memory")
        except ValueError:
            self.show_error("Invalid value for memory")
        self.update_heartbeat()
    
    def memory_add(self):
        """Add current value to memory"""
        try:
            current = self.display_var.get()
            self.memory += float(current)
            self.update_memory_display()
            self.status_var.set("Value added to memory")
        except ValueError:
            self.show_error("Invalid value for memory operation")
        self.update_heartbeat()
    
    def memory_subtract(self):
        """Subtract current value from memory"""
        try:
            current = self.display_var.get()
            self.memory -= float(current)
            self.update_memory_display()
            self.status_var.set("Value subtracted from memory")
        except ValueError:
            self.show_error("Invalid value for memory operation")
        self.update_heartbeat()
    
    def update_display(self):
        """Update the calculator display"""
        if self.current_expression:
            self.display_var.set(self.current_expression)
            self.expression_var.set(self.current_expression)
        else:
            self.display_var.set("0")
            self.expression_var.set("")
    
    def update_memory_display(self):
        """Update memory display"""
        self.memory_var.set(f"Memory: {self.memory}")
    
    def show_error(self, message: str):
        """Display error message"""
        self.display_var.set("Error")
        self.status_var.set(f"Error: {message}")
        self.current_expression = ""
        self.result_displayed = True
    
    def update_heartbeat(self):
        """Update framework heartbeat"""
        if self.instance:
            self.instance.last_heartbeat = time.time()


# For standalone testing
if __name__ == "__main__":
    import time
    
    root = tk.Tk()
    root.title("Calculator Test")
    root.geometry("500x700")
    
    # Mock instance
    class MockInstance:
        def __init__(self):
            self.last_heartbeat = time.time()
            self.capabilities = type('obj', (object,), {
                'has_menu': True,
                'has_statusbar': True
            })()
    
    instance = MockInstance()
    app = CalculatorApp(root, instance, None)
    
    root.mainloop()
