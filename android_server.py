"""
Android entry point for the embedded Python backend.
Called by Chaquopy's PythonBackendService.java.
"""
import os
import sys
import threading


def run_server(port: int = 8000):
    """Start the FastAPI server on the given port."""
    # Ensure the backend package is importable
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # Set environment defaults for Android
    os.environ.setdefault("AI_API_KEY", "")
    os.environ.setdefault("AI_BASE_URL", "https://ollama.com/v1")
    os.environ.setdefault("AI_MODEL", "glm-4.7")
    os.environ.setdefault("PORT", str(port))

    import uvicorn
    from backend.main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=False,
    )
