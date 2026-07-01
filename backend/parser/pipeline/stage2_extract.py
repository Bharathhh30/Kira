import fitz
import pdfplumber
from concurrent.futures import ThreadPoolExecutor


def _extract_text(pdf_path: str) -> str:
    """Extracts all text from the PDF using pdfplumber."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            pages_text.append(text if text is not None else "")
    return "\n".join(pages_text)


def _extract_links(pdf_path: str) -> list[dict]:
    """Extracts all embedded URI links and their page numbers/bounding boxes using PyMuPDF (fitz)."""
    links = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_links = page.get_links()
        for link in page_links:
            if "uri" in link:
                rect = link["from"]  # fitz.Rect object
                rect_list = [rect.x0, rect.y0, rect.x1, rect.y1]
                links.append(
                    {"uri": link["uri"], "page_number": page_num, "rect": rect_list}
                )
    doc.close()
    return links


def _extract_metadata(pdf_path: str) -> dict:
    """Extracts the document metadata using PyMuPDF (fitz)."""
    doc = fitz.open(pdf_path)
    meta = doc.metadata
    doc.close()
    return meta


def extract(pdf_path: str) -> dict:
    """
    Runs three extractions concurrently using ThreadPoolExecutor:
      1. Text content (pdfplumber)
      2. Hyperlinks from annotation layer (PyMuPDF)
      3. Document metadata (PyMuPDF)

    Returns a dict with raw_text, raw_links, and metadata. If any extractor
    fails, its key is set to None and details are added to extraction_warnings.
    """
    warnings = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_text = executor.submit(_extract_text, pdf_path)
        future_links = executor.submit(_extract_links, pdf_path)
        future_meta = executor.submit(_extract_metadata, pdf_path)

        # Retrieve text extraction result
        try:
            raw_text = future_text.result()
        except Exception as e:
            raw_text = None
            warnings.append(f"Text extraction failed: {str(e)}")

        # Retrieve link extraction result
        try:
            raw_links = future_links.result()
        except Exception as e:
            raw_links = None
            warnings.append(f"Link extraction failed: {str(e)}")

        # Retrieve metadata extraction result
        try:
            metadata = future_meta.result()
        except Exception as e:
            metadata = None
            warnings.append(f"Metadata extraction failed: {str(e)}")

    res = {"raw_text": raw_text, "raw_links": raw_links, "metadata": metadata}

    if warnings:
        res["extraction_warnings"] = warnings

    return res
