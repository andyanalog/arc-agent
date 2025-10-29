from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import all endpoints
from api.endpoints import app as api_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main app
app = FastAPI(
    title="ArcAgent Backend API",
    description="AI-powered payment assistant backend",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API endpoints
app.mount("/", api_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)