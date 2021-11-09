from datetime import datetime

import pytz


def time_request_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command

    if command_classifications is None:
        command_classifications = []

    if 'time in' in modified_command:
        timezones = pytz.all_timezones
        right_of_keyword = modified_command.split('time in')[1]

        for place in right_of_keyword.split():
            for timezone in timezones:
                if place in timezone.lower():
                    country_time_zone = pytz.timezone(timezone)
                    current_time = datetime.now(country_time_zone).strftime('%I:%M %p')
                    ai_engine_instance.talk(f'The time in {place} is {current_time}')
                    ai_engine_instance.set_idle_state(True)
                    return

        ai_engine_instance.talk("I don't have access to that timezone")

    current_time = datetime.now().strftime('%I:%M %p')
    ai_engine_instance.talk(f'Your local time is {current_time}')

    if 'time_request' in command_classifications:
        command_classifications.remove('time_request')

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
