import sys
from PyQt6.QtWidgets import QApplication
from config import load_config
from ui.setup_window import SetupWindow
from ui.main_window import MainWindow
import globals 

def main():
    app = QApplication(sys.argv)
    config = load_config()
    if config.get("SPOTIPY_CLIENT_ID") and config.get("SPOTIPY_CLIENT_SECRET") and config.get("SPOTIPY_REDIRECT_URI"):
        window = MainWindow()
    else:
        window = SetupWindow()
    globals.main_window = window  
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
