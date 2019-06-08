from spotify import Spotify
from google import Google
import json
import inquirer
import tqdm

with open("config/config.json") as json_file:
    config = json.load(json_file)

spotify_config = config.get("spotify")

if not (spotify_config.get("client_id") and spotify_config.get("client_secret") and spotify_config.get("redirect_uri")):
    print("Please update your spotify configuration:")
    questions = [
        inquirer.Text("client_id", message="What's your Client ID?"),
        inquirer.Text("client_secret", message="What's your Client Secret?"),
        inquirer.Text("redirect_uri", message="What's your Redirect URI?")
    ]

    answers = inquirer.prompt(questions)
    config["spotify"]["client_id"] = answers["client_id"]
    config["spotify"]["client_secret"] = answers["client_secret"]
    config["spotify"]["redirect_uri"] = answers["redirect_uri"]

    with open("config/config.json", "w") as json_file:
        json.dump(config, json_file)

spotify = Spotify(spotify_config)

google_config = config.get("google")

if not (google_config.get("api_key") and google_config.get("client_id") and google_config.get("client_secret") and google_config.get("redirect_uri")):
    print("Please update your google configuration:")
    questions = [
        inquirer.Text("api_key", message="What's your API Key?"),
        inquirer.Text("client_id", message="What's your Client ID?"),
        inquirer.Text("client_secret", message="What's your Client Secret?"),
        inquirer.Text("redirect_uri", message="What's your Redirect URI?")
    ]

    answers = inquirer.prompt(questions)
    config["google"]["api_key"] = answers["api_key"]
    config["google"]["client_id"] = answers["client_id"]
    config["google"]["client_secret"] = answers["client_secret"]
    config["google"]["redirect_uri"] = answers["redirect_uri"]

    with open("config/config.json", "w") as json_file:
        json.dump(config, json_file)

google = Google(google_config)

playlist_names = []
playlists = dict()

for i in spotify.user_playlists():
    playlist_names.append(i.get("name"))
    playlists[i.get("name")] = i.get("id")

questions = [
    inquirer.List(
        "playlist_name", message="Which playlists do you want to convert?", choices=playlist_names)
]

answers = inquirer.prompt(questions)
playlist_name = answers.get("playlist_name")
playlist_id = playlists[answers.get("playlist_name")]

tracks = []
for t in spotify.playlist_tracks(playlist_id):
    tracks.append("{} {}".format(t.get("track").get("name"),
                                 t.get("track").get("artists")[0].get("name")))

youtube_playlist_id = google.create_playlist(playlist_name).get("id")

for t in tqdm.tqdm(tracks):
    video_id = google.search(t)
    google.add_video(youtube_playlist_id, video_id)

print("Finished the conversion.\n Thank's for using my converter!")
