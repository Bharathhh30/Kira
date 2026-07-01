import os
import fitz
from parser.config import DIGITAL_PDF_THRESHOLD


def detect_pdf_type(file_path: str) -> dict:
    """
    Ingests a PDF file and classifies it as digital (has text layer) or scanned (no text layer).
    Handles corrupt, password-protected, or missing files gracefully.

    Returns:
        dict: {
            "success": bool,
            "is_digital": bool or None,
            "error_type": str or None,
            "message": str or None
        }
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "is_digital": None,
            "error_type": "FileNotFound",
            "message": f"File not found: {file_path}",
        }

    doc = None
    try:
        doc = fitz.open(file_path)

        # Check if the document is encrypted/password protected
        if doc.is_encrypted:
            doc.close()
            return {
                "success": False,
                "is_digital": None,
                "error_type": "PasswordProtectedPDF",
                "message": "The PDF file is password-protected.",
            }

        # Check if there are pages in the PDF
        if len(doc) == 0:
            doc.close()
            return {
                "success": False,
                "is_digital": None,
                "error_type": "CorruptPDF",
                "message": "The PDF has zero pages or is corrupted.",
            }

        # Extract text from the first page
        page = doc[0]
        text = page.get_text()

        doc.close()

        is_digital = len(text.strip()) > DIGITAL_PDF_THRESHOLD

        return {
            "success": True,
            "is_digital": is_digital,
            "error_type": None,
            "message": None,
        }

    except fitz.FileDataError as e:
        if doc:
            try:
                doc.close()
            except Exception:
                pass
        return {
            "success": False,
            "is_digital": None,
            "error_type": "CorruptPDF",
            "message": f"PyMuPDF failed to parse file (FileDataError): {str(e)}",
        }
    except Exception as e:
        if doc:
            try:
                doc.close()
            except Exception:
                pass

        # Check if the exception message indicates encryption or password, just in case
        err_msg = str(e).lower()
        if "encrypted" in err_msg or "password" in err_msg:
            return {
                "success": False,
                "is_digital": None,
                "error_type": "PasswordProtectedPDF",
                "message": f"Encrypted PDF detected: {str(e)}",
            }

        return {
            "success": False,
            "is_digital": None,
            "error_type": "CorruptPDF",
            "message": f"An unexpected error occurred while parsing the PDF: {str(e)}",
        }
