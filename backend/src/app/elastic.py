import os
from dotenv import load_dotenv, find_dotenv
# REMOVED: from elasticsearch import AsyncElasticsearch

# Find and load the .env file from the project root
load_dotenv(find_dotenv())

# Load credentials from environment variables
HOSTS = os.environ.get("ELASTIC_HOSTS")
API_KEY = os.environ.get("ELASTIC_API_KEY")

# Check if secrets were loaded correctly
if not HOSTS or not API_KEY:
    raise ValueError("ELASTIC_HOSTS and ELASTIC_API_KEY must be set in the .env file")

# REMOVED: es_client = AsyncElasticsearch(...)
# Just print confirmation that config is loaded
print("Elastic config loaded (HOSTS and API_KEY). Client is created on demand.")
