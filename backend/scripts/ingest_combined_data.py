import asyncio
import os
import pandas as pd
from elasticsearch import helpers
from app.elastic import es_client
from tqdm import tqdm
import numpy as np

# --- Configuration ---
INPUT_COMBINED_FILE = os.path.join("data", "combined_planet_star_data.csv")
INDEX_NAME = "planets"
CHUNK_SIZE = 500

# --- Determine project root ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_COMBINED_PATH = os.path.join(PROJECT_ROOT, INPUT_COMBINED_FILE)

print("Starting data ingestion process...")

# --- Read Input File ---
try:
    print(f"Reading combined data from: {INPUT_COMBINED_PATH}")
    df = pd.read_csv(INPUT_COMBINED_PATH, comment='#', low_memory=False)
    print(f"Read {len(df)} records.")
except FileNotFoundError:
    print(f"ERROR: Combined data file not found at {INPUT_COMBINED_PATH}")
    exit()

# --- DATA CLEANING ---
print("Cleaning data types...")
numeric_cols = [
    'pl_orbper', 'pl_masse', 'pl_rade', 'sy_dist',
    'star_plx_value', 'star_rvz_radvel', 'star_fe_h',
    'star_U', 'star_B', 'star_V', 'star_R', 'star_I',
    'star_J', 'star_H', 'star_K'
]
integer_cols = ['disc_year']
date_cols = ['pl_pubdate', 'releasedate']

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

for col in integer_cols:
     if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

print("Cleaning date fields...")
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        print(f"  Cleaned date column: {col}")
    else:
        print(f"  Warning: Expected date column '{col}' not found.")

print("Finished cleaning data types.")
# --- END DATA CLEANING ---

# --- Prepare Data for Bulk Ingest ---
def generate_actions(dataframe, index_name):
    print("\nGenerating actions for bulk ingest...")
    total_rows = len(dataframe)
    progress = tqdm(total=total_rows, unit="docs", desc="Generating Actions")
    for index, row in dataframe.iterrows():
        doc_raw = row.to_dict()
        doc_clean = {}
        for key, value in doc_raw.items():
            if pd.isna(value):
                doc_clean[key] = None
            elif isinstance(value, pd.Timestamp):
                 doc_clean[key] = value.isoformat()
            else:
                doc_clean[key] = value
        progress.update(1)
        yield {
            "_index": index_name,
            "_source": doc_clean,
        }
    progress.close()
    print("\nFinished generating actions.")

# --- Main Async Function ---
async def ingest_data():
    print(f"Checking connection to Elastic...")
    if not await es_client.ping():
        print("ERROR: Connection to Elasticsearch failed.")
        return
    print(f"Connection successful.")

    print(f"Starting FULL bulk ingestion of {len(df)} documents into index '{INDEX_NAME}'...")
    print(f"(Using chunk size: {CHUNK_SIZE})")

    try:
        success_count = 0
        fail_count = 0
        action_generator = generate_actions(df, INDEX_NAME)
        progress = tqdm(total=len(df), unit="docs", desc="Ingesting")

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
            progress.update(1)

        progress.close()
        print(f"\nBulk ingestion finished.")
        print(f"Successfully ingested: {success_count} documents.")
        print(f"Failed actions: {fail_count}")

    except Exception as e:
        print(f"\nERROR during bulk ingestion: {e}")
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Stopping ingestion.")
    finally:
        # --- SIMPLIFIED CLEANUP ---
        try:
            # Check if client object exists and has close method
            if 'es_client' in locals() and hasattr(es_client, 'close'):
                 await es_client.close()
                 print("Elastic client closed.")
        except Exception as close_err:
             print(f"Error closing Elastic client: {close_err}")
        # --- END SIMPLIFIED CLEANUP ---

# --- Run the async function ---
if __name__ == "__main__":
    asyncio.run(ingest_data())
