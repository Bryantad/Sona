"""
xml - XML parsing and generation for Sona stdlib

Provides XML operations:
- parse: Parse XML string/file
- build: Build XML from dictionary
- to_string: Convert XML to string
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def parse(source):
    """
    Parse XML from string or file.
    
    Args:
        source: XML string or file path
    
    Returns:
        Dictionary representation
    
    Example:
        data = xml.parse("<root><item>value</item></root>")
        # {'root': {'item': 'value'}}
    """
    try:
        if source.startswith('<'):
            # Parse from string
            root = ET.fromstring(source)
        else:
            # Parse from file
            tree = ET.parse(source)
            root = tree.getroot()
        
        return _element_to_dict(root)
    except Exception as e:
        raise RuntimeError(f"XML parsing failed: {e}")


def _element_to_dict(element):
    """Convert XML element to dictionary."""
    result = {}
    
    # Add attributes
    if element.attrib:
        result['@attributes'] = dict(element.attrib)
    
    # Add text content
    if element.text and element.text.strip():
        if len(element) == 0:  # No children
            return element.text.strip()
        result['@text'] = element.text.strip()
    
    # Add children
    for child in element:
        child_data = _element_to_dict(child)
        
        if child.tag in result:
            # Multiple children with same tag
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data
    
    return {element.tag: result} if result else {element.tag: element.text}


def build(data, root_name='root'):
    """
    Build XML from dictionary.
    
    Args:
        data: Dictionary to convert
        root_name: Root element name
    
    Returns:
        XML string
    
    Example:
        xml_str = xml.build({'item': 'value', 'count': 5}, 'root')
        # <?xml version="1.0"?><root><item>value</item><count>5</count></root>
    """
    root = ET.Element(root_name)
    _dict_to_element(root, data)
    
    # Convert to string with pretty printing
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def _dict_to_element(parent, data):
    """Convert dictionary to XML elements."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == '@attributes':
                # Set attributes on parent
                parent.attrib.update(value)
            elif key == '@text':
                # Set text on parent
                parent.text = str(value)
            else:
                # Create child element
                if isinstance(value, list):
                    for item in value:
                        child = ET.SubElement(parent, key)
                        _dict_to_element(child, item)
                else:
                    child = ET.SubElement(parent, key)
                    _dict_to_element(child, value)
    else:
        # Leaf value
        parent.text = str(data)


def to_string(element):
    """
    Convert XML element to string.
    
    Args:
        element: XML element
    
    Returns:
        XML string
    
    Example:
        xml_str = xml.to_string(root_element)
    """
    return ET.tostring(element, encoding='unicode')


def find(element, path):
    """
    Find elements by XPath.
    
    Args:
        element: XML element to search
        path: XPath expression
    
    Returns:
        List of matching elements
    
    Example:
        items = xml.find(root, ".//item[@type='important']")
    """
    if isinstance(element, str):
        element = ET.fromstring(element)
    
    return element.findall(path)


def find_one(element, path):
    """
    Find first matching element by XPath.
    
    Args:
        element: XML element to search
        path: XPath expression
    
    Returns:
        First matching element or None
    
    Example:
        item = xml.find_one(root, ".//item")
    """
    if isinstance(element, str):
        element = ET.fromstring(element)
    
    return element.find(path)


def get_text(element, path, default=''):
    """
    Get text content from element by XPath.
    
    Args:
        element: XML element
        path: XPath expression
        default: Default value if not found
    
    Returns:
        Text content or default
    
    Example:
        name = xml.get_text(root, ".//name", "Unknown")
    """
    if isinstance(element, str):
        element = ET.fromstring(element)
    
    found = element.find(path)
    return found.text if found is not None and found.text else default


def get_attr(element, path, attr, default=None):
    """
    Get attribute value from element by XPath.
    
    Args:
        element: XML element
        path: XPath expression
        attr: Attribute name
        default: Default value if not found
    
    Returns:
        Attribute value or default
    
    Example:
        id_val = xml.get_attr(root, ".//item", "id", 0)
    """
    if isinstance(element, str):
        element = ET.fromstring(element)
    
    found = element.find(path)
    return found.get(attr, default) if found is not None else default


def validate(xml_string, schema=None):
    """
    Validate XML string.
    
    Args:
        xml_string: XML string to validate
        schema: XML schema (optional)
    
    Returns:
        True if valid, False otherwise
    
    Example:
        is_valid = xml.validate("<root><item/></root>")
    """
    try:
        ET.fromstring(xml_string)
        return True
    except Exception:
        return False


def prettify(xml_string):
    """
    Pretty-print XML string.
    
    Args:
        xml_string: XML string
    
    Returns:
        Formatted XML string
    
    Example:
        pretty = xml.prettify("<root><item/></root>")
    """
    try:
        dom = minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ")
    except Exception as e:
        raise RuntimeError(f"XML prettify failed: {e}")


def to_dict(xml_string):
    """
    Convert XML string to dictionary (alias for parse).
    
    Args:
        xml_string: XML string
    
    Returns:
        Dictionary representation
    
    Example:
        data = xml.to_dict("<root><item>value</item></root>")
    """
    return parse(xml_string)


__all__ = [
    'parse', 'build', 'to_string', 'find', 'find_one',
    'get_text', 'get_attr', 'validate', 'prettify', 'to_dict'
]
