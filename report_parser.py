"""
report_parser.py
Extracts and cleans text from uploaded medical reports (PDF, Images, and direct text).
Handles text PDFs, image OCR via Tesseract/Pillow, and direct text reports.
"""

import os
import re

try:
    import pymupdf as fitz  # type: ignore
except ImportError:
    try:
        import fitz  # type: ignore
    except ImportError:
        fitz = None

try:
    import pypdf  # type: ignore
except ImportError:
    try:
        import PyPDF2 as pypdf  # type: ignore
    except ImportError:
        pypdf = None

try:
    from PIL import Image  # type: ignore
except ImportError:
    Image = None

try:
    import pytesseract  # type: ignore
except ImportError:
    pytesseract = None


class ExtractionError(Exception):
    """Custom exception raised when text extraction fails or yields insufficient content."""
    pass

# Alias for backwards compatibility
PDFExtractionError = ExtractionError


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text page-by-page from a PDF file using PyMuPDF (or pypdf as fallback),
    cleans whitespace, and returns combined readable text.
    """
    if not os.path.exists(file_path):
        raise PDFExtractionError("PDF file not found on the server.")

    extracted_pages = []

    # Method 1: PyMuPDF (fitz)
    if fitz is not None:
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")
                if page_text:
                    cleaned_page_text = clean_extracted_text(page_text)
                    if cleaned_page_text:
                        extracted_pages.append(f"--- Page {page_num + 1} ---\n{cleaned_page_text}")
            doc.close()
        except Exception:
            pass

    # Method 2: pypdf / PyPDF2 fallback if PyMuPDF extracted nothing
    if not extracted_pages and pypdf is not None:
        try:
            reader = pypdf.PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text:
                    cleaned_page_text = clean_extracted_text(page_text)
                    if cleaned_page_text:
                        extracted_pages.append(f"--- Page {page_num + 1} ---\n{cleaned_page_text}")
        except Exception:
            pass

    combined_text = "\n\n".join(extracted_pages).strip()

    # Check if any substantial readable text was found
    alphanumeric_chars = re.sub(r'[^a-zA-Z0-9]', '', combined_text)
    if not combined_text or len(alphanumeric_chars) < 20:
        return "This PDF appears to contain scanned images. Text extraction was not possible."

    return combined_text


def extract_text_from_image(file_path: str) -> str:
    """
    Extracts text from medical report image files (JPG, PNG, WEBP) using pytesseract/Pillow.
    """
    if not os.path.exists(file_path):
        raise ExtractionError("Image file not found on the server.")

    if Image is None:
        raise ExtractionError("Pillow library is not installed for image processing.")

    try:
        img = Image.open(file_path)
        # Convert image to RGB if needed
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")

        extracted_text = ""
        if pytesseract is not None:
            try:
                extracted_text = pytesseract.image_to_string(img)
            except Exception:
                extracted_text = ""

        cleaned = clean_extracted_text(extracted_text)
        alphanumeric_chars = re.sub(r'[^a-zA-Z0-9]', '', cleaned)

        if not cleaned or len(alphanumeric_chars) < 15:
            # Signal that local OCR couldn't read sufficient text
            return ""

        return cleaned

    except Exception as e:
        raise ExtractionError(f"Image processing error: {str(e)}")


def clean_extracted_text(text: str) -> str:
    """
    Cleans extracted text by normalizing line breaks, removing non-printable
    characters, and compressing consecutive whitespace.
    """
    if not text:
        return ""

    # Replace multiple empty lines with maximum 2 newlines
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)

    # Normalize excessive spaces and tabs on the same line
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]

    # Remove excessive blank lines
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line:
            cleaned_lines.append(line)
            blank_count = 0
        else:
            if blank_count == 0:
                cleaned_lines.append("")
                blank_count += 1

    return "\n".join(cleaned_lines).strip()
