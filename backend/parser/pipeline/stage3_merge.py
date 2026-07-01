import re
import fitz
from urllib.parse import urlparse


def classify_url(url: str) -> str:
    """
    Classifies a URL into one of:
    linkedin, github, twitter, portfolio, email, coding_profile, other.
    """
    url_lower = url.lower()
    if "linkedin" in url_lower:
        return "linkedin"
    elif "github.io" in url_lower:
        return "portfolio"
    elif "github" in url_lower:
        return "github"
    elif "twitter" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "mailto:" in url_lower or "@" in url_lower:
        return "email"
    elif any(
        domain in url_lower
        for domain in [
            "leetcode",
            "hackerrank",
            "codeforces",
            "codechef",
            "geeksforgeeks",
            "kaggle",
        ]
    ):
        return "coding_profile"
    elif any(domain in url_lower for domain in ["vercel.app", "netlify.app"]):
        return "live_demo"
    elif (
        any(kw in url_lower for kw in ["portfolio", "website", "blog", "about.me"])
        or "personal" in url_lower
    ):
        return "portfolio"
    else:
        return "other"


def get_domain(url: str) -> str:
    """Extracts the base domain name from a URL for deduplication."""
    url_lower = url.lower()
    # Normalize email / mailto
    if url_lower.startswith("mailto:"):
        parts = url_lower.split("@")
        if len(parts) > 1:
            return parts[-1]
    if "@" in url_lower and not url_lower.startswith(("http://", "https://")):
        parts = url_lower.split("@")
        return parts[-1]

    if not url_lower.startswith(("http://", "https://")):
        url_lower = "https://" + url_lower

    try:
        parsed = urlparse(url_lower)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        # Remove port if any
        domain = domain.split(":")[0]
        return domain
    except Exception:
        return url_lower


def merge(extract_output: dict, pdf_path: str) -> dict:
    """
    Performs Stage 3 pre-merge logic:
    1. Anchor text resolution for embedded links by checking intersection with words.
    2. Plain-text URL extraction from raw_text with domain-based deduplication.
    3. Merging the payload into a structured dictionary.
    """
    raw_text = extract_output.get("raw_text") or ""
    raw_links = extract_output.get("raw_links") or []
    metadata = extract_output.get("metadata")

    enriched_links = []
    enriched_domains = set()

    # 1. Anchor Text Resolution
    if raw_links and pdf_path:
        doc = None
        try:
            doc = fitz.open(pdf_path)
            for link in raw_links:
                uri = link.get("uri")
                page_number = link.get("page_number", 0)
                rect_coords = link.get("rect")

                if not uri:
                    continue

                anchor_text = ""
                # Make sure the page exists in the PDF
                if doc and 0 <= page_number < len(doc):
                    page = doc[page_number]
                    # get_text("words") returns tuples: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
                    words = page.get_text("words")
                    link_rect = fitz.Rect(rect_coords)

                    matching_words = []
                    for w in words:
                        word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
                        # Check intersection
                        intersection = link_rect & word_rect
                        if not intersection.is_empty:
                            matching_words.append(w[4])

                    if matching_words:
                        anchor_text = " ".join(matching_words)

                classified_type = classify_url(uri)
                enriched_links.append(
                    {
                        "url": uri,
                        "anchor_text": anchor_text.strip(),
                        "type": classified_type,
                        "page_number": page_number,
                    }
                )

                domain = get_domain(uri)
                if domain:
                    enriched_domains.add(domain)
        except Exception as e:
            # If doc opening fails, we still pass through links without anchor text
            print(f"Warning: Failed to open PDF for anchor text resolution: {e}")
            for link in raw_links:
                uri = link.get("uri")
                if uri:
                    enriched_links.append(
                        {
                            "url": uri,
                            "anchor_text": "",
                            "type": classify_url(uri),
                            "page_number": link.get("page_number", 0),
                        }
                    )
                    domain = get_domain(uri)
                    if domain:
                        enriched_domains.add(domain)
        finally:
            if doc:
                doc.close()

    # 2. Plain-text URL detection
    text_urls = []
    if raw_text:
        # Standard URL regex pattern matching HTTP/HTTPS/WWW URLs
        url_pattern = re.compile(r'(https?://[^\s<>"]+|www\.[^\s<>"]+)')
        matches = url_pattern.findall(raw_text)

        seen_urls = set()
        for raw_url in matches:
            # Clean up trailing punctuation
            url = raw_url
            while url and url[-1] in ".,;:)!?]'\">":
                url = url[:-1]

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            domain = get_domain(url)

            # Deduplicate against enriched_links using domain matching
            if domain not in enriched_domains:
                classified_type = classify_url(url)
                text_urls.append(
                    {"url": url, "type": classified_type, "source": "text"}
                )

    return {
        "text": raw_text,
        "embedded_links": enriched_links,
        "text_urls": text_urls,
        "metadata": metadata,
    }
