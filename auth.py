import os
from spotipy.oauth2 import SpotifyOAuth

def create_spotify_oauth(client_id, client_secret, redirect_uri):
    # Determine a cache path in the user's AppData folder
    appdata = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
    if not appdata:
        appdata = os.path.abspath(".")
    cache_dir = os.path.join(appdata, "LyriFy")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, ".cache")

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-read-currently-playing",
        cache_path=cache_path
    )
