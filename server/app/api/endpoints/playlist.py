from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.models.playlist import PlaylistDownload
from app.services.youtube import youtube_service
from app.core.security import get_current_user
import os

router = APIRouter()

@router.post("/download")
async def download_playlist(
    playlist: PlaylistDownload,
    current_user: str = Depends(get_current_user)
):
    try:
        zip_path = youtube_service.download_playlist(playlist.url)
        return FileResponse(zip_path, media_type='application/octet-stream', filename=os.path.basename(zip_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))