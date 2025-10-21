import os
from dotenv import load_dotenv, find_dotenv
from elasticsearch import AsyncElasticsearch # Use the ASYNC client

# Find and load the .env file from the project root
# (find_dotenv searches upwards from the current file)
load_dotenv(find_dotenv())

# Load credentials from environment variables (set by load_dotenv)
HOSTS = os.environ.get("ELASTIC_HOSTS")
API_KEY = os.environ.get("ELASTIC_API_KEY")

# Check if secrets were loaded correctly
if not HOSTS or not API_KEY:
    # This error helps debug if .env is missing or variables are named wrong
    raise ValueError("ELASTIC_HOSTS and ELASTIC_API_KEY must be set in the .env file")

# Create the globally accessible Elasticsearch client instance
# Use the 'hosts' parameter for the URL list
es_client = AsyncElasticsearch(
    hosts=[HOSTS],
    api_key=API_KEY
)

print("Elastic client initialized.") # Optional: Confirmation message
