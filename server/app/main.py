from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import playlist
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(playlist.router, prefix=settings.API_V1_STR + "/playlist", tags=["playlist"])

@app.get("/")
async def root():
    return {"message": "Welcome to the YouTube Playlist Downloader API"}