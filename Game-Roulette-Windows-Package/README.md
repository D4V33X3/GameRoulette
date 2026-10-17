# Game Roulette — Windows package

This package includes the Game Roulette source, its launcher-cover feature, a custom neon Game Roulette app icon, and a Windows build script to create a standalone desktop app. The icon is applied to the built EXE and the application window.

## Recommended: build a standalone Windows app

1. Extract this ZIP to a folder you own, such as `Documents\Game Roulette`. Do not build it inside `C:\Program Files`.
2. Install Python 3.10 or newer from <https://www.python.org/downloads/windows/> if it is not already installed. This is only needed to build the app, not to run the finished executable. You do not need to tick any option that requires administrator access; if the installer offers **Install for all users**, leave it unchecked.
3. Double-click **Build Game Roulette.bat**. It creates a local `.venv`, downloads the build dependencies, and packages the app. Internet access is needed for the first build. It should not request administrator access.
4. When it says the build succeeded, open `dist\Game Roulette\` and double-click `Game Roulette.exe`.
5. Keep the entire `dist\Game Roulette` folder together. You can move or copy that folder to another location you can write to. Do not copy only the EXE, because its bundled files are beside it.

The executable is configured to request the same permissions as the user who launches it (`asInvoker`), not administrator permissions. Game Roulette settings and cached covers remain in your user profile.

## About Windows Defender SmartScreen

This build is not digitally signed. Windows may still show **Windows protected your PC** or another reputation warning for a new, unsigned app. Packaging alone cannot guarantee that SmartScreen will stop warning. Do not turn off Defender or lower your Windows security settings to run it. If you plan to share the app publicly, the proper long-term solution is to sign releases with a trusted code-signing certificate and distribute consistent builds. Even signed apps can be scanned or blocked if Microsoft Defender identifies a real threat.

If Microsoft Defender shows a malware detection rather than a SmartScreen reputation warning, do not bypass it; check the detection and investigate the build first.

## Run from source instead

`Run Game Roulette.bat` starts the Python version. It installs requirements into your current Python environment, so the standalone build above is preferred for everyday use.

## Launcher cover art

When you manually import launcher games, Game Roulette tries to find cover art using the public Steam Store search API. Exact normalized title matches are accepted to reduce incorrect covers. Some games may not have a match. No launcher login or credentials are used.

## Automatic prebuilt Windows downloads (GitHub Releases)

This repository includes a GitHub Actions workflow at `.github/workflows/windows-release.yml`.

- To test a build, open **Actions → Build Windows release → Run workflow**. The ZIP appears under the run's **Artifacts** section.
- To publish a downloadable release, push a version tag such as `v1.0.0`. GitHub Actions builds the app on a Windows runner and attaches `Game-Roulette-Windows.zip` to that GitHub Release.
- The ZIP contains the complete `Game Roulette` folder. Extract it and run `Game Roulette.exe`; do not move the EXE out of its folder.

The build workflow has not been run in this environment. Check the Actions run and test the generated ZIP on Windows before sharing it publicly. An unsigned build may still trigger Windows SmartScreen.
