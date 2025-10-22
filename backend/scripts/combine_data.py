import os
import pandas as pd

# --- Configuration ---
# Input files relative to project root
INPUT_PLANET_FILE = os.path.join("data", "nasa_exoplanets.csv")
INPUT_SIMBAD_FILE = os.path.join("data", "simbad_host_stars.csv") # The file we just created
# Output file relative to project root
OUTPUT_COMBINED_FILE = os.path.join("data", "combined_planet_star_data.csv")

# --- Determine project root from script location ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_PLANET_PATH = os.path.join(PROJECT_ROOT, INPUT_PLANET_FILE)
INPUT_SIMBAD_PATH = os.path.join(PROJECT_ROOT, INPUT_SIMBAD_FILE)
OUTPUT_COMBINED_PATH = os.path.join(PROJECT_ROOT, OUTPUT_COMBINED_FILE)

print("Starting data combination process...")

# --- Read Input Files ---
try:
    print(f"Reading planets from: {INPUT_PLANET_PATH}")
    planets_df = pd.read_csv(INPUT_PLANET_PATH, comment='#')
    print(f"Read {len(planets_df)} planet entries.")
except FileNotFoundError:
    print(f"ERROR: Planet file not found at {INPUT_PLANET_PATH}")
    exit()

try:
    print(f"Reading SIMBAD star data from: {INPUT_SIMBAD_PATH}")
    # Important: Ensure the 'simbad_main_id' is read as string to preserve formatting
    simbad_df = pd.read_csv(INPUT_SIMBAD_PATH, dtype={'simbad_main_id': str})
    print(f"Read {len(simbad_df)} SIMBAD entries.")
except FileNotFoundError:
    print(f"ERROR: SIMBAD file not found at {INPUT_SIMBAD_PATH}")
    print("Please run the download_simbad.py script first.")
    exit()

# --- Prepare for Merge ---
# Rename planet host name column for clarity before merge
planets_df.rename(columns={'hostname': 'query_target_star'}, inplace=True)

# SIMBAD query might return multiple entries per star name query.
# We need to decide how to handle this. Simplest for MVP: drop duplicates based on the star name used for query.
# NOTE: This assumes 'user_specified_id' reliably contains the name we queried with. Check CSV output if issues.
if 'user_specified_id' in simbad_df.columns:
    print(f"SIMBAD df initial size: {len(simbad_df)}")
    simbad_df_unique = simbad_df.drop_duplicates(subset=['user_specified_id'], keep='first')
    print(f"SIMBAD df size after dropping duplicates by 'user_specified_id': {len(simbad_df_unique)}")
    # Prepare the join column in SIMBAD data
    simbad_df_unique.rename(columns={'user_specified_id': 'query_target_star'}, inplace=True)
    join_column = 'query_target_star'
else:
    print("Warning: 'user_specified_id' column not found in SIMBAD data. Cannot reliably deduplicate based on query name.")
    # Fallback or alternative join strategy needed if this happens
    # For now, let's try joining on simbad_main_id if it exists, though it might not match hostname perfectly
    if 'simbad_main_id' in simbad_df.columns:
         print("Attempting to join on 'simbad_main_id' as fallback.")
         planets_df.rename(columns={'query_target_star': 'simbad_main_id'}, inplace=True) # Risky rename
         simbad_df_unique = simbad_df.drop_duplicates(subset=['simbad_main_id'], keep='first')
         join_column = 'simbad_main_id'
    else:
        print("ERROR: Cannot determine join column for SIMBAD data.")
        exit()


# --- Merge DataFrames ---
print(f"Merging planet data with star data on column: '{join_column}'...")
# Use 'left' merge to keep all planets, even if star data is missing
combined_df = pd.merge(planets_df, simbad_df_unique, on=join_column, how='left')
print(f"Merge complete. Resulting table has {len(combined_df)} rows and {len(combined_df.columns)} columns.")

# Optional: Add prefix to SIMBAD columns to avoid name collisions
simbad_cols = [col for col in simbad_df_unique.columns if col != join_column]
col_rename_map = {col: f"star_{col}" for col in simbad_cols}
combined_df.rename(columns=col_rename_map, inplace=True)
print("Renamed SIMBAD columns with 'star_' prefix.")

# --- Save Combined File ---
try:
    combined_df.to_csv(OUTPUT_COMBINED_PATH, index=False, encoding='utf-8')
    print(f"Successfully saved combined data to '{OUTPUT_COMBINED_PATH}'")
except Exception as e:
    print(f"ERROR saving combined file: {e}")

