import asyncio
import os
import pandas as pd
from elasticsearch import helpers
from app.elastic import es_client
from tqdm import tqdm
import time
import google.auth
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from vertexai.preview.language_models import TextEmbeddingModel
import numpy as np # Import numpy for type checking

# --- Configuration ---
# ... (Config remains the same) ...
INPUT_ARXIV_FILE = os.path.join("data", "arxiv_abstracts.csv")
INDEX_NAME = "planets"
CHUNK_SIZE = 50
GCP_PROJECT_ID = "project-kepler-elastic"
GCP_LOCATION = "us-central1"
EMBEDDING_MODEL_NAME = "gemini-embedding-001"

# --- Determine project root ---
# ... (Path setup remains the same) ...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_ARXIV_PATH = os.path.join(PROJECT_ROOT, INPUT_ARXIV_FILE)

print("Starting arXiv ingestion process...")

# --- Initialize Vertex AI Client ---
# ... (Remains the same) ...
try:
    print(f"Initializing Vertex AI client for project '{GCP_PROJECT_ID}' in '{GCP_LOCATION}'...")
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
    print("Vertex AI client and embedding model initialized.")
except Exception as e:
    print(f"ERROR: Failed to initialize Vertex AI client/model: {e}")
    exit()

# --- Read Input File ---
# ... (Reading CSV remains the same) ...
try:
    print(f"Reading arXiv abstracts from: {INPUT_ARXIV_PATH}")
    df = pd.read_csv(INPUT_ARXIV_PATH).fillna('')
    print(f"Read {len(df)} abstracts.")
except FileNotFoundError:
    print(f"ERROR: arXiv data file not found at {INPUT_ARXIV_PATH}")
    exit()

# --- Prepare Data & Generate Embeddings ---
# ... (get_embeddings function remains the same) ...
def get_embeddings(texts: list[str]) -> list[list[float]] | None:
    try:
        # *** ADD output_dimensionality parameter ***
        response = embedding_model.get_embeddings(
            texts,
            output_dimensionality=768  # Match your Elasticsearch mapping
        )
        embeddings = [embedding.values for embedding in response]
        if len(embeddings) != len(texts):
             print(f"Warning: Mismatch in embedding count ({len(embeddings)}) vs text count ({len(texts)})")
             return None
        return embeddings
    except Exception as e:
        print(f"\nERROR calling Vertex AI embedding API ({type(e).__name__}): {e}")
        time.sleep(2)
        return None



# *** UPDATED generate_arxiv_actions ***
def generate_arxiv_actions(dataframe, index_name):
    print("\nGenerating actions and embeddings...")
    progress = tqdm(total=len(dataframe), unit="docs", desc="Embedding/Generating Actions")
    
    for i in range(0, len(dataframe), CHUNK_SIZE):
        chunk_df = dataframe.iloc[i:i + CHUNK_SIZE].copy()
        abstract_texts = chunk_df['abstract'].tolist()
        embeddings = get_embeddings(abstract_texts)

        if embeddings is not None and len(embeddings) == len(chunk_df):
            # Process each row with its corresponding embedding
            for (index, row), embedding in zip(chunk_df.iterrows(), embeddings):
                doc_clean = {}
                
                for key, value in row.items():
                    # Handle different data types
                    if pd.isna(value) or value is pd.NA or value is pd.NaT:
                        doc_clean[key] = None
                    elif isinstance(value, pd.Timestamp):
                        doc_clean[key] = value.isoformat()
                    elif isinstance(value, (np.integer, int)):
                        doc_clean[key] = int(value)
                    elif isinstance(value, (np.floating, float)):
                        try:
                            if np.isnan(value) or np.isinf(value):
                                doc_clean[key] = None
                            else:
                                doc_clean[key] = float(value)
                        except (TypeError, ValueError):
                            doc_clean[key] = None
                    elif isinstance(value, (np.bool_, bool)):
                        doc_clean[key] = bool(value)
                    else:
                        doc_clean[key] = value
                
                # Add the embedding as a list
                doc_clean['abstract_vector'] = embedding if isinstance(embedding, list) else list(embedding)

                progress.update(1)
                yield {
                    "_index": index_name,
                    "_id": doc_clean.get("arxiv_id", f"row_{index}"),
                    "_source": doc_clean,
                }
        else:
            print(f"Skipping chunk starting at index {i} due to embedding error.")
            progress.update(len(chunk_df))
    
    progress.close()
    print("\nFinished generating actions and embeddings.")

# --- Main Async Function (ingest_arxiv_data) remains the same ---
# ... (Includes connection check, bulk ingest loop, final print messages, finally block) ...
async def ingest_arxiv_data():
    print(f"Checking connection to Elastic...")
    if not await es_client.ping():
        print("ERROR: Connection to Elasticsearch failed.")
        return
    print(f"Connection successful.")

    print(f"Starting bulk ingestion of {len(df)} arXiv abstracts with embeddings...")
    print(f"(Using chunk size: {CHUNK_SIZE})")

    try:
        success_count = 0
        fail_count = 0
        action_generator = generate_arxiv_actions(df, INDEX_NAME)
        ingest_progress = tqdm(total=len(df), unit="docs", desc="Ingesting Abstracts")

        async for ok, action in helpers.async_streaming_bulk(
            client=es_client,
            actions=action_generator,
            chunk_size=CHUNK_SIZE,
            raise_on_error=False,
            request_timeout=120
            ):
            if ok:
                success_count += 1
            else:
                fail_count += 1
                error_info = action.get('index', {}).get('error', {})
                doc_id_info = action.get('index', {}).get('_id', 'N/A')
                reason = error_info.get('reason', 'Unknown reason')
                print(f"\nFailed action (Doc ID: {doc_id_info}): Type={error_info.get('type')} Reason={reason}")
            ingest_progress.update(1)

        ingest_progress.close()
        print(f"\nBulk ingestion finished.")
        print(f"Successfully ingested/updated: {success_count} documents.")
        print(f"Failed actions: {fail_count}")

    except Exception as e:
        print(f"\nERROR during bulk ingestion: {e}")
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Stopping ingestion.")
    finally:
        try:
            if 'es_client' in locals() and hasattr(es_client, 'close'):
                 await es_client.close()
                 print("Elastic client closed.")
        except Exception as close_err:
             print(f"Error closing Elastic client: {close_err}")

# --- Run the async function ---
if __name__ == "__main__":
    asyncio.run(ingest_arxiv_data())
