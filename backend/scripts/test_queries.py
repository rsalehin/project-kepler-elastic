import asyncio
from app.elastic import es_client # Our async client
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import os
import json

# --- Configuration ---
INDEX_NAME = "planets"
EXPECTED_EMBEDDING_DIM = 768

# --- Google Cloud Vertex AI Configuration ---
GCP_PROJECT_ID = "project-kepler-elastic"
GCP_LOCATION = "us-central1"
EMBEDDING_MODEL_NAME = "gemini-embedding-001"

# --- Sample Queries ---
# *** ADJUST THIS to match the EXACT case in your CSV if different ***
KEYWORD_QUERY_PLANET_NAME = "TRAPPIST-1 e"
# *** END ADJUST ***
VECTOR_QUERY_TEXT = "finding water on rocky exoplanets"
HYBRID_PLANET_NAME = "TRAPPIST-1 e" # Check case for this too if needed
HYBRID_QUERY_TEXT = "potential habitability indicators"

# --- Initialize Vertex AI Client ---
# ... (Remains the same) ...
try:
    print(f"Initializing Vertex AI client for project '{GCP_PROJECT_ID}' in '{GCP_LOCATION}'...")
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
    print("Vertex AI client and embedding model initialized.")
except Exception as e:
    print(f"ERROR: Failed to initialize Vertex AI client/model: {e}")
    embedding_model = None

# --- Helper to print results ---
# ... (Remains the same) ...
def print_results(title, response):
    print(f"\n--- {title} ---")
    if response and 'hits' in response and 'hits' in response['hits']:
        hits = response['hits']['hits']
        print(f"Found {len(hits)} results:")
        for i, hit in enumerate(hits[:3]): # Print top 3
            score = hit.get('_score', 'N/A')
            source = hit.get('_source', {})
            name = source.get('pl_name') or source.get('title') or hit.get('_id')
            try: score_str = f"{float(score):.4f}"
            except: score_str = str(score)
            print(f"  {i+1}. Score: {score_str} | Name/ID: {name}")
    else:
        print("No results found or error in response.")
    print("-" * (len(title) + 6))

# --- Main Async Function ---
async def run_queries():
    print(f"\nChecking connection to Elastic...")
    if not await es_client.ping():
        print("ERROR: Connection to Elasticsearch failed.")
        return
    print(f"Connection successful.")

    # --- 1. Keyword Search (Exact Case) ---
    print(f"\nRunning Keyword Search (Exact Case) for planet: '{KEYWORD_QUERY_PLANET_NAME}'")
    try:
        response_kw = await es_client.search(
            index=INDEX_NAME,
            query={
                "term": {
                    "pl_name.keyword": KEYWORD_QUERY_PLANET_NAME # Uses .keyword field
                }
            }
        )
        print_results(f"Keyword Search Results (Exact) for '{KEYWORD_QUERY_PLANET_NAME}'", response_kw)
    except Exception as e:
        print(f"ERROR during exact keyword search: {e}")

    # --- 1b. Keyword Search (Case Insensitive) ---
    print(f"\nRunning Keyword Search (Case Insensitive) for planet: '{KEYWORD_QUERY_PLANET_NAME.lower()}'")
    try:
        response_kw_ci = await es_client.search(
            index=INDEX_NAME,
            query={
                "term": {
                     # Still use .keyword, but add case_insensitive flag
                    "pl_name.keyword": {
                         "value": KEYWORD_QUERY_PLANET_NAME.lower(), # Often better to lowercase query
                         "case_insensitive": True
                    }
                }
            }
        )
        print_results(f"Keyword Search Results (Case Insensitive) for '{KEYWORD_QUERY_PLANET_NAME.lower()}'", response_kw_ci)
    except Exception as e:
        print(f"ERROR during case-insensitive keyword search: {e}")


    # --- 2. Vector Search ---
    # ... (Remains the same, uses output_dimensionality) ...
    if embedding_model:
        print(f"\nRunning Vector Search for text: '{VECTOR_QUERY_TEXT}'")
        try:
            query_vector_response = embedding_model.get_embeddings(
                [VECTOR_QUERY_TEXT],
                output_dimensionality=EXPECTED_EMBEDDING_DIM
            )
            query_vector = query_vector_response[0].values
            print(f"  (Generated query vector dimension: {len(query_vector)})")

            response_vec = await es_client.search(
                index=INDEX_NAME,
                knn={
                    "field": "abstract_vector",
                    "query_vector": query_vector,
                    "k": 5, "num_candidates": 50
                },
                 _source=["arxiv_id", "title"]
            )
            print_results(f"Vector Search Results for '{VECTOR_QUERY_TEXT}'", response_vec)
        except Exception as e:
            print(f"ERROR during vector search: {e}")
    else:
        print("\nSkipping Vector Search - embedding model error.")

    # --- 3. Hybrid Search ---
    # ... (Remains the same, uses output_dimensionality) ...
    if embedding_model:
        print(f"\nRunning Hybrid Search for planet '{HYBRID_PLANET_NAME}' & text '{HYBRID_QUERY_TEXT}'")
        try:
            hybrid_vector_response = embedding_model.get_embeddings(
                [HYBRID_QUERY_TEXT],
                output_dimensionality=EXPECTED_EMBEDDING_DIM
            )
            hybrid_vector = hybrid_vector_response[0].values
            print(f"  (Generated hybrid query vector dimension: {len(hybrid_vector)})")

            response_hyb = await es_client.search(
                index=INDEX_NAME,
                query={ "term": { "pl_name.keyword": HYBRID_PLANET_NAME } }, # Assumes HYBRID_PLANET_NAME case is correct
                knn={
                    "field": "abstract_vector",
                    "query_vector": hybrid_vector,
                    "k": 5, "num_candidates": 50,
                },
                 _source=["arxiv_id", "title", "pl_name"]
            )
            print_results(f"Hybrid Search Results for '{HYBRID_PLANET_NAME}' + '{HYBRID_QUERY_TEXT}'", response_hyb)
        except Exception as e:
            print(f"ERROR during hybrid search: {e}")
    else:
         print("\nSkipping Hybrid Search - embedding model error.")

    # --- Cleanup ---
    # ... (Remains the same) ...
    try:
        if 'es_client' in locals() and hasattr(es_client, 'close'):
             await es_client.close()
             print("\nElastic client closed.")
    except Exception as close_err:
         print(f"Error closing Elastic client: {close_err}")

# --- Run the async function ---
if __name__ == "__main__":
    asyncio.run(run_queries())
