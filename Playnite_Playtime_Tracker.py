import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Menu
import os
import json
import configparser
import psutil
import threading
import time
import sys
import urllib.request
import urllib.error
import io
from PIL import Image, ImageTk, ImageFilter, ImageDraw
import webbrowser
import pystray
from pystray import MenuItem as item
import atexit
import socket

MAX_RETRIES = 5
BASE_DELAY = 3  # Initial delay in seconds

# Define icon_image globally or in a scope accessible to all functions
icon_image = None

def fetch_image(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    request = urllib.request.Request(url, headers=headers)
    retries = 0

    while retries < MAX_RETRIES:
        try:
            with urllib.request.urlopen(request) as response:
                return response.read()
        except Exception as e:
            print(f"Error fetching image: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                print(f"Retrying in {BASE_DELAY} seconds...")
                time.sleep(BASE_DELAY)

    print("Max retries reached. Unable to fetch image.")
    return None

class GameLinkApp:
    def __init__(self, master):
        self.icon_image = None  # Define icon_image attribute
        self.monitor_started = False  # Add monitor_started attribute
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.master = master
        self.master.title("Playtime Tracker")

        # Calculate screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Calculate window width and height
        window_width = 410
        window_height = 340

        # Calculate window position for centering
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Download the icon image from URL
        icon_url = "https://static.wixstatic.com/media/4db758_e30629a0335e4051ae8bc23f3f2c219f~mv2.png/v1/fit/w_500,h_500,q_90/4db758_e30629a0335e4051ae8bc23f3f2c219f~mv2.webp"
        icon_data = fetch_image(icon_url)

        # Convert the downloaded image to a format compatible with tkinter
        if icon_data:
            icon_image = Image.open(io.BytesIO(icon_data))
            icon_photo = ImageTk.PhotoImage(icon_image)

            # Set the window icon
            self.master.iconphoto(True, icon_photo)

        # Watermark
        watermark_font = ("Helvetica", 8)  # Set default font size
        watermark_text = "Designed & Created by: M0VER"
        self.watermark_label = tk.Label(self.master, text=watermark_text, fg="grey", font=watermark_font)
        self.watermark_label.pack(side=tk.BOTTOM)

        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.ini_file = 'Config.ini'

        self.fetch_and_display_image("https://static.wixstatic.com/media/4db758_14e6d6ac8107470d8136d8fbda34c56e~mv2.png/v1/fit/w_256,h_256,q_90/4db758_14e6d6ac8107470d8136d8fbda34c56e~mv2.webp", "https://www.nexusmods.com/users/105540373?tab=user+files")
        
        # Initialize self.config as a ConfigParser object
        self.config = configparser.ConfigParser()

        # Read the INI file
        read_success = self.config.read(self.ini_file)
        print("INI file read status:", read_success)

        # Check if PREFS section is in config
        if 'PREFS' in self.config:
            print("PREFS section found in config.")
        else:
            print("PREFS section not found in config.")
    
        # Initialize minimize_to_tray_enabled using the config value
        self.minimize_to_tray_enabled = self.get_minimize_to_tray_preference()
        #print("Minimize to tray preference from config:", self.minimize_to_tray_enabled)

        # Initialize start_minimized_enabled using the config value
        self.start_minimized_enabled = self.get_start_minimized_preference()
        print("Start minimized preference from config:", self.start_minimized_enabled)

        # Check if INI file exists, create if not
        if not os.path.exists(self.ini_file):
            self.create_ini_file()

        # Read existing config
        self.config.read(self.ini_file)

        # Check if GAME_LINKS section exists, create if not
        if 'GAME_LINKS' not in self.config:
            self.config['GAME_LINKS'] = {}
            with open(self.ini_file, 'w') as configfile:
                self.config.write(configfile)

        # Check if PREFS section exists, create if not
        if 'PREFS' not in self.config:
            self.config['PREFS'] = {}
            with open(self.ini_file, 'w') as configfile:
                self.config.write(configfile)

        self.frame = tk.Frame(self.master)
        self.frame.pack(padx=20, pady=20)

        self.label = tk.Label(self.frame, text="Add Game .exe File:")
        self.label.grid(row=0, column=0, padx=90, pady=10)  # Center horizontally

        self.browse_button = tk.Button(self.frame, text="Browse", command=self.browse_file, cursor="hand2")
        self.browse_button.grid(row=1, column=0, padx=5, pady=5)  # Center horizontally

        self.games_listbox = tk.Listbox(self.frame, width=50)
        self.games_listbox.grid(row=2, column=0, columnspan=2, pady=10)
        self.populate_games_listbox()

        # Bind key events for loading config (CTRL+O) and saving config (CTRL+S)
        master.bind("<Control-o>", self.reload_ini_file)
        master.bind("<Control-s>", self.save_ini_file)

        self.games_listbox.bind('<Delete>', self.delete_game)  # Bind the Delete key to delete_game method
        self.games_listbox.bind("<MouseWheel>", self.scroll_listbox)

        self.tracking_label = tk.Label(self.frame, text="Currently Tracking: NONE")
        self.tracking_label.grid(row=3, column=0, columnspan=2)

        # Create File menu
        self.menu_bar = Menu(master)
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Reload Config", command=self.reload_ini_file)
        self.file_menu.add_command(label="Save Config", command=self.save_ini_file)  # Add Save INI File option
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.master.config(menu=self.menu_bar)

        # Create Settings menu
        self.settings_menu = Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Add To Icon Tray", command=self.toggle_minimize_to_tray)
        self.settings_menu.add_command(label="Start Minimized", command=self.toggle_start_minimized)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

        # Create Help menu
        self.help_menu = Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Keybinds", command=self.show_keybinds)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Playnite Script", command=self.show_script)
        self.help_menu.add_command(label="Preferences", command=self.show_prefs)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Start monitoring game processes
        self.monitor_thread = threading.Thread(target=self.monitor_games)
        self.monitor_thread.daemon = True  # Daemonize the thread so it exits when the main program exits
        self.monitor_thread.start()

        # Minimize to tray
        self.minimize_to_tray(icon_data)

    def toggle_start_minimized(self):
        # Toggle the preference value
        self.start_minimized_enabled = not self.start_minimized_enabled
        # Update the preference in config.ini
        self.set_start_minimized_preference(self.start_minimized_enabled)

    def get_start_minimized_preference(self):
        # Read the preference from config.ini, default to False if not found
        if 'PREFS' in self.config and 'start_minimized_enabled' in self.config['PREFS']:
            pref_value = self.config['PREFS'].getboolean('start_minimized_enabled')
            print("Start minimized preference read from config:", pref_value)
            return pref_value
        else:
            print("Start minimized preference not found in config. Defaulting to False.")
            return False
    
    def set_start_minimized_preference(self, value):
        # Set the preference in config.ini
        if 'PREFS' not in self.config:
            self.config['PREFS'] = {}
        self.config['PREFS']['start_minimized_enabled'] = str(value)
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def start_minimized(self):
        if self.start_minimized_enabled:
            self.master.iconify()  # Minimize the window when starting the application

    def minimize_to_tray(self, image_data):
        # Check if the preference is enabled before minimizing to tray
        if not self.minimize_to_tray_enabled:
            #print("Minimize to tray preference is disabled. Not minimizing to tray.")
            return

        try:
            icon_image = Image.open(io.BytesIO(image_data))
        except FileNotFoundError:
            print("Error: Image data not found.")
            return
    
        def on_tray_clicked(icon, item):
            # Restore the application window
            self.master.after(0, lambda: self.master.deiconify())  # Call deiconify from the main thread

        menu = pystray.Menu(pystray.MenuItem("Open", on_tray_clicked))

        self.tray = pystray.Icon("Playtime Tracker", icon_image, "Playtime Tracker", menu)

        # Run tray in a separate thread to avoid blocking the main thread
        tray_thread = threading.Thread(target=self.tray.run)
        tray_thread.daemon = True
        tray_thread.start()

        # Register a function to remove the tray icon and exit the application when it's closed
        atexit.register(lambda: self.tray.stop())

    def toggle_minimize_to_tray(self):
        # Toggle the preference value
        self.minimize_to_tray_enabled = not self.minimize_to_tray_enabled
        # Update the preference in config.ini
        self.set_minimize_to_tray_preference(self.minimize_to_tray_enabled)

    def get_minimize_to_tray_preference(self):
        # Read the preference from config.ini, default to True if not found
        if 'PREFS' in self.config and 'minimize_to_tray_enabled' in self.config['PREFS']:
            pref_value = self.config['PREFS'].getboolean('minimize_to_tray_enabled')
            #print("Preference value read from config:", pref_value)
            return pref_value
        else:
            #print("Preference not found in config. Defaulting to True.")
            return False
    
    def set_minimize_to_tray_preference(self, value):
        # Set the preference in config.ini
        if 'PREFS' not in self.config:
            self.config['PREFS'] = {}
        self.config['PREFS']['minimize_to_tray_enabled'] = str(value)
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
    
    def show_window(self):
        # Function to restore the application window when clicked on the tray icon
        self.master.deiconify()

    def show_keybinds(self):
        keybinds_info = """
Delete Game: DEL key
Load Config: CTRL+O
Save Config: CTRL+S
        """
        messagebox.showinfo("Keybinds", keybinds_info)

    def show_prefs(self):
        keybinds_info = """
Add To Icon Tray: Adds an icon to the system icon tray.

Start Minimized: Starts the app minimized.
        """
        messagebox.showinfo("Preferences", keybinds_info)

    def show_about(self):
        about_info = r"""
This application allows Playnite to track the playtime of games that use a launcher OR the apllication stops and restarts.

To start tracking games, add their .exe file paths using the Browse button and give them a name.

Games can be deleted from the list using the Delete key.

Add the exe for Playnite Tracker as the game exe in playnite.

Start the game by adding in a batch script command to start the .exe OR shortcut to the game you wish to start in PLaynite Game Details (Script tab).
        """
        messagebox.showinfo("About", about_info)

    def show_script(self):
        about_info = r"""
You will have to add a batch script command to start the game, seen as playnite will be starting the tracker instead of the game.

Some games can be started directly from the .exe but others might need you to instead load the laucnher or a shortcut (.lnk) that's up to you to work out what's best for the game.

Firstly, you need to add the Playnite Tracker as the game .exe, do this by going onto the game in Playnite and opening the "game details" window.
Then you go into the "Actions" section and set the "Path" to Playnite Tracker.

Next we add the command to start the game. In the "game details" window go into the "Scripts" tab.

----------------------------------------------------------------------------

example command to start the game "Bully"

from shortcut:

START /D "G:\My Drive\Gaming Files\Starters\PLAYNITE START\Bully" "" "Bully.lnk"

from exe:

START /D "G:\My Drive\Gaming Files\Starters\PLAYNITE START\Bully" "" "Bully.exe"
        
        """
        messagebox.showinfo("About", about_info)

    def fetch_and_display_image(self, image_url, click_url):
        image_data = fetch_image(image_url)
        if image_data:
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((50, 50), Image.LANCZOS)  # Resize the image with antialiasing using LANCZOS filter

            # Create a circular mask
            mask = Image.new("L", (image.width, image.height), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, mask.width, mask.height), fill=255)

            # Apply the circular mask to the image
            image = Image.composite(image, Image.new("RGBA", (image.width, image.height), (0, 0, 0, 0)), mask)

            photo = ImageTk.PhotoImage(image)

            # Create a label to display the image
            self.image_label = tk.Label(self.master, image=photo)
            self.image_label.image = photo  # Keep a reference to the image to prevent it from being garbage collected

            # Bind a callback function to the label to open the click URL
            self.image_label.bind("<Button-1>", lambda event, url=click_url: webbrowser.open(url))

            # Change cursor to hand when hovering over the label
            self.image_label.bind("<Enter>", lambda event: self.image_label.config(cursor="hand2"))

            # Restore default cursor when leaving the label
            self.image_label.bind("<Leave>", lambda event: self.image_label.config(cursor=""))

            # Position the image label in the top right corner
            self.image_label.place(relx=1.0, rely=0, anchor='ne')  # Place in the top right corner

    def browse_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if filepath:
            game_name = self.prompt_for_game_name()
            if game_name:
                link_info = {'name': game_name, 'path': filepath}
                existing_links = self.config['GAME_LINKS']
                existing_paths = {json.loads(value)['path'] for value in existing_links.values()}
                if link_info['path'] in existing_paths:
                    messagebox.showerror("Duplicate Link", "This game has already been added.")
                else:
                    link_key = f'Link{len(existing_links) + 1}'
                    existing_links[link_key] = json.dumps(link_info)
                    self.config['GAME_LINKS'] = existing_links
                    with open(self.ini_file, 'w') as configfile:
                        self.config.write(configfile)
                    self.populate_games_listbox()

    def prompt_for_game_name(self):
        game_name = simpledialog.askstring("Game Name", "Enter the name of the game:")
        return game_name

    def populate_games_listbox(self):
        self.games_listbox.delete(0, tk.END)
        if 'GAME_LINKS' in self.config:
            for link_key, link_info in self.config['GAME_LINKS'].items():
                # Parse the JSON string to extract the name
                name = json.loads(link_info)['name']
                self.games_listbox.insert(tk.END, name)

    def delete_game(self, event=None):
        selected_index = self.games_listbox.curselection()
        if selected_index:
            selected_game = self.games_listbox.get(selected_index)
            for link_key, link_info in list(self.config['GAME_LINKS'].items()):
                if json.loads(link_info)['name'] == selected_game:
                    del self.config['GAME_LINKS'][link_key]
                    with open(self.ini_file, 'w') as configfile:
                        self.config.write(configfile)
                    self.update_link_names()  # Update link names after deletion
                    self.populate_games_listbox()
                    break

    def update_link_names(self):
        # Reorder the link keys in sequential order
        game_links = self.config['GAME_LINKS']
        new_game_links = {}
        for index, (link_key, link_info) in enumerate(game_links.items(), start=1):
            new_link_key = f'link{index}'
            new_game_links[new_link_key] = link_info
        self.config['GAME_LINKS'] = new_game_links
        with open(self.ini_file, 'w') as configfile:
            self.config.write(configfile)
                
    def scroll_listbox(self, event):
        # Adjust the view of the listbox based on mouse wheel motion
        if event.delta < 0:
            self.games_listbox.yview_scroll(1, "units")
        else:
            self.games_listbox.yview_scroll(-1, "units")

    def save_ini_file(self, event=None):  # Add the event parameter with a default value of None
        with open(self.ini_file, 'w') as configfile:
            self.config.write(configfile)

    def reload_ini_file(self, event=None):
        self.config.read(self.ini_file)
        self.populate_games_listbox()

    def create_ini_file(self):
        # Create the INI file with [GAME_LINKS] section
        with open(self.ini_file, 'w') as configfile:
            configfile.write("[GAME_LINKS]\n")

    def on_closing(self):
        self.save_ini_file()
        if hasattr(self, 'tray') and self.minimize_to_tray_enabled:  # Check if tray icon is created and preference is enabled
            self.tray.stop()
            self.master.destroy()
        else:
            self.master.destroy()

    def monitor_games(self):
        # Wait for 5 minutes before starting the monitoring loop
        time.sleep(150)  # in seconds

        game_started = False  # Flag to track if a game has started
        while True:
            current_game = "NONE"
            for link_info in self.config['GAME_LINKS'].values():
                game_path = json.loads(link_info)['path']
                for process in psutil.process_iter(['exe']):
                    try:
                        if process.exe() and os.path.samefile(process.exe(), game_path):
                            current_game = json.loads(link_info)['name']
                            game_started = True  # Set the flag to True if a game is found running
                    except (psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError):
                        # Handle cases where process information cannot be retrieved
                        pass
    
            # Schedule GUI update
            self.master.after(0, lambda: self.update_tracking_label(current_game, game_started))
        
            # Check if a game has started and then stopped running to exit the app
            if game_started and current_game == "NONE":
                print("No game is running. Exiting...")
                self.on_closing()
                break

            time.sleep(10)  # Adjust the sleep time as needed

    def update_tracking_label(self, current_game, game_started):
        # Update tracking label only if a game has started
        if game_started:
            self.tracking_label.config(text=f"Currently Tracking: {current_game}")
        else:
            self.tracking_label.config(text="Currently Tracking: NONE")

LOCK_PORT = 12345  # Choose a port number that is not commonly used

def acquire_lock():
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("localhost", LOCK_PORT))
        return lock_socket
    except socket.error:
        print("Another instance of the app is already running. Exiting...")
        sys.exit(1)

def main():
    # Attempt to acquire a lock
    lock_socket = acquire_lock()

    # Proceed with launching the app
    root = tk.Tk()
    app = GameLinkApp(root)
    # Start minimized if the preference is enabled
    app.start_minimized()
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Call on_closing when window is closed
    root.mainloop()

    # Close the lock socket when the application exits
    lock_socket.close()

if __name__ == "__main__":
    main()
