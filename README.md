# LyriFy

LyriFy is a Windows application that displays synchronized song lyrics from Spotify in a draggable, transparent widget overlay. It uses Spotify’s OAuth authentication and the [Spotipy](https://spotipy.readthedocs.io/) library to retrieve currently playing tracks and their lyrics (via a lyrics API). The user interface is built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/).

## Table of Contents

- [Features](#features)
- [Installation & Usage](#installation--usage)
  - [Getting Spotify API Credentials](#getting-spotify-api-credentials)
  - [Running in Development](#running-in-development)
  - [Building the EXE](#building-the-exe)
  - [Creating an Installer with Inno Setup](#creating-an-installer-with-inno-setup)
- [Dependencies](#dependencies)
- [License](#license)

## Features

- **Spotify Authentication:** Authenticate with Spotify using OAuth.
- **Transparent Lyrics Widget:** Displays the current track’s lyrics in a draggable overlay.
- **User Configuration:** Easily update or clear your Spotify credentials via the UI.

## Installation & Usage

### Getting Spotify API Credentials

To use LyriFy, you need to set up a Spotify Developer account and get API credentials:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Click **Login** and sign in with your Spotify account.
3. Click **Create an App** and enter the required details.
4. Once the app is created, go to **Settings** and set the Redirect URI to:
   ```
   http://localhost:8888/callback/
   ```
5. Copy the **Client ID** and **Client Secret**—you will need these to authenticate LyriFy.

### Running in Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ZahidGazi/LyriFy.git
   cd LyriFy
   ```
2. **Install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python main.py
   ```
   - Enter your Spotify Client ID, Client Secret, and Redirect URI.
   - Click **Authenticate with Spotify** to log in.
   - Once authenticated, click **Add Lyrics Widget** to launch the overlay.

### Building the EXE

You can package the application into a standalone executable using [PyInstaller](https://www.pyinstaller.org/).

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```
2. **Build the EXE:**
   ```bash
   pyinstaller --onefile --noconsole --windowed --name LyriFy main.py --add-data "res/icon.ico;res" --icon=res/icon.ico
   ```
   - The resulting executable will be in the `dist` folder.

### Creating an Installer with Inno Setup

1. **Download and install [Inno Setup](http://www.jrsoftware.org/isinfo.php).**
2. **Create an Inno Setup script** (example provided in the repository).
3. **Compile the script with Inno Setup** to generate an installer.

## Dependencies

- [PyQt6](https://pypi.org/project/PyQt6/)
- [Spotipy](https://pypi.org/project/spotipy/)
- [Requests](https://pypi.org/project/requests/)
- [PyInstaller](https://pypi.org/project/pyinstaller/)

Install dependencies using:
```bash
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License.  

**You MUST include the original MIT License file in any distribution, modification, or derivative work of this project.**    

For more details, see the [LICENSE](LICENSE.txt) file.
