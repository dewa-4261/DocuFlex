import os
import io
import PyPDF2
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import re


def merge_pdfs(input_files, output_file):
    """Merge multiple PDF files into a single PDF file

    Args:
        input_files (list): List of file paths to PDFs to merge
        output_file (str): Path to save the merged PDF
    """
    pdf_merger = PyPDF2.PdfMerger()
    
    for pdf_file in input_files:
        pdf_merger.append(pdf_file)
    
    with open(output_file, 'wb') as output:
        pdf_merger.write(output)


def split_pdf(input_file, output_dir, page_ranges=''):
    """Split a PDF file into separate PDFs, either by individual pages or by page ranges

    Args:
        input_file (str): Path to the PDF file to split
        output_dir (str): Directory to save the split PDFs
        page_ranges (str, optional): Page ranges in format: "1-3,5-7,9". If empty, splits each page.
    
    Returns:
        list: Paths to the output files
    """
    with open(input_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        
        # Parse page ranges if provided
        ranges = []
        if page_ranges:
            range_parts = page_ranges.split(',')
            for part in range_parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    ranges.append((max(1, start), min(num_pages, end)))
                else:
                    page = int(part)
                    if 1 <= page <= num_pages:
                        ranges.append((page, page))
        else:
            # Split each page individually
            ranges = [(i, i) for i in range(1, num_pages + 1)]
        
        output_files = []
        
        for i, (start, end) in enumerate(ranges):
            pdf_writer = PyPDF2.PdfWriter()
            
            for page_num in range(start - 1, end):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            output_path = os.path.join(output_dir, f'split_{i+1}.pdf')
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            output_files.append(output_path)
        
        return output_files


def convert_pdf_to_images(input_file, output_dir, dpi=200):
    """Convert a PDF file to a set of images (one per page)

    Args:
        input_file (str): Path to the PDF file
        output_dir (str): Directory to save the output images
        dpi (int, optional): DPI for the output images. Defaults to 200.
    
    Returns:
        list: Paths to the output image files
    """
    from pdf2image import convert_from_path
    
    images = convert_from_path(input_file, dpi=dpi)
    output_files = []
    
    for i, image in enumerate(images):
        output_path = os.path.join(output_dir, f'page_{i+1}.png')
        image.save(output_path, 'PNG')
        output_files.append(output_path)
    
    return output_files


def compress_pdf(input_file, output_file, quality='medium'):
    """Compress a PDF file

    Args:
        input_file (str): Path to the PDF file to compress
        output_file (str): Path to save the compressed PDF
        quality (str, optional): Compression quality ('low', 'medium', 'high'). Defaults to 'medium'.
    """
    # Import here to avoid circular imports
    from pdf2image import convert_from_path
    from PIL import Image
    
    # Set DPI based on quality
    quality_settings = {
        'low': 72,
        'medium': 150,
        'high': 300
    }
    dpi = quality_settings.get(quality, 150)
    
    try:
        # Convert PDF to images
        images = convert_from_path(input_file, dpi=dpi)
        
        # Create a new PDF from the images
        pdf_writer = PyPDF2.PdfWriter()
        
        for image in images:
            # Convert PIL image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG', quality=int(dpi * 0.3))
            img_bytes.seek(0)
            
            # Create PDF from image
            temp_pdf = PyPDF2.PdfReader(img_bytes)
            pdf_writer.add_page(temp_pdf.pages[0])
        
        # Save the compressed PDF
        with open(output_file, 'wb') as f:
            pdf_writer.write(f)
    except Exception as e:
        # If there's an error, try a simpler approach
        # Just copy pages without re-encoding
        with open(input_file, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Add all pages from the original PDF
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Write to output file
            with open(output_file, 'wb') as output:
                pdf_writer.write(output)


def add_watermark_to_pdf(input_file, output_file, watermark_text='WATERMARK', opacity=0.3):
    """Add a text watermark to each page of a PDF

    Args:
        input_file (str): Path to the PDF file
        output_file (str): Path to save the watermarked PDF
        watermark_text (str, optional): Text for the watermark. Defaults to 'WATERMARK'.
        opacity (float, optional): Opacity of the watermark (0.0 to 1.0). Defaults to 0.3.
    """
    # Create a watermark PDF
    watermark_pdf = io.BytesIO()
    c = canvas.Canvas(watermark_pdf, pagesize=letter)
    
    # Register a default font
    c.setFont("Helvetica", 60)
    
    # Set transparency
    c.setFillAlpha(opacity)
    
    # Add rotated text
    c.saveState()
    c.translate(letter[0]/2, letter[1]/2)
    c.rotate(45)
    c.setFillColorRGB(0, 0, 0)  # black text
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    
    c.save()
    watermark_pdf.seek(0)
    
    # Read the watermark PDF
    watermark_reader = PyPDF2.PdfReader(watermark_pdf)
    watermark_page = watermark_reader.pages[0]
    
    # Read the original PDF
    with open(input_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Apply watermark to each page
        for page in pdf_reader.pages:
            page.merge_page(watermark_page)
            pdf_writer.add_page(page)
        
        # Write the watermarked PDF
        with open(output_file, 'wb') as output:
            pdf_writer.write(output)


def lock_pdf(input_file, output_file, password):
    """Add password protection to a PDF file

    Args:
        input_file (str): Path to the PDF file
        output_file (str): Path to save the password-protected PDF
        password (str): Password to set for the PDF
    """
    with open(input_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Add all pages from the original PDF
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Encrypt with the provided password
        pdf_writer.encrypt(password)
        
        # Write the encrypted PDF
        with open(output_file, 'wb') as output:
            pdf_writer.write(output)


def unlock_pdf(input_file, output_file, password):
    """Remove password protection from a PDF file

    Args:
        input_file (str): Path to the password-protected PDF file
        output_file (str): Path to save the unlocked PDF
        password (str): Password to unlock the PDF
    """
    with open(input_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Check if PDF is encrypted
        if pdf_reader.is_encrypted:
            # Try to decrypt with the provided password
            pdf_reader.decrypt(password)
            
            # Create a new PDF without encryption
            pdf_writer = PyPDF2.PdfWriter()
            
            # Add all pages from the original PDF
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Write the unencrypted PDF
            with open(output_file, 'wb') as output:
                pdf_writer.write(output)
        else:
            # If not encrypted, just copy the file
            import shutil
            shutil.copyfile(input_file, output_file)


def images_to_pdf(input_files, output_file, page_size='letter'):
    """Convert multiple images to a single PDF file

    Args:
        input_files (list): List of image file paths
        output_file (str): Path to save the PDF
        page_size (str/tuple, optional): Page size for the PDF. Defaults to 'letter'.
    """
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from PIL import Image
    
    # Determine page size
    if isinstance(page_size, str):
        if page_size.lower() == 'letter':
            page_size = letter
        elif page_size.lower() == 'a4':
            page_size = A4
    
    # Create a new PDF
    c = canvas.Canvas(output_file, pagesize=page_size)
    
    # Add each image as a page
    for img_path in input_files:
        img = Image.open(img_path)
        
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        img_width, img_height = img.size
        
        # Calculate scale to fit the image on the page
        page_width, page_height = page_size
        width_ratio = page_width / img_width
        height_ratio = page_height / img_height
        scale_ratio = min(width_ratio, height_ratio)
        
        # Calculate dimensions and position to center the image
        width = img_width * scale_ratio
        height = img_height * scale_ratio
        x = (page_width - width) / 2
        y = (page_height - height) / 2
        
        # Save to temporary file for import (canvas.drawImage has issues with some image formats)
        img_temp = io.BytesIO()
        img.save(img_temp, format='JPEG')
        img_temp.seek(0)
        
        # Add the image to the PDF
        c.drawImage(img_temp, x, y, width=width, height=height)
        
        # Add a new page for the next image
        c.showPage()
    
    # Save the PDF
    c.save()


def word_to_pdf(input_file, output_file):
    """Convert a Word document to PDF
    This is a basic implementation without direct Word-to-PDF conversion.
    In a production environment, you would use libraries like unoconv, 
    LibreOffice/OpenOffice with PyOO, or a commercial service.

    Args:
        input_file (str): Path to the Word document
        output_file (str): Path to save the PDF
    """
    try:
        # Try to use docx2pdf if available
        from docx2pdf import convert
        convert(input_file, output_file)
    except ImportError:
        # Fallback to using python-docx and reportlab
        import docx
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        
        # Extract text from the Word document
        doc = docx.Document(input_file)
        text_content = []
        
        for paragraph in doc.paragraphs:
            text_content.append(paragraph.text)
        
        # Create a PDF with the extracted text
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        styles = getSampleStyleSheet()
        flowables = []
        
        for text in text_content:
            para = Paragraph(text, styles['Normal'])
            flowables.append(para)
        
        doc.build(flowables)


def excel_to_pdf(input_file, output_file):
    """Convert an Excel spreadsheet to PDF
    This is a basic implementation without direct Excel-to-PDF conversion.
    In a production environment, you would use libraries like unoconv, 
    LibreOffice/OpenOffice with PyOO, or a commercial service.

    Args:
        input_file (str): Path to the Excel spreadsheet
        output_file (str): Path to save the PDF
    """
    try:
        # Try to use win32com if on Windows
        import win32com.client
        import os
        
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        workbook = excel.Workbooks.Open(os.path.abspath(input_file))
        workbook.ExportAsFixedFormat(0, os.path.abspath(output_file))  # 0 = PDF format
        workbook.Close()
        excel.Quit()
    except ImportError:
        # Fallback to using pandas and reportlab
        import pandas as pd
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        
        # Read Excel file into pandas DataFrames
        sheets = pd.read_excel(input_file, sheet_name=None)
        
        # Create a PDF
        doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))
        story = []
        
        # Add each sheet as a table in the PDF
        for sheet_name, df in sheets.items():
            # Convert DataFrame to a list of lists for the Table
            data = [df.columns.tolist()] + df.values.tolist()
            
            # Convert all data to strings to ensure it can be rendered
            data = [[str(cell) for cell in row] for row in data]
            
            # Create a Table with the data
            table = Table(data)
            
            # Add style to the table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            table.setStyle(style)
            
            # Add the table to the story
            story.append(Table([[sheet_name]], style=[('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold')]))
            story.append(table)
            story.append(Table([[""]]))  # Add space between sheets
        
        # Build the PDF
        doc.build(story) 