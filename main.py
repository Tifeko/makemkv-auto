import subprocess
import csv
import os
import requests
import tkinter as tk
import json
from tkinter import simpledialog
from dotenv import load_dotenv

load_dotenv()
drive_number = 0
output_folder_root = "output"
minlength_title = 15
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
release_year = None
movie_name = None
movie_id = None
discord = True
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

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
    global release_year, movie_name, movie_id
    selection = listbox.curselection()
    if selection:
        index = selection[0]
        movie = movies_data[index]

        # los opslaan
        release_year = movie["release_date"].split("-")[0]
        movie_name = movie["title"]
        movie_id = movie["id"]

        root.destroy()  # sluit venster

disc_name = get_disc_label(f"/dev/sr{drive_number}")

print(disc_name)

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
    for movie in movies_data:
        listbox.insert(tk.END, movie["title"])
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
    for movie in movies_data:
        listbox.insert(tk.END, movie["title"])
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
        for movie in movies_data:
            listbox.insert(tk.END, movie["title"])
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

output_folder = f"{output_folder_root}/{movie_name} ({release_year}) [tmdbid-{movie_id}]"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


subprocess.run(["makemkvcon", f"--minlength={minlength_title}", "mkv", f"disc:{drive_number}", "all", output_folder])
subprocess.run(["eject", f"/dev/sr{drive_number}"])
if discord:
    webhook_url = DISCORD_WEBHOOK

    # The message payload
    data = {
        "content": "Hello from Python!"  # This is the message that will be sent
    }

    # Send the POST request
    response = requests.post(webhook_url, json=data)


