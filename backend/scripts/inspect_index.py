import asyncio
from app.elastic import es_client # Our async client
import json

# --- Configuration ---
INDEX_NAME = "planets"

# --- Main Async Function ---
async def inspect_index():
    print(f"Checking connection to Elastic...")
    try:
        if not await es_client.ping():
            print("ERROR: Connection to Elasticsearch failed.")
            return
        print(f"Connection successful.")
    except Exception as ping_err:
        print(f"ERROR pinging Elasticsearch: {ping_err}")
        return # Exit if ping fails

    # --- 1. Count Documents ---
    try:
        count_response = await es_client.count(index=INDEX_NAME)
        doc_count = count_response.get('count', 0)
        print(f"\n--- Document Count ---")
        print(f"Index '{INDEX_NAME}' contains {doc_count} documents.")
        print("-" * 20)
        if doc_count == 0:
            print("Index is empty. Ingestion likely failed or targeted the wrong index.")
            return # No point sampling if empty
    except Exception as e:
        print(f"ERROR counting documents: {e}")
        return # Exit if count fails

    # --- 2. Retrieve Sample Documents ---
    try:
        print(f"\n--- Sample Documents (First 2) ---")
        # Search without a query, asking for 2 documents
        search_response = await es_client.search(
            index=INDEX_NAME,
            size=2 # Get 2 documents
            # No 'query' means match all
        )

        if search_response and 'hits' in search_response and 'hits' in search_response['hits']:
            hits = search_response['hits']['hits']
            if not hits:
                print("No documents found, although count reported > 0 (this is unexpected).")
            else:
                for i, hit in enumerate(hits):
                    print(f"\nDocument {i+1} (ID: {hit.get('_id', 'N/A')}):")
                    # Pretty print the '_source' field (the actual data)
                    print(json.dumps(hit.get('_source', {}), indent=2))
        else:
            print("Error retrieving sample documents or response format unexpected.")
        print("-" * 26)

    except Exception as e:
        print(f"ERROR retrieving sample documents: {e}")

    finally:
        # --- Cleanup ---
        try:
            if 'es_client' in locals() and hasattr(es_client, 'close'):
                 await es_client.close()
                 print("\nElastic client closed.")
        except Exception as close_err:
             print(f"Error closing Elastic client: {close_err}")

# --- Run the async function ---
if __name__ == "__main__":
    asyncio.run(inspect_index())
