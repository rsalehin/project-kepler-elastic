import os
import pandas as pd
from astroquery.simbad import Simbad
from tqdm import tqdm

# --- Configuration ---
INPUT_PLANET_FILE = os.path.join("data", "nasa_exoplanets.csv")
OUTPUT_SIMBAD_FILE = os.path.join("data", "simbad_host_stars.csv")

# --- WORKING SIMBAD FIELDS ---
# Use bundles for complex measurements instead of individual fields
SIMBAD_FIELDS = [
    "sp",           # Spectral Type (basic field, already included by default)
    "otypes",       # Object Types
    "parallax",     # Bundle: adds plx_value, plx_err, plx_bibcode
    "velocity",     # Bundle: adds rvz_radvel, rvz_err, rvz_type, rvz_bibcode
    # Fluxes - these work as individual fields
    "U", "B", "V", "R", "I",
    "J", "H", "K"
]
# --- END FIELDS ---

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_PLANET_PATH = os.path.join(PROJECT_ROOT, INPUT_PLANET_FILE)
OUTPUT_SIMBAD_PATH = os.path.join(PROJECT_ROOT, OUTPUT_SIMBAD_FILE)

print(f"Reading host star names from: {INPUT_PLANET_PATH}")

try:
    planets_df = pd.read_csv(INPUT_PLANET_PATH, comment='#')
    host_star_names = planets_df['hostname'].unique()
    print(f"Found {len(host_star_names)} unique host star names.")
except FileNotFoundError:
    print(f"ERROR: Input file not found at {INPUT_PLANET_PATH}")
    exit()
except KeyError:
    print(f"ERROR: Could not find 'hostname' column in {INPUT_PLANET_PATH}")
    exit()

# Limit to first 10 stars for testing
# host_star_names = host_star_names[:10]
print(f"--- Limiting query to first {len(host_star_names)} stars for testing ---")

custom_simbad = Simbad()
custom_simbad.add_votable_fields(*SIMBAD_FIELDS)
custom_simbad.TIMEOUT = 120

print(f"Querying SIMBAD for {len(host_star_names)} stars...")

chunk_size = 100
all_results_list = []
failed_stars = []

for i in tqdm(range(0, len(host_star_names), chunk_size)):
    chunk = host_star_names[i:i + chunk_size]
    try:
        result_table = custom_simbad.query_objects(chunk)
        if result_table:
            all_results_list.extend([dict(row) for row in result_table])
        else:
            print(f"Warning: Query for chunk {chunk} returned no results.")
            failed_stars.extend(chunk)
    except Exception as e:
        print(f"\nERROR querying SIMBAD chunk for stars {chunk}: {e}")
        failed_stars.extend(chunk)

print(f"\nFinished querying SIMBAD.")
if failed_stars:
    print(f"Warning: Failed to retrieve data for {len(failed_stars)} stars: {failed_stars}")

if all_results_list:
    results_df = pd.DataFrame(all_results_list)
    # Rename MAIN_ID for clarity
    if 'MAIN_ID' in results_df.columns:
        results_df.rename(columns={'MAIN_ID': 'simbad_main_id'}, inplace=True)
    
    try:
        results_df.to_csv(OUTPUT_SIMBAD_PATH, index=False, encoding='utf-8')
        print(f"Successfully saved data for {len(results_df)} stars to '{OUTPUT_SIMBAD_PATH}'")
        print(f"\nColumns retrieved: {list(results_df.columns)}")
    except Exception as e:
        print(f"ERROR saving results to CSV: {e}")
else:
    print("No results retrieved from SIMBAD. Output file not created.")
