from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import contextlib
from elasticsearch import AsyncElasticsearch
import asyncio

# Import our config and agent function
from src.app.config import ELASTIC_HOSTS, ELASTIC_API_KEY
from src.app.llm import run_agent_conversation

# --- Pydantic Models for Request/Response ---
# This defines the expected JSON structure for our API
class ChatRequest(BaseModel):
    prompt: str
    # session_id: str | None = None # Optional: for chat history later

class ChatResponse(BaseModel):
    text: str | None = None
    plot_path: str | None = None
    error: str | None = None

# --- Manage Elasticsearch Client Lifecycle ---
# We'll create one client instance when the app starts
# and close it when the app shuts down.
es_client_store = {}

@contextlib.asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Context manager to handle application startup and shutdown.
    """
    print("FastAPI app starting...")
    if not ELASTIC_HOSTS or not ELASTIC_API_KEY:
        raise ValueError("ELASTIC_HOSTS and ELASTIC_API_KEY must be set in .env")
    
    # Startup: Create the client and store it
    print("Initializing global Elasticsearch client...")
    client = AsyncElasticsearch(
        hosts=[ELASTIC_HOSTS],
        api_key=ELASTIC_API_KEY
    )
    if not await client.ping():
         print("ERROR: Failed to connect to Elasticsearch on startup.")
         # You might want to raise an exception here to stop the app
    else:
         print("Global Elasticsearch client connected.")
         es_client_store["client"] = client
    
    yield # The app is now running
    
    # Shutdown: Close the client
    print("FastAPI app shutting down...")
    client = es_client_store.get("client")
    if client:
        try:
            await client.close()
            print("Global Elasticsearch client closed.")
        except Exception as e:
            print(f"Error closing Elasticsearch client: {e}")

# --- Create FastAPI App with Lifespan ---
app = FastAPI(title="Project Kepler API", lifespan=app_lifespan)

# --- Endpoints ---
@app.get("/health")
def read_health():
    """ A simple health check endpoint. """
    return {"status": "ok"}

# --- *** NEW CHAT ENDPOINT *** ---
@app.post("/chat")
async def handle_chat(request: ChatRequest) -> ChatResponse:
    """
    Main endpoint to handle user chat messages.
    Receives a prompt, passes it to the Gemini agent,
    and returns the agent's response.
    """
    es_client = es_client_store.get("client")
    if not es_client:
        print("ERROR: /chat endpoint called but ES client is not available.")
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized.")

    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        # Call our agent function
        agent_result = await run_agent_conversation(request.prompt, es_client)
        
        if "error" in agent_result:
            # Pass agent errors back to the client
            raise HTTPException(status_code=500, detail=agent_result["error"])
        
        # Return the successful response
        return ChatResponse(
            text=agent_result.get("text"),
            plot_path=agent_result.get("plot_path")
        )

    except Exception as e:
        print(f"ERROR in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
