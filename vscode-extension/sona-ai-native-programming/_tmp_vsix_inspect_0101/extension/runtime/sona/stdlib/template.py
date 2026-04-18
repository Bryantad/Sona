"""
template - Simple template engine for Sona stdlib

Provides template rendering:
- render: Render template with variables
- Supports {{variable}} syntax
"""

import re


def render(template, context):
    """
    Render template with context variables.
    
    Args:
        template: Template string
        context: Dictionary of variables
    
    Returns:
        Rendered string
    
    Example:
        result = template.render(
            "Hello {{name}}, you have {{count}} messages",
            {"name": "John", "count": 5}
        )
        # "Hello John, you have 5 messages"
    """
    result = template
    
    # Replace {{variable}}
    for key, value in context.items():
        pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
        result = re.sub(pattern, str(value), result)
    
    return result


def render_file(file_path, context):
    """
    Render template from file.
    
    Args:
        file_path: Path to template file
        context: Dictionary of variables
    
    Returns:
        Rendered string
    
    Example:
        result = template.render_file("email.txt", {"name": "John"})
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        template_str = f.read()
    
    return render(template_str, context)


def render_loop(template, items_key, items, context=None):
    """
    Render template with loop.
    
    Args:
        template: Template string with {{#items}}...{{/items}} blocks
        items_key: Key name for loop items
        items: List of items to iterate
        context: Additional context variables
    
    Returns:
        Rendered string
    
    Example:
        result = template.render_loop(
            "Users: {{#users}}- {{name}}\\n{{/users}}",
            "users",
            [{"name": "John"}, {"name": "Jane"}]
        )
    """
    context = context or {}
    
    # Find loop blocks
    pattern = r'\{\{#' + re.escape(items_key) + r'\}\}(.*?)\{\{/' + re.escape(items_key) + r'\}\}'
    
    def replace_loop(match):
        loop_template = match.group(1)
        result = []
        for item in items:
            loop_context = {**context, **item}
            result.append(render(loop_template, loop_context))
        return ''.join(result)
    
    return re.sub(pattern, replace_loop, template, flags=re.DOTALL)


def render_conditional(template, context):
    """
    Render template with conditionals.
    
    Args:
        template: Template with {{#if var}}...{{/if}} blocks
        context: Dictionary of variables
    
    Returns:
        Rendered string
    
    Example:
        result = template.render_conditional(
            "{{#if premium}}Premium user{{/if}}",
            {"premium": True}
        )
    """
    # Find conditional blocks
    pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'
    
    def replace_conditional(match):
        var_name = match.group(1)
        content = match.group(2)
        
        if context.get(var_name):
            return render(content, context)
        return ''
    
    result = re.sub(pattern, replace_conditional, template, flags=re.DOTALL)
    return render(result, context)


def escape_html(text):
    """Escape HTML special characters."""
    import html
    return html.escape(str(text))


def render_safe(template, context):
    """Render template with HTML escaping."""
    escaped_context = {k: escape_html(v) for k, v in context.items()}
    return render(template, escaped_context)


__all__ = [
    'render',
    'render_file',
    'render_loop',
    'render_conditional',
    'escape_html',
    'render_safe',
]
