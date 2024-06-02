import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
from ytmusicapi import YTMusic

# authentication

with open("creds.json") as json_file:
    creds = json.load(json_file)

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=creds["spotify"]["client_id"],
        client_secret=creds["spotify"]["client_secret"],
        redirect_uri=creds["spotify"]["callback_url"],
        scope="playlist-modify-private",
    )
)

ytmusic = YTMusic("oauth.json")


def add_song_to_yt(song_title, artist_name, playlist_id):
    # Search for the song
    search_results = ytmusic.search(query=f"{song_title} {artist_name}", filter="songs")

    if not search_results:
        print("Song not found.")
        return False

    # Find the first matching song
    song = next(
        (
            item
            for item in search_results
            if item["resultType"] == "song"
            and artist_name.lower()
            in (artist["name"].lower() for artist in item["artists"])
        ),
        None,
    )

    if not song:
        # No exact match found, print first item found and prompt user for input
        first_item = search_results[0]
        print("--------------------------------")
        print(f"Search results for {song_title} by {artist_name}:")
        print(
            f"Found song: {first_item['title']} by {', '.join(artist['name'] for artist in first_item['artists'])}"
        )
        user_input = (
            input(
                "No exact match found. Do you want to continue with this song? (y/n): "
            )
            .strip()
            .lower()
        )

        if user_input == "y":
            song = first_item
        else:
            print("Action canceled by user.")
            return False

    # Add the song to the playlist
    song_video_id = song["videoId"]
    ytmusic.add_playlist_items(playlist_id, [song_video_id])
    print(f"Added {song_title} by {artist_name} to the playlist.")
    return True


def get_playlist_tracks(playlist_id, platform):
    if platform == "spotify":
        results = sp.playlist_tracks(playlist_id)
        items = results["items"]
        # Fetch all tracks if there are more than 100
        while results["next"]:
            results = sp.next(results)
            items.extend(results["items"])
        tracks = [
            [item["track"]["name"], item["track"]["artists"][0]["name"]]
            for item in items
        ]
        return tracks

    elif platform == "youtube":
        playlist = ytmusic.get_playlist(playlist_id)
        return [
            [track["title"], track["artists"][0]["name"]]
            for track in playlist["tracks"]
        ]


playlists = creds["playlist_ids"]["spotify"].keys()

failed_tracks = {playlist: [] for playlist in playlists}

for playlist in playlists:
    spotify_id = creds["playlist_ids"]["spotify"][playlist]
    yt_id = creds["playlist_ids"]["youtube"][playlist]

    spotify_tracks = get_playlist_tracks(spotify_id, "spotify")
    yt_tracks = get_playlist_tracks(yt_id, "youtube")

    missing_tracks = [track for track in spotify_tracks if track not in yt_tracks]

    for track in missing_tracks:
        success = add_song_to_yt(track[0], track[1], yt_id)
        if not success:
            failed_tracks[playlist].append(track)

print(failed_tracks)
