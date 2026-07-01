import pytest
import uuid
from parser.pipeline.stage6_store import store, init_db


@pytest.mark.asyncio
async def test_init_db():
    """Test that init_db executes without raising exceptions."""
    await init_db()


@pytest.mark.asyncio
async def test_store_success():
    """Test successful no-op storage return values."""
    candidate_id = str(uuid.uuid4())
    mock_validate_output = {
        "validated": {
            "personal": {"name": "Vasanth Kolla", "email": "kollavasanth7@gmail.com"},
            "experience": [],
        },
        "confidence": 0.86,
        "parse_status": "success",
    }

    # Run store
    result = await store(mock_validate_output, candidate_id)

    # Assert return payload
    assert result["parse_status"] == "success"
    assert result["record_id"] == candidate_id
    assert "stored_at" in result
    assert isinstance(result["stored_at"], str)
