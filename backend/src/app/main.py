from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import contextlib
from elasticsearch import AsyncElasticsearch
import asyncio
import os # Import os for path operations

# *** NEW IMPORTS ***
from fastapi.staticfiles import StaticFiles

# Import our config and agent function
from src.app.config import ELASTIC_HOSTS, ELASTIC_API_KEY
from src.app.llm import run_agent_conversation

# --- Pydantic Models (unchanged) ---
class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    text: str | None = None
    plot_path: str | None = None
    error: str | None = None

# --- Manage Elasticsearch Client Lifecycle (unchanged) ---
es_client_store = {}

@contextlib.asynccontextmanager
async def app_lifespan(app: FastAPI):
    print("FastAPI app starting...")
    if not ELASTIC_HOSTS or not ELASTIC_API_KEY:
        raise ValueError("ELASTIC_HOSTS and ELASTIC_API_KEY must be set in .env")
    
    print("Initializing global Elasticsearch client...")
    client = AsyncElasticsearch(
        hosts=[ELASTIC_HOSTS],
        api_key=ELASTIC_API_KEY
    )
    if not await client.ping():
         print("ERROR: Failed to connect to Elasticsearch on startup.")
    else:
         print("Global Elasticsearch client connected.")
         es_client_store["client"] = client
    
    yield
    
    print("FastAPI app shutting down...")
    client = es_client_store.get("client")
    if client:
        try:
            await client.close()
            print("Global Elasticsearch client closed.")
        except Exception as e:
            print(f"Error closing Elasticsearch client: {e}")

# --- Create FastAPI App with Lifespan (unchanged) ---
app = FastAPI(title="Project Kepler API", lifespan=app_lifespan)

# --- *** MOUNT STATIC DIRECTORY *** ---
# Get the absolute path to the 'static' directory (src/app/static)
# __file__ is src/app/main.py
# os.path.dirname(__file__) is src/app
# os.path.join(...) gives src/app/static
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Ensure the directory exists (optional, but good)
os.makedirs(static_dir, exist_ok=True) 
print(f"Serving static files from: {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
# --- *** END MOUNT *** ---


# --- Endpoints ---
@app.get("/health")
def read_health():
    """ A simple health check endpoint. """
    return {"status": "ok"}

# --- Chat Endpoint (unchanged) ---
@app.post("/chat")
async def handle_chat(request: ChatRequest) -> ChatResponse:
    es_client = es_client_store.get("client")
    if not es_client:
        print("ERROR: /chat endpoint called but ES client is not available.")
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized.")
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        agent_result = await run_agent_conversation(request.prompt, es_client)
        
        if "error" in agent_result:
            raise HTTPException(status_code=500, detail=agent_result["error"])
        
        return ChatResponse(
            text=agent_result.get("text"),
            plot_path=agent_result.get("plot_path") # This path will now be servable
        )
    except Exception as e:
        print(f"ERROR in /chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
