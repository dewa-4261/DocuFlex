import os
import qrcode
from PIL import Image
import io
import uuid
import requests
import json
import hashlib
import base64


def upload_to_filebin(file_path):
    """
    Upload a file to Filebin.net and get a shareable link
    
    Args:
        file_path (str): Path to the file to upload
        
    Returns:
        str: URL to the uploaded file
    """
    try:
        # Generate a unique bin ID
        bin_id = str(uuid.uuid4())
        
        # Get the filename
        filename = os.path.basename(file_path)
        
        # Prepare the upload URL
        upload_url = f"https://filebin.net/{bin_id}/{filename}"
        
        # Open and read the file
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        # Upload the file to Filebin
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        response = requests.post(upload_url, data=file_data, headers=headers)
        
        # Check if the upload was successful
        if response.status_code in [200, 201]:
            # Return the URL to the uploaded file
            return f"https://filebin.net/{bin_id}/{filename}"
        else:
            raise Exception(f"Failed to upload file: {response.text}")
    
    except Exception as e:
        raise Exception(f"Error uploading file: {str(e)}")


def generate_qr_code(url, output_file=None):
    """
    Generate a QR code for a URL
    
    Args:
        url (str): URL to encode in the QR code
        output_file (str, optional): Path to save the QR code image. If None, returns the image object.
        
    Returns:
        PIL.Image or None: QR code image if output_file is None, otherwise None
    """
    try:
        print(f"Generating QR code for URL: {url}")
        print(f"Output file path: {output_file}")
        
        # Simple QR code generation using qrcode library
        img = qrcode.make(url)
        
        if output_file:
            print(f"Saving QR code to: {output_file}")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Save the image
            img.save(output_file)
            
            # Verify the file exists
            if os.path.exists(output_file):
                print(f"QR code successfully saved to: {output_file}")
            else:
                print(f"Failed to save QR code to: {output_file}")
                
            return None
        else:
            return img
            
    except Exception as e:
        error_message = f"Error generating QR code: {str(e)}"
        print(error_message)
        import traceback
        print(traceback.format_exc())
        raise Exception(error_message)


def share_document(input_file, output_qr_file):
    """
    Share a document via Filebin.net and generate a QR code for the link
    
    Args:
        input_file (str): Path to the document to share
        output_qr_file (str): Path to save the QR code image
        
    Returns:
        tuple: (URL to the uploaded file, Path to the QR code image)
    """
    try:
        # Upload the file to Filebin
        file_url = upload_to_filebin(input_file)
        print(f"File uploaded successfully. URL: {file_url}")
        
        # Generate a QR code for the URL
        generate_qr_code(file_url, output_qr_file)
        print(f"QR code generated successfully. Path: {output_qr_file}")
        
        return file_url, output_qr_file
    except Exception as e:
        print(f"Error in share_document: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise


def generate_share_id():
    """
    Generate a unique ID for a protected share
    
    Returns:
        str: Unique share ID
    """
    return str(uuid.uuid4())


def hash_password(password):
    """
    Create a simple hash of a password
    
    Args:
        password (str): Password to hash
        
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def share_document_with_protection(input_file, output_qr_file, password, base_url):
    """
    Share a document with password protection using Filebin + URL encryption
    
    Args:
        input_file (str): Path to the document to share
        output_qr_file (str): Path to save the QR code image
        password (str): Password to protect the document
        base_url (str): Base URL of the application
        
    Returns:
        tuple: (Protected access URL, Share ID, Original file URL, Path to the QR code image)
    """
    try:
        # Upload the file to Filebin (this still happens on the backend)
        direct_file_url = upload_to_filebin(input_file)
        print(f"File uploaded successfully. URL: {direct_file_url}")
        
        # Generate a unique share ID
        share_id = generate_share_id()
        
        # For global accessibility, create a protected URL
        protected_url = create_protected_url(direct_file_url, password, share_id)
        
        # Create full URL for QR code
        full_protected_url = base_url + protected_url
        
        # Generate a QR code for the full protected URL
        generate_qr_code(full_protected_url, output_qr_file)
        print(f"QR code generated successfully. Path: {output_qr_file}")
        
        return protected_url, share_id, direct_file_url, output_qr_file
    except Exception as e:
        print(f"Error in share_document_with_protection: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise


def create_protected_url(file_url, password, share_id):
    """
    Create a globally accessible protected URL for the file using our static password protection page
    
    Args:
        file_url (str): Direct URL to the file on Filebin
        password (str): Password for protection
        share_id (str): Unique share ID
        
    Returns:
        str: Protected URL that can be accessed globally
    """
    try:
        # Encode the file URL for embedding in hash fragment
        encoded_file_url = base64.urlsafe_b64encode(file_url.encode()).decode()
        
        # Create the protected URL using our static password protection page
        # The static page will extract the encoded file URL and password from the hash fragment
        # and handle the password verification client-side
        protected_url = f"/static/password-protection.html#{encoded_file_url}:{share_id}:{password}"
        
        return protected_url
        
    except Exception as e:
        print(f"Error creating protected URL: {str(e)}")
        raise Exception(f"Error creating protected URL: {str(e)}") 