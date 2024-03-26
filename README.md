# PlaytimeTrackerApp
PlaytimeTrackerApp enhances Playnite's tracking accuracy by monitoring playtime alongside game executables. It ensures precise tracking for games with non-standard launch methods, such as intermittent executable launches or additional launchers.

## Details

PlaytimeTrackerApp operates seamlessly alongside game executables, ensuring accurate playtime tracking for games in Playnite that have unconventional launch methods. Key features and components of the app include:

- **Accurate Tracking**: By monitoring playtime alongside game executables, PlaytimeTrackerApp ensures precise tracking even for games with non-standard launch methods.

- **User-friendly Interface**: The application provides a user-friendly interface for configuring preferences and monitoring tracking status.

-  **Adding Games**: It's very simple to add games, just press the "browse" button and point to the game's .exe file. 

- **Configuration**: PlaytimeTrackerApp uses a configuration file (config.ini) to store and load user preferences.

- **Threaded Execution**: PlaytimeTrackerApp executes the tracking process in a separate thread, preventing freezing of the user interface during operation.

- **Exit Handling**: The application saves user preferences upon closing, ensuring that settings are retained for future sessions.

## Usage

First, you need to add the PlaytimeTrackerApp as the game .exe in Playnite, do this by going onto the game in Playnite and opening the "game details" window.
Next you go into the "Actions" section and set the "Path" to your "Playtime Tracker.exe".

You will have to add a batch script command (can also be PowerShell & IronPython) to start the game in Playnite, seen as it will be starting the tracker instead of the game.

Some games can be started directly from the .exe but others might need you to instead load the launcher or a shortcut (.lnk) that's up to you to work out what's best for the game.

PlaytimeTrackerApp will then run alongside the game executable/launcher when opened in Playnite and exits with it (allows Playnite to track playtime & if minimised, the Playnite window restores correctly).

----------------------------------------------------------------------------

Example command to start the game "Bully" in Playnite.

from shortcut:

START /D "G:\My Drive\Gaming Files\Starters\PLAYNITE START\Bully" "" "Bully.lnk"

from exe:

START /D "G:\My Drive\Gaming Files\Starters\PLAYNITE START\Bully" "" "Bully.exe"
