import pytest
from httpx import AsyncClient, ASGITransport
# This next line will cause an error because Python can't find 'app' yet!
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    """
    Tests that the /health endpoint returns HTTP 200 OK
    and a JSON body {'status': 'ok'}.
    """
    # We need to install our package before this test can run successfully
    # We'll do that in the next step! For now, expect an import error.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
