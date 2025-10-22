import asyncio
from app.elastic import es_client # Import our pre-configured async client
from elasticsearch import helpers # For helper functions

# --- Configuration ---
INDEX_NAME = "planets" # The name for our Elasticsearch index

# --- Index Mapping Definition ---
# This defines the 'schema' for our data in Elasticsearch
# We specify data types for key fields. Others will be dynamically mapped.
# 'keyword' is for exact matches (like IDs, categories)
# 'text' is for full-text search (like names, abstracts)
# 'float', 'integer', 'date' are for numerical/date fields
INDEX_MAPPING = {
    "properties": {
        # --- Planet Fields (Examples) ---
        "pl_name": {"type": "keyword"}, # Planet Name (exact match often useful)
        "hostname": {"type": "keyword"}, # Host Star Name (exact match)
        "discoverymethod": {"type": "keyword"},
        "disc_year": {"type": "integer"},
        "pl_orbper": {"type": "float"}, # Orbital Period (days)
        "pl_masse": {"type": "float"}, # Planet Mass (Earth Mass)
        "pl_rade": {"type": "float"}, # Planet Radius (Earth Radius)
        "sy_dist": {"type": "float"}, # Distance (parsecs)

        # --- Star Fields (Examples from SIMBAD, prefixed with 'star_') ---
        "star_simbad_main_id": {"type": "keyword"},
        "star_sp_type": {"type": "keyword"}, # Spectral Type
        "star_plx_value": {"type": "float"}, # Parallax
        "star_rvz_radvel": {"type": "float"}, # Radial Velocity
        "star_fe_h": {"type": "float"}, # Metallicity

        # --- arXiv Fields (Placeholders for later) ---
        "arxiv_id": {"type": "keyword"},
        "title": {"type": "text", "analyzer": "standard"},
        "abstract": {"type": "text", "analyzer": "standard"},
        "published_date": {"type": "date"},

        # --- Vector Field (Placeholder for later embedding task) ---
        # "abstract_vector": {
        #     "type": "dense_vector",
        #     "dims": 768, # Dimension depends on embedding model
        #     "index": True,
        #     "similarity": "cosine"
        # }
    }
}

# --- Main Async Function ---
async def create_index():
    print(f"Checking connection to Elastic...")
    if not await es_client.ping():
        print("ERROR: Connection to Elasticsearch failed.")
        return

    print(f"Connection successful.")

    # Check if index already exists
    if await es_client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists. Deleting it...")
        try:
            await es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])
            print(f"Index '{INDEX_NAME}' deleted.")
        except Exception as e:
            print(f"ERROR deleting index: {e}")
            return

    # Create the new index with the specified mapping
    print(f"Creating index '{INDEX_NAME}' with mapping...")
    try:
        await es_client.indices.create(
            index=INDEX_NAME,
            mappings=INDEX_MAPPING,
            ignore=[400, 404] # Ignore error if index already exists (race condition)
        )
        print(f"Index '{INDEX_NAME}' created successfully.")
    except Exception as e:
        print(f"ERROR creating index: {e}")
    finally:
        # Always close the client connection when done
        await es_client.close()
        print("Elastic client closed.")


# --- Run the async function ---
if __name__ == "__main__":
    asyncio.run(create_index())
