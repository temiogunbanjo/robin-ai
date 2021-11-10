import random
from core.processor import WordProcessor
from utils.utils import starts_with, to_capitalize_case


def greetings_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command
    wp = WordProcessor()

    if command_classifications is None:
        command_classifications = []

    def process_and_save_response(original_command, a_greeting, response):
        sliced_command = original_command.split(a_greeting)
        remaining_command_after_greeting = sliced_command[1] if len(sliced_command) >= 2 else sliced_command
        # if command starts with greeting
        if starts_with(original_command, a_greeting):
            if a_greeting in ['hey', 'hi', 'hello']:
                response_to_command.append(f"{to_capitalize_case(a_greeting)} {random.choice(wp.get_affiliations())}!")
            else:
                response_to_command.append(response)
            # If additional command exist, continue
            return remaining_command_after_greeting.strip()
        return None

    for greeting in ['good morning', 'good afternoon', 'good evening', 'hello', 'hi', 'hey']:
        # if command starts with greeting and no other command after
        remaining_command = process_and_save_response(modified_command, greeting, f'{greeting} to you too.')
        # Greeting was found and has been responded to
        if remaining_command is '':
            break
        elif remaining_command is not None:
            modified_command = ai_engine_instance.sanitize_command(remaining_command)
            has_modified_command = True

    for greeting in ["what's up", "what's good", 'howdy', 'how are you', 'how are you doing']:
        ai_response = f"I'm good and happy, Thank you for asking."
        remaining_command = process_and_save_response(modified_command, greeting, ai_response)
        # Greeting was found and has been responded to
        if remaining_command is '':
            command_classifications.clear()
            break
        elif remaining_command is not None:
            modified_command = ai_engine_instance.sanitize_command(remaining_command)
            has_modified_command = True

    if 'greetings' in command_classifications:
        command_classifications.remove('greetings')

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
