import pytest
import os
from src.app.llm import get_gemini_response
from src.app.config import GCP_CREDENTIALS_PATH # To check if credentials exist

# Mark this test to skip if GCP credentials are not configured
# (Prevents test failures in environments without secrets, like basic CI later)
pytestmark = pytest.mark.skipif(
    not GCP_CREDENTIALS_PATH or not os.path.exists(GCP_CREDENTIALS_PATH),
    reason="Requires GCP credentials configuration (GOOGLE_APPLICATION_CREDENTIALS)"
)

@pytest.mark.asyncio
async def test_get_gemini_response_integration():
    """
    Integration test: Calls the actual Gemini API with a simple prompt.
    Checks if a non-empty string response is received.
    """
    prompt = "Why is the sky blue? Answer concisely."
    response = await get_gemini_response(prompt)

    # Basic assertion: Did we get *any* text back?
    assert response is not None
    assert isinstance(response, str)
    assert len(response.strip()) > 0
    print(f"Test Prompt: {prompt}") # Optional: print prompt/response for context
    print(f"Test Response: {response}")
