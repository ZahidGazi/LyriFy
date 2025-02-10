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
        self.spotify = spotipy.Spotify(auth=token_info["access_token"])

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
        self.timer.start(1000)

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
                    artist = track["item"]["artists"][0]["name"]
                    return song, artist
                else:
                    self.idleSearch += 1
                    return None, None
        except Exception as e:
            self.idleSearch += 1
            logger.error(f"Exception in get_current_song: {str(e)}")
            QMessageBox.critical(globals.main_window, "Error", "An error occurred while sending request to spotify api, could be network issue, try refreshing. see logs for more details. ")
        return None, None

    def get_song_lyrics(self, song, artist):
        query = f"{song} {artist}"
        url = f"https://api.textyl.co/api/lyrics?q={query}"
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
        except Exception as e:
            logger.error(f"Exception in get_song_lyrics: {str(e)}")
            QMessageBox.critical(globals.main_window, "Error", "An error occurred while fetching lyrics, could be network issue, try refreshing. see logs for more details. ")
        return []

    def fetch_song_and_lyrics(self):
        if self.idleSearch > 5:
            return
        song, artist = self.get_current_song()
        if (song and song != self.current_song) or self.isRefreshed:
            self.isRefreshed = False
            self.current_song = song
            self.lyrics_data = self.get_song_lyrics(song, artist)
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

    def update_lyrics(self):
        if self.idleSearch > 5:
            self.setText("<p style='font-size:20px; color:orange;'>No song playing...</p>"
                         "<p style='font-size:15px; color:gray;'>Please play a song on Spotify and Refresh.</p>")
            return
        if self.current_song == "":
            self.fetch_song_and_lyrics()
        if self.isRefreshed:
            self.setText("<p style='font-size:20px; color:orange;'>Refreshing...</p>")
        elif self.lyrics_data:
            for i, lyric in enumerate(reversed(self.lyrics_data)):
                if lyric["seconds"] <= self.current_time:
                    formatted_current = self.format_text(lyric["lyrics"])
                    prev_line = self.lyrics_data[-(i + 2)]["lyrics"] if i + 1 < len(self.lyrics_data) else ""
                    formatted_prev = self.format_text(prev_line, 50) if prev_line else ""
                    next_line = self.lyrics_data[-i]["lyrics"] if i > 0 else ""
                    formatted_next = self.format_text(next_line, 50) if next_line else ""
                    self.setText(
                        f"<p style='font-size:15px; color:gray;'>{formatted_prev}</p>"
                        f"<p style='font-size:25px; color:cyan;'>{formatted_current}</p>"
                        f"<p style='font-size:15px; color:gray;'>{formatted_next}</p>"
                    )
                    break
        else:
            self.setText("<p style='font-size:20px; color:cyan;'>No lyrics found.</p>")
        self.current_time += 1

    def get_current_playback_time(self):
        track = self.spotify.currently_playing()
        if track and track["is_playing"]:
            self.song_duration = int(track["item"]["duration_ms"])
            playback_time = track["progress_ms"] / 1000
            return playback_time
        return 0
