from PIL import Image
from io import BytesIO
import mimetypes
from pathlib import Path

def analyze_image_content(file_content: bytes, filename: str = None):
    """Extract image metadata from file content"""
    try:
        # Load image from bytes
        image = Image.open(BytesIO(file_content))
        
        # Get resolution (width, height)
        width, height = image.size
        
        # Get color mode
        color_mode = image.mode  # 'RGB', 'RGBA', 'L' (grayscale), 'CMYK', etc.
        
        # Get format/extension
        image_format = image.format  # 'JPEG', 'PNG', 'GIF', etc.
        
        # Extension from filename or format
        if filename:
            extension = Path(filename).suffix.lower()
        else:
            # Map format to extension
            format_to_ext = {
                'JPEG': '.jpg',
                'PNG': '.png', 
                'GIF': '.gif',
                'BMP': '.bmp',
                'WEBP': '.webp'
            }
            extension = format_to_ext.get(image_format, '.unknown')
        
        return {
            'width': width,
            'height': height,
            'color_mode': color_mode,
            'extension': extension,
            'format': image_format,
            'file_size': len(file_content)
        }
        
    except Exception as e:
        # Return defaults if image analysis fails
        return {
            'width': 0,
            'height': 0,
            'color_mode': 'unknown',
            'extension': Path(filename).suffix.lower() if filename else '.unknown',
            'format': 'unknown',
            'file_size': len(file_content)
        }