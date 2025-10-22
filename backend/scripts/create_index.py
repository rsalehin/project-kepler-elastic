import asyncio
from app.elastic import es_client # Import our pre-configured async client
from elasticsearch import helpers

# --- Configuration ---
INDEX_NAME = "planets"
# <<< NEW: Specify embedding dimension >>>
EMBEDDING_DIM = 768 # For textembedding-gecko models

# --- Index Mapping Definition ---
INDEX_MAPPING = {
    "properties": {
        # --- Planet Fields ---
        "pl_name": {"type": "keyword"},
        "hostname": {"type": "keyword"},
        "discoverymethod": {"type": "keyword"},
        "disc_year": {"type": "integer"},
        "pl_orbper": {"type": "float"},
        "pl_masse": {"type": "float"},
        "pl_rade": {"type": "float"},
        "sy_dist": {"type": "float"},

        # --- Star Fields ---
        "star_simbad_main_id": {"type": "keyword"},
        "star_sp_type": {"type": "keyword"},
        "star_plx_value": {"type": "float"},
        "star_rvz_radvel": {"type": "float"},
        "star_fe_h": {"type": "float"},
        # Add other star fields if needed, or rely on dynamic mapping

        # --- arXiv Fields ---
        "arxiv_id": {"type": "keyword"},
        "title": {"type": "text", "analyzer": "standard"},
        "abstract": {"type": "text", "analyzer": "standard"},
        "published_date": {"type": "date"},

        # --- <<< NEW: Vector Field Definition >>> ---
        "abstract_vector": {
            "type": "dense_vector",
            "dims": EMBEDDING_DIM, # Use the configured dimension
            "index": True,         # Make the vector searchable
            "similarity": "cosine" # Use cosine similarity for search
        }
        # --- <<< END VECTOR FIELD >>> ---
    }
}

# --- Main Async Function ---
async def create_index():
    print(f"Checking connection to Elastic...")
    if not await es_client.ping():
        print("ERROR: Connection to Elasticsearch failed.")
        return
    print(f"Connection successful.")

    # Always delete existing index to ensure mapping is updated
    print(f"Checking if index '{INDEX_NAME}' exists...")
    if await es_client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' exists. Deleting it to apply new mapping...")
        try:
            await es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])
            print(f"Index '{INDEX_NAME}' deleted.")
        except Exception as e:
            print(f"ERROR deleting index: {e}")
            # Optional: Decide whether to proceed if deletion fails
            # return
    else:
        print(f"Index '{INDEX_NAME}' does not exist.")

    # Create the new index with the specified mapping
    print(f"Creating index '{INDEX_NAME}' with updated mapping (including vector field)...")
    try:
        await es_client.indices.create(
            index=INDEX_NAME,
            mappings=INDEX_MAPPING,
            ignore=[400] # Ignore only 'resource_already_exists_exception'
        )
        print(f"Index '{INDEX_NAME}' created/updated successfully.")
    except Exception as e:
        print(f"ERROR creating index: {e}")
    finally:
        try:
            if 'es_client' in locals() and hasattr(es_client, 'close'):
                 await es_client.close()
                 print("Elastic client closed.")
        except Exception as close_err:
             print(f"Error closing Elastic client: {close_err}")

# --- Run the async function ---
if __name__ == "__main__":
    asyncio.run(create_index())
