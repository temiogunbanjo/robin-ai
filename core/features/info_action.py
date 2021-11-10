import re
import time
from people_also_ask import get_simple_answer
from people_also_ask.google import GoogleSearchRequestFailedError
from core.processor import WordProcessor
from utils.utils import ai_should_proceed_with_action


def info_request_handler(ai_engine_instance, command, command_classifications=None):
    response_to_command = []
    has_modified_command = False
    modified_command = command

    if command_classifications is None:
        command_classifications = []

    ai_info_request_pattern = re.compile(
        r"(what|what'?s|why|who|when) ((is)?|was|will|would|were)\s*your\s"
    )
    user_info_request_pattern = re.compile(
        r"(what|what'?s|why|who|when) ((is)?|was|will|would|were)\s*my\s"
    )

    if ai_info_request_pattern.search(modified_command) is not None:
        start_index = ai_info_request_pattern.search(modified_command).end()
        formatted_command = f"[color={ai_engine_instance.green_text_color}]You:[/color] " \
                            f"My {modified_command[start_index:].strip()}..."
        ai_engine_instance.display_on_ui(WordProcessor().transform_speech_to_other_person(formatted_command))
        time.sleep(2)
        ai_engine_instance.talk("Honestly, i don't really know much about myself. But i was created to make your "
                                "work so much easier. You can check out my companies website at "
                                "temiogunbanjo.herokuapp.com for more info about me.")

    elif user_info_request_pattern.search(modified_command) is not None:
        ai_engine_instance.talk("I don't know much. But I am here to serve you and learn too.")

    else:
        # Request for General info pattern
        info_request_pattern = re.compile(r"(what|what'?s|why|who|when) (is|was|will|would|were)\s")

        pattern_match = info_request_pattern.search(modified_command)
        formatted_question = original_question = modified_command

        if pattern_match is not None:
            pos = pattern_match.span()
            formatted_question = original_question[pos[1]:]

        if ai_should_proceed_with_action():
            ai_engine_instance.talk("Please hold on, i am running a google search for you...")
        else:
            ai_engine_instance.talk("Please wait...")

        time.sleep(0.5)

        try:
            print(original_question)
            google_answer = get_simple_answer(original_question)
            g_answer = google_answer if google_answer is not '' else "I didn't get a response from my " \
                                                                     "search."
            ai_engine_instance.talk(g_answer)

            if google_answer is '':
                ai_engine_instance.talk("Searching wikipedia...")
                raise GoogleSearchRequestFailedError(None, original_question)
        except GoogleSearchRequestFailedError as g_err:
            import wikipedia
            print(f"google_err: {g_err}")
            try:
                print(formatted_question)
                wiki_answer = wikipedia.summary(formatted_question, 3, True)
                ai_engine_instance.talk('According to wikipedia...')
                time.sleep(0.5)
                ai_engine_instance.talk(wiki_answer)
            except Exception as wiki_err:
                try:
                    print(f"wiki_err: {wiki_err}")
                    ai_engine_instance.talk("I couldn't get a response from google for you. "
                                            "But let me display it on the web for you instead...")
                    from pywhatkit import search
                    time.sleep(1)
                    search(original_question)
                except Exception:
                    ai_engine_instance.talk("I couldn't access the internet. Your device seems to be offline")

    if "info_request" in command_classifications:
        command_classifications.remove("info_request")

    return {
        "original_command": command,
        "modified_command": modified_command,
        "has_modified_command": has_modified_command,
        "command_classifications": command_classifications,
        "responses": response_to_command
    }
