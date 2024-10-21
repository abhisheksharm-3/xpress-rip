import os
import yt_dlp
import concurrent.futures
import time
from pathlib import Path
import psutil
import math
from typing import List, Dict
import zipfile
import shutil

def get_optimal_workers():
    cpu_count = psutil.cpu_count(logical=False)
    memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
    optimal_workers = min(cpu_count * 2, math.floor(memory_gb / 1))
    return min(optimal_workers, 16)

def create_download_directory(filepath: str) -> str:
    if not filepath:
        filepath = "./Downloads"
    Path(filepath).mkdir(parents=True, exist_ok=True)
    return filepath

def format_size(bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def progress_hook(d: Dict):
    if d['status'] == 'downloading':
        try:
            speed = format_size(d['speed']) + '/s' if d.get('speed') else 'Unknown speed'
            downloaded = format_size(d['downloaded_bytes'])
            total = format_size(d['total_bytes']) if d.get('total_bytes') else 'Unknown size'
            percent = d['downloaded_bytes'] / d['total_bytes'] * 100 if d.get('total_bytes') else 0
            print(f"\r{d['filename']}: {percent:.1f}% | {downloaded}/{total} | {speed}", end='', flush=True)
        except Exception:
            pass
    elif d['status'] == 'finished':
        print(f"\nFinished downloading: {d['filename']}")

def download_audio(url: str, filepath: str, index: int = None, total: int = None) -> bool:
    ydl_opts = {
        'format': 'bestaudio/best',
        'paths': {'home': filepath},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': {'default': '%(title)s.%(ext)s'},
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
        'extract_flat': False,
        'fragment_retries': 10,
        'retries': 10,
        'file_access_retries': 5,
        'retry_sleep': 5,
        'concurrent_fragment_downloads': 8,
        'buffersize': 1024 * 1024,
        'http_chunk_size': 10485760,
        'ratelimit': None,
        'throttledratelimit': None,
        'socket_timeout': 30,
        'extractor_retries': 5,
        'format_sort': ['abr', 'asr', 'res', 'br', 'size'],
        'format_sort_force': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"\n[{index}/{total}] Successfully downloaded: {info.get('title', 'Unknown Title')}")
            return True
    except Exception as e:
        print(f"\n[{index}/{total}] Error downloading {url}: {str(e)}")
        return False

class YouTubeService:
    def __init__(self):
        self.download_dir = create_download_directory("./Downloads")

    def download_playlist(self, playlist_url: str) -> str:
        max_workers = get_optimal_workers()
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                if not playlist_info:
                    raise ValueError("Error: Could not load playlist information")

                videos = playlist_info['entries']
                total_videos = len(videos)
                print(f"\nFound {total_videos} videos in playlist")
                print(f"Using {max_workers} concurrent downloads for optimal speed...")
                print("Starting downloads with maximum speed configuration...\n")

                successful = 0
                failed = 0
                start_time = time.time()

                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for index, video in enumerate(videos, 1):
                        video_url = f"https://www.youtube.com/watch?v={video['id']}"
                        future = executor.submit(download_audio, video_url, self.download_dir, index, total_videos)
                        futures.append(future)

                    for future in concurrent.futures.as_completed(futures):
                        if future.result():
                            successful += 1
                        else:
                            failed += 1

                duration = time.time() - start_time
                avg_time = duration / total_videos if total_videos > 0 else 0

                print("\nDownload Summary:")
                print(f"Total time: {duration:.2f} seconds")
                print(f"Average time per video: {avg_time:.2f} seconds")
                print(f"Successfully downloaded: {successful} videos")
                print(f"Failed to download: {failed} videos")
                print(f"Files saved to: {os.path.abspath(self.download_dir)}")

                # Create zip file
                zip_filename = f"playlist_{int(time.time())}.zip"
                zip_path = os.path.join(self.download_dir, zip_filename)
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(self.download_dir):
                        for file in files:
                            if file.endswith('.mp3'):
                                zipf.write(os.path.join(root, file), file)

                # Clean up individual mp3 files
                for file in os.listdir(self.download_dir):
                    if file.endswith('.mp3'):
                        os.remove(os.path.join(self.download_dir, file))

                return zip_path

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise

youtube_service = YouTubeService()