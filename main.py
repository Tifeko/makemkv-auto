import subprocess
import csv
import os
import requests
import tkinter as tk
import json
import time
import pyudev
import shutil
import threading
from pathlib import Path
from tkinter import simpledialog
from dotenv import load_dotenv
from os import listdir
from os.path import isfile, join

load_dotenv()
drive_number = 0
output_folder_root = "output"
minlength_title = 100
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
release_year = None
movie_name = None
movie_id = None
listbox_extra = None
output_folder_extra = None
extra_disc = None
movie = None
root_extra = None
discord = True
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")
handbrake_flatpak = True

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('block')

def get_disc_label(device):
    try:
        # 'volname' works on many Linux systems
        result = subprocess.check_output(["volname", device], text=True).strip()
        if result:
            return result
    except Exception:
        pass
    
    try:
        # fallback: use lsblk to extract LABEL
        result = subprocess.check_output(["lsblk", "-no", "LABEL", device], text=True).strip()
        if result:
            return result
    except Exception:
        pass
    
    return None

def select_movie(event=None):
    global release_year, movie_name, movie_id, listbox_extra, output_folder_extra, extra_disc, root_extra
    selection = listbox.curselection()
    if selection:
        if selection == (0,):
            extra_disc = True
            root.destroy()
            root_extra = tk.Tk()
            root_extra.title("Selecteer de film?")
            listbox_extra = tk.Listbox(root_extra, height=15, width=60)
            listbox_extra.pack(pady=10)
            output_folder_extra = [f for f in listdir(output_folder_root)]
            for movie in output_folder_extra:
                listbox_extra.insert(tk.END, movie)
            listbox_extra.bind("<Double-1>", extra_selecteren)
            listbox_extra.bind("<Return>", extra_selecteren)
        else:
            extra_disc = False
            index = selection[0]
            index = index - 1
            movie = movies_data[index]

            # los opslaan
            release_year = movie["release_date"].split("-")[0]
            movie_name = movie["title"]
            movie_id = movie["id"]

            root.destroy()  # sluit venster

def extra_selecteren(event=None):
    global movie, root_extra
    selection = listbox_extra.curselection()
    index = selection[0]
    movie = output_folder_extra[index]
    root_extra.destroy()


def handbrake(folder):
    print(f"Starting Handbrake with extras: {extra_disc}")
    if extra_disc:
        print(f"Starting Handbrake with extras and {folder}")
        directory = Path(folder)
        for file in directory.rglob("*"):  # rglob allows recursion
            if file.is_file():
                print(f"Transcoding: {file}")
                file_path = Path(file)
                subprocess.run(["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb", "-i", file, "-o", f"{output_folder_root}/{movie}/extras/{file_path.name}", "--preset-import-file", "preset.json"])
        shutil.remove(folder)
    else:
        os.rename(folder, f"{folder}_old")
        os.makedirs(folder)
        os.makedirs(f"{folder}/extras")
        directory = Path(f"{folder}_old")
        for file in directory.rglob("*"):  # rglob allows recursion
            if file.is_file():
                print(f"Transcoding: {file}")
                if "/extras/" in str(file).replace("\\", "/"):
                    extras_file = Path(file)
                    subprocess.run(["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb", "-i", file, "-o", f"{folder}/extras/{extras_file.name}", "--preset-import-file", "preset.json"])
                    
                else:
                    file_path = Path(file)
                    subprocess.run(["flatpak", "run", "--command=HandBrakeCLI", "fr.handbrake.ghb", "-i", file, "-o", f"{folder}/{file_path.name}", "--preset-import-file", "preset.json"])

while True:
    print("Waiting for Disc")
    for device in iter(monitor.poll, None):
        if 'sr' in device.device_node:
            # Only trigger if media is present
            if device.get('ID_CDROM_MEDIA') == '1':
                break

    disc_name = get_disc_label(f"/dev/sr{drive_number}")

    print(f"Disc Inserted: {disc_name}")

    #get list of movies:

    url = f"https://api.themoviedb.org/3/search/movie?query={disc_name}&include_adult=false&language=en-US&page=1"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    response = requests.get(url, headers=headers)

    if response.text == '{"page":1,"results":[],"total_pages":1,"total_results":0}':
        print("niets gevonden")
        film = simpledialog.askstring("makemkv-auto", "Wat is de naam van de film?")
        url = f"https://api.themoviedb.org/3/search/movie?query={film}&include_adult=false&language=en-US&page=1"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_API_KEY}"
        }

        response = requests.get(url, headers=headers)
        movies = json.loads(response.text)
        movies_data = movies["results"]
        root = tk.Tk()
        root.title("Selecteer de film?")
        listbox = tk.Listbox(root, height=15, width=60)
        listbox.pack(pady=10)
        listbox.insert(tk.END, "Extra")
        for movie in movies_data:
            listbox.insert(tk.END, f"{movie["title"]} ({movie["release_date"].split("-")[0]})")
        listbox.bind("<Double-1>", select_movie)
        listbox.bind("<Return>", select_movie)
        root.mainloop()
        print("Naam:", movie_name)
        print("Release jaar:", release_year)
        print("ID:", movie_id)
    else:
        movies = json.loads(response.text)
        movies_data = movies["results"]
        root = tk.Tk()
        root.title("Selecteer de film?")
        listbox = tk.Listbox(root, height=15, width=60)
        listbox.pack(pady=10)
        listbox.insert(tk.END, "Extra")
        for movie in movies_data:
            listbox.insert(tk.END, f"{movie["title"]} ({movie["release_date"].split("-")[0]})")
        listbox.bind("<Double-1>", select_movie)
        listbox.bind("<Return>", select_movie)
        root.mainloop()
        if movie_name == None:
            print("niets gevonden")
            film = simpledialog.askstring("makemkv-auto", "Wat is de naam van de film?")
            url = f"https://api.themoviedb.org/3/search/movie?query={film}&include_adult=false&language=en-US&page=1"

            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {TMDB_API_KEY}"
            }

            response = requests.get(url, headers=headers)
            movies = json.loads(response.text)
            movies_data = movies["results"]
            root = tk.Tk()
            root.title("Selecteer de film?")
            listbox = tk.Listbox(root, height=15, width=60)
            listbox.pack(pady=10)
            listbox.insert(tk.END, "Extra")
            for movie in movies_data:
                listbox.insert(tk.END, f"{movie["title"]} ({movie["release_date"].split("-")[0]})")
            listbox.bind("<Double-1>", select_movie)
            listbox.bind("<Return>", select_movie)
            root.mainloop()
            print("Naam:", movie_name)
            print("Release jaar:", release_year)
            print("ID:", movie_id)
        else:
            print("Naam:", movie_name)
            print("Release jaar:", release_year)
            print("ID:", movie_id)

    if extra_disc:
        output_folder = "extras_disc"
    else:
        output_folder = f"{movie_name} ({release_year}) [tmdbid-{movie_id}]"

    if not os.path.exists(f"{output_folder_root}/temp_folder"):
        os.makedirs(f"{output_folder_root}/temp_folder")


    #subprocess.run(["makemkvcon", f"--minlength={minlength_title}", "mkv", f"disc:{drive_number}", "all", f"{output_folder_root}/temp_folder"])
    item_path = f"{output_folder_root}/temp_folder"
    new_dir_name = output_folder
    new_dir_path = os.path.join(output_folder_root, new_dir_name)
    extras_dir = os.path.join(new_dir_path, 'extras')

    if not extra_disc:
        os.makedirs(new_dir_path, exist_ok=True)
        os.makedirs(extras_dir, exist_ok=True)
        files = [f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))]
        if not files:
            continue
        
        largest_file = max(files, key=lambda x: os.path.getsize(os.path.join(item_path, x)))
        
        ext = os.path.splitext(largest_file)[1]
        new_video_name = f"{new_dir_name}{ext}"
        
        try:
            shutil.move(os.path.join(item_path, largest_file), os.path.join(new_dir_path, new_video_name))

            if not extra_disc:
                for f in files:
                    if f == largest_file:
                        continue
                    shutil.move(os.path.join(item_path, f), os.path.join(extras_dir, f))
            
            os.rmdir(item_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process {item}: {str(e)}")

    subprocess.run(["eject", f"/dev/sr{drive_number}"])
    if discord:
        webhook_url = DISCORD_WEBHOOK

        # The message payload
        data = {
            "content": f"<@{DISCORD_USER_ID}> De Disc is klaar"  # This is the message that will be sent
        }

        # Send the POST request
        response = requests.post(webhook_url, json=data)
    if handbrake_flatpak:
        if extra_disc:
            handbrake_folder = f"{output_folder_root}/temp_folder"
        else:
            handbrake_folder = f"{output_folder_root}/{output_folder}"
        threading.Thread(
            target=handbrake,
            args=(handbrake_folder,),
            daemon=True
        ).start()