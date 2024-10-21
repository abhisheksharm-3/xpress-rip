from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_download_playlist():
    response = client.post(
        "/api/v1/playlist/download",
        json={"url": "https://www.youtube.com/playlist?list=PLExample"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    assert "downloaded_tracks" in response.json()

def test_download_playlist_invalid_url():
    response = client.post(
        "/api/v1/playlist/download",
        json={"url": "invalid_url"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 400