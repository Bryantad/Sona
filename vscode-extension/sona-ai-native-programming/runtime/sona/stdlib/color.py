"""
color - Color manipulation for Sona stdlib

Provides color utilities:
- rgb/hex: Color conversion
- lighten/darken: Color adjustment
- Color: Color class
"""


class Color:
    """RGB color."""
    
    def __init__(self, r, g, b):
        """
        Initialize color.
        
        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
        
        Example:
            red = color.Color(255, 0, 0)
        """
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
    
    def to_hex(self):
        """
        Convert to hex string.
        
        Returns:
            Hex color string
        
        Example:
            hex_color = red.to_hex()  # "#ff0000"
        """
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def to_rgb(self):
        """
        Convert to RGB tuple.
        
        Returns:
            (r, g, b) tuple
        
        Example:
            rgb = color.to_rgb()  # (255, 0, 0)
        """
        return (self.r, self.g, self.b)
    
    def lighten(self, amount=0.1):
        """
        Lighten color.
        
        Args:
            amount: Lighten amount (0-1)
        
        Returns:
            New Color object
        
        Example:
            lighter = red.lighten(0.2)
        """
        factor = 1 + amount
        return Color(
            int(self.r * factor),
            int(self.g * factor),
            int(self.b * factor)
        )
    
    def darken(self, amount=0.1):
        """
        Darken color.
        
        Args:
            amount: Darken amount (0-1)
        
        Returns:
            New Color object
        
        Example:
            darker = red.darken(0.2)
        """
        factor = 1 - amount
        return Color(
            int(self.r * factor),
            int(self.g * factor),
            int(self.b * factor)
        )
    
    def __str__(self):
        """String representation."""
        return self.to_hex()


def rgb(r, g, b):
    """
    Create color from RGB.
    
    Args:
        r: Red (0-255)
        g: Green (0-255)
        b: Blue (0-255)
    
    Returns:
        Color object
    
    Example:
        red = color.rgb(255, 0, 0)
    """
    return Color(r, g, b)


def hex_to_rgb(hex_color):
    """
    Convert hex to RGB color.
    
    Args:
        hex_color: Hex string (#RRGGBB or RRGGBB)
    
    Returns:
        Color object
    
    Example:
        red = color.hex_to_rgb("#ff0000")
    """
    hex_color = hex_color.lstrip('#')
    return Color(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )


def blend(color1, color2, ratio=0.5):
    """
    Blend two colors.
    
    Args:
        color1: First color
        color2: Second color
        ratio: Blend ratio (0=color1, 1=color2)
    
    Returns:
        Blended Color object
    
    Example:
        purple = color.blend(red, blue, 0.5)
    """
    return Color(
        int(color1.r * (1 - ratio) + color2.r * ratio),
        int(color1.g * (1 - ratio) + color2.g * ratio),
        int(color1.b * (1 - ratio) + color2.b * ratio)
    )


def grayscale(c):
    """
    Convert color to grayscale.
    
    Args:
        c: Color object
    
    Returns:
        Grayscale Color object
    
    Example:
        gray = color.grayscale(red)
    """
    avg = int((c.r + c.g + c.b) / 3)
    return Color(avg, avg, avg)


def invert(c):
    """
    Invert color.
    
    Args:
        c: Color object
    
    Returns:
        Inverted Color object
    
    Example:
        inverted = color.invert(red)  # Cyan
    """
    return Color(255 - c.r, 255 - c.g, 255 - c.b)


def rgb_to_hsl(c):
    """
    Convert RGB color to HSL.
    
    Args:
        c: Color object
    
    Returns:
        (h, s, l) tuple (h: 0-360, s/l: 0-100)
    
    Example:
        hsl = color.rgb_to_hsl(red)  # (0, 100, 50)
    """
    r, g, b = c.r / 255.0, c.g / 255.0, c.b / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2
    
    if max_c == min_c:
        h = s = 0
    else:
        diff = max_c - min_c
        s = diff / (2 - max_c - min_c) if l > 0.5 else diff / (max_c + min_c)
        
        if max_c == r:
            h = ((g - b) / diff + (6 if g < b else 0)) / 6
        elif max_c == g:
            h = ((b - r) / diff + 2) / 6
        else:
            h = ((r - g) / diff + 4) / 6
    
    return (int(h * 360), int(s * 100), int(l * 100))


def hsl_to_rgb(h, s, l):
    """
    Convert HSL to RGB color.
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)
    
    Returns:
        Color object
    
    Example:
        red = color.hsl_to_rgb(0, 100, 50)
    """
    h, s, l = h / 360.0, s / 100.0, l / 100.0
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return Color(int(r * 255), int(g * 255), int(b * 255))


def saturate(c, amount=0.1):
    """
    Increase color saturation.
    
    Args:
        c: Color object
        amount: Saturation increase (0-1)
    
    Returns:
        Saturated Color object
    
    Example:
        saturated = color.saturate(red, 0.2)
    """
    h, s, l = rgb_to_hsl(c)
    s = min(100, s + amount * 100)
    return hsl_to_rgb(h, s, l)


def desaturate(c, amount=0.1):
    """
    Decrease color saturation.
    
    Args:
        c: Color object
        amount: Saturation decrease (0-1)
    
    Returns:
        Desaturated Color object
    
    Example:
        desaturated = color.desaturate(red, 0.2)
    """
    h, s, l = rgb_to_hsl(c)
    s = max(0, s - amount * 100)
    return hsl_to_rgb(h, s, l)


def rotate_hue(c, degrees):
    """
    Rotate color hue.
    
    Args:
        c: Color object
        degrees: Degrees to rotate (0-360)
    
    Returns:
        Rotated Color object
    
    Example:
        rotated = color.rotate_hue(red, 120)  # Green
    """
    h, s, l = rgb_to_hsl(c)
    h = (h + degrees) % 360
    return hsl_to_rgb(h, s, l)


def contrast_ratio(c1, c2):
    """
    Calculate contrast ratio between two colors (WCAG).
    
    Args:
        c1: First Color object
        c2: Second Color object
    
    Returns:
        Contrast ratio (1-21)
    
    Example:
        ratio = color.contrast_ratio(black, white)  # 21
    """
    def luminance(c):
        r, g, b = c.r / 255.0, c.g / 255.0, c.b / 255.0
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    l1 = luminance(c1)
    l2 = luminance(c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_light(c):
    """
    Check if color is light.
    
    Args:
        c: Color object
    
    Returns:
        True if light, False if dark
    
    Example:
        color.is_light(white)  # True
    """
    h, s, l = rgb_to_hsl(c)
    return l > 50


# Common colors
BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)


__all__ = [
    'Color',
    'rgb',
    'hex_to_rgb',
    'blend',
    'grayscale',
    'invert',
    'rgb_to_hsl',
    'hsl_to_rgb',
    'saturate',
    'desaturate',
    'rotate_hue',
    'contrast_ratio',
    'is_light',
    'BLACK',
    'WHITE',
    'RED',
    'GREEN',
    'BLUE',
    'YELLOW',
    'CYAN',
    'MAGENTA',
]
