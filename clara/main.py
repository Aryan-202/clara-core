"""Main Application Entrypoint and FastAPI Server Initialization.

This module initializes the root FastAPI application, registers API and WebSocket
routes, defines default health-check endpoints, and provides the CLI runner command.
"""

from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from clara.api.ws.router import router as ws_router
from clara.auth import auth_router

app: FastAPI = FastAPI(
    title="Clara Core API",
    description="Autonomous AI agent and personal workspace automation backend.",
    version="0.1.0",
)
"""Root FastAPI application instance."""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clara: FastAPI = app
"""Alias for backwards compatibility with existing clara imports and scripts."""

app.include_router(ws_router)
app.include_router(auth_router)


@app.get("/")
async def root() -> Dict[str, str]:
    """Health-check and service status endpoint.

    Returns:
        Dict[str, str]: Status message confirming the backend service is operational.
    """
    return {
        "msg": "clara backend is running"
    }


def main() -> None:
    """CLI entrypoint to start the Clara Core backend server via Uvicorn.

    Example:
        $ clara
    """
    import uvicorn
    uvicorn.run("clara.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
