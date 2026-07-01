import pytest
from unittest.mock import MagicMock, patch
from parser.pipeline.stage4_llm import extract_structured


@pytest.fixture
def mock_merge_output():
    return {
        "text": "John Doe\nSoftware Engineer\nGitHub: https://github.com/johndoe",
        "embedded_links": [
            {
                "url": "https://github.com/johndoe",
                "anchor_text": "GitHub",
                "type": "github",
                "page_number": 0,
            }
        ],
        "metadata": {"title": "John Doe Resume"},
    }


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_extract_structured_gemini_success(mock_post, mock_merge_output):
    """Test when Gemini API succeeds, it returns the parsed output."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '{"personal": {"name": "John Doe"}, "experience": []}'}
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    # Run
    with patch("parser.config.GEMINI_API_KEY", "valid_mock_key"):
        result = await extract_structured(mock_merge_output)

    assert result["parse_status"] == "success"
    assert result["provider"] == "gemini"
    assert result["parsed"] == {"personal": {"name": "John Doe"}, "experience": []}


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_extract_structured_gemini_fail(mock_post, mock_merge_output):
    """Test when Gemini fails, it returns api_error."""
    # Gemini fails
    mock_post.side_effect = Exception("Gemini error")

    # Run
    with patch("parser.config.GEMINI_API_KEY", "valid_mock_key"):
        result = await extract_structured(mock_merge_output)

    assert result["parse_status"] == "api_error"
    assert result["provider"] == "none"
    assert result["parsed"] is None
    assert "Gemini error" in result["reason"]


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_extract_structured_markdown_cleaning(mock_post, mock_merge_output):
    """Test that markdown fences are cleaned before parsing JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '```json\n{"personal": {"name": "John Doe"}}\n```'}
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    with patch("parser.config.GEMINI_API_KEY", "valid_mock_key"):
        result = await extract_structured(mock_merge_output)

    assert result["parse_status"] == "success"
    assert result["parsed"] == {"personal": {"name": "John Doe"}}


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_extract_structured_json_error(mock_post, mock_merge_output):
    """Test that malformed JSON response is caught and returns json_error status."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": "No details found on resume."}]}}
        ]
    }
    mock_post.return_value = mock_response

    with patch("parser.config.GEMINI_API_KEY", "valid_mock_key"):
        result = await extract_structured(mock_merge_output)

    assert result["parse_status"] == "json_error"
    assert result["parsed"] is None
    assert result["raw_response"] == "No details found on resume."
    assert result["reason"] is not None
