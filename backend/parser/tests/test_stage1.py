import fitz

# pyrefly: ignore [missing-import]
from parser.pipeline.stage1_ingestion import detect_pdf_type


def create_digital_pdf(path: str, text_content: str):
    """Helper to create a digital PDF with text content."""
    doc = fitz.open()
    page = doc.new_page()
    # Insert text at a visible position
    page.insert_text((50, 50), text_content)
    doc.save(path)
    doc.close()


def create_scanned_pdf(path: str, text_content: str):
    """Helper to create a scanned PDF (text rasterized as image, no text layer)."""
    # 1. Create temporary doc to render the text
    doc_temp = fitz.open()
    page_temp = doc_temp.new_page()
    page_temp.insert_text((50, 50), text_content)
    pix = page_temp.get_pixmap()
    img_bytes = pix.tobytes("png")
    doc_temp.close()

    # 2. Insert the rendered image into the final PDF (so it contains only an image)
    doc_scanned = fitz.open()
    page_sc = doc_scanned.new_page()
    page_sc.insert_image(page_sc.rect, stream=img_bytes)
    doc_scanned.save(path)
    doc_scanned.close()


def create_encrypted_pdf(path: str, text_content: str, password: str):
    """Helper to create a password-protected PDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text_content)
    doc.save(path, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password)
    doc.close()


def create_corrupt_file(path: str):
    """Helper to write random corrupt binary data to a file."""
    with open(path, "wb") as f:
        f.write(
            b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nThis is corrupt data, not a real PDF structure."
        )


def test_detect_pdf_type_digital(tmp_path):
    """Test 10 digital PDFs are correctly classified."""
    for i in range(10):
        file_path = str(tmp_path / f"digital_resume_{i}.pdf")
        # Ensure text content is well above the 100 character threshold
        text = (
            f"Resume of Candidate #{i}\n"
            + "Name: Alex Smith\n"
            + "Skills: Python, Go, C++, SQL, Docker, Kubernetes\n"
            + "Experience: 5 years working as a software developer doing backend development and API design.\n"
            + "Education: BS in Computer Science from Tech University."
        )

        create_digital_pdf(file_path, text)

        result = detect_pdf_type(file_path)

        assert result["success"] is True
        assert result["is_digital"] is True
        assert result["error_type"] is None
        assert result["message"] is None


def test_detect_pdf_type_scanned(tmp_path):
    """Test 10 scanned PDFs are correctly classified (no text layer)."""
    for i in range(10):
        file_path = str(tmp_path / f"scanned_resume_{i}.pdf")
        text = f"Scanned resume page #{i} for manual verification. OCR needed."

        create_scanned_pdf(file_path, text)

        result = detect_pdf_type(file_path)

        assert result["success"] is True
        assert result["is_digital"] is False
        assert result["error_type"] is None
        assert result["message"] is None


def test_detect_pdf_type_password_protected(tmp_path):
    """Test password protected PDFs are identified without crashing."""
    file_path = str(tmp_path / "encrypted_resume.pdf")
    create_encrypted_pdf(
        file_path, "Highly confidential resume details.", "super_secret_pw"
    )

    result = detect_pdf_type(file_path)

    assert result["success"] is False
    assert result["is_digital"] is None
    assert result["error_type"] == "PasswordProtectedPDF"
    assert (
        "password" in result["message"].lower()
        or "encrypt" in result["message"].lower()
    )


def test_detect_pdf_type_corrupt(tmp_path):
    """Test corrupt PDFs return a structured error instead of crashing."""
    file_path = str(tmp_path / "corrupt_resume.pdf")
    create_corrupt_file(file_path)

    result = detect_pdf_type(file_path)

    assert result["success"] is False
    assert result["is_digital"] is None
    assert result["error_type"] == "CorruptPDF"
    assert result["message"] is not None


def test_detect_pdf_type_file_not_found():
    """Test non-existent files are handled gracefully."""
    result = detect_pdf_type("non_existent_file_path_12345.pdf")

    assert result["success"] is False
    assert result["is_digital"] is None
    assert result["error_type"] == "FileNotFound"
    assert "file not found" in result["message"].lower()
