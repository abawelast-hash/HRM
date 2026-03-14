"""ShamIn — FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.presentation.api.routes.tasks import router as tasks_router

app = FastAPI(
    title="ShamIn API",
    description="SYP/USD Exchange Rate Forecaster API",
    version="1.0.0-beta",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks_router)


@app.get("/")
async def root():
    return {"app": "ShamIn", "status": "running", "version": "1.0.0-beta"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
