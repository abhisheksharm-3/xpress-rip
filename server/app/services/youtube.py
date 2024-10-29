from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Callable
import concurrent.futures
import math
import os
import psutil
import time
import zipfile
import yt_dlp
from fastapi import HTTPException
from urllib.parse import urlparse, parse_qs

class AudioFormat(Enum):
    MP3 = "mp3"
    M4A = "m4a"
    WAV = "wav"

@dataclass
class DownloadConfig:
    format: AudioFormat = AudioFormat.MP3
    quality: str = "320"
    max_workers: int = 16
    chunk_size: int = 10485760  # 10MB
    buffer_size: int = 1024 * 1024  # 1MB
    retry_attempts: int = 10
    socket_timeout: int = 30

@dataclass
class Song:
    title: str
    duration: str
    thumbnail: str

@dataclass
class PlaylistMetadata:
    title: str
    channel_name: str
    video_count: int
    total_duration: str
    thumbnail_url: str
    songs: List[Song]

class SystemUtils:
    @staticmethod
    def get_optimal_workers() -> int:
        cpu_count = psutil.cpu_count(logical=False)
        memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
        optimal_workers = min(cpu_count * 2, math.floor(memory_gb / 1))
        return min(optimal_workers, 16)

    @staticmethod
    def format_size(bytes_size: int) -> str:
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(bytes_size)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.2f} {units[unit_index]}"

    @staticmethod
    def format_duration(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return f"{hours}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes}:{seconds:02d}"

class DownloadManager:
    def __init__(self, config: DownloadConfig):
        self.config = config
        
    def create_ydl_opts(self, output_dir: Path, progress_hook: Optional[Callable] = None) -> Dict:
        return {
            'format': 'bestaudio/best',
            'paths': {'home': str(output_dir)},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.config.format.value,
                'preferredquality': self.config.quality,
            }],
            'outtmpl': {'default': '%(title)s.%(ext)s'},
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook] if progress_hook else None,
            'fragment_retries': self.config.retry_attempts,
            'retries': self.config.retry_attempts,
            'concurrent_fragment_downloads': 8,
            'buffersize': self.config.buffer_size,
            'http_chunk_size': self.config.chunk_size,
            'socket_timeout': self.config.socket_timeout,
            'format_sort': ['abr', 'asr', 'res', 'br', 'size'],
            'format_sort_force': True,
        }

    def download_audio(self, url: str, output_dir: Path, index: Optional[int] = None, total: Optional[int] = None) -> bool:
        def progress_callback(d: Dict):
            if d['status'] == 'downloading':
                try:
                    speed = f"{SystemUtils.format_size(d['speed'])}/s" if d.get('speed') else 'Unknown speed'
                    downloaded = SystemUtils.format_size(d['downloaded_bytes'])
                    total_size = SystemUtils.format_size(d['total_bytes']) if d.get('total_bytes') else 'Unknown size'
                    percent = d['downloaded_bytes'] / d['total_bytes'] * 100 if d.get('total_bytes') else 0
                    print(f"\r{d['filename']}: {percent:.1f}% | {downloaded}/{total_size} | {speed}", end='', flush=True)
                except Exception:
                    pass
            elif d['status'] == 'finished':
                print(f"\nFinished downloading: {d['filename']}")

        try:
            with yt_dlp.YoutubeDL(self.create_ydl_opts(output_dir, progress_callback)) as ydl:
                info = ydl.extract_info(url, download=True)
                if index and total:
                    print(f"\n[{index}/{total}] Successfully downloaded: {info.get('title', 'Unknown Title')}")
                return True
        except Exception as e:
            if index and total:
                print(f"\n[{index}/{total}] Error downloading {url}: {str(e)}")
            return False

class PlaylistDownloader:
    def __init__(self, download_manager: DownloadManager):
        self.download_manager = download_manager
        self.base_dir = Path("./Downloads")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def download_playlist(self, playlist_url: str) -> Path:
        try:
            playlist_info = self._get_playlist_info(playlist_url)
            if not playlist_info or 'entries' not in playlist_info:
                raise ValueError("Could not load playlist information")

            videos = playlist_info['entries']
            total_videos = len(videos)
            print(f"\nFound {total_videos} videos in playlist")
            
            max_workers = min(SystemUtils.get_optimal_workers(), self.download_manager.config.max_workers)
            print(f"Using {max_workers} concurrent downloads for optimal speed...")

            successful, failed = self._download_videos(videos, max_workers)
            
            zip_path = self._create_zip_archive()
            self._cleanup_mp3_files()
            
            self._print_summary(successful, failed, total_videos)
            
            return zip_path

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    def _get_playlist_info(self, url: str) -> Dict:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _download_videos(self, videos: List[Dict], max_workers: int) -> tuple[int, int]:
        successful = failed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for index, video in enumerate(videos, 1):
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                future = executor.submit(
                    self.download_manager.download_audio,
                    video_url,
                    self.base_dir,
                    index,
                    len(videos)
                )
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    successful += 1
                else:
                    failed += 1

        return successful, failed

    def _create_zip_archive(self) -> Path:
        zip_path = self.base_dir / f"playlist_{int(time.time())}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in self.base_dir.glob('*.mp3'):
                zipf.write(file_path, file_path.name)
        return zip_path

    def _cleanup_mp3_files(self):
        for file_path in self.base_dir.glob('*.mp3'):
            file_path.unlink()

    def _print_summary(self, successful: int, failed: int, total: int):
        print("\nDownload Summary:")
        print(f"Successfully downloaded: {successful} videos")
        print(f"Failed to download: {failed} videos")
        print(f"Files saved to: {self.base_dir.absolute()}")

class PlaylistDataFetcher:
    def __init__(self):
        self.ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}

    @staticmethod
    def extract_playlist_id(url: str) -> str:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        playlist_id = query_params.get('list', [None])[0]
        
        if not playlist_id:
            raise HTTPException(status_code=400, detail="Invalid playlist URL")
            
        return playlist_id

    def get_playlist_data(self, url: str) -> PlaylistMetadata:
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
                
                if not playlist_info:
                    raise HTTPException(status_code=404, detail="Could not fetch playlist information")

                songs = [
                    Song(
                        title=entry['title'],
                        duration="NA",
                        thumbnail=entry.get('thumbnail', '')
                    )
                    for entry in playlist_info['entries']
                    if entry is not None
                ]

                return PlaylistMetadata(
                    title=playlist_info.get('title', 'Unknown Playlist'),
                    channel_name=playlist_info.get('uploader', 'Unknown Channel'),
                    video_count=len(songs),
                    total_duration="NA",
                    thumbnail_url=playlist_info.get('thumbnail', songs[0].thumbnail if songs else ""),
                    songs=songs
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch playlist data: {str(e)}")

def create_youtube_service() -> tuple[PlaylistDownloader, PlaylistDataFetcher]:
    config = DownloadConfig()
    download_manager = DownloadManager(config)
    playlist_downloader = PlaylistDownloader(download_manager)
    playlist_data_fetcher = PlaylistDataFetcher()
    
    return playlist_downloader, playlist_data_fetcher