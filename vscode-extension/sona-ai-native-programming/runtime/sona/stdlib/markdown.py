"""
markdown - Markdown processing for Sona stdlib

Provides Markdown operations:
- to_html: Convert Markdown to HTML
- parse: Parse Markdown structure
"""

import re


def to_html(markdown_text):
    """
    Convert Markdown to HTML.
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        HTML string
    
    Example:
        html = markdown.to_html("# Hello\\n\\nThis is **bold**.")
    """
    html = markdown_text
    
    # Headers
    html = re.sub(r'^######\s+(.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^#####\s+(.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
    
    # Code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    
    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    
    # Images
    html = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<img src="\2" alt="\1">', html)
    
    # Line breaks
    html = re.sub(r'\n\n', '</p><p>', html)
    html = '<p>' + html + '</p>'
    
    return html


def parse(markdown_text):
    """
    Parse Markdown structure.
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        List of elements
    
    Example:
        elements = markdown.parse("# Title\\n\\nParagraph")
    """
    elements = []
    lines = markdown_text.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        # Headers
        if line.startswith('#'):
            level = len(re.match(r'^#+', line).group())
            text = line.lstrip('#').strip()
            elements.append({'type': 'header', 'level': level, 'text': text})
        
        # Code block
        elif line.startswith('```'):
            elements.append({'type': 'code_block', 'lang': line[3:].strip()})
        
        # List item
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:].strip()
            elements.append({'type': 'list_item', 'text': text})
        
        # Paragraph
        else:
            elements.append({'type': 'paragraph', 'text': line})
    
    return elements


def extract_headers(markdown_text):
    """
    Extract all headers from Markdown.
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        List of header dictionaries
    
    Example:
        headers = markdown.extract_headers("# Title\\n## Subtitle")
        # [{'level': 1, 'text': 'Title'}, {'level': 2, 'text': 'Subtitle'}]
    """
    headers = []
    for line in markdown_text.split('\n'):
        if line.startswith('#'):
            level = len(re.match(r'^#+', line).group())
            text = line.lstrip('#').strip()
            headers.append({'level': level, 'text': text})
    return headers


def extract_links(markdown_text):
    """
    Extract all links from Markdown.
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        List of link dictionaries
    
    Example:
        links = markdown.extract_links("[text](url)")
        # [{'text': 'text', 'url': 'url'}]
    """
    pattern = r'\[(.+?)\]\((.+?)\)'
    matches = re.findall(pattern, markdown_text)
    return [{'text': text, 'url': url} for text, url in matches]


def extract_images(markdown_text):
    """
    Extract all images from Markdown.
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        List of image dictionaries
    
    Example:
        images = markdown.extract_images("![alt](src)")
        # [{'alt': 'alt', 'src': 'src'}]
    """
    pattern = r'!\[(.+?)\]\((.+?)\)'
    matches = re.findall(pattern, markdown_text)
    return [{'alt': alt, 'src': src} for alt, src in matches]


def extract_code_blocks(markdown_text):
    """
    Extract code blocks from Markdown.
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        List of code block dictionaries
    
    Example:
        blocks = markdown.extract_code_blocks(md)
        # [{'lang': 'python', 'code': '...'}]
    """
    blocks = []
    lines = markdown_text.split('\n')
    in_block = False
    current_block = {'lang': '', 'code': []}
    
    for line in lines:
        if line.startswith('```'):
            if in_block:
                blocks.append({
                    'lang': current_block['lang'],
                    'code': '\n'.join(current_block['code'])
                })
                current_block = {'lang': '', 'code': []}
                in_block = False
            else:
                current_block['lang'] = line[3:].strip()
                in_block = True
        elif in_block:
            current_block['code'].append(line)
    
    return blocks


def to_plain_text(markdown_text):
    """
    Convert Markdown to plain text (strip formatting).
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        Plain text string
    
    Example:
        text = markdown.to_plain_text("**bold** text")
        # "bold text"
    """
    text = markdown_text
    
    # Remove images
    text = re.sub(r'!\[(.+?)\]\((.+?)\)', r'\1', text)
    
    # Remove links (keep text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1', text)
    
    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove code
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]+?```', '', text)
    
    return text.strip()


def word_count(markdown_text):
    """
    Count words in Markdown (excluding code).
    
    Args:
        markdown_text: Markdown string
    
    Returns:
        Word count
    
    Example:
        count = markdown.word_count("# Title\\n\\nParagraph text")
    """
    text = to_plain_text(markdown_text)
    words = text.split()
    return len(words)


def add_toc(markdown_text, max_level=3):
    """
    Add table of contents to Markdown.
    
    Args:
        markdown_text: Markdown string
        max_level: Maximum header level to include
    
    Returns:
        Markdown with TOC prepended
    
    Example:
        with_toc = markdown.add_toc(md, max_level=2)
    """
    headers = extract_headers(markdown_text)
    toc_lines = ['## Table of Contents\n']
    
    for header in headers:
        if header['level'] <= max_level:
            indent = '  ' * (header['level'] - 1)
            anchor = header['text'].lower().replace(' ', '-')
            toc_lines.append(f"{indent}- [{header['text']}](#{anchor})")
    
    toc = '\n'.join(toc_lines) + '\n\n'
    return toc + markdown_text


def escape(text):
    """
    Escape special Markdown characters.
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text
    
    Example:
        escaped = markdown.escape("*special* chars")
        # "\\*special\\* chars"
    """
    special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text


__all__ = [
    'to_html', 'parse', 'extract_headers', 'extract_links', 'extract_images',
    'extract_code_blocks', 'to_plain_text', 'word_count', 'add_toc', 'escape'
]
