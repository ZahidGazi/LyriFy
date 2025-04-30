import warnings

import requests
import spotipy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)
from urllib3.exceptions import InsecureRequestWarning

import globals
from logger import logger


class LyricsAPI:
    """Handles fetching lyrics from various API sources."""

    _lrclib_session = requests.Session()
    _textyl_session = requests.Session()

    @staticmethod
    def fetch_lyrics(song, album, artist, duration):
        """
        Fetch lyrics from available APIs in order of preference.

        Args:
            song: Song title
            album: Album name
            artist: Artist name
            duration: Song duration in milliseconds

        Returns:
            List of lyrics data or empty list if no lyrics found
        """
        # Try lrclib.net's cache endpoint first
        # lyrics_data = LyricsAPI._try_lrclib_cache(song, album, artist, duration)
        # if lyrics_data:
        #     logger.info(f"Lyrics found from lrclib cache for {song} by {artist}")
        #     return lyrics_data

        # Then try lrclib.net's regular endpoint
        lyrics_data = LyricsAPI._try_lrclib_api(song, album, artist, duration)
        if lyrics_data:
            logger.info(f"Lyrics found from lrclib for {song} by {artist}")
            return lyrics_data

        # Finally fall back to textyl's API
        lyrics_data = LyricsAPI._try_textyl_api(song, artist)
        if lyrics_data:
            logger.info(f"Lyrics found from textyl for {song} by {artist}")
            return lyrics_data

        return []

    @staticmethod
    def _try_lrclib_cache(song, album, artist, duration):
        """Try to fetch lyrics from lrclib.net's cache endpoint."""
        try:
            lrclib_cache_url = "https://lrclib.net/api/get_cache"
            params = {
                "track_name": song,
                "artist_name": artist,
                "album_name": album,
                "duration": int(duration / 1000),  # Convert ms to seconds
            }
            response = LyricsAPI._lrclib_session.get(lrclib_cache_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return LyricsAPI._format_lrclib_data(data)
        except Exception as e:
            logger.error(f"Exception in _try_lrclib_cache: {str(e)}")
        return []

    @staticmethod
    def _try_lrclib_api(song, album, artist, duration):
        """Try to fetch lyrics from lrclib.net's regular endpoint."""
        try:
            lrclib_url = "https://lrclib.net/api/get"
            params = {
                "track_name": song,
                "artist_name": artist,
                "album_name": album,
                "duration": int(duration / 1000),  # Convert ms to seconds
            }
            response = LyricsAPI._lrclib_session.get(lrclib_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return LyricsAPI._format_lrclib_data(data)
        except Exception as e:
            logger.error(f"Exception in _try_lrclib_api: {str(e)}")
        return []

    @staticmethod
    def _try_textyl_api(song, artist):
        """Try to fetch lyrics from textyl's API."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InsecureRequestWarning)
                query = f"{song} {artist}"
                url = f"https://api.textyl.co/api/lyrics?q={query}"
                response = LyricsAPI._textyl_session.get(url, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return data
        except Exception as e:
            logger.error(f"Exception in _try_textyl_api: {str(e)}")
        return []

    @staticmethod
    def _format_lrclib_data(lrclib_data):
        """
        Convert lrclib.net data format to the format expected by the app.

        Args:
            lrclib_data: Raw data from lrclib API

        Returns:
            Formatted lyrics data list or empty list on error
        """
        try:
            if not lrclib_data or not lrclib_data.get("syncedLyrics"):
                return []

            formatted_data = []
            # Parse the synced lyrics which are in LRC format
            lrc_lines = lrclib_data["syncedLyrics"].strip().split("\n")

            for line in lrc_lines:
                # LRC format: [MM:SS.xx]Lyrics text
                if line.startswith("[") and "]" in line:
                    time_tag = line[1 : line.find("]")]
                    lyrics_text = line[line.find("]") + 1 :].strip()

                    # Skip empty lyrics or metadata lines
                    if (
                        not lyrics_text
                        or time_tag.startswith("ar:")
                        or time_tag.startswith("al:")
                        or time_tag.startswith("ti:")
                    ):
                        continue

                    # Parse the timestamp (format: MM:SS.xx)
                    try:
                        if ":" in time_tag:
                            minutes, seconds = time_tag.split(":")
                            total_seconds = int(minutes) * 60 + float(seconds)

                            formatted_data.append(
                                {"seconds": total_seconds, "lyrics": lyrics_text}
                            )
                    except ValueError:
                        continue

            # Sort by timestamp
            formatted_data.sort(key=lambda x: x["seconds"])
            return formatted_data
        except Exception as e:
            logger.error(f"Error formatting lrclib data: {str(e)}")
            return []


class SpotifyPlayer:
    """Handles interactions with the Spotify API."""

    def __init__(self, sp_oauth):
        """
        Initialize the Spotify player.

        Args:
            sp_oauth: SpotifyOAuth instance for authentication
        """
        session = requests.Session()
        self.spotify = spotipy.Spotify(auth_manager=sp_oauth, requests_session=session)

    def get_current_song(self):
        """
        Get information about the currently playing song.

        Returns:
            Tuple of (song, album, artist, current_time, duration) or
            (None, None, None, 0, 0) if no song is playing
        """
        try:
            track = self.spotify.currently_playing()
            if track and track["is_playing"]:
                song = track["item"]["name"]
                album = track["item"]["album"]["name"]
                artist = track["item"]["artists"][0]["name"]
                current_time = int(track["progress_ms"] / 1000)
                duration = track["item"]["duration_ms"]
                return song, album, artist, current_time, duration
        except Exception as e:
            logger.error(f"Exception in get_current_song: {str(e)}")
            self._show_error(
                "An error occurred while sending request to Spotify API, could be network issue, try refreshing. See logs for more details."
            )
        return None, None, None, 0, 0

    def get_current_playback_time(self):
        """
        Get the current playback time of the playing song.

        Returns:
            Current playback time in seconds or 0 if no song is playing
        """
        try:
            track = self.spotify.currently_playing()
            if track and track["is_playing"]:
                return track["progress_ms"] / 1000
        except Exception as e:
            logger.error(f"Exception in get_current_playback_time: {str(e)}")
        return 0

    @staticmethod
    def _show_error(message):
        """Show an error message dialog."""
        QMessageBox.critical(globals.main_window, "Error", message)


class LyricsOverlay(QLabel):
    """A floating overlay widget that displays synchronized lyrics for the current Spotify song."""

    REFRESH_INTERVAL = 500  # ms
    SONG_CHECK_INTERVAL = 5000  # ms
    MAX_IDLE_SEARCHES = 5

    def __init__(self, sp_oauth, token_info, parent=None):
        """
        Initialize the lyrics overlay.

        Args:
            sp_oauth: SpotifyOAuth instance for authentication
            token_info: Token information for Spotify API
            parent: Parent widget
        """
        super().__init__(parent)

        # Validate token info
        if not token_info:
            token_info = sp_oauth.get_cached_token()
        if not token_info:
            raise Exception(
                "No token info available. Ensure authentication is complete."
            )

        # Initialize Spotify player
        self.spotify_player = SpotifyPlayer(sp_oauth)

        # Configure UI
        self._configure_window()
        self._configure_font_and_style()
        self._create_control_div()

        # Initialize state
        self._initialize_attributes()
        self._setup_timers()

        # Set initial message
        self.setText(
            "<p style='font-size:20px; color:yellow;'>Widget loaded, waiting for song...</p>"
        )

    def _initialize_attributes(self):
        """Initialize instance attributes."""
        self.current_song = ""
        self.lyrics_data = []
        self.current_time = 1
        self.song_duration = 0
        self.isRefreshed = False
        self.idleSearch = 0

    def _configure_window(self):
        """Configure window properties."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("color: white;")
        self.resize(400, 200)

        # Position window in top-right corner
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geo.width() - self.width() - 50, 50)

    def _configure_font_and_style(self):
        """Configure font and text alignment."""
        self.setFont(QFont("Arial", 20))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _setup_timers(self):
        """Set up timers for updating lyrics and checking for song changes."""
        # Timer for updating lyrics display
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_lyrics)
        self.timer.start(self.REFRESH_INTERVAL)

        # Timer for checking current song and fetching lyrics
        self.song_timer = QTimer(self)
        self.song_timer.timeout.connect(self.fetch_song_and_lyrics)
        self.song_timer.start(self.SONG_CHECK_INTERVAL)

    def _create_control_div(self):
        """Create the control panel with buttons and time display."""
        control_div_height = 40
        self.control_div = QWidget(self)
        self.control_div.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.control_div.setGeometry(
            0, self.height() - control_div_height, self.width(), control_div_height
        )

        layout = QHBoxLayout(self.control_div)
        layout.setContentsMargins(10, 10, 10, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Time label
        self.time_label = QLabel(self.control_div)
        self.time_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 12px;"
        )
        self.time_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )
        layout.addWidget(self.time_label)

        # Refresh button
        self.refresh_button = QPushButton(self.control_div)
        refresh_icon = QIcon("res/refresh.ico")
        self.refresh_button.setIcon(refresh_icon)
        self.refresh_button.setFixedSize(20, 20)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.3); /* light cyan glow */
                border-radius: 5px;
            }
        """)
        self.refresh_button.clicked.connect(self.do_refresh)
        layout.addWidget(self.refresh_button)

        # Exit button
        self.exit_button = QPushButton(self.control_div)
        close_icon = QIcon("res/close.ico")
        self.exit_button.setIcon(close_icon)
        self.exit_button.setFixedSize(20, 20)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.3); /* light red glow */
                border-radius: 5px;
            }
        """)
        self.exit_button.clicked.connect(QApplication.quit)
        layout.addWidget(self.exit_button)

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging the window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging the window."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "old_pos"):
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def do_refresh(self):
        """Handle refresh button click."""
        self.isRefreshed = True
        self.idleSearch = 0

    def fetch_song_and_lyrics(self):
        """Fetch current song information and lyrics if needed."""
        if self.idleSearch > self.MAX_IDLE_SEARCHES:
            return

        song, album, artist, current_time, duration = (
            self.spotify_player.get_current_song()
        )
        self.current_time = current_time
        self.song_duration = duration

        if (song and song != self.current_song) or self.isRefreshed:
            self.isRefreshed = False
            self.current_song = song

            # Fetch lyrics for the new song
            self.lyrics_data = LyricsAPI.fetch_lyrics(song, album, artist, duration)
        else:
            # Increment idle search counter if no song is playing
            if not song:
                self.idleSearch += 1

    def update_lyrics(self):
        """Update the lyrics display based on current playback time."""
        if self.idleSearch > self.MAX_IDLE_SEARCHES:
            self.setText(
                "<p style='font-size:20px; color:orange;'>No song playing...</p>"
                "<p style='font-size:15px; color:gray;'>Please play a song on Spotify and Refresh.</p>"
            )
            return

        # Fetch song and lyrics if not already done
        if self.current_song == "":
            self.fetch_song_and_lyrics()

        # Update time display
        self._update_time_display()

        # Update lyrics display
        if self.isRefreshed:
            self.setText("<p style='font-size:20px; color:orange;'>Refreshing...</p>")
        elif self.lyrics_data:
            self._update_lyrics_display()
        else:
            self.setText("<p style='font-size:20px; color:cyan;'>No lyrics found.</p>")

        # Increment current time for next update
        self.current_time += 0.5

    def _update_time_display(self):
        """Update the time display in the control panel."""
        if self.song_duration > 0:
            current_formatted = self._format_time(self.current_time)
            duration_formatted = self._format_time(
                self.song_duration / 1000
            )  # Convert ms to seconds
            self.time_label.setText(f"{current_formatted} / {duration_formatted}")
        else:
            self.time_label.setText("0:00 / 0:00")

    def _update_lyrics_display(self):
        """Update the lyrics display with current, previous, and next lines."""
        current_lyric_index = self._find_current_lyric_index()
        if current_lyric_index is not None:
            formatted_prev = self._get_formatted_lyric(current_lyric_index - 1, 50)
            formatted_current = self._get_formatted_lyric(current_lyric_index, 25)
            formatted_next = self._get_formatted_lyric(current_lyric_index + 1, 50)

            self.setText(
                f"<p style='font-size:15px; color:gray;'>{formatted_prev}</p>"
                f"<p style='font-size:25px; color:cyan;'>{formatted_current}</p>"
                f"<p style='font-size:15px; color:gray;'>{formatted_next}</p>"
            )

    def _find_current_lyric_index(self):
        """
        Find the index of the current lyric based on the current playback time.

        Returns:
            Index of the current lyric or None if no matching lyric found
        """
        for i, lyric in enumerate(reversed(self.lyrics_data)):
            if lyric["seconds"] <= self.current_time:
                # Convert from reversed index to actual index in self.lyrics_data
                return len(self.lyrics_data) - i - 1
        return None

    def _get_formatted_lyric(self, index, max_length=25):
        """
        Get and format a lyric at the specified index.

        Args:
            index: The index of the lyric in self.lyrics_data
            max_length: Maximum line length before wrapping

        Returns:
            Formatted lyric text or empty string if index is invalid
        """
        if 0 <= index < len(self.lyrics_data):
            lyric_text = self.lyrics_data[index]["lyrics"]
            return self._format_text(lyric_text, max_length)
        return ""

    @staticmethod
    def _format_text(text, max_length=25):
        """
        Format text with line breaks for display.

        Args:
            text: Text to format
            max_length: Maximum line length before wrapping

        Returns:
            Formatted text with HTML line breaks
        """
        result = ""
        while len(text) > max_length:
            space_index = text[:max_length].rfind(" ")
            if space_index != -1:
                result += text[:space_index] + "<br/>"
                text = text[space_index + 1 :]
            else:
                result += text[:max_length] + "<br/>"
                text = text[max_length:]
        return result + text

    @staticmethod
    def _format_time(seconds):
        """
        Convert seconds to MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
