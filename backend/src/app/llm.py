import vertexai
from vertexai.generative_models import GenerativeModel, Part
import src.app.config as config # Import config
import os
import asyncio # For running the test function

# --- Constants ---
CHAT_MODEL_NAME = "gemini-2.5-flash"
_llm_model = None # Use a private variable to store the initialized model

# --- Initialization Function ---
def _initialize_vertex_ai():
    """Initializes Vertex AI if not already done."""
    global _llm_model
    # Check if already initialized (simple check)
    # A more robust check might involve querying the SDK's state
    if _llm_model is not None:
        return True

    try:
        print("Attempting to initialize Vertex AI...")
        # Explicitly check credentials path from config
        if not config.GCP_CREDENTIALS_PATH or not os.path.exists(config.GCP_CREDENTIALS_PATH):
             print(f"ERROR: GCP credentials path not found or invalid: {config.GCP_CREDENTIALS_PATH}")
             return False

        # Ensure the environment variable is set (might be redundant, but safe)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GCP_CREDENTIALS_PATH

        vertexai.init(project=config.GCP_PROJECT_ID, location=config.GCP_LOCATION)
        _llm_model = GenerativeModel(CHAT_MODEL_NAME)
        print(f"Vertex AI Initialized. Gemini model '{CHAT_MODEL_NAME}' loaded.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize Vertex AI or load model: {e}")
        _llm_model = None # Ensure it's None on failure
        return False

# --- Core Function ---
async def get_gemini_response(prompt: str) -> str | None:
    """
    Sends a prompt to the configured Gemini model and returns the text response.
    Initializes Vertex AI if needed.
    """
    # Attempt initialization right before the call
    if not _initialize_vertex_ai():
        print("ERROR: Vertex AI Initialization failed. Cannot get response.")
        return None # Return None if initialization failed

    # Model should now be loaded if initialization succeeded
    if not _llm_model:
         print("ERROR: LLM model is unexpectedly None after initialization attempt.")
         return None

    print(f"\nSending prompt to Gemini: '{prompt[:50]}...'")
    try:
        response = await _llm_model.generate_content_async(prompt)

        if response and response.candidates and response.candidates[0].content.parts:
            text_response = response.candidates[0].content.parts[0].text
            print(f"Received response from Gemini: '{text_response[:50]}...'")
            return text_response
        else:
            print("ERROR: Received invalid or empty response from Gemini.")
            # print(f"Full Response: {response}") # For debugging
            return None

    except Exception as e:
        print(f"ERROR calling Gemini API: {e}")
        return None

# --- Simple test function (remains the same) ---
async def _test_llm_connection():
    # No need to check credentials here, _initialize_vertex_ai will do it
    print("\n--- Testing Gemini Connection ---")
    test_prompt = "Explain the concept of an exoplanet transit in one sentence."
    response = await get_gemini_response(test_prompt)
    if response:
        print(f"\nTest successful! Response received:\n{response}")
    else:
        print("\nTest failed! No response received.")
    print("---------------------------------")

if __name__ == "__main__":
    # Ensure .env is loaded if running directly
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    # Update config vars after loading .env if needed
    config.GCP_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    asyncio.run(_test_llm_connection())
