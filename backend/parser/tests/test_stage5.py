import pytest
import copy
from parser.pipeline.stage5_validate import validate


@pytest.fixture
def valid_merge_output():
    return {
        "text": "John Doe Resume\nSoftware Engineer",
        "embedded_links": [],
        "metadata": {},
    }


@pytest.fixture
def perfect_parsed_dict():
    return {
        "personal": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123456",
            "location": "NY",
        },
        "links": {"github": "https://github.com/johndoe"},
        "experience": [
            {
                "company": "Tech Corp",
                "title": "Engineer",
                "start_date": "2020-01",
                "end_date": "2022-01",
            }
        ],
        "skills": {"technical": ["Python"]},
    }


@pytest.mark.asyncio
async def test_validate_success(valid_merge_output, perfect_parsed_dict):
    """Valid extraction returns success and populated validated dict."""
    llm_output = {
        "parse_status": "success",
        "parsed": perfect_parsed_dict,
        "provider": "gemini",
    }

    result = await validate(llm_output, valid_merge_output["text"], valid_merge_output)

    assert result["parse_status"] == "success"
    assert result["validated"] is not None
    assert result["validated"]["personal"]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_validate_partial_fields(valid_merge_output, perfect_parsed_dict):
    """Partial data (some nulls) still validates successfully."""
    parsed = copy.deepcopy(perfect_parsed_dict)
    parsed["personal"]["location"] = None
    parsed["experience"] = []

    llm_output = {
        "parse_status": "success",
        "parsed": parsed,
        "provider": "gemini",
    }

    result = await validate(llm_output, valid_merge_output["text"], valid_merge_output)

    assert result["parse_status"] == "success"
    assert result["validated"]["personal"]["location"] is None
    assert result["validated"]["experience"] == []


@pytest.mark.asyncio
async def test_validate_schema_error(valid_merge_output, perfect_parsed_dict):
    """Missing required field raises schema_error."""
    parsed = copy.deepcopy(perfect_parsed_dict)
    del parsed["experience"][0]["company"]

    llm_output = {
        "parse_status": "success",
        "parsed": parsed,
        "provider": "gemini",
    }

    result = await validate(llm_output, valid_merge_output["text"], valid_merge_output)

    assert result["parse_status"] == "schema_error"
    assert result["validated"] is None
    assert "error_details" in result


@pytest.mark.asyncio
async def test_validate_propagates_api_error(valid_merge_output):
    """If Stage 4 failed, Stage 5 propagates that status immediately."""
    llm_output = {
        "parse_status": "api_error",
        "parsed": None,
        "reason": "Gemini API failed",
    }

    result = await validate(llm_output, valid_merge_output["text"], valid_merge_output)

    assert result["parse_status"] == "api_error"
    assert result["validated"] is None
    assert result["error_details"] == "Gemini API failed"


@pytest.mark.asyncio
async def test_validate_no_second_api_call(valid_merge_output, perfect_parsed_dict):
    """Stage 5 never touches the network — no extract_structured attribute on module."""
    import parser.pipeline.stage5_validate as s5

    assert not hasattr(s5, "extract_structured")
