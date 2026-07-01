import fitz
from parser.pipeline.stage2_extract import extract
from parser.pipeline.stage3_merge import merge, classify_url, get_domain


def create_stage3_test_pdf(path: str):
    """Helper to create a PDF with embedded links, text URLs, and overlapping words."""
    doc = fitz.open()
    page = doc.new_page()

    # 1. Render the text physically at specific coordinates
    # We write "GitHub Profile" at (50, 100)
    page.insert_text((50, 100), "GitHub Profile", fontsize=11)

    # We write plain-text URLs in a normal paragraph
    page.insert_text(
        (50, 150),
        "Portfolio: https://mywebsite.com\nDuplicate Link: https://github.com/shashankraj28/another-repo",
    )

    # 2. Add an embedded link annotation directly overlapping the "GitHub Profile" text
    # Rect spans x: 45 to 150, y: 90 to 105
    link_rect = fitz.Rect(45, 88, 160, 106)
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": link_rect,
            "uri": "https://github.com/shashankraj28",
        }
    )

    doc.save(path)
    doc.close()


def test_classify_url():
    """Verify URL classification rules."""
    assert classify_url("https://www.linkedin.com/in/johndoe") == "linkedin"
    assert classify_url("https://github.com/shashankraj") == "github"
    assert classify_url("https://twitter.com/johndoe") == "twitter"
    assert classify_url("https://x.com/johndoe") == "twitter"
    assert classify_url("mailto:test@example.com") == "email"
    assert classify_url("test@example.com") == "email"
    assert classify_url("https://leetcode.com/problemset") == "coding_profile"
    assert classify_url("https://myportfolio.github.io") == "portfolio"
    assert classify_url("https://bharathhh30.vercel.app/") == "live_demo"
    assert classify_url("https://mysite.netlify.app") == "live_demo"
    assert classify_url("https://example.com/other") == "other"


def test_get_domain():
    """Verify domain extraction and normalization."""
    assert get_domain("https://www.linkedin.com/in/johndoe") == "linkedin.com"
    assert get_domain("http://github.com/shashankraj") == "github.com"
    assert get_domain("www.leetcode.com/problemset") == "leetcode.com"
    assert get_domain("mailto:test@example.com") == "example.com"
    assert get_domain("test@example.com") == "example.com"


def test_merge_and_link_enrichment(tmp_path):
    """Test full merge pipeline: anchor text resolution and domain deduplication."""
    pdf_path = str(tmp_path / "stage3_test.pdf")
    create_stage3_test_pdf(pdf_path)

    # 1. Run Stage 2 extraction
    extract_output = extract(pdf_path)

    # 2. Run Stage 3 merge
    merged_output = merge(extract_output, pdf_path)

    # Assert return structure
    assert "text" in merged_output
    assert "embedded_links" in merged_output
    assert "text_urls" in merged_output
    assert "metadata" in merged_output

    # Verify raw text is preserved
    assert "GitHub Profile" in merged_output["text"]
    assert "https://mywebsite.com" in merged_output["text"]

    # Verify embedded link enrichment
    assert len(merged_output["embedded_links"]) == 1
    emb_link = merged_output["embedded_links"][0]
    assert emb_link["url"] == "https://github.com/shashankraj28"
    assert emb_link["type"] == "github"
    assert emb_link["page_number"] == 0
    # The words "GitHub" and "Profile" should be correctly resolved as anchor text
    assert "GitHub" in emb_link["anchor_text"]
    assert "Profile" in emb_link["anchor_text"]

    # Verify plain-text URL detection and domain-level deduplication
    # We expect https://mywebsite.com to be detected (since domain mywebsite.com is not in embedded links)
    # We expect https://github.com/shashankraj28/another-repo to be FILTERED OUT (since domain github.com is already in embedded links)
    assert len(merged_output["text_urls"]) == 1
    txt_url = merged_output["text_urls"][0]
    assert txt_url["url"] == "https://mywebsite.com"
    assert txt_url["type"] == "portfolio"
    assert txt_url["source"] == "text"
