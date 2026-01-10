from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
import asyncio
import subprocess

from app.routes import main_router

app = FastAPI(title="RAG API", version="0.1.0")

logger = logging.getLogger(__name__)

# Incluir router principal con todos los endpoints
app.include_router(main_router)

# --- SEED AUTOMÁTICO DE DATOS EN STARTUP ---
@app.on_event("startup")
async def startup_event():
    logger.info("Running startup event for auto-ingestion seed...")
    seed_script_path = "/workspace/scripts/seed_demo_data.py"
    if Path(seed_script_path).exists():
        logger.info(f"Executing seed script: {seed_script_path}")
        # Ejecutar el seed en un hilo aparte para no bloquear el arranque
        asyncio.create_task(
            asyncio.to_thread(
                subprocess.run,
                ["python", seed_script_path],
                capture_output=True,
                text=True,
                check=False
            )
        )
    else:
        logger.warning(f"Seed script not found at {seed_script_path}. Skipping auto-ingestion.")
# --- FIN SEED AUTOMÁTICO ---


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})


# Servir archivos estáticos
static_dir = Path(__file__).parent / "static"
logger.info(f"Static directory path: {static_dir}")
logger.info(f"Static directory exists: {static_dir.exists()}")

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"✓ Static files mounted from {static_dir}")
else:
    logger.warning(f"✗ Static directory not found at {static_dir}")


@app.get("/")
async def serve_index():
    """Serve the main index.html file"""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        logger.info(f"✓ Serving index.html from {index_path}")
        return FileResponse(str(index_path), media_type="text/html")
    logger.warning(f"✗ index.html not found at {index_path}")
    return JSONResponse({"message": "Welcome to RAF Chatbot API", "status": "running"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)