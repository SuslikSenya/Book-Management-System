import pytest

@pytest.mark.asyncio
async def test_client_type(client):
    print("CLIENT TYPE:", type(client))
    assert hasattr(client, "post") and hasattr(client, "get")