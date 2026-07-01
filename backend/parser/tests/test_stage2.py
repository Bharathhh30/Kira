import fitz
from unittest.mock import patch
from parser.pipeline.stage2_extract import extract


def create_rich_pdf(path: str):
    """Helper to create a PDF with text, metadata, and a URI link."""
    doc = fitz.open()
    page = doc.new_page()

    # 1. Add some text content
    page.insert_text(
        (50, 50),
        "Resume of Candidate John Doe\nExperience: Python Developer\nPortfolio: GitHub link below",
    )

    # 2. Add an embedded link annotation
    link_rect = fitz.Rect(50, 100, 150, 120)
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": link_rect,
            "uri": "https://github.com/shashankraj28",
        }
    )

    # 3. Add metadata
    doc.set_metadata(
        {
            "title": "John Doe Resume",
            "author": "John Doe",
            "subject": "Developer Application",
        }
    )

    doc.save(path)
    doc.close()


def test_extract_success(tmp_path):
    """Test successful concurrent extraction of text, links, and metadata."""
    pdf_path = str(tmp_path / "rich_resume.pdf")
    create_rich_pdf(pdf_path)

    result = extract(pdf_path)

    # Assertions on return keys
    assert "raw_text" in result
    assert "raw_links" in result
    assert "metadata" in result
    assert "extraction_warnings" not in result

    # Assertions on content
    assert "Resume of Candidate John Doe" in result["raw_text"]
    assert "Python Developer" in result["raw_text"]

    assert len(result["raw_links"]) == 1
    link = result["raw_links"][0]
    assert link["uri"] == "https://github.com/shashankraj28"
    assert link["page_number"] == 0
    # Rect coordinates check [x0, y0, x1, y1]
    assert isinstance(link["rect"], list)
    assert len(link["rect"]) == 4
    assert link["rect"] == [50.0, 100.0, 150.0, 120.0]

    assert result["metadata"]["title"] == "John Doe Resume"
    assert result["metadata"]["author"] == "John Doe"


def test_extract_partial_failure(tmp_path):
    """Test that if one extractor fails, the others complete, returning None and warnings."""
    pdf_path = str(tmp_path / "rich_resume.pdf")
    create_rich_pdf(pdf_path)

    # Mock text extraction to raise an exception
    with patch(
        "parser.pipeline.stage2_extract._extract_text",
        side_effect=Exception("Mocked text extraction error"),
    ):
        result = extract(pdf_path)

        # Verify text is None and warning is logged
        assert result["raw_text"] is None
        assert "extraction_warnings" in result
        assert any(
            "Text extraction failed: Mocked text extraction error" in w
            for w in result["extraction_warnings"]
        )

        # Verify links and metadata still extracted successfully
        assert result["raw_links"] is not None
        assert len(result["raw_links"]) == 1
        assert result["raw_links"][0]["uri"] == "https://github.com/shashankraj28"

        assert result["metadata"] is not None
        assert result["metadata"]["title"] == "John Doe Resume"
