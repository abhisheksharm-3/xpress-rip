from typing import List
from fastapi import Query
from pydantic import BaseModel, HttpUrl

class PlaylistDownload(BaseModel):
    url: str

class Song(BaseModel):
    title: str
    duration: str
    thumbnail: HttpUrl

class PlaylistData(BaseModel):
    title: str
    channelName: str
    videoCount: int
    totalDuration: str
    thumbnailUrl: HttpUrl
    songs: List[Song]

class PlaylistRequest(BaseModel):
    url: HttpUrl
    fast_mode: bool = Query(default=False, description="Use fast mode without duration info")