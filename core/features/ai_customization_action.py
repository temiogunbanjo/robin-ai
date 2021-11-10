import random

from core.processor import WordProcessor
from core.config import Config


def ai_customization_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command
    conf = Config()

    if command_classifications is None:
        command_classifications = []

    if "voice" in modified_command:
        confirm_voice_change_message = 'Did you ask me to change my voice?'

        def yes_callback(*args):
            ai_engine_instance.talk('switching to next voice available...')
            index_of_next_voice = int(ai_engine_instance.config['default_voice']) + 1
            if index_of_next_voice >= len(ai_engine_instance.config['voices']):
                index_of_next_voice = 0

            # Set new voice
            ai_engine_instance.config['default_voice'] = index_of_next_voice
            conf.save_config(conf.path)

            ai_engine_instance.talk(f'Now using voice {index_of_next_voice + 1}')

        def no_callback(robin_instance, cm):
            robin_instance.talk('Ok, i thought i heard something else')

        ai_engine_instance.ask_for_confirmation(command, confirm_voice_change_message, yes_callback, no_callback)

    if 'ai_customisation_requests' in command_classifications:
        command_classifications.remove('ai_customisation_requests')

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
