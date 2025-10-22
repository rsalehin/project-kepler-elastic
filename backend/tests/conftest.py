import pytest
import asyncio
import pytest_asyncio # <-- IMPORT THIS
from elasticsearch import AsyncElasticsearch
from src.app.config import ELASTIC_HOSTS, ELASTIC_API_KEY

@pytest_asyncio.fixture(scope="function") # <-- USE pytest_asyncio.fixture
async def es_test_client():
    """Pytest fixture to create and tear down an Elasticsearch async client."""
    if not ELASTIC_HOSTS or not ELASTIC_API_KEY:
        pytest.fail("ELASTIC_HOSTS or ELASTIC_API_KEY not configured in .env")

    # Create client instance
    client = AsyncElasticsearch(
        hosts=[ELASTIC_HOSTS],
        api_key=ELASTIC_API_KEY
    )
    
    # Check connection before yielding
    try:
        await client.ping()
        print("Test ES client connected.")
    except Exception as e:
        # Close client if ping fails, then fail test
        try: await client.close()
        except: pass
        pytest.fail(f"Failed to connect test ES client: {e}")

    yield client # Provide the client to the test function

    # Teardown: Close the client after the test function finishes
    print("Closing test ES client...")
    try:
        await client.close()
        print("Test ES client closed.")
    except Exception as e:
        print(f"Error closing test ES client: {e}")
