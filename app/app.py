import os
import uuid
import shutil
import traceback
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime, timedelta
from threading import Thread
import time
import PyPDF2
from PIL import Image
import humanize  # For human-readable file sizes
import re
import zipfile
import base64
import io
from deep_translator import GoogleTranslator

# Import utility functions from utils
from utils.pdf_utils import (
    merge_pdfs, split_pdf, convert_pdf_to_images, compress_pdf, add_watermark_to_pdf,
    lock_pdf, unlock_pdf, images_to_pdf, word_to_pdf, excel_to_pdf
)
from utils.image_utils import (
    convert_image_to_pdf, remove_background, compress_image, add_watermark_to_image,
    resize_image, crop_image, convert_to_jpg, convert_from_jpg
)
from utils import (merge_pdfs, split_pdf, convert_pdf_to_images, compress_pdf, add_watermark_to_pdf,
                   convert_image_to_pdf, remove_background, compress_image, add_watermark_to_image,
                   share_document, generate_qr_code, share_document_with_protection, hash_password,
                   generate_share_id, create_protected_url, extract_text_from_pdf, extract_text_from_image)

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {
    'pdf': ['pdf'],
    'image': ['png', 'jpg', 'jpeg', 'gif', 'webp']
}
app.config['TEMP_FILES_LIFETIME'] = 60 * 30  # 30 minutes in seconds
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # For session management

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Storage for protected document information (in a real app, this would be in a database)
protected_documents = {}

def allowed_file(filename, file_type=None):
    """Check if the file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type:
        return ext in app.config['ALLOWED_EXTENSIONS'][file_type]
    else:
        # Check in all allowed extensions
        for extensions in app.config['ALLOWED_EXTENSIONS'].values():
            if ext in extensions:
                return True
        return False

def get_file_type(filename):
    """Get the type of file (pdf or image)"""
    if '.' not in filename:
        return None
    ext = filename.rsplit('.', 1)[1].lower()
    
    for file_type, extensions in app.config['ALLOWED_EXTENSIONS'].items():
        if ext in extensions:
            return file_type
    return None

def get_file_info(file_path):
    """Get file information for preview page"""
    file_info = {}
    
    # Basic file info
    file_size = os.path.getsize(file_path)
    file_info['file_size'] = humanize.naturalsize(file_size)
    
    # Creation time
    created_time = datetime.fromtimestamp(os.path.getctime(file_path))
    file_info['created_time'] = created_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # File type specific info
    filename = os.path.basename(file_path)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext == 'pdf':
        file_info['file_type'] = 'pdf'
        # Get PDF page count
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                file_info['page_count'] = len(pdf_reader.pages)
        except:
            file_info['page_count'] = None
    elif ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        file_info['file_type'] = 'image'
        # Get image dimensions
        try:
            with Image.open(file_path) as img:
                file_info['dimensions'] = f"{img.width} × {img.height} px"
        except:
            file_info['dimensions'] = None
    elif ext == 'zip':
        file_info['file_type'] = 'zip'
    else:
        file_info['file_type'] = 'other'
    
    return file_info

def cleanup_old_files():
    """Background thread to clean up old files"""
    while True:
        now = datetime.now()
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_modified > timedelta(seconds=app.config['TEMP_FILES_LIFETIME']):
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    app.logger.error(f"Error cleaning up file {filepath}: {e}")
        time.sleep(300)  # Check every 5 minutes

# Start the cleanup thread
cleanup_thread = Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and detect file type"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Generate a unique filename to prevent overwriting
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        file_type = get_file_type(filename)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'original_filename': filename,
            'file_type': file_type,
            'file_path': file_path
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/preview/<path:filename>')
def preview_file(filename):
    """Show file preview page"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return redirect(url_for('home'))
    
    # Special handling for QR code images - serve directly
    if filename.startswith('qr_') and filename.endswith('.png'):
        return send_file(file_path, mimetype='image/png')
        
    # Get the file info
    file_info = get_file_info(file_path)
    
    # Calculate a relative path for download URL
    download_url = url_for('download_file', filename=filename)
    
    # Use the original filename (without UUID) for display
    original_filename = '_'.join(filename.split('_')[1:]) if '_' in filename else filename
    
    return render_template('preview.html', 
                          original_filename=original_filename,
                          download_url=download_url,
                          file_size=file_info['file_size'],
                          created_time=file_info['created_time'],
                          file_type=file_info['file_type'],
                          page_count=file_info.get('page_count'),
                          dimensions=file_info.get('dimensions'))

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a processed file"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return redirect(url_for('home'))
    
    # Use the original filename (without UUID) for download
    download_name = '_'.join(filename.split('_')[1:]) if '_' in filename else filename
    
    return send_file(file_path, as_attachment=True, download_name=download_name)

# PDF processing routes

@app.route('/pdf/merge', methods=['POST'])
def merge_pdf_files():
    """Merge multiple PDF files"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files or len(files) < 2:
        return jsonify({'error': 'At least two PDF files are required for merging'}), 400
    
    temp_files = []
    
    # Save all uploaded PDF files
    for file in files:
        if file and allowed_file(file.filename, 'pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            file.save(file_path)
            temp_files.append(file_path)
        else:
            # Clean up any saved files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return jsonify({'error': 'All files must be PDF files'}), 400
    
    try:
        # Create output filename with UUID
        output_filename = f"merged_{uuid.uuid4()}.pdf"
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        merge_pdfs(temp_files, output_file)
        
        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Redirect to preview page
        return redirect(url_for('preview_file', filename=output_filename))
    
    except Exception as e:
        # Clean up any saved files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if os.path.exists(output_file):
            os.remove(output_file)
        
        return jsonify({'error': str(e)}), 500

@app.route('/pdf/split', methods=['POST'])
def split_pdf_file():
    """Split a PDF file into separate pages"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Get page ranges (optional)
            page_ranges = request.form.get('page_ranges', '')
            
            # Create output directory and file names with UUID
            output_dir_name = f"split_{uuid.uuid4()}"
            output_dir = os.path.join(app.config['UPLOAD_FOLDER'], output_dir_name)
            os.makedirs(output_dir, exist_ok=True)
            
            output_files = split_pdf(file_path, output_dir, page_ranges)
            
            # Create a zip file with a UUID filename
            zip_filename = f"split_{uuid.uuid4()}.zip"
            zip_path_without_ext = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename[:-4])
            shutil.make_archive(zip_path_without_ext, 'zip', output_dir)
            
            # Clean up
            os.remove(file_path)
            shutil.rmtree(output_dir)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=zip_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

@app.route('/pdf/to-images', methods=['POST'])
def convert_pdf_to_images_route():
    """Convert a PDF file to images"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            dpi = int(request.form.get('dpi', 200))
            
            # Create output directory and file names with UUID
            output_dir_name = f"pdf_images_{uuid.uuid4()}"
            output_dir = os.path.join(app.config['UPLOAD_FOLDER'], output_dir_name)
            os.makedirs(output_dir, exist_ok=True)
            
            convert_pdf_to_images(file_path, output_dir, dpi)
            
            # Create a zip file with a UUID filename
            zip_filename = f"pdf_images_{uuid.uuid4()}.zip"
            zip_path_without_ext = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename[:-4])
            shutil.make_archive(zip_path_without_ext, 'zip', output_dir)
            
            # Clean up
            os.remove(file_path)
            shutil.rmtree(output_dir)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=zip_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

@app.route('/pdf/compress', methods=['POST'])
def compress_pdf_route():
    """Compress a PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            quality = request.form.get('quality', 'medium')
            
            # Create output filename with UUID
            output_filename = f"compressed_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            compress_pdf(file_path, output_file, quality)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

@app.route('/pdf/watermark', methods=['POST'])
def add_watermark_to_pdf_route():
    """Add a watermark to a PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            watermark_text = request.form.get('watermark_text', 'WATERMARK')
            opacity = float(request.form.get('opacity', 0.3))
            
            # Create output filename with UUID
            output_filename = f"watermarked_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            add_watermark_to_pdf(file_path, output_file, watermark_text, opacity)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

# Image processing routes

@app.route('/image/to-pdf', methods=['POST'])
def convert_image_to_pdf_route():
    """Convert an image to a PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Create output filename with UUID
            output_filename = f"image_to_pdf_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            convert_image_to_pdf(file_path, output_file)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/image/remove-background', methods=['POST'])
def remove_background_route():
    """Remove the background from an image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Create output filename with UUID
            base_name, ext = os.path.splitext(filename)
            output_filename = f"nobg_{uuid.uuid4()}{ext}"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            remove_background(file_path, output_file)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/image/compress', methods=['POST'])
def compress_image_route():
    """Compress an image file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            quality = int(request.form.get('quality', 85))
            
            # Create output filename with UUID
            base_name, ext = os.path.splitext(filename)
            output_filename = f"compressed_{uuid.uuid4()}{ext}"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            compress_image(file_path, output_file, quality)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            error_details = traceback.format_exc()
            app.logger.error(f"Error compressing image: {e}\n{error_details}")
            return jsonify({'error': str(e), 'details': error_details}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/image/watermark', methods=['POST'])
def add_watermark_to_image_route():
    """Add a watermark to an image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            watermark_text = request.form.get('watermark_text', 'WATERMARK')
            opacity = float(request.form.get('opacity', 0.3))
            
            # Create output filename with UUID
            base_name, ext = os.path.splitext(filename)
            output_filename = f"watermarked_{uuid.uuid4()}{ext}"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            add_watermark_to_image(file_path, output_file, watermark_text, opacity)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/pdf/word-to-pdf', methods=['POST'])
def word_to_pdf_route():
    """Convert a Word document to PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and file.filename.lower().endswith(('.doc', '.docx')):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Create output filename with UUID
            output_filename = f"word_to_pdf_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            word_to_pdf(file_path, output_file)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a Word document (.doc or .docx)'}), 400

@app.route('/pdf/excel-to-pdf', methods=['POST'])
def excel_to_pdf_route():
    """Convert an Excel spreadsheet to PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and file.filename.lower().endswith(('.xls', '.xlsx')):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Create output filename with UUID
            output_filename = f"excel_to_pdf_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            excel_to_pdf(file_path, output_file)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an Excel spreadsheet (.xls or .xlsx)'}), 400

@app.route('/pdf/images-to-pdf', methods=['POST'])
def images_to_pdf_route():
    """Convert multiple images to a single PDF file"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    temp_files = []
    
    # Save all uploaded image files
    for file in files:
        if file and allowed_file(file.filename, 'image'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            file.save(file_path)
            temp_files.append(file_path)
        else:
            # Clean up any saved files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return jsonify({'error': 'All files must be images'}), 400
    
    try:
        # Create output filename with UUID
        output_filename = f"images_to_pdf_{uuid.uuid4()}.pdf"
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        images_to_pdf(temp_files, output_file)
        
        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Redirect to preview page
        return redirect(url_for('preview_file', filename=output_filename))
    
    except Exception as e:
        # Clean up any saved files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if os.path.exists(output_file):
            os.remove(output_file)
        
        return jsonify({'error': str(e)}), 500

@app.route('/pdf/unlock', methods=['POST'])
def unlock_pdf_route():
    """Remove password protection from a PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    if file and allowed_file(file.filename, 'pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Create output filename with UUID
            output_filename = f"unlocked_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            unlock_pdf(file_path, output_file, password)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

@app.route('/pdf/lock', methods=['POST'])
def lock_pdf_route():
    """Add password protection to a PDF file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if file and allowed_file(file.filename, 'pdf'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Create output filename with UUID
            output_filename = f"locked_{uuid.uuid4()}.pdf"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            lock_pdf(file_path, output_file, password)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

@app.route('/image/resize', methods=['POST'])
def resize_image_route():
    """Resize an image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            resize_type = request.form.get('resize_type', 'percentage')
            
            # Create output filename with UUID
            base_name, ext = os.path.splitext(filename)
            output_filename = f"resized_{uuid.uuid4()}{ext}"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            if resize_type == 'percentage':
                percentage = int(request.form.get('percentage', 100))
                resize_image(file_path, output_file, resize_type='percentage', percentage=percentage)
            else:  # dimensions
                width = request.form.get('width')
                height = request.form.get('height')
                maintain_aspect_ratio = 'maintain_aspect_ratio' in request.form
                
                # Convert to integers if provided
                width = int(width) if width else None
                height = int(height) if height else None
                
                resize_image(file_path, output_file, resize_type='dimensions', 
                             width=width, height=height, 
                             maintain_aspect_ratio=maintain_aspect_ratio)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/image/crop', methods=['POST'])
def crop_image_route():
    """Crop an image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Get crop coordinates and dimensions
            x = int(request.form.get('x', 0))
            y = int(request.form.get('y', 0))
            width = int(request.form.get('crop_width', 0))
            height = int(request.form.get('crop_height', 0))
            
            # Create output filename with UUID
            base_name, ext = os.path.splitext(filename)
            output_filename = f"cropped_{uuid.uuid4()}{ext}"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            crop_image(file_path, output_file, x, y, width, height)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/image/to-jpg', methods=['POST'])
def convert_to_jpg_route():
    """Convert an image to JPG format"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and allowed_file(file.filename, 'image'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            quality = int(request.form.get('quality', 90))
            
            # Create output filename with UUID
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_{uuid.uuid4()}.jpg"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            convert_to_jpg(file_path, output_file, quality)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be an image'}), 400

@app.route('/image/from-jpg', methods=['POST'])
def convert_from_jpg_route():
    """Convert a JPG image to another format"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and file.filename.lower().endswith(('.jpg', '.jpeg')):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            format = request.form.get('format', 'png').lower()
            
            # Create output filename with UUID
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_{uuid.uuid4()}.{format}"
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            convert_from_jpg(file_path, output_file, format)
            
            # Clean up
            os.remove(file_path)
            
            # Redirect to preview page
            return redirect(url_for('preview_file', filename=output_filename))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a JPG image'}), 400

@app.route('/image/batch-process', methods=['POST'])
def batch_process_images():
    """Process multiple images at once"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    temp_files = []
    output_files = []
    
    # Save all uploaded image files
    for file in files:
        if file and allowed_file(file.filename, 'image'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            file.save(file_path)
            temp_files.append((file_path, filename))
        else:
            # Clean up any saved files
            for temp_file, _ in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return jsonify({'error': 'All files must be images'}), 400
    
    try:
        process_type = request.form.get('process_type', 'compress')
        
        # Create output directory for processed files
        output_dir_name = f"batch_{process_type}_{uuid.uuid4()}"
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        
        for file_path, orig_filename in temp_files:
            base_name, ext = os.path.splitext(orig_filename)
            
            if process_type == 'compress':
                quality = int(request.form.get('quality', 85))
                output_filename = f"{base_name}_compressed{ext}"
                output_file = os.path.join(output_dir, output_filename)
                compress_image(file_path, output_file, quality)
                output_files.append(output_file)
            
            elif process_type == 'resize':
                percentage = int(request.form.get('percentage', 50))
                output_filename = f"{base_name}_resized{ext}"
                output_file = os.path.join(output_dir, output_filename)
                resize_image(file_path, output_file, 'percentage', percentage)
                output_files.append(output_file)
            
            elif process_type == 'to_jpg':
                quality = int(request.form.get('quality', 90))
                output_filename = f"{base_name}.jpg"
                output_file = os.path.join(output_dir, output_filename)
                convert_to_jpg(file_path, output_file, quality)
                output_files.append(output_file)
            
            elif process_type == 'to_png':
                output_filename = f"{base_name}.png"
                output_file = os.path.join(output_dir, output_filename)
                # Open and save as PNG
                image = Image.open(file_path)
                image.save(output_file, 'PNG')
                output_files.append(output_file)
            
            elif process_type == 'to_webp':
                quality = int(request.form.get('quality', 80))
                output_filename = f"{base_name}.webp"
                output_file = os.path.join(output_dir, output_filename)
                # Open and save as WebP
                image = Image.open(file_path)
                image.save(output_file, 'WebP', quality=quality)
                output_files.append(output_file)
        
        # Create a zip file with all processed images
        zip_filename = f"batch_{process_type}_{uuid.uuid4()}.zip"
        zip_path_without_ext = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename[:-4])
        shutil.make_archive(zip_path_without_ext, 'zip', output_dir)
        
        # Clean up
        for temp_file, _ in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        shutil.rmtree(output_dir)
        
        # Redirect to preview page
        return redirect(url_for('preview_file', filename=zip_filename))
        
    except Exception as e:
        # Clean up any saved files
        for temp_file, _ in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        error_details = traceback.format_exc()
        app.logger.error(f"Error in batch processing: {e}\n{error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500
    
    return jsonify({'error': 'Invalid processing type'}), 400

@app.route('/document/share', methods=['POST'])
def share_document_route():
    """Share a document via Filebin.net and generate a QR code"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Generate QR code filename
            qr_filename = f"qr_{uuid.uuid4()}.png"
            qr_file_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
            
            app.logger.info(f"Sharing document: {filename}")
            app.logger.info(f"Original file path: {file_path}")
            app.logger.info(f"QR code will be saved to: {qr_file_path}")
            
            # Share document and get link
            file_url, qr_path = share_document(file_path, qr_file_path)
            
            app.logger.info(f"Document shared successfully. URL: {file_url}")
            app.logger.info(f"QR code generated at: {qr_path}")
            app.logger.info(f"QR file exists: {os.path.exists(qr_file_path)}")
            
            # Clean up the original file
            os.remove(file_path)
            
            # Return the preview page with both the QR code and the link
            return render_template('share_preview.html', 
                                   qr_filename=qr_filename, 
                                   file_url=file_url,
                                   original_filename=filename)
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            error_details = traceback.format_exc()
            app.logger.error(f"Error sharing document: {e}")
            app.logger.error(error_details)
            return jsonify({'error': str(e), 'details': error_details}), 500
    
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/qrcode/<path:filename>')
def get_qrcode(filename):
    """Serve QR code images directly"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'QR code image not found'}), 404
        
    return send_file(file_path, mimetype='image/png')

@app.route('/document/protected-share', methods=['POST'])
def protected_share_document_route():
    """Share a document with password protection (globally accessible)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    password = request.form.get('password')
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    file = request.files['file']
    
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Generate QR code filename
            qr_filename = f"qr_{uuid.uuid4()}.png"
            qr_file_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
            
            app.logger.info(f"Sharing protected document: {filename}")
            app.logger.info(f"Original file path: {file_path}")
            app.logger.info(f"QR code will be saved to: {qr_file_path}")
            
            # Get server URL from request
            base_url = request.url_root.rstrip('/')
            
            # Share document with protection - this now returns a fully accessible protected URL
            protected_url, share_id, direct_file_url, qr_path = share_document_with_protection(
                file_path, qr_file_path, password, base_url
            )
            
            # Convert the relative protected URL to an absolute URL
            full_protected_url = base_url + protected_url
            
            app.logger.info(f"Document shared successfully. Protected URL: {full_protected_url}")
            app.logger.info(f"Share ID: {share_id}")
            app.logger.info(f"Direct file URL: {direct_file_url}")
            app.logger.info(f"QR code generated at: {qr_path}")
            app.logger.info(f"QR file exists: {os.path.exists(qr_file_path)}")
            
            # Clean up the original file
            os.remove(file_path)
            
            # Calculate expiry time (6 months from now)
            expiry_time = (datetime.now() + timedelta(days=180)).strftime("%B %d, %Y")
            
            # Return the preview page with the QR code and protected access information
            return render_template('protected_share_preview.html', 
                                  qr_filename=qr_filename,
                                  qr_code_path=url_for('get_qrcode', filename=qr_filename),
                                  file_url=full_protected_url,
                                  share_link=full_protected_url,
                                  password=password,
                                  original_filename=filename,
                                  filename=filename,
                                  expiry_time=expiry_time)
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            error_details = traceback.format_exc()
            app.logger.error(f"Error sharing protected document: {e}")
            app.logger.error(error_details)
            return jsonify({'error': str(e), 'details': error_details}), 500
    
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/protected/<string:share_id>', methods=['GET', 'POST'])
def access_protected_document(share_id):
    """Access a password-protected shared document"""
    # Check if share ID exists
    if share_id not in protected_documents:
        return redirect(url_for('home'))
    
    document_info = protected_documents[share_id]
    
    # Check if it's a POST request (password submission)
    if request.method == 'POST':
        submitted_password = request.form.get('password')
        
        # Verify password
        if submitted_password == document_info['password']:
            # Password correct, redirect to the actual file
            return redirect(document_info['file_url'])
        else:
            # Password incorrect, show error
            return render_template('protected_access.html',
                                  filename=document_info['filename'],
                                  share_id=share_id,
                                  error='Incorrect password. Please try again.')
    
    # It's a GET request, show password entry form
    return render_template('protected_access.html',
                          filename=document_info['filename'],
                          share_id=share_id)

@app.route('/test-protected-access')
def test_protected_access():
    """Route to test the protected access functionality"""
    return redirect(url_for('static', filename='test-protected-access.html'))

@app.route('/document/ocr', methods=['POST'])
def ocr_document_route():
    """Extract text from a document using OCR"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            app.logger.info(f"Processing OCR for file: {filename}")
            
            # Extract text based on file type
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext == '.pdf':
                extracted_text = extract_text_from_pdf(file_path)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                extracted_text = extract_text_from_image(file_path)
            else:
                raise Exception(f"Unsupported file format for OCR: {file_ext}")
            
            # Save extracted text to a file
            text_filename = f"ocr_{uuid.uuid4()}.txt"
            text_file_path = os.path.join(app.config['UPLOAD_FOLDER'], text_filename)
            
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
                
            app.logger.info(f"OCR processing complete. Text saved to: {text_file_path}")
            
            # Clean up the original file
            os.remove(file_path)
            
            # Return the results page
            return render_template('ocr_result.html',
                                   original_filename=filename,
                                   extracted_text=extracted_text,
                                   text_filename=text_filename)
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            error_details = traceback.format_exc()
            app.logger.error(f"Error processing OCR: {e}")
            app.logger.error(error_details)
            return jsonify({'error': str(e), 'details': error_details}), 500
    
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/download/text/<path:filename>')
def download_text(filename):
    """Download a text file containing extracted text"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return redirect(url_for('home'))
    
    # Use the original filename (without UUID) for download
    download_name = f"ocr_extracted_text_{datetime.now().strftime('%Y%m%d')}.txt"
    
    return send_file(file_path, as_attachment=True, download_name=download_name)

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech_api():
    """Generate speech from text (API endpoint)"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request, JSON expected'}), 400
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # In a real implementation, you would use a text-to-speech service
    # This is a stub that returns a success message
    return jsonify({
        'success': True,
        'message': 'Text-to-speech request processed. This is a placeholder API endpoint.'
    })

@app.route('/api/translate', methods=['POST'])
def translate_text_api():
    """Translate text (API endpoint)"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request, JSON expected'}), 400
    
    data = request.get_json()
    text = data.get('text', '')
    target_language = data.get('target_language', 'en')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Use GoogleTranslator from deep-translator library for translation
        translator = GoogleTranslator(source='auto', target=target_language)
        
        # Limit text length if too long
        max_length = 5000  # Google Translate has a limit on text length
        if len(text) > max_length:
            text = text[:max_length] + "..."
            truncated = True
        else:
            truncated = False
        
        # Perform translation
        translated_text = translator.translate(text)
        
        # Add note if text was truncated
        if truncated:
            translated_text += "\n\n[Note: Original text was truncated due to length limitations]"
        
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'target_language': target_language
        })
    except Exception as e:
        app.logger.error(f"Translation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Translation error: {str(e)}"
        }), 500

# Documentation routes
@app.route('/documentation')
def documentation():
    """Render the documentation page"""
    return render_template('documentation.html')

@app.route('/documentation/tesseract-guide')
def tesseract_guide():
    """Render the Tesseract OCR installation guide"""
    return render_template('tesseract_guide.html')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting the application: {e}")
        print(traceback.format_exc()) 


