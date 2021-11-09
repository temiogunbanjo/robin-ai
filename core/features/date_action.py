from datetime import datetime


def date_request_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command

    if command_classifications is None:
        command_classifications = []

    print(datetime.today())

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
