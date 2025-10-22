import asyncio
# from app.elastic import es_client # <-- REMOVE THIS LINE
from elasticsearch import AsyncElasticsearch # Keep this for type hinting
from vertexai.language_models import TextEmbeddingModel
import src.app.config as config
import json
import traceback
import os
import uuid
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend (IMPORTANT!)
import matplotlib.pyplot as plt
import pandas as pd

# --- Configuration (from config or define here) ---
INDEX_NAME = "planets"
EMBEDDING_MODEL_NAME = config.EMBEDDING_MODEL_NAME
EXPECTED_EMBEDDING_DIM = 768
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# --- Initialize Embedding Model (remains the same) ---
_embedding_model = None
def _initialize_embedding_model():
    global _embedding_model
    if _embedding_model is not None: return True
    try:
        _embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
        return True
    except Exception as e:
        print(f"ERROR: Failed to load embedding model in tools.py: {e}")
        _embedding_model = None
        return False

# --- Search Tool Function (remains the same) ---
async def search_elastic(
    es_client: AsyncElasticsearch, # Argument is correct
    text_query: str,
    keyword_filter_field: str | None = None,
    keyword_filter_value: str | None = None
) -> str:
    # ... (code from previous step, no changes) ...
    print(f"\n--- Running Elastic Search Tool ---")
    print(f"  Text Query: '{text_query}'")
    print(f"  Keyword Filter: {keyword_filter_field} = '{keyword_filter_value}'")
    if not _initialize_embedding_model():
        return json.dumps({"error": "Embedding model not available."})
    try:
        query_vector_response = _embedding_model.get_embeddings(
            [text_query], output_dimensionality=EXPECTED_EMBEDDING_DIM
        )
        query_vector = query_vector_response[0].values
    except Exception as e:
        print(f"ERROR getting query embedding: {e}")
        return json.dumps({"error": f"Failed to get embedding: {e}"})
    search_payload = {
        "knn": { "field": "abstract_vector", "query_vector": query_vector, "k": 5, "num_candidates": 50 },
        "_source": ["pl_name", "hostname", "arxiv_id", "title", "abstract", "published_date"]
    }
    if keyword_filter_field and keyword_filter_value:
        search_payload["query"] = {
            "term": { keyword_filter_field: { "value": keyword_filter_value, "case_insensitive": True } }
        }
        print(f"  Applied keyword filter.")
    try:
        print(f"  Executing ES search...")
        response = await es_client.search( index=INDEX_NAME, **search_payload )
        print(f"  ES search completed. Found {response['hits']['total']['value']} total potential hits.")
        results = response.get('hits', {}).get('hits', [])
        formatted_results = []
        for hit in results[:5]:
             formatted_results.append({ "score": hit.get('_score'), "id": hit.get('_id'), "source": hit.get('_source') })
        print(f"--- Elastic Search Tool Finished (Returning {len(formatted_results)} results) ---")
        return json.dumps(formatted_results)
    except Exception as e:
        print(f"ERROR during Elasticsearch search: {e}")
        print(traceback.format_exc())
        return json.dumps({"error": f"Elasticsearch query failed: {e}"})

# --- Plotting Tool Function (remains the same) ---
async def plot_planet_comparison(
    es_client: AsyncElasticsearch,
    planet_names: list[str],
    x_property: str,
    y_property: str
) -> str:
    # ... (code from previous step, no changes) ...
    print(f"\n--- Running Plotting Tool ---")
    print(f"  Planets: {planet_names}")
    print(f"  X-Axis: {x_property}, Y-Axis: {y_property}")
    if not planet_names:
        return json.dumps({"error": "No planet names provided for plotting."})
    try:
        query = { "terms": { "pl_name.keyword": [name.lower() for name in planet_names] } }
        fields_to_fetch = ["pl_name", x_property, y_property]
        response = await es_client.search(
            index=INDEX_NAME, query=query, _source=fields_to_fetch, size=len(planet_names)
        )
        hits = response.get('hits', {}).get('hits', [])
        if not hits:
            return json.dumps({"error": "Could not find data for the requested planets."})
        data = []
        for hit in hits:
            source = hit.get('_source', {})
            if source.get(x_property) is not None and source.get(y_property) is not None:
                data.append({ "name": source.get("pl_name"), "x": source.get(x_property), "y": source.get(y_property) })
        if not data:
            return json.dumps({"error": f"Found planets, but none had valid data for '{x_property}' and '{y_property}'."})
        print(f"  Found data for {len(data)} planets.")
        df = pd.DataFrame(data)
        plt.figure(figsize=(10, 6))
        plt.scatter(df['x'], df['y'])
        for i, row in df.iterrows():
            plt.annotate(row['name'], (row['x'], row['y']), xytext=(5,5), textcoords='offset points')
        plt.title(f"Planet Comparison: {y_property} vs. {x_property}")
        plt.xlabel(x_property)
        plt.ylabel(y_property)
        plt.grid(True)
        filename = f"plot_{uuid.uuid4()}.png"
        save_path = os.path.join(STATIC_DIR, filename) 
        plt.savefig(save_path)
        plt.close()
        print(f"  Plot saved to: {save_path}")
        web_path = f"/static/{filename}"
        return json.dumps({"plot_path": web_path})
    except Exception as e:
        print(f"ERROR during plotting: {e}")
        print(traceback.format_exc())
        return json.dumps({"error": f"Plotting failed: {e}"})

# --- Test function (remains the same) ---
async def _test_plotting_tool():
    print("Please test plotting via pytest: pytest -v -k test_plot_planet_comparison")

if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    config.GCP_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    asyncio.run(_test_plotting_tool())
