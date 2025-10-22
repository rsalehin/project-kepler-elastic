import pytest
# REMOVED: from app.elastic import es_client - No longer exists

@pytest.mark.asyncio
# Accept the fixture as an argument
async def test_elastic_ping(es_test_client): # <-- USE FIXTURE
    """ Tests that the Elastic client fixture connects successfully. """
    # Fixture already calls ping during setup, just assert it exists
    assert es_test_client is not None, "Elastic client fixture failed to create"

    # Optional: Ping again within the test if desired
    is_connected = await es_test_client.ping()
    assert is_connected is True, "Client failed to ping within the test"
