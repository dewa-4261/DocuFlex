import os
import tempfile
import subprocess
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def is_tesseract_installed():
    """
    Check if Tesseract OCR is installed and available
    
    Returns:
        bool: True if Tesseract is installed, False otherwise
    """
    try:
        # Try to get tesseract version
        result = subprocess.run(['tesseract', '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True,
                               timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False

def check_tesseract():
    """Check if Tesseract is installed and raise an error if not"""
    if not is_tesseract_installed():
        raise RuntimeError(
            "Tesseract OCR is not installed or not in PATH. "
            "Please install Tesseract OCR to use the OCR functionality. "
            "See docs/TESSERACT_INSTALLATION.md for detailed installation instructions."
        )

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using OCR
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    # Check if Tesseract is installed
    check_tesseract()
    
    try:
        # Create a temporary directory for the image files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300, output_folder=temp_dir)
            
            # Extract text from each image
            extracted_text = ""
            for i, image in enumerate(images):
                # Extract text from the image
                page_text = pytesseract.image_to_string(image)
                
                # Add page number and text to the result
                extracted_text += f"\n\n--- Page {i+1} ---\n\n"
                extracted_text += page_text
            
            return extracted_text.strip()
    
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_image(image_path):
    """
    Extract text from an image file using OCR
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Extracted text from the image
    """
    # Check if Tesseract is installed
    check_tesseract()
    
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Extract text from the image
        extracted_text = pytesseract.image_to_string(image)
        
        return extracted_text.strip()
    
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}") 