import random
import re
import time

import plyer
import speech_recognition as sr
from threading import Thread, current_thread, main_thread

from core.config import Config
from core.features.calculation_action import calculation_request_handler
from core.features.date_action import date_request_handler
from core.features.greetings import greetings_handler
from core.features.info_action import info_request_handler
from core.features.media_action import media_request_handler
from core.features.system_action import system_action_handler
from core.features.time_action import time_request_handler
from core.features.ai_customization_action import ai_customization_handler
from core.processor import WordProcessor

from utils.multitask import display_calling_process
from utils.utils import contains, starts_with, to_capitalize_case, remove_list_elements

# TODO: Add a webbrowser python package
# webbrowser

conf = Config()
ai_pref_path = conf.path


class Robin:
    def __init__(self, ui=None):
        self.config = conf.load_config()
        self.config['name'] = to_capitalize_case(self.config['name'])
        self.word_processor = WordProcessor()
        self.listener = sr.Recognizer()
        self.tts_engine = None
        self.questions = []
        self.ui = ui
        self.idle = True
        self.green_text_color = "#77FF77"

    def introduce_ai(self):
        bio = f"My name is {self.config['name']}. I am an AI developed by DeePlug Gadgets team to make " \
              f"automation a whole lot easier and friendlier. I can do some things like..."
        self.talk(bio)
        time.sleep(0.5)

        p = self.ui.robinGUI.create_popup()
        p.open()

    def set_idle_state(self, idle):
        print(f"setting idle to {idle}")
        self.idle = idle
        if idle is True:
            self.execute_ui_action("check_bg_processes_status", idle)

    def startup_message(self):
        """ Returns message that would be spoken at start up """
        if self.config["is_first_launch"] is True:
            message = f"Hi, I am {self.config['name']}, your virtual assistant. To talk to me, please say " \
                      f"'hello {self.config['name']}', or tap the mic button."
        else:
            affiliation = random.choice(['friend', 'buddy', 'paddy', 'yo'])
            message = f"Hey {affiliation}! What can i do for you today?"
        return message

    def execute_ui_action(self, callback_name, *args):
        """
        Checks if instance of self.ui has been initialized and then executes callback if true
        else skip
        """
        if self.ui is not None:
            getattr(self.ui, callback_name)(*args)
            return True
        return False

    def sanitize_command(self, command):
        # Convert command to lowercase
        command = command.lower()
        words_list = ['i said ', 'what i said was ', 'what i said is ', f'hello {self.config["name"]}',
                      f'hey {self.config["name"]}', 'can you ', self.config["name"]]
        if contains(command, words_list):
            for i in range(len(words_list)):
                if command.startswith(words_list[i]) > -1:
                    command = command.replace(words_list[i], '')
                    command = command.strip()
        return command

    def remember_command(self, command):
        self.questions.append(command)

    def forget_command(self):
        if len(self.questions) > 0:
            self.questions.pop()

    def display_on_ui(self, message):
        success = self.execute_ui_action('update_ui_screen', message)
        if success is False:
            print(message)

    def audio_to_text(self, **kwargs):
        mic_is_listening = False
        language = self.config["language"] or 'en-us'
        try:
            _input = sr.Microphone()
            with _input as source:
                self.listener.adjust_for_ambient_noise(source)
                # Display listening and do mic animation
                mic_is_listening = True
                self.execute_ui_action('start_mic_animation')
                self.display_on_ui('Listening...')

                # Listen with specified source device
                recorded_audio = self.listener.listen(source, 15, 25)

                mic_is_listening = False
                self.execute_ui_action('stop_mic_animation')
                self.display_on_ui('Processing...')
                # Translate recorded audio to command
                return self.listener.recognize_google(recorded_audio, language=language)
        finally:
            if mic_is_listening:
                self.execute_ui_action('stop_mic_animation')

    def listen(self, is_asking_for_confirmation=False, confirmation_callbacks=None):
        def callback(instance, is_asking_for_confirmation, confirmation_callbacks):
            try:
                instance.set_idle_state(False)
                command = self.audio_to_text()
                # Process command
                instance.display_on_ui(f'[color={instance.green_text_color}]You:[/color] {command}')
                time.sleep(2)
                instance.process_command(command, is_asking_for_confirmation, confirmation_callbacks)
                instance.set_idle_state(True)
            except sr.UnknownValueError as unknown_value:
                if unknown_value is not '':
                    print(str(unknown_value))

                # If user has not being asked
                if is_asking_for_confirmation is False:
                    # Ask user to repeat question, if something was said
                    message = "Sorry I couldn't process what you said. Did you say something?"

                    def yes_callback(*args):
                        c = args[1]
                        instance.forget_command()
                        if 'i said' in c:
                            what_was_said = c.split('i said')[1]
                            print(what_was_said)
                        instance.talk('ok, what did you say?')
                        instance.listen(True)

                    def no_callback(robin_instance, c):
                        robin_instance.forget_command()
                        self.talk('ok, bye!')
                        instance.set_idle_state(True)

                    instance.ask_for_confirmation(None, message, yes_callback, no_callback)
                else:
                    instance.talk("I didn't hear anything")
                    self.forget_command()
                    instance.set_idle_state(True)

            except sr.RequestError:
                instance.talk("I cannot listen to your commands while your device is offline")
                instance.set_idle_state(True)

            except Exception as ex:
                instance.talk(ex)
                instance.set_idle_state(True)

        # Run callback on a different thread to avoid blocking main thread
        if current_thread() is main_thread():
            ask_confirmation_thread = Thread(target=callback, daemon=True, args=(
                self, is_asking_for_confirmation, confirmation_callbacks
            ))
            ask_confirmation_thread.start()
        else:
            callback(self, is_asking_for_confirmation, confirmation_callbacks)

    def ask_for_confirmation(self, command, message=None, yes_callback=None, no_callback=None):
        if message is None:
            message = f'You said, {self.word_processor.transform_speech_to_other_person(command)}. Am I right?'

        print(self.questions)
        # Confirm command
        if len(self.questions) == 0:
            self.talk(message)
            self.remember_command(command)
            confirmation_callbacks = {
                "yes": yes_callback,
                "no": no_callback
            }
            self.listen(True, confirmation_callbacks)

        # Command might be a confirmation
        else:
            if contains(command, self.word_processor.get_examples('confirmations')):
                if yes_callback is not None:
                    yes_callback(self, self.questions[0])
                return True
            elif contains(command, self.word_processor.get_examples('disagreements')):
                if no_callback is not None:
                    no_callback(self, self.questions[0])
                return False
            else:
                self.talk("Sorry, I didn't quite understand that")
                self.forget_command()
                return None

    def process_command(self, command, is_asking_for_confirmation=False, confirmation_callbacks=None):
        def callback(instance, command, is_asking_for_confirmation, confirmation_callbacks):

            confirmation_callbacks = {
                "yes": None, "no": None
            } if confirmation_callbacks is None else confirmation_callbacks

            # Remove unnecessary words in command
            command = instance.sanitize_command(command)
            command = instance.word_processor.transform_text_to_numbers(command)
            has_modified_command = False
            command_classification = instance.word_processor.get_classification(command)

            # ====[START]===================================================================
            # Casual greetings command
            if 'greetings' in command_classification:
                results = greetings_handler(instance, command, command_classification)
                command = results["modified_command"]
                response_to_command = " ".join(results["responses"])
                command_classification = results["command_classifications"]
                has_modified_command = results["has_modified_command"]

                # Respond on a separate thread to avoid blocking current thread
                response_thread = Thread(target=instance.talk, daemon=True, args=(response_to_command,))
                response_thread.start()
                time.sleep(0.5)

                # if len(command_classification) <= 0:
                #     instance.set_idle_state(True)
                #     return

            # Permission request
            if 'permission_request' in command_classification:
                instance.talk('Yeah sure')
                time.sleep(0.5)
                command_classification.remove('permission_request')

                for starter in instance.word_processor.get_starters('permission_request'):
                    found = re.match(starter, command)
                    if found:
                        command = command[found.end():].strip()
                        has_modified_command = True
                        break

            # Gratitude
            if 'gratitude' in command_classification:
                instance.talk('Yeah sure. Anytime!')
                time.sleep(0.5)
                command_classification.remove('gratitude')
                if len(command_classification) <= 0:
                    instance.set_idle_state(True)
                    return

            # =====[END]====================================================================

            # Classify remaining command
            command_classification = instance.word_processor.get_classification(command)

            # Remove "greeting", "permission", and "gratitude" requests from classification
            command_classification = remove_list_elements(command_classification, [
                "greetings", "gratitude", "permission_request"
            ])

            # If the AI doesn't understand the remaining command after being modified, return
            if len(command_classification) == 0 and has_modified_command:
                instance.set_idle_state(True)
                return

            # ====[START]===================================================================
            # Exit request
            if 'sendoffs' in command_classification:
                instance.talk("Goodbye! Let's talk again later.")
                instance.set_idle_state(False)
                instance.ui.exit()

            # AI info requests
            elif 'name_request' in command_classification:
                instance.talk(f'My name is {instance.config["name"]}')

            # Time requests
            elif 'time_request' in command_classification:
                results = time_request_handler(instance, command, command_classification)
                command_classification = results["command_classifications"]

            # Date request
            elif 'date_request' in command_classification:
                results = date_request_handler(instance, command, command_classification)
                command_classification = results["command_classifications"]

            # Media request
            elif 'media_request' in command_classification:
                results = media_request_handler(instance, command, command_classification)
                command_classification = results["command_classifications"]

            # System task requests
            elif 'system_action_request' in command_classification:
                results = system_action_handler(instance, command, command_classification)
                command_classification = results["command_classifications"]

            # Calculation request
            elif 'calculation_request' in command_classification:
                results = calculation_request_handler(instance, command, command_classification)
                command_classification = results["command_classifications"]

            # AI customisation requests
            elif "ai_customisation_requests" in command_classification:
                results = ai_customization_handler(instance, command, command_classification)
                has_modified_command = results["has_modified_command"]

            # Request for info about something
            elif 'info_request' in command_classification:
                if contains(command, r'tell me\s*(.+)?\s*about you(rself)?'):
                    instance.introduce_ai()
                    return

                if contains(command, [r'my (\w+)?(\s*)battery percent', r'the (\w+)?(\s*)battery percent']):
                    battery_percent = plyer.battery.status["percentage"]
                    instance.talk(f'Your PC battery is currently at {battery_percent}%')
                    return

                # Remove this starters
                starters = ['do you know', 'who is', 'who was', 'who were', 'tell me about', 'i want to know']
                if starts_with(command, starters):
                    for phrase in starters:
                        if phrase in command:
                            command = command.split(phrase)[1].strip()

                formatted_command = command
                results = info_request_handler(instance, formatted_command, command_classification)
                command_classification = results["command_classifications"]

            # Dismissal command
            elif 'dismissals' in command_classification:
                instance.talk('Ok, sure!')
                instance.forget_command()

            # Unknown classifications
            else:
                # Default confirmation callbacks
                def yes_callback(*args):
                    responses_to_give = [
                        "Sadly, I am still unable to fully understand your command for now.",
                        "Uhm, I don't really know how to respond to this kinds of requests yet.",
                        "Still learning."
                    ]
                    instance.talk(random.choice(responses_to_give))
                    time.sleep(0.5)

                    try:
                        instance.talk("But here is what I got from the web...")
                        from pywhatkit import search
                        query = args[1]
                        search(query)
                    except Exception:
                        instance.talk("I couldn't access the internet. Your device seems to be offline")

                def no_callback(*args):
                    responses_to_give = ["ok", "Ouch sorry about that", "My bad"]
                    instance.forget_command()
                    instance.talk(f'{random.choice(responses_to_give)}, what did you say?')
                    instance.listen()

                if is_asking_for_confirmation is True:
                    instance.ask_for_confirmation(command, yes_callback=confirmation_callbacks['yes'],
                                                  no_callback=confirmation_callbacks['no'])
                else:
                    instance.ask_for_confirmation(command, yes_callback=yes_callback, no_callback=no_callback)

            time.sleep(1)
            instance.set_idle_state(True)
            # =====[END]====================================================================

        if current_thread() is main_thread():
            process_thread = Thread(target=callback, args=(
                self, command, is_asking_for_confirmation, confirmation_callbacks), daemon=True)
            process_thread.start()
        else:
            callback(self, command, is_asking_for_confirmation, confirmation_callbacks)

    def talk(self, text, display_message=True):
        def speak(string_to_speak, ai_instance):
            try:
                _tts_engine = conf.get_tts_engine(voice_index=self.config['default_voice'])
                _tts_engine.say(string_to_speak)
                _tts_engine.runAndWait()
            except RuntimeError as ree:
                print(ree)
                time.sleep(0.5)

        self.set_idle_state(False)
        if display_message:
            self.display_on_ui(f"[color={self.green_text_color}]{self.config['name']}:[/color] {text}")
            self.execute_ui_action('audio_visualizer_action')
        speak(text, self)

    def stop_talk(self):
        # self.tts_engine
        pass

    def exit(self):
        self.ui.robin_background_service.should_exit = True
        conf.save_config(ai_pref_path, self.config)


class RobinInterface:
    def __init__(self, robin_instance=None, ui_instance=None):
        self.listener = sr.Recognizer()
        self.stop_listen_in_bg = None
        self.robin = robin_instance
        self.ui = ui_instance
        self.process_db = None

    def __init_robin_instance(self):
        """ Initializes robin instance and saves it """
        self.robin = Robin(self.ui)

    def verify_robin_instance(self, ui=None):
        """
        Checks if instance of robin engine has been initialized. If it has been initialized,
        skip else initialized robin instance
        """
        if self.robin is None:
            if self.ui is None:
                self.ui = ui
            self.__init_robin_instance()

    #   UI HANDLERS ===================================================================
    def robin_listen_action(self, ui=None):
        display_calling_process('AppBGListener: robin_listen_action')
        self.verify_robin_instance(ui)
        self.robin.set_idle_state(False)
        self.ui.robin_background_service.pause_capture(False)
        self.robin.listen()

    def robin_stop_listen_action(self, ui=None):
        display_calling_process('AppBGListener: robin_stop_listen_action')
        self.verify_robin_instance(ui)
        self.robin.set_idle_state(True)
        self.robin.execute_ui_action('stop_mic_animation')

    def robin_read_action(self, command, ui=None):
        display_calling_process('AppBGListener: robin_read_action')
        try:
            self.verify_robin_instance(ui)
            self.ui.robin_background_service.pause_capture(False)
            self.robin.set_idle_state(False)
            self.robin.display_on_ui(f'You: {command}')
            time.sleep(1)
            # Process command
            self.robin.process_command(command)
        except Exception as ex:
            print('robin_read_action: ', ex)

# stop_it = False
# wp = Robin()
# while stop_it is False:
#     sentence = input('Type in a sentence: ')
#     wp.process_command(sentence)
#
#     stop_command = input('Type "stop" to exit or press enter to continue:\n>>>')
#     print()
#     if stop_command is 'stop':
#         stop_it = True
