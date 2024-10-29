from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.models.playlist import PlaylistData, PlaylistDownload, PlaylistRequest
import os

from app.services.youtube import create_youtube_service

router = APIRouter()
playlist_downloader, playlist_data_fetcher = create_youtube_service()

@router.post("/download")
async def download_playlist(
    playlist: PlaylistDownload,
):
    try:
        zip_path = playlist_downloader.download_playlist(playlist.url)
        return FileResponse(zip_path, media_type='application/octet-stream', filename=os.path.basename(zip_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/info", response_model=PlaylistData)
async def get_playlist_data(request: PlaylistRequest):
    """
    Fetch playlist data for a given YouTube playlist URL.
    """
    try:
        return playlist_data_fetcher.get_playlist_data(str(request.url))
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch playlist data: {str(e)}"
        )