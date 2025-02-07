import os
import subprocess
import sys
import webbrowser

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtGui import QIcon
from config import save_config, CONFIG_FILE
from auth import create_spotify_oauth
from logger import logger

class SetupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LyriFy - Auth Setup")
        self.setWindowIcon(QIcon("res/icon.ico"))
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.resize(400, 350)

        # Input fields for Spotify credentials
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("SPOTIPY_CLIENT_ID")
        self.layout.addWidget(QLabel("Client ID:"))
        self.layout.addWidget(self.client_id_input)

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("SPOTIPY_CLIENT_SECRET")
        self.layout.addWidget(QLabel("Client Secret:"))
        self.layout.addWidget(self.client_secret_input)

        self.redirect_uri_input = QLineEdit()
        self.redirect_uri_input.setPlaceholderText("SPOTIPY_REDIRECT_URI (e.g. http://localhost:8888/callback)")
        self.layout.addWidget(QLabel("Redirect URI:"))
        self.layout.addWidget(self.redirect_uri_input)

        # Button to launch Spotify auth
        self.auth_button = QPushButton("Authenticate with Spotify")
        self.auth_button.clicked.connect(self.authenticate)
        self.layout.addWidget(self.auth_button)

        # Field to paste the redirected URL after authentication
        self.redirected_url_input = QLineEdit()
        self.redirected_url_input.setPlaceholderText("Paste redirected URL here")
        self.layout.addWidget(QLabel("Redirected URL:"))
        self.layout.addWidget(self.redirected_url_input)

        # Button to complete the authentication
        self.complete_auth_button = QPushButton("Complete Authentication")
        self.complete_auth_button.clicked.connect(self.complete_auth)
        self.layout.addWidget(self.complete_auth_button)

        # Button to add the lyrics widget (enabled only after successful auth)
        self.add_widget_button = QPushButton("Add Lyrics Widget")
        self.add_widget_button.clicked.connect(self.add_widget)
        self.add_widget_button.setEnabled(False)
        self.layout.addWidget(self.add_widget_button)

        # Button to clear configuration
        self.clear_config_button = QPushButton("Clear Config")
        self.clear_config_button.clicked.connect(self.clear_config)
        self.layout.addWidget(self.clear_config_button)

        self.sp_oauth = None
        self.token_info = None

    def open_browser(self, url):
        try:
            if sys.platform == "win32":
                # Build a single command string with proper quoting.
                cmd = 'start "" "{}"'.format(url)
                subprocess.Popen(cmd, shell=True)
            else:
                webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")



    def authenticate(self):
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        redirect_uri = self.redirect_uri_input.text().strip()
        if not (client_id and client_secret and redirect_uri):
            QMessageBox.warning(self, "Missing Info", "Please enter all credentials.")
            return

        # Save credentials to config file
        config = {
            "SPOTIPY_CLIENT_ID": client_id,
            "SPOTIPY_CLIENT_SECRET": client_secret,
            "SPOTIPY_REDIRECT_URI": redirect_uri
        }
        save_config(config)

        self.sp_oauth = create_spotify_oauth(client_id, client_secret, redirect_uri)
        auth_url = self.sp_oauth.get_authorize_url()
        self.open_browser(auth_url)
        QMessageBox.information(
            self, "Authorize",
            "A browser window has been opened. Please log in to Spotify and then paste the redirected URL below."
        )

    def complete_auth(self):
        if not self.sp_oauth:
            QMessageBox.warning(self, "Error", "Please click 'Authenticate with Spotify' first.")
            return
        redirected_url = self.redirected_url_input.text().strip()
        if not redirected_url:
            QMessageBox.warning(self, "Missing URL", "Please paste the redirected URL.")
            return
        code = self.sp_oauth.parse_response_code(redirected_url)
        if code:
            self.token_info = self.sp_oauth.get_access_token(code)
            if self.token_info:
                QMessageBox.information(self, "Success", "Authentication successful!")
                self.add_widget_button.setEnabled(True)
            else:
                QMessageBox.critical(self, "Error", "Failed to obtain token.")
        else:
            QMessageBox.critical(self, "Error", "Failed to parse the code from the URL.")

    def add_widget(self):
        self.hide()
        # Import LyricsOverlay here to avoid circular dependency
        from ui.lyrics_overlay import LyricsOverlay
        self.lyrics_overlay = LyricsOverlay(self.sp_oauth, self.token_info)
        self.lyrics_overlay.show()

    def clear_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                os.remove(CONFIG_FILE)
                QMessageBox.information(self, "Clear Config", "Configuration cleared successfully!")
                self.client_id_input.clear()
                self.client_secret_input.clear()
                self.redirect_uri_input.clear()
                self.redirected_url_input.clear()
                self.add_widget_button.setEnabled(False)
                self.sp_oauth = None
                self.token_info = None
            except Exception as e:
                logger.error(f"Failed to clear config: {e}")
                QMessageBox.critical(self, "Error", f"Failed to clear config: {e}")
        else:
            QMessageBox.information(self, "Clear Config", "No configuration file exists.")
