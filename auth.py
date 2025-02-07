from spotipy.oauth2 import SpotifyOAuth

def create_spotify_oauth(client_id, client_secret, redirect_uri):
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-read-currently-playing"
    )
