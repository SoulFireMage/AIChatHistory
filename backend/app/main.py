import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .config import get_settings
from .api import api_router

settings = get_settings()

app = FastAPI(
    title="Conversation Vault",
    description="Import, store, and browse LLM conversation history",
    version="1.0.0"
)

# CORS middleware (for development)
if settings.env == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files and frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        """Serve the main frontend page."""
        index_file = frontend_path / "templates" / "index.html"
        if index_file.exists():
            return index_file.read_text()
        return """
        <html>
            <head><title>Conversation Vault</title></head>
            <body>
                <h1>Conversation Vault API</h1>
                <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development"
    )
