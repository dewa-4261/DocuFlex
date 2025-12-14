#!/usr/bin/env python3
"""
Test script for OCR functionality.
This script will extract text from a sample PDF or image file.
"""

import os
import sys
from utils.ocr_utils import extract_text_from_pdf, extract_text_from_image, is_tesseract_installed

def main():
    """Main function to test OCR functionality"""
    # Check if Tesseract is installed first
    if not is_tesseract_installed():
        print("ERROR: Tesseract OCR is not installed or not in PATH.")
        print("Please install Tesseract OCR to use the OCR functionality.")
        print("See docs/TESSERACT_INSTALLATION.md for detailed installation instructions.")
        return 1

    # Check if a file path was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python test_ocr.py <file_path>")
        print("Supported formats: PDF, JPG, PNG, TIFF")
        return 1

    # Get the file path from the command-line arguments
    file_path = sys.argv[1]

    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        return 1

    # Get the file extension
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    try:
        # Extract text based on the file type
        if file_extension == '.pdf':
            print(f"Processing PDF file: {file_path}")
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']:
            print(f"Processing image file: {file_path}")
            extracted_text = extract_text_from_image(file_path)
        else:
            print(f"Unsupported file format: {file_extension}")
            print("Supported formats: PDF, JPG, PNG, TIFF, BMP")
            return 1

        # Print the extracted text
        print("\nExtracted Text:")
        print("-" * 50)
        print(extracted_text)
        print("-" * 50)
        print("\nText extraction completed successfully!")
        return 0

    except Exception as e:
        print(f"Error during OCR processing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 