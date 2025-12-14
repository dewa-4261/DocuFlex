# Docuflex utility modules
from .pdf_utils import merge_pdfs, split_pdf, convert_pdf_to_images, compress_pdf, add_watermark_to_pdf
from .image_utils import convert_image_to_pdf, remove_background, compress_image, add_watermark_to_image
from .document_utils import share_document, generate_qr_code, share_document_with_protection, hash_password, generate_share_id, create_protected_url
from .ocr_utils import extract_text_from_pdf, extract_text_from_image 