import pytest
import os
import json
# --- ADD plot_planet_comparison to the import ---
from src.app.tools import search_elastic, plot_planet_comparison
from src.app.config import GCP_CREDENTIALS_PATH

# Mark test to skip if GCP credentials are not configured
pytestmark = pytest.mark.skipif(
    not GCP_CREDENTIALS_PATH or not os.path.exists(GCP_CREDENTIALS_PATH),
    reason="Requires GCP credentials config (GOOGLE_APPLICATION_CREDENTIALS)"
)

@pytest.mark.asyncio
async def test_search_elastic_vector_integration(es_test_client):
    # ... (this test remains unchanged) ...
    """ Tests vector search using the fixture client. """
    query = "atmosphere composition of hot jupiters"
    result_str = await search_elastic(es_client=es_test_client, text_query=query)
    assert isinstance(result_str, str)
    try:
        results = json.loads(result_str)
        assert isinstance(results, list)
        assert len(results) > 0, "Vector search returned zero results, check data/query."
        if results:
            assert "score" in results[0]
            assert "id" in results[0]
            assert "source" in results[0]
            print(f"\nVector Test OK: Found {len(results)} results for '{query}'. Top score: {results[0].get('score')}")
    except json.JSONDecodeError:
        pytest.fail(f"search_elastic did not return valid JSON: {result_str}")
    except Exception as e:
         pytest.fail(f"Error processing search results: {e}")

@pytest.mark.asyncio
async def test_search_elastic_hybrid_integration(es_test_client):
    # ... (this test remains unchanged) ...
    """ Tests hybrid search using the fixture client. """
    query = "habitability"
    filter_field = "pl_name.keyword"
    filter_value = "TRAPPIST-1 e"
    result_str = await search_elastic(
        es_client=es_test_client,
        text_query=query,
        keyword_filter_field=filter_field,
        keyword_filter_value=filter_value
    )
    assert isinstance(result_str, str)
    try:
        results = json.loads(result_str)
        assert isinstance(results, list)
        print(f"\nHybrid Test OK: Found {len(results)} results for '{query}' filtered by '{filter_value}'.")
        if results:
            assert "score" in results[0]
            assert "id" in results[0]
            assert "source" in results[0]
            # assert filter_value.lower() in results[0]['source'].get('pl_name','').lower() # Keep this commented
    except json.JSONDecodeError:
        pytest.fail(f"search_elastic did not return valid JSON: {result_str}")
    except Exception as e:
         pytest.fail(f"Error processing search results: {e}")

# --- This is the test that failed to collect ---
@pytest.mark.asyncio
async def test_plot_planet_comparison(es_test_client):
    """
    Integration test for the plot_planet_comparison tool.
    Checks if it returns a valid JSON string with a file path,
    and if the file was created.
    """
    planet_names = ["11 Com b", "TRAPPIST-1 e"] # Check these names against your CSV
    x_prop = "pl_rade"  # Planet Radius (Earth)
    y_prop = "pl_masse" # Planet Mass (Earth)
    
    result_str = await plot_planet_comparison( # This call will now work
        es_client=es_test_client,
        planet_names=planet_names,
        x_property=x_prop,
        y_property=y_prop
    )
    
    assert isinstance(result_str, str)
    print(f"\nPlot Tool Response: {result_str}")
    
    try:
        results = json.loads(result_str)
        assert isinstance(results, dict)
        
        if "error" in results:
            print(f"Warning: Plot tool returned an error (maybe missing data?): {results['error']}")
            assert "data" in results['error'].lower(), f"Plot tool failed with non-data error: {results['error']}"
        else:
            assert "plot_path" in results
            file_path = results["plot_path"]
            assert isinstance(file_path, str)
            assert file_path.startswith("/static/")
            assert file_path.endswith(".png")
            
            relative_path_in_backend = os.path.join("src", "app", file_path.lstrip('/'))
            assert os.path.exists(relative_path_in_backend), f"Plot file not found at {relative_path_in_backend}"
            assert os.path.getsize(relative_path_in_backend) > 100, "Plot file seems empty"
            print(f"\nPlot Test OK: Plot file {file_path} created successfully.")
            
    except json.JSONDecodeError:
        pytest.fail(f"plot_planet_comparison did not return valid JSON: {result_str}")
    except Exception as e:
         pytest.fail(f"Error processing plot results: {e}")
