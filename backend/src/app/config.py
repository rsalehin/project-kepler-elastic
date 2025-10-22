import os
from dotenv import load_dotenv, find_dotenv

# Load .env file from project root
dotenv_path = find_dotenv()
if dotenv_path:
    print(f"Loading .env file from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("Warning: .env file not found.")

# Elastic Config (already used by app/elastic.py)
ELASTIC_HOSTS = os.environ.get("ELASTIC_HOSTS")
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY")

# Google Cloud Config
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "project-kepler-elastic") # Allow override via env
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1") # Allow override
GCP_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# --- Credential Check ---
# Check if the GCP credentials path exists and is set
if GCP_CREDENTIALS_PATH and os.path.exists(GCP_CREDENTIALS_PATH):
    print(f"Google Cloud credentials found at: {GCP_CREDENTIALS_PATH}")
    # The google-cloud libraries automatically use GOOGLE_APPLICATION_CREDENTIALS
else:
    print("---------------------------------------------------------")
    print("WARNING: GOOGLE_APPLICATION_CREDENTIALS path not found!")
    print(f"  -> Path set in env var: {GCP_CREDENTIALS_PATH}")
    print("  -> Ensure .env file is in project root and contains:")
    print("     GOOGLE_APPLICATION_CREDENTIALS=\"<absolute_path_to_key.json>\"")
    print("  -> Or ensure the environment variable is set manually.")
    print("---------------------------------------------------------")
    # Decide if you want to raise an error or just warn:
    # raise ValueError("GCP Credentials not configured correctly.")

# Embedding Model Config (can add Gemini chat model later)
EMBEDDING_MODEL_NAME = "gemini-embedding-001"

print("Configuration loaded.")
