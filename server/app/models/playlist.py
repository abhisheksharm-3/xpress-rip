from pydantic import BaseModel

class PlaylistDownload(BaseModel):
    url: str