import pytest
# This import will fail initially!
from app.elastic import es_client

@pytest.mark.asyncio
async def test_elastic_ping():
    """
    Tests that the Elastic client can be created and can ping the cluster.
    Assumes ELASTIC_HOSTS and ELASTIC_API_KEY are in the environment (via .env).
    """
    assert es_client is not None, "Elastic client instance should be created"

    # The async client's .ping() returns True on success, raises error on fail
    is_connected = await es_client.ping()

    assert is_connected is True, "Client should successfully ping the cluster"
