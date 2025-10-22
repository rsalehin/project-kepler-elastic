import arxiv
import csv
import os

# --- Determine script location and project root ---
# Get the directory where THIS script file lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assume the project root is two levels up from the script's directory (scripts -> backend -> project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# --- Configuration ---
SEARCH_QUERY = "cat:astro-ph.EP"
MAX_RESULTS = 5000
# Construct the output path relative to the calculated project root
OUTPUT_FILENAME_ABSOLUTE = os.path.join(PROJECT_ROOT, "data", "arxiv_abstracts.csv")

# --- Debugging: Print absolute path ---
print(f"DEBUG: Script directory: {SCRIPT_DIR}")
print(f"DEBUG: Calculated project root: {PROJECT_ROOT}")
print(f"DEBUG: Attempting to save file to absolute path: {OUTPUT_FILENAME_ABSOLUTE}")
# --- End Debugging ---

# --- Main Script ---
print(f"Searching arXiv for '{SEARCH_QUERY}'...")
# ... (rest of the script remains the same, ensuring it uses OUTPUT_FILENAME_ABSOLUTE)
client = arxiv.Client()
search = arxiv.Search(
  query = SEARCH_QUERY,
  max_results = MAX_RESULTS,
  sort_by = arxiv.SortCriterion.SubmittedDate
)
print(f"Found results. Processing up to {MAX_RESULTS} abstracts...")

results_processed = 0
os.makedirs(os.path.dirname(OUTPUT_FILENAME_ABSOLUTE), exist_ok=True)

try:
    with open(OUTPUT_FILENAME_ABSOLUTE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['arxiv_id', 'title', 'abstract', 'published_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in client.results(search):
            try:
                writer.writerow({
                    'arxiv_id': result.get_short_id(),
                    'title': result.title,
                    'abstract': result.summary.replace('\n', ' '),
                    'published_date': result.published.strftime('%Y-%m-%d')
                })
                results_processed += 1
                if results_processed % 50 == 0:
                     print(f"  Processed {results_processed} abstracts...")
            except Exception as write_error:
                 print(f"  ERROR writing abstract ID {result.get_short_id()}: {write_error}")

except Exception as e:
    print(f"An error occurred during search or file opening: {e}")
    print("Stopping download. The output file might be incomplete.")

print(f"\nFinished processing.")
if os.path.exists(OUTPUT_FILENAME_ABSOLUTE) and os.path.getsize(OUTPUT_FILENAME_ABSOLUTE) > 0:
    print(f"Successfully saved {results_processed} abstracts to '{OUTPUT_FILENAME_ABSOLUTE}'")
else:
    print(f"ERROR: File was NOT saved correctly to '{OUTPUT_FILENAME_ABSOLUTE}'. Processed {results_processed} abstracts.")
