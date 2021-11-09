import os
import re
import time

from pipe import traverse, where, select, sort
from plyer import storagepath

from utils.utils import starts_with, contains, get_most_similar_elements, prefix_list_elements


def find_media_on_device(search_query, action):
    song, artist, *arg = search_query.split('by') if search_query.find(' by ') >= 0 else (search_query, None)

    if contains(search_query, ["music", r"song(s)?", r"sound(s)?", "beats", r"mixtape(s)?"]):
        extensions = ['.mp3', '.ogg', '.m4a', '.mpeg', '.aac']
        files_list = [
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_music_dir(), topdown=True)],
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_downloads_dir(), topdown=True)]
        ]

    elif contains(search_query, [r"video(s)?", r"film(s)?", r"movie(s)?"]):
        extensions = ['.mp4', '.webm', '.mov', '.flv', '.avi']
        files_list = [
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_videos_dir(), topdown=True)],
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_downloads_dir(), topdown=True)]
        ]

    else:
        extensions = [
            '.mp3', '.ogg', '.m4a', '.mpeg', '.aac',
            '.mp4', '.webm', '.mov', '.flv', '.avi'
        ]
        files_list = [
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_videos_dir(), topdown=True)],
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_music_dir(), topdown=True)],
            [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
             os.walk(storagepath.get_downloads_dir(), topdown=True)]
        ]

    # use each word in song title and artist name as keywords
    media_keywords = [*song.strip().split(), str(artist).strip()]

    # Full list of relevant media files
    available_media_list = list(
        files_list | traverse
        | select(lambda file: file.lower())
        | where(lambda file: any([file.endswith(ext) for ext in extensions]))
    )

    # A copy of available_media_list with the dir path removed from each files
    available_media_file_names = list(
        available_media_list | select(lambda f: f.split("\\")[-1])
    )

    # Get all matching media files in available_media_file_names by song keywords
    # Filters non matching media
    # Sort list of tuples from maximum keyword_counts to minimum
    # Convert sorted list of tuples back to list of media files using index_of_media_in_list
    # Return a list of tuples in format: (index_of_media_in_list, no_of_keywords_it_contains)
    selections = list(
        get_most_similar_elements(media_keywords, available_media_file_names)
        | where(lambda el: el[1] > 0)
        | sort(reverse=True)
        | select(lambda el: available_media_list[el[0]])
    )

    # Return the required media file
    if len(selections) == 0:
        media_selected = None if action is not 'any' else available_media_list[0]
    else:
        media_selected = selections[0]

    return media_selected


def media_request_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command

    if command_classifications is None:
        command_classifications = []

    split_command_into_list = [modified_command]
    wildcard_selection_pattern = re.compile(
        r"any (.+)(movie(s)?|film(s)?|songs(s)?|video(s)?|mixtape(s)?|album(s)?)")

    # Check if play or find keyword has words after it
    if 'play' in modified_command:
        split_command_into_list = re.sub(r'(play(\s+me)?)', 'play', modified_command).split('play')

    elif 'find' in modified_command and contains(modified_command, ['song', 'music', 'video']):
        split_command_into_list = modified_command.split('find')

    elif starts_with(modified_command, 'sing'):
        split_command_into_list = modified_command.split('sing')

    index = 1 if len(split_command_into_list) > 1 else 0
    song_title = split_command_into_list[index].strip()

    # Search for music on PC and play if found
    ai_engine_instance.talk(f'Searching for {song_title} on your device...')
    action = None if wildcard_selection_pattern.search(song_title) is None else "any"
    result = find_media_on_device(song_title, action)

    if result is None:
        ai_engine_instance.talk(f"I couldn't find {song_title}...")
        time.sleep(0.8)
        ai_engine_instance.talk(f'Searching YouTube...')
        try:
            from pywhatkit import playonyt
            playonyt(song_title)
        except Exception:
            ai_engine_instance.talk("Something went wrong. Your device seems to be offline")
    else:
        song_title = result.split("\\")[-1]
        ai_engine_instance.talk(f"Playing {song_title}...")
        ai_engine_instance.ui.robinGUI.play_sound(result)

    if "media_request" in command_classifications:
        command_classifications.remove("media_request")

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
