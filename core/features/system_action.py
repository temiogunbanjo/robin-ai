import json
import os
import re
import time

import plyer
from pipe import traverse, where, select, sort
from speech_recognition import UnknownValueError

from core.processor import WordProcessor
from utils.utils import contains, get_most_similar_elements, prefix_list_elements


def perform_os_action(command, target, action):
    import plyer
    from plyer import storagepath
    import os
    # from plyer.utils import platform

    if target is "wifi":
        wifi_name = 'Wi-Fi'
        os.system('netsh interface show interface')

        if action is "off":
            try:
                plyer.wifi.disable()
            except Exception as ex:
                print(ex)
                os.popen(f'netsh interface set interface \"{wifi_name}\" DISABLED')

        elif action is "on":
            try:
                plyer.wifi.enable()
            except Exception as ex:
                print(ex)
                os.popen(f'netsh interface set interface \"{wifi_name}\" enabled')

    elif target is "screenshot":
        try:
            from plyer import screenshot
            screenshot.file_path = storagepath.get_pictures_dir()
            screenshot.capture()
        except Exception as ex:
            return ex

    elif target is "media":
        song, artist, *arg = command.split('by') if command.find(' by ') >= 0 else (command, None)

        if contains(command, ["music", r"song(s)?", r"sound(s)?", "beats", r"mixtape(s)?"]):
            extensions = ['.mp3', '.ogg', '.m4a', '.mpeg', '.aac']
            files_list = [
                [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
                 os.walk(storagepath.get_music_dir(), topdown=True)],
                [prefix_list_elements(f"{root}\\", files) for root, dirs, files in
                 os.walk(storagepath.get_downloads_dir(), topdown=True)]
            ]

        elif contains(command, [r"video(s)?", r"film(s)?", r"movie(s)?"]):
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


def system_action_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command

    if command_classifications is None:
        command_classifications = []

    pattern_string = r'(open|launch|close|activate|deactivate|start|stop|((turn|put) (on|off)))\s*(.*)\s+'
    off_keywords = ['stop', 'close', 'turn off', 'put off', 'activate']
    on_keywords = ['start', 'launch', 'open', 'turn on', 'put on', 'deactivate']
    action = "off" if contains(modified_command, off_keywords) else "on"

    # Turn wifi on or off
    if re.compile(r'{0}(wifi|wi-fi)'.format(pattern_string)).search(modified_command) is not None:
        perform_os_action(modified_command, 'wifi', action)
        ai_engine_instance.talk(f"Turning {action} Wi-Fi...")

    # Take a screenshot
    elif "screenshot" in modified_command:
        ai_engine_instance.talk(f"Taking Screenshot...")
        result = perform_os_action(modified_command, 'screenshot', action)
        if result:
            ai_engine_instance.talk(result)

    # Set reminder
    elif "remind" in modified_command:
        ai_engine_instance.talk(f"Setting Reminder...")
        result = perform_os_action(modified_command, 'reminder', action)
        if result:
            ai_engine_instance.talk(result)

    elif "restart" in modified_command and \
            contains(modified_command, [r"(my\s+)?laptop", r"(my\s+)?computer", r"(my\s+)?pc"]):

        def yes_callback(*args):
            ai_engine_instance.talk("Ok, Restarting your device...")
            os.system("shutdown /r /t 1")

        def no_callback(*args):
            ai_engine_instance.talk("Ok")

        ai_engine_instance.ask_for_confirmation(
            message="Did you ask me to restart your device?",
            yes_callback=yes_callback,
            no_callback=no_callback,
            command=modified_command
        )

    # Shut down
    elif ("shutdown" in modified_command or "shut down" in modified_command) and \
            contains(modified_command, [r"(my\s+)?laptop", r"(my\s+)?computer", r"(my\s+)?pc"]):

        def yes_callback(*args):
            ai_engine_instance.talk("Ok, Shutting down your device...")
            os.system("shutdown /s /t 1")

        def no_callback(*args):
            ai_engine_instance.talk("Ok")

        ai_engine_instance.ask_for_confirmation(
            message="Did you ask me to shutdown your device?",
            yes_callback=yes_callback,
            no_callback=no_callback,
            command=modified_command
        )

    # elif control panel run script
    else:
        with open('storage/apps.json', 'r') as apps:
            content = apps.read()
        known_apps = json.loads(content)
        all_starter_pattern = '|'.join(ai_engine_instance.word_processor.get_starters('system_action_request'))
        # Remove everything just before the app name
        app_name = re.sub(r'(.*)' + all_starter_pattern, '', modified_command)
        app_scripts = None

        for each_app in known_apps:
            if contains(app_name, each_app['alias']):
                app_name = each_app['name']
                app_scripts = each_app['scripts']
                break

        def operation_result_response(app, action, status_code):
            if status_code == 0:
                ai_engine_instance.talk(f'Done!')
            else:
                action = "opening" if action == 'open' else 'closing'
                ai_engine_instance.talk(f'An error occurred while {action} {app}')

        if contains(modified_command, off_keywords) and app_scripts is not None:
            ai_engine_instance.talk(f'Closing {app_name} and all subprocesses...')
            result = os.system(app_scripts['close'])
            operation_result_response(app_name, 'close', result)

        elif contains(modified_command, on_keywords) and app_scripts is not None:
            ai_engine_instance.talk(f'Opening {app_name}...')
            result = os.system(app_scripts['open'])
            time.sleep(0.8)
            operation_result_response(app_name, 'open', result)

        else:
            ai_engine_instance.talk(f"I don't know {app_name}, or probably i didn't understand your command.")
            time.sleep(0.5)
            ai_engine_instance.talk(f"Can you show me where {app_name} is installed "
                                    f"so i can access it next time?")

            def file_select_callback(files):
                if len(files) == 0:
                    ai_engine_instance.set_idle_state(True)
                    return

                dir_list = files[0].split('\\')
                dir_path = '/'.join(dir_list[:-1])
                app_exe = dir_list[-1]

                ai_engine_instance.talk(f"You picked {dir_path} as the location of \"{app_name}\". ")
                repeat = 2
                new_app_name = None

                while repeat > 0:
                    try:
                        ai_engine_instance.talk(f"Please what name should i use to store this app?")
                        new_app_name = ai_engine_instance.audio_to_text()
                        ai_engine_instance.talk(f"I heard {new_app_name}. is this correct?")
                        confirmation = ai_engine_instance.audio_to_text()
                        _classification = WordProcessor().get_classification(confirmation)

                        if 'confirmations' in _classification:
                            repeat = 0
                        elif 'dismissals' in _classification:
                            ai_engine_instance.talk("Okay, sure thing boss")
                            repeat = 0
                            return
                        elif 'disagreements' in _classification:
                            ai_engine_instance.talk("Okay")
                            new_app_name = app_name
                            repeat += 1

                    except UnknownValueError:
                        ai_engine_instance.talk(f"I didn't hear anything.")
                        time.sleep(0.3)
                    finally:
                        repeat -= 1

                time.sleep(0.3)
                new_app_name = app_name if new_app_name is None else new_app_name
                ai_engine_instance.talk(f"Saving {app_name} as {new_app_name}...")

                app_info = {
                    "name": f"{new_app_name}",
                    "alias": [f"{new_app_name.lower()}"],
                    "location": f"{dir_path}/{app_exe}",
                    "scripts": {
                        "open": f"cd \"{dir_path}\" && start {app_exe}",
                        "close": f"cd \"{dir_path}\" && taskkill /F /IM \"{app_exe}\" /T"
                    }
                }

                known_apps.append(app_info)
                with open('storage/apps.json', 'w') as app_store_file:
                    app_store_file.write(json.dumps(known_apps, indent=2))

                time.sleep(0.2)
                ai_engine_instance.talk(f"Done. {new_app_name} has been added to known apps.")
                ai_engine_instance.set_idle_state(True)

            try:
                plyer.filechooser.open_file(on_selection=file_select_callback)
            except NotImplementedError:
                ai_engine_instance.ui.robinGUI.create_filedialog(callback=file_select_callback)

    if "system_action_request" in command_classifications:
        command_classifications.remove("system_action_request")

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
