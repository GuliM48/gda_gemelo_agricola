from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router import router

app = FastAPI(
    title="GDA - Gemelo Digital Agrícola API",
    description="API for the Agricultural Digital Twin Backend",
    version="1.0.0"
)

# CORS config to allow the frontend to interact
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to actual frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to GDA Backend API. Use /api/v1/regiones to check connectivity."}
