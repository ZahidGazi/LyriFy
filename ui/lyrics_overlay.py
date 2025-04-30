import requests
import spotipy
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QPushButton, QStyle, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
import globals

from logger import logger
class LyricsOverlay(QLabel):
    def __init__(self, sp_oauth, token_info, parent=None):
        super().__init__(parent)
        if not token_info:
            token_info = sp_oauth.get_cached_token()
        if not token_info:
            raise Exception("No token info available. Ensure authentication is complete.")
        # Use auth_manager for automatic token refresh
        self.spotify = spotipy.Spotify(auth_manager=sp_oauth)

        self._configure_window()
        self._configure_font_and_style()
        self._initialize_attributes()
        self._setup_timers()
        self._create_control_div()

        self.setText("<p style='font-size:20px; color:yellow;'>Widget loaded, waiting for song...</p>")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "old_pos"):
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def _configure_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("color: white;")
        self.resize(400, 200)
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geo.width() - self.width() - 50, 50)

    def _configure_font_and_style(self):
        self.setFont(QFont("Arial", 20))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _initialize_attributes(self):
        self.current_song = ""
        self.lyrics_data = []
        self.current_time = 1
        self.song_duration = 0
        self.isRefreshed = False
        self.idleSearch = 0

    def _setup_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_lyrics)
        self.timer.start(500)

        self.song_timer = QTimer(self)
        self.song_timer.timeout.connect(self.fetch_song_and_lyrics)
        self.song_timer.start(5000)

    def _create_control_div(self):
        control_div_height = 40
        self.control_div = QWidget(self)
        self.control_div.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.control_div.setGeometry(0, self.height() - control_div_height, self.width(), control_div_height)
        layout = QHBoxLayout(self.control_div)
        layout.setContentsMargins(10, 10, 10, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel(self.control_div)
        self.time_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.time_label)

        self.refresh_button = QPushButton(self.control_div)
        refresh_icon = QIcon("res/refresh.ico")  # Ensure this file exists
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

        self.exit_button = QPushButton(self.control_div)
        close_icon = QIcon("res/close.ico")  # Ensure this file exists
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

    def do_refresh(self):
        self.isRefreshed = True
        self.idleSearch = 0

    def get_current_song(self):
        try:
            if (self.current_time * 1000 > self.song_duration) or self.isRefreshed:
                track = self.spotify.currently_playing()
                if track and track["is_playing"]:
                    song = track["item"]["name"]
                    album = track["item"]["album"]["name"]
                    artist = track["item"]["artists"][0]["name"]
                    current_time = int(track["progress_ms"] / 1000)
                    duration = track["item"]["duration_ms"]
                    return song, album, artist, current_time, duration
                else:
                    self.idleSearch += 1
                    return None, None, None, None, None
        except Exception as e:
            self.idleSearch += 1
            logger.error(f"Exception in get_current_song: {str(e)}")
            QMessageBox.critical(globals.main_window, "Error", "An error occurred while sending request to spotify api, could be network issue, try refreshing. see logs for more details. ")
        return None, None, None, None, None

    def get_song_lyrics(self, song, album, artist):
        # First try lrclib.net's cache endpoint
        try:
            lrclib_cache_url = "https://lrclib.net/api/get_cache"
            params = {
                "track_name": song,
                "artist_name": artist,
                "album_name": album,
                "duration": int(self.song_duration / 1000)
            }
            response = requests.get(lrclib_cache_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Convert lrclib format to the format expected by the app
                    formatted_data = self._format_lrclib_data(data)
                    if formatted_data:
                        logger.info(f"Lyrics found from lrclib cache for {song} by {artist}")
                        return formatted_data
        except Exception as e:
            logger.error(f"Exception in get_song_lyrics (lrclib cache): {str(e)}")

        # If cache fails, try lrclib.net's regular endpoint
        try:
            lrclib_url = "https://lrclib.net/api/get"
            params = {
                "track_name": song,
                "artist_name": artist,
                "album_name": album,
                "duration": int(self.song_duration / 1000)
            }
            response = requests.get(lrclib_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Convert lrclib format to the format expected by the app
                    formatted_data = self._format_lrclib_data(data)
                    if formatted_data:
                        logger.info(f"Lyrics found from lrclib for {song} by {artist}")
                        return formatted_data
        except Exception as e:
            logger.error(f"Exception in get_song_lyrics (lrclib): {str(e)}")

        # If both lrclib endpoints fail, fall back to textyl's API
        query = f"{song} {artist}"
        url = f"https://api.textyl.co/api/lyrics?q={query}"
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data:
                    logger.info(f"Lyrics found from textyl for {song} by {artist}")
                    return data
        except Exception as e:
            logger.error(f"Exception in get_song_lyrics (textyl): {str(e)}")
            QMessageBox.critical(globals.main_window, "Error", "An error occurred while fetching lyrics, could be network issue, try refreshing. see logs for more details. ")
        return []

    def _format_lrclib_data(self, lrclib_data):
        """Convert lrclib.net data format to the format expected by the app."""
        try:
            if not lrclib_data or not lrclib_data.get("syncedLyrics"):
                return []

            formatted_data = []
            # Parse the synced lyrics which are in LRC format
            lrc_lines = lrclib_data["syncedLyrics"].strip().split("\n")

            for line in lrc_lines:
                # LRC format: [MM:SS.xx]Lyrics text
                if line.startswith("[") and "]" in line:
                    time_tag = line[1:line.find("]")]
                    lyrics_text = line[line.find("]")+1:].strip()

                    # Skip empty lyrics or metadata lines
                    if not lyrics_text or time_tag.startswith("ar:") or time_tag.startswith("al:") or time_tag.startswith("ti:"):
                        continue

                    # Parse the timestamp (format: MM:SS.xx)
                    try:
                        if ":" in time_tag:
                            minutes, seconds = time_tag.split(":")
                            total_seconds = int(minutes) * 60 + float(seconds)

                            formatted_data.append({
                                "seconds": total_seconds,
                                "lyrics": lyrics_text
                            })
                    except ValueError:
                        continue

            # Sort by timestamp
            formatted_data.sort(key=lambda x: x["seconds"])
            return formatted_data
        except Exception as e:
            logger.error(f"Error formatting lrclib data: {str(e)}")
            return []

    def fetch_song_and_lyrics(self):
        if self.idleSearch > 5:
            return
        song, album, artist, current_time, duration = self.get_current_song()
        if (song and song != self.current_song) or self.isRefreshed:
            self.isRefreshed = False
            self.current_song = song
            self.current_time = current_time
            self.song_duration = duration
            self.lyrics_data = self.get_song_lyrics(song, album, artist)
        else:
            self.current_time = self.get_current_playback_time()

    @staticmethod
    def format_text(text, max_length=25):
        result = ""
        while len(text) > max_length:
            space_index = text[:max_length].rfind(" ")
            if space_index != -1:
                result += text[:space_index] + "<br/>"
                text = text[space_index + 1:]
            else:
                result += text[:max_length] + "<br/>"
                text = text[max_length:]
        return result + text

    def format_time(self, seconds):
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_lyrics(self):
        if self.idleSearch > 5:
            self.setText("<p style='font-size:20px; color:orange;'>No song playing...</p>"
                         "<p style='font-size:15px; color:gray;'>Please play a song on Spotify and Refresh.</p>")
            return

        # Fetch song and lyrics if not already done
        if self.current_song == "":
            self.fetch_song_and_lyrics()

        # Update time display
        if self.song_duration > 0:
            current_formatted = self.format_time(self.current_time)
            duration_formatted = self.format_time(self.song_duration / 1000)  # Convert ms to seconds
            self.time_label.setText(f"{current_formatted} / {duration_formatted}")
        else:
            self.time_label.setText("0:00 / 0:00")

        # Update lyrics display
        if self.isRefreshed:
            self.setText("<p style='font-size:20px; color:orange;'>Refreshing...</p>")
            return
        elif self.lyrics_data:
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
        else:
            self.setText("<p style='font-size:20px; color:cyan;'>No lyrics found.</p>")

        self.current_time += 0.5

    def _find_current_lyric_index(self):
        """Find the index of the current lyric based on the current playback time."""
        for i, lyric in enumerate(reversed(self.lyrics_data)):
            if lyric["seconds"] <= self.current_time:
                # Convert from reversed index to actual index in self.lyrics_data
                return len(self.lyrics_data) - i - 1
        return None

    def _get_formatted_lyric(self, index, max_length=25):
        """Get and format a lyric at the specified index.

        Args:
            index: The index of the lyric in self.lyrics_data
            max_length: Maximum line length before wrapping

        Returns:
            Formatted lyric text or empty string if index is invalid
        """
        if 0 <= index < len(self.lyrics_data):
            lyric_text = self.lyrics_data[index]["lyrics"]
            return self.format_text(lyric_text, max_length)
        return ""

    def get_current_playback_time(self):
        track = self.spotify.currently_playing()
        if track and track["is_playing"]:
            self.song_duration = int(track["item"]["duration_ms"])
            playback_time = track["progress_ms"] / 1000
            return playback_time
        return 0