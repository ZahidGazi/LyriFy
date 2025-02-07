import os
from logger import logger

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtGui import QIcon
from config import load_config, CONFIG_FILE
from auth import create_spotify_oauth

class MainWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LyriFy")
        self.setWindowIcon(QIcon("res/icon.ico"))
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.resize(300, 200)

        # Button to launch the lyrics widget
        self.add_widget_button = QPushButton("Add Lyrics Widget")
        self.add_widget_button.clicked.connect(self.launch_widget)
        self.layout.addWidget(self.add_widget_button)

        # Button to clear the config file
        self.clear_config_button = QPushButton("Clear Config")
        self.clear_config_button.clicked.connect(self.clear_config)
        self.layout.addWidget(self.clear_config_button)
        
        # Button to change configuration
        self.change_config_button = QPushButton("Change Config")
        self.change_config_button.clicked.connect(self.change_config)
        self.layout.addWidget(self.change_config_button)

        config = load_config()
        if not config:
            QMessageBox.critical(self, "Error", "No configuration found. Please run the setup.")
            self.sp_oauth = None
            self.token_info = None
        else:
            try:
                self.sp_oauth = create_spotify_oauth(
                    config["SPOTIPY_CLIENT_ID"],
                    config["SPOTIPY_CLIENT_SECRET"],
                    config["SPOTIPY_REDIRECT_URI"]
                )
                self.token_info = self.sp_oauth.get_cached_token()
            except Exception as e:
                logger.error(f"Failed to authenticate: {e}")
                QMessageBox.critical(self, "Error", "Failed to authenticate: Please run the setup again.")
                self.sp_oauth = None
                self.token_info = None
    def launch_widget(self):
        if not self.token_info:
            QMessageBox.critical(self, "Error", "No token found. Please reauthenticate.")
            return
        from ui.lyrics_overlay import LyricsOverlay
        self.lyrics_overlay = LyricsOverlay(self.sp_oauth, self.token_info)
        self.lyrics_overlay.show()
        self.hide()

    def clear_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                os.remove(CONFIG_FILE)
                QMessageBox.information(self, "Clear Config", "Configuration cleared successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear config: {e}")
        else:
            QMessageBox.information(self, "Clear Config", "No configuration file exists.")

    def change_config(self):
        from ui.setup_window import SetupWindow
        self.hide()  # Hide current MainWindow
        self.setup_window = SetupWindow()
        self.setup_window.show()
