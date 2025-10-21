from fastapi import FastAPI

# 1. Create the main application instance (the "bulb")
app = FastAPI(title="Project Kepler API")

# 2. Define the /health endpoint (the "switch")
@app.get("/health")
def read_health():
    """
    A simple health check endpoint.
    Returns {'status': 'ok'} if the API is running.
    """
    return {"status": "ok"}
