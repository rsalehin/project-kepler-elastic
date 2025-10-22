import vertexai
from vertexai.generative_models import GenerativeModel, Part, Tool, FunctionDeclaration
import src.app.config as config
import src.app.tools as tools
import os
import asyncio
import json
import traceback

# --- Constants ---
CHAT_MODEL_NAME = "gemini-2.5-pro" # Or gemini-2.5-flash, as you prefer
_llm_model = None

# --- Tool Definitions (The "Manual" for Gemini) ---

# 1. Define the search_elastic tool
search_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="search_elastic",
            description="Searches the astronomical database (Elasticsearch) for exoplanets and research papers using vector and keyword search. Use this for questions about planet properties, star properties, or finding research papers.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "text_query": {
                        "type": "STRING",
                        "description": "The natural language semantic query to search for (e.g., 'water on rocky planets', 'habitable exoplanets')."
                    },
                    "keyword_filter_field": {
                        "type": "STRING",
                        "description": "Optional. The exact database field to filter on (e.g., 'pl_name.keyword', 'hostname.keyword')."
                    },
                    "keyword_filter_value": {
                        "type": "STRING",
                        "description": "Optional. The exact value for the keyword filter (e.g., 'TRAPPIST-1 e')."
                    }
                },
                "required": ["text_query"]
            },
        ),
    ]
)

# 2. Define the plot_planet_comparison tool (keep definition for later)
plot_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="plot_planet_comparison",
            description="Generates a scatter plot comparing two properties for a list of specific planets. Use this when the user explicitly asks for a plot or visual comparison.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "planet_names": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "A list of one or more exact planet names to plot (e.g., ['11 Com b', 'TRAPPIST-1 e'])."
                    },
                    "x_property": {
                        "type": "STRING",
                        "description": "The database field to plot on the X-axis (e.g., 'pl_rade' for radius, 'pl_masse' for mass)."
                    },
                    "y_property": {
                        "type": "STRING",
                        "description": "The database field to plot on the Y-axis (e.g., 'pl_masse', 'pl_orbper')."
                    }
                },
                "required": ["planet_names", "x_property", "y_property"]
            },
        ),
    ]
)

# --- *** FIX: Create a list of ONLY the search tool *** ---
AGENT_TOOLS = [search_tool] # <-- THIS IS THE IMPORTANT FIX
# --- *** END FIX *** ---

# --- Initialization Function ---
def _initialize_vertex_ai():
    global _llm_model
    if _llm_model is not None:
        return True
    try:
        print("Attempting to initialize Vertex AI...")
        if not config.GCP_CREDENTIALS_PATH or not os.path.exists(config.GCP_CREDENTIALS_PATH):
             print(f"ERROR: GCP credentials path not found or invalid: {config.GCP_CREDENTIALS_PATH}")
             return False
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GCP_CREDENTIALS_PATH
        vertexai.init(project=config.GCP_PROJECT_ID, location=config.GCP_LOCATION)
        # Load the model, now including ONLY the search tool
        _llm_model = GenerativeModel(CHAT_MODEL_NAME, tools=AGENT_TOOLS)
        print(f"Vertex AI Initialized. Gemini model '{CHAT_MODEL_NAME}' loaded with tools.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize Vertex AI or load model: {e}")
        _llm_model = None
        return False

# --- Core Agent Conversation Function ---
async def run_agent_conversation(prompt: str, es_client) -> dict:
    if not _initialize_vertex_ai():
        return {"error": "Vertex AI Initialization failed."}
    if not _llm_model:
         return {"error": "LLM model is unexpectedly None."}

    print(f"\n--- Starting Agent Conversation ---")
    print(f"User Prompt: '{prompt}'")
    try:
        chat = _llm_model.start_chat()
        response = await chat.send_message_async(prompt)
        
        if response.candidates and response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            function_name = function_call.name
            args = dict(function_call.args)
            print(f"Gemini requested tool call: {function_name}({args})")

            function_response_data = None
            if function_name == "search_elastic":
                function_response_data = await tools.search_elastic(
                    es_client=es_client,
                    text_query=args.get("text_query"),
                    keyword_filter_field=args.get("keyword_filter_field"),
                    keyword_filter_value=args.get("keyword_filter_value")
                )
            # (Plotting logic is implicitly disabled since the tool wasn't provided)
            else:
                function_response_data = json.dumps({"error": f"Unknown tool name '{function_name}' or tool not enabled."})

            print(f"Tool response (first 200 chars): {function_response_data[:200]}...")
            response = await chat.send_message_async(
                Part.from_function_response(
                    name=function_name,
                    response={"content": function_response_data}
                )
            )

        if response.candidates and response.candidates[0].content.parts[0].text:
            final_text = response.candidates[0].content.parts[0].text
            print(f"Gemini final response: '{final_text[:50]}...'")
            
            if "plot_path" in final_text:
                 try:
                    plot_data = json.loads(final_text)
                    if 'plot_path' in plot_data:
                         return {"plot_path": plot_data['plot_path']}
                 except json.JSONDecodeError:
                    pass
            
            return {"text": final_text}
        else:
            print(f"Warning: Agent did not return final text. Full response: {response}")
            return {"error": "Received invalid final response from Gemini."}

    except Exception as e:
        print(f"ERROR during agent conversation: {e}")
        print(traceback.format_exc())
        return {"error": f"Agent conversation failed: {e}"}

# --- Test function ---
async def _test_llm_connection():
    # ... (remains the same) ...
    print("\n--- Testing Simple Gemini Connection (No Tools) ---")
    simple_model = None
    try:
        # This will init _llm_model with tools, but we create a new simple one
        if not _initialize_vertex_ai():
             return
        simple_model = GenerativeModel(CHAT_MODEL_NAME) # No tools
        prompt = "Explain an exoplanet transit in one sentence."
        response = await simple_model.generate_content_async(prompt)
        if response and response.text:
             print(f"\nTest successful! Response received:\n{response.text}")
        else: print("\nTest failed! No response received.")
    except Exception as e:
        print(f"Test failed: {e}")
    print("---------------------------------")

if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    config.GCP_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    asyncio.run(_test_llm_connection())
