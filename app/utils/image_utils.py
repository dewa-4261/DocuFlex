import os
from PIL import Image, ImageDraw, ImageFont
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import numpy as np


def convert_image_to_pdf(input_file, output_file):
    """Convert an image to a PDF file

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the PDF file
    """
    # Open the image
    image = Image.open(input_file)
    
    # If the image has an alpha channel, convert it to RGB
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    
    # Create a PDF with the same size as the image
    c = canvas.Canvas(output_file, pagesize=(image.width, image.height))
    
    # Save image to a temporary file
    temp_img = io.BytesIO()
    image.save(temp_img, format='JPEG')
    temp_img.seek(0)
    
    # Add the image to the PDF
    c.drawImage(temp_img, 0, 0, width=image.width, height=image.height)
    c.save()


def remove_background(input_file, output_file):
    """Remove the background from an image.
    This function uses multiple methods to remove the background:
    1. Primary method: rembg library (neural network-based)
    2. Fallback: OpenCV-based segmentation
    3. Last resort: Simple thresholding (original method)

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the output image
    """
    try:
        # Method 1: Use rembg (u2net) - most effective but may be slow
        try:
            import rembg
            
            # Read the input image
            with open(input_file, 'rb') as i:
                input_data = i.read()
            
            # Process the image with rembg
            output_data = rembg.remove(input_data)
            
            # Save the output image
            with open(output_file, 'wb') as o:
                o.write(output_data)
            
            return
        except (ImportError, Exception) as e:
            print(f"rembg method failed: {str(e)}")
            # Continue to next method if this fails
        
        # Method 2: Use OpenCV-based segmentation
        try:
            import cv2
            
            # Read the image
            img = cv2.imread(input_file)
            
            # Convert to RGB for better processing
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Create a mask using GrabCut algorithm
            mask = np.zeros(img.shape[:2], np.uint8)
            bgdModel = np.zeros((1, 65), np.float64)
            fgdModel = np.zeros((1, 65), np.float64)
            
            # Set a rectangle that roughly covers the foreground object
            height, width = img.shape[:2]
            rect = (width//10, height//10, width*8//10, height*8//10)
            
            # Apply GrabCut algorithm
            cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
            
            # Create mask where sure background and probable background are 0, and the rest are 1
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Multiply the image with the mask to get the foreground
            img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            img_rgba[:, :, 3] = mask2 * 255
            
            # Convert back to PIL Image and save
            result = Image.fromarray(cv2.cvtColor(img_rgba, cv2.COLOR_BGRA2RGBA))
            result.save(output_file)
            
            return
        except (ImportError, Exception) as e:
            print(f"OpenCV method failed: {str(e)}")
            # Continue to next method if this fails
        
        # Method 3: Fall back to the original simple method (threshold-based)
        # Open the image
        image = Image.open(input_file)
        
        # If the image doesn't have an alpha channel already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get the data
        data = np.array(image)
        
        # Simple background removal: convert white/light colors to transparent
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        
        # White/light background detection with improved threshold
        # Detect white/light colors and grayish colors that are likely background
        light_mask = (r > 220) & (g > 220) & (b > 220)
        gray_mask = (abs(r - g) < 15) & (abs(g - b) < 15) & (abs(b - r) < 15) & (r > 180) & (g > 180) & (b > 180)
        mask = light_mask | gray_mask
        
        # Set those pixels to transparent
        data[:,:,3] = np.where(mask, 0, 255)
        
        # Create a new image with the modified data
        result = Image.fromarray(data)
        
        # Save the image
        result.save(output_file)
        
    except Exception as e:
        # If all methods fail, just copy the original file
        import shutil
        shutil.copy(input_file, output_file)
        raise Exception(f"All background removal methods failed: {str(e)}")


def compress_image(input_file, output_file, quality=85):
    """Compress an image by reducing its quality

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the compressed image
        quality (int, optional): Compression quality (1-100). Defaults to 85.
    """
    # Open the image
    image = Image.open(input_file)
    
    # Get the format from the output file
    img_format = os.path.splitext(output_file)[1].upper().replace('.', '')
    
    # If the format is not recognized, default to JPEG
    if img_format not in ['JPEG', 'JPG', 'PNG', 'WEBP', 'GIF']:
        img_format = 'JPEG'
    
    # Convert format to one that Pillow recognizes
    if img_format == 'JPG':
        img_format = 'JPEG'
    
    # Handle different image modes based on target format
    if img_format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
        # Create a white background for transparent images
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        else:
            background.paste(image, mask=image.convert('RGBA').split()[3])
        image = background
    elif image.mode == 'P' and img_format != 'GIF':
        # Convert palette images to RGB unless it's a GIF
        image = image.convert('RGB')
    
    # Save with the correct parameters based on format
    if img_format == 'JPEG':
        image.save(output_file, format=img_format, quality=quality, optimize=True)
    elif img_format == 'PNG':
        image.save(output_file, format=img_format, optimize=True)
    elif img_format == 'WEBP':
        image.save(output_file, format=img_format, quality=quality, lossless=False)
    elif img_format == 'GIF':
        image.save(output_file, format=img_format, optimize=True)
    else:
        # Default case
        image.save(output_file)


def add_watermark_to_image(input_file, output_file, watermark_text='WATERMARK', opacity=0.3):
    """Add a text watermark to an image

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the watermarked image
        watermark_text (str, optional): Text for the watermark. Defaults to 'WATERMARK'.
        opacity (float, optional): Opacity of the watermark (0.0 to 1.0). Defaults to 0.3.
    """
    # Open the image
    image = Image.open(input_file)
    
    # Create a transparent overlay for the watermark
    watermark = Image.new('RGBA', image.size, (255, 255, 255, 0))
    
    # Get a drawing context
    draw = ImageDraw.Draw(watermark)
    
    # Get the size of the image
    width, height = image.size
    
    # Calculate the appropriate font size (adjust this as needed)
    font_size = int(min(width, height) / 10)
    
    try:
        # Try to use a default font
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        # If arial is not available, use the default font
        font = ImageFont.load_default()
    
    # Get the text size
    left, top, right, bottom = font.getbbox(watermark_text)
    text_width = right - left
    text_height = bottom - top
    
    # Calculate text position (centered and rotated)
    position = ((width - text_width) / 2, (height - text_height) / 2)
    
    # Set the opacity
    opacity_int = int(255 * opacity)
    
    # Draw the text
    draw.text(position, watermark_text, fill=(0, 0, 0, opacity_int), font=font)
    
    # Apply the watermark
    watermarked = Image.alpha_composite(image.convert('RGBA'), watermark)
    
    # If the original image wasn't RGBA, convert back
    if image.mode != 'RGBA':
        watermarked = watermarked.convert(image.mode)
    
    # Save the image
    watermarked.save(output_file)


def resize_image(input_file, output_file, resize_type='percentage', percentage=100, width=None, height=None, maintain_aspect_ratio=True):
    """Resize an image based on percentage or specific dimensions

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the resized image
        resize_type (str, optional): 'percentage' or 'dimensions'. Defaults to 'percentage'.
        percentage (int, optional): Percentage to scale the image. Defaults to 100.
        width (int, optional): New width in pixels. Defaults to None.
        height (int, optional): New height in pixels. Defaults to None.
        maintain_aspect_ratio (bool, optional): Whether to maintain aspect ratio when resizing by dimensions. Defaults to True.
    """
    # Open the image
    image = Image.open(input_file)
    
    # Get original size
    original_width, original_height = image.size
    
    if resize_type == 'percentage':
        # Calculate new dimensions based on percentage
        new_width = int(original_width * percentage / 100)
        new_height = int(original_height * percentage / 100)
    else:  # dimensions
        if width is not None and height is not None:
            new_width = width
            new_height = height
            
            # Maintain aspect ratio if needed
            if maintain_aspect_ratio:
                aspect_ratio = original_width / original_height
                
                # If width forces a change in height
                if width / height > aspect_ratio:
                    new_width = int(height * aspect_ratio)
                else:
                    new_height = int(width / aspect_ratio)
        elif width is not None:
            # Calculate height to maintain aspect ratio
            aspect_ratio = original_width / original_height
            new_width = width
            new_height = int(width / aspect_ratio)
        elif height is not None:
            # Calculate width to maintain aspect ratio
            aspect_ratio = original_width / original_height
            new_height = height
            new_width = int(height * aspect_ratio)
        else:
            # No dimensions provided, keep original
            new_width, new_height = original_width, original_height
    
    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Save the resized image
    resized_image.save(output_file)


def crop_image(input_file, output_file, x, y, width, height):
    """Crop an image to the specified region

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the cropped image
        x (int): Left coordinate of the crop region
        y (int): Top coordinate of the crop region
        width (int): Width of the crop region
        height (int): Height of the crop region
    """
    # Open the image
    image = Image.open(input_file)
    
    # Calculate the crop box (left, upper, right, lower)
    crop_box = (x, y, x + width, y + height)
    
    # Crop the image
    cropped_image = image.crop(crop_box)
    
    # Save the cropped image
    cropped_image.save(output_file)


def convert_to_jpg(input_file, output_file, quality=90):
    """Convert an image to JPG format

    Args:
        input_file (str): Path to the image file
        output_file (str): Path to save the JPG image
        quality (int, optional): JPG quality (1-100). Defaults to 90.
    """
    # Open the image
    image = Image.open(input_file)
    
    # If the image has an alpha channel, convert to RGB
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        # Create a white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        
        # Paste the image on the background
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        else:
            background.paste(image, mask=image.convert('RGBA').split()[3])
        
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save as JPG
    image.save(output_file, 'JPEG', quality=quality)


def convert_from_jpg(input_file, output_file, format='PNG'):
    """Convert a JPG image to another format

    Args:
        input_file (str): Path to the JPG image file
        output_file (str): Path to save the converted image
        format (str, optional): Target format (PNG, WebP, BMP, TIFF). Defaults to 'PNG'.
    """
    # Open the image
    image = Image.open(input_file)
    
    # Convert format
    format = format.upper()
    
    if format == 'PNG':
        image.save(output_file, 'PNG')
    elif format == 'WEBP':
        image.save(output_file, 'WebP', quality=90)
    elif format == 'BMP':
        image.save(output_file, 'BMP')
    elif format == 'TIFF':
        image.save(output_file, 'TIFF', compression='tiff_deflate')
    else:
        # Default to PNG if format not recognized
        image.save(output_file, 'PNG') 