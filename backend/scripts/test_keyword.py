import asyncio
from app.elastic import es_client
import json # Import json at the top

INDEX_NAME = "planets"

async def check_mapping():
    # Ping is important, check connection first
    try:
        if not await es_client.ping():
            print("Connection failed")
            return
        print("Connection successful.") # Added success message
    except Exception as ping_err:
        print(f"Error pinging Elasticsearch: {ping_err}")
        # Attempt to close if ping fails but client exists
        try: await es_client.close()
        except: pass # Ignore errors during close after ping fail
        return

    # Get Mapping
    try:
        mapping_response = await es_client.indices.get_mapping(index=INDEX_NAME)
        print("\nMapping for 'planets' index:")
        # *** CORRECTED PRINTING: Convert response object to dict ***
        print(json.dumps(dict(mapping_response), indent=2))
        # *** END CORRECTION ***
    except Exception as e:
        print(f"Error getting mapping: {e}")
    finally:
        # Ensure client is closed
        try:
            if 'es_client' in locals() and hasattr(es_client, 'close'):
                 # Check if transport exists and is not already closed might be needed
                 # For simplicity, just try closing.
                 await es_client.close()
                 # print("Elastic client closed.") # Less verbose for just checking
        except Exception as close_err:
             print(f"Error closing Elastic client: {close_err}")

if __name__ == "__main__":
    asyncio.run(check_mapping())
