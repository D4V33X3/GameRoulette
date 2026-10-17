# 🎮 Game Roulette

**Let the wheel decide what you play next!**

Game Roulette is a Windows desktop application designed to help gamers decide what to play from their game collection. Instead of spending ages browsing launchers and scrolling through your library, add your games to a wheel, spin it, and let chance choose your next adventure.

Whether you play PC games, retro games, or a mixture of both, Game Roulette gives you a simple way to discover something to play.

---

## 📖 Table of Contents

- [Features](#-features)
- [How Game Roulette Works](#-how-game-roulette-works)
- [Supported Game Sources](#-supported-game-sources)
- [Steam Online Library Import](#-steam-online-library-import)
- [Managing Your Games](#-managing-your-games)
- [Themes and Appearance](#-themes-and-appearance)
- [Cover Art](#-cover-art)
- [Installation](#-installation)
- [How to Use](#-how-to-use)
- [Building from Source](#-building-from-source)
- [Privacy and API Keys](#-privacy-and-api-keys)
- [Known Limitations](#-known-limitations)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Credits](#-credits)

---

## ✨ Features

### 🎡 Game Roulette Wheel

- Add games to your personal roulette wheel.
- Spin the wheel to randomly select a game.
- Display the winning game when the wheel stops.
- Enjoy a visual way to choose your next game instead of endlessly browsing your collection.

### 🎮 Game Library Management

- Maintain a collection of games in one place.
- Add games to your library.
- Remove an individual game using **Remove Selected Game**.
- Clear your entire game collection using **Remove All Games**, with confirmation before removing everything.
- Manage the games available for random selection.

### 🕹️ Game Launcher Integration

Game Roulette can help discover locally installed games from supported launchers, including:

- Steam
- Epic Games Launcher
- GOG Galaxy
- Ubisoft Connect
- EA app
- Xbox app

Local discovery depends on the launcher, installation method, and available information on your computer. Not every game or launcher installation will necessarily be detected.

Launcher scanning and importing are intended to be user-initiated. Game Roulette should not automatically scan and import every launcher library without your permission.

### ☁️ Steam Online Library Import

Game Roulette supports importing a Steam library through Steam's Web API.

This can help you add eligible games from your Steam account even if they are not currently installed on your computer.

You will need:

- Your SteamID64.
- A Steam Web API key.
- A Steam profile and game library accessible through the API.

**Important:** An imported game that is not installed locally cannot be launched until you install it. Online library import adds games to your collection; it does not download or install them.

Online library importing for Epic Games, GOG, Ubisoft Connect, EA, and Xbox is not currently implemented.

### 🖼️ Game Cover Art

- Display cover artwork for games where artwork is available.
- Use a local cover-art folder to organise your own images.
- Give your collection a more visual, game-library-style appearance.

Artwork availability depends on the images provided or configured. Some games may need their cover art added manually.

### 🪟 Glass-Style Interface

Game Roulette includes a glass-inspired interface and multiple themes, allowing you to choose an appearance that suits your setup.

The available themes include different visual styles, with dark and colourful options designed to complement a gaming desktop.

### 💿 Retro Game Support

Game Roulette can also be used to organise retro games and ROM-based collections.

Its ROM scanning functionality can help discover supported files, while CUE/BIN duplicate handling helps prevent the same disc-based game from appearing multiple times when its files are scanned together.

Supported file types and launch behaviour depend on the configured paths, files, and any required emulators.

---

## 🎡 How Game Roulette Works

The basic process is simple:

1. Add games to your collection.
2. Import games from a supported local source, or import your eligible Steam library online.
3. Review your collection and remove any games you do not want included.
4. Spin the roulette wheel.
5. Let Game Roulette choose a winner.
6. Launch the selected game if it is installed and a valid launch method is available.

The goal is to make choosing a game quicker, easier, and more fun.

---

## 🎮 Supported Game Sources

Game Roulette is designed to work with a mixture of modern PC games and retro game collections.

| Source | Current support |
|---|---|
| Steam | Local discovery and online library import |
| Epic Games Launcher | Local discovery where detectable |
| GOG Galaxy | Local discovery where detectable |
| Ubisoft Connect | Local discovery where detectable |
| EA app | Local discovery where detectable |
| Xbox app | Local discovery where detectable |
| ROM collections | Local scanning for supported files |
| Other games | Can be added manually where the application supports it |

**Please note:** Local discovery is not the same as online account integration. Game Roulette does not currently provide online library importing for every launcher listed above.

---

## ☁️ Steam Online Library Import

Steam online import is useful if you have a large library and want to include games you have not installed.

### What you need

**1. Your SteamID64**

Your SteamID64 is the numeric identifier associated with your Steam account.

**2. A Steam Web API key**

You can request a key through the official Steam Community developer page:

https://steamcommunity.com/dev/apikey

Only enter your API key into the application or configuration field intended for it. Do not publish your key in screenshots, GitHub commits, public issues, or shared configuration files.

**3. An accessible Steam library**

Steam's API visibility rules can affect which games are returned. Private or restricted library information may not be available.

### What the import does

- Retrieves eligible games from your Steam library.
- Helps you include games that are not installed.
- Adds imported titles to your Game Roulette collection.

Importing games does not install them or guarantee that every title can be launched directly.

---

## 🧹 Managing Your Games

Game Roulette includes controls to help keep your collection organised.

### Remove Selected Game

Use this when you want to remove one game without affecting the rest of your collection.

### Remove All Games

Use this when you want to clear the entire collection and start again.

The application asks for confirmation before carrying out the remove-all action, helping to prevent accidental deletion.

**Always read confirmation prompts carefully before clearing your collection.**

---

## 🎨 Themes and Appearance

Game Roulette includes six visual themes, alongside its glass-inspired interface styling.

The themes are intended to let you personalise the application's appearance while keeping the main purpose clear: browsing your games and choosing what to play.

---

## 🖼️ Cover Art

Game cover art makes it easier to recognise games at a glance and gives your collection a more visual layout.

Where supported, you can use a local cover folder to keep artwork organised.

If a cover is missing, check that the correct image exists and that it is stored in the expected location. Artwork is not guaranteed to be available for every title.

---

## 💻 Installation

### Option 1: Download a Windows release

1. Open the project's **Releases** page on GitHub.
2. Open the latest stable release.
3. Download the Windows ZIP file if one is attached to that release.
4. Extract the ZIP file to a folder on your computer.
5. Open the extracted folder.
6. Run `Game Roulette.exe` if the executable is included.

Do not run the application directly from inside the compressed ZIP.

**Windows security note:** If the downloaded executable is unsigned, Windows may show a Microsoft Defender SmartScreen warning. This is not, by itself, proof that an application is malicious, but it also does not prove the application is safe. Only download Game Roulette from the official project repository, and do not bypass a warning unless you have independently verified the file and trust its source.

If the release contains only source code and no Windows executable ZIP, use the source-code instructions below.

### Option 2: Run from source

You will need:

- Windows.
- Python 3.12 or a compatible version supported by the project.
- Git, or a downloaded copy of the repository.

Steps:

1. Download or clone the repository.
2. Extract the files if you downloaded a ZIP.
3. Open the project folder.
4. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the application:

   ```bash
   python game_roulette.py
   ```

If your copy of the project contains a `Run Game Roulette.bat` file, you can also use that launcher if it is configured for your installation.

---

## 🛠️ Building from Source

Developers can build a Windows executable using the included build scripts.

### Requirements

- Windows.
- Python 3.12, as used by the current Windows build workflow.
- The dependencies listed in `requirements.txt`.
- PyInstaller.
- The application's icon file.

### Build using the included script

If your project copy includes `Build Game Roulette.bat` or `Build-Windows.ps1`, open or run the appropriate build script and follow its instructions.

The repository's automated Windows build uses GitHub Actions to build the application on a Windows runner and package the resulting files into a ZIP archive.

### Build manually

From the project folder, install the required dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller PySide6
```

Then run the project's build script if available. The exact PyInstaller arguments should match the current build workflow so that the application includes its required Qt files and icon.

The resulting executable and supporting files should be tested on a Windows computer before publishing a release.

---

## 🔐 Privacy and API Keys

Game Roulette's local game discovery may inspect supported launcher data or installation locations when you explicitly request a scan or import.

Steam online import uses the Steam Web API and requires a SteamID64 and API key.

Keep your API key private:

- Do not commit API keys to GitHub.
- Do not share configuration files containing secrets.
- Do not post your key in bug reports or screenshots.
- Revoke and replace a key if you believe it has been exposed.

Online imports depend on the relevant service's API availability, permissions, and privacy settings.

Refer to the current source code to understand exactly how settings, imported game information, and any API credentials are stored.

---

## ⚠️ Known Limitations

Game Roulette is an evolving project. The following limitations are important to understand:

- **Launcher detection:** Local discovery depends on information available on the computer. Some games may not be detected.
- **Online imports:** Steam online library import is supported; online library imports for the other listed launchers are not currently implemented.
- **Uninstalled games:** A game can appear in an imported library without being installed. It cannot be launched until it is installed and a valid launch path is available.
- **Steam visibility:** Private profiles and restricted API data may prevent some games from being imported.
- **Cover artwork:** Some titles may not have artwork available automatically.
- **ROM compatibility:** Scanning and launching depend on supported files, paths, and any required emulator configuration.
- **Executable signing:** Windows builds may be unsigned. SmartScreen warnings can occur, particularly for new downloads.
- **Compatibility:** Game Roulette is primarily intended for Windows desktop use. Other operating systems are not guaranteed to work.

---

## 🧰 Troubleshooting

### The application will not open

- Extract the downloaded ZIP completely.
- Check that you have downloaded the Windows build rather than the source-code archive.
- Try launching the executable from its extracted folder.
- If you built from source, confirm that Python and the dependencies installed correctly.

### Some games are missing

- Run the relevant local scan or import yourself.
- Check the installation paths and launcher data.
- For Steam online import, verify the SteamID64, API key, and library visibility settings.

### A game appears but will not launch

- Confirm that the game is installed.
- Check whether the launcher or executable path is valid.
- Some games require their original launcher or additional configuration.

### Steam online import returns no games

- Verify your SteamID64.
- Verify that your API key is correct.
- Check the visibility of your Steam profile and game details.
- Confirm that the Steam API is available and that the account's information can be accessed.

### Cover art is missing

- Check the local cover-art folder and file names.
- Confirm that the image is in a supported format.
- Add the missing artwork manually if necessary.

### Windows shows a security warning

Only download the application from the official GitHub repository. An unsigned application may receive a warning even when it is not malicious. Do not assume a file is safe merely because it has a familiar name.

---

## 🗺️ Roadmap

Possible future improvements include:

- Additional launcher integrations.
- More reliable game detection and import.
- Further library management options.
- Improvements to cover-art handling.
- Additional themes and interface refinements.
- Continued improvements to Windows packaging and distribution.

The roadmap may change as the project develops. Features listed as future improvements should not be considered implemented until they appear in a released version.

---

## 📜 License

Game Roulette is distributed under the licence included in this repository.

Please read the `LICENSE` file before using, modifying, or redistributing the project.

Do not assume that the project permits commercial resale or redistribution unless the actual licence explicitly grants those rights.

---

## 🙌 Credits

- **PySide6 / Qt** — desktop application interface.
- **PyInstaller** — packaging Python applications into Windows executables.
- **Steam Web API** — Steam library data used by the online import feature.
- **GitHub Actions** — automated Windows builds and release packaging.

Game Roulette is an independent project and is not affiliated with or endorsed by Steam, Epic Games, GOG, Ubisoft, Electronic Arts, Xbox, or their respective owners.

---

## ❤️ Enjoy Your Games!

Game Roulette is built to make choosing your next game less of a chore and more of an adventure.

Add your games, spin the wheel, and see where your next gaming session takes you.

**Stop scrolling. Start spinning.** 🎮

