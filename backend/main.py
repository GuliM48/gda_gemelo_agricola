import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

try:
    from .api.router import router
except ImportError:
    from api.router import router

app = FastAPI(
    title="GDA - Gemelo Digital Agrícola API",
    description="API for the Agricultural Digital Twin Backend",
    version="1.0.0"
)

# CORS config to allow frontend, Streamlit, and dev tools to interact
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Ruta a la build del frontend (React + Vite)
BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = DIST_DIR / "assets"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

@app.get("/", tags=["frontend"], response_class=HTMLResponse)
def root():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1>🌾 GDA — Gemelo Digital Agrícola API</h1>
            <p>API REST operativa. Visita <a href="/docs">/docs</a> para la documentación interactiva Swagger.</p>
        </body>
    </html>
    """

@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    fav = DIST_DIR / "favicon.svg"
    if fav.exists():
        return FileResponse(str(fav))
    return None

@app.get("/icons.svg", include_in_schema=False)
def icons():
    ico = DIST_DIR / "icons.svg"
    if ico.exists():
        return FileResponse(str(ico))
    return None

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "GDA Digital Twin API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)


