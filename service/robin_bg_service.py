import random
import time
from datetime import datetime

import speech_recognition as sr
from plyer import notification

from core.config import Config
from utils.utils import starts_with, contains, ai_should_proceed_with_action, to_capitalize_case


class RobinBackgroundService:
    def __init__(self, robin_instance, abl_instance, ui):
        self.robin = robin_instance
        self.abl = abl_instance
        self.ui = ui
        self.sr_daemon = None
        self.first_run = True
        self.stop = False
        self.should_exit = False
        self.idleness_count = 0
        self.wp = self.robin.word_processor
        self.affiliations = self.wp.get_affiliations()
        self.__idleness_reminders = [
            f"Hey! Did you know I tell funny jokes too? Just say 'hello {self.robin.config['name']}, tell me a joke!'",
            f"Hey there! Did you know i play games too? Just say 'hello {self.robin.config['name']}', lets have fun!",
            f"Did you know i can help you turn on or turn off your computer? "
            f"Just say 'hello {self.robin.config['name']}, shut down my computer!'",
            f"Did you know that you can change my name to whatever you like? Just ask!"
        ]

    def startup_message(self):
        """ Returns message that would be spoken at start_capture up """
        if eval(self.robin.config["is_first_launch"]):
            message = f"Hi there! I am {to_capitalize_case(self.robin.config['name'])} the Virtual Assistant. " \
                      f"For starters, please say \"Hello {self.robin.config['name']}!\" to activate me. Or you can " \
                      f"also just tap the \"Speak\" button too."
        else:
            affiliation = random.choice(self.affiliations)
            message = f"Hey {affiliation}! What can i do for you today?"
        return message

    def capture_activation_phrase(self, bg_listener, audio):
        """
        Background listener callback which processes phrases recorded in the background
        """
        try:
            print('BG: Processing...')
            activation_phrase = bg_listener.recognize_google(audio)
            activation_phrase = activation_phrase.lower()
            print(f'You: {activation_phrase}')

            # activation_phrase.starts_with(f"hello {self.robin.config['name']}"):
            if starts_with(activation_phrase, r"(({1})|({2}))(.)? {0}".format(
                    self.robin.config["name"].lower(),
                    "good (morning|afternoon|evening)",
                    "hey|hi|hello"
            ) or contains(activation_phrase, self.robin.config["name"].lower())):
                self.pause_capture(False)
                self.robin.talk('Hi, what can i do for you?')
                self.robin.listen()
        except sr.UnknownValueError as unknown_value:
            if unknown_value is not '':
                print(None)

        except sr.HTTPError as http_error:
            print('HTTP Error:', http_error)

        except sr.RequestError as request_error:
            print(request_error)

        except sr.WaitTimeoutError as wait_error:
            print(wait_error)

        except Exception as ex:
            print(ex)
            print('Capture is Exiting...')
            self.exit(self.ui)

    def pause_capture(self, wait_for_stop):
        """ Kills background listening daemonic thread """
        print("listener is paused")
        if self.sr_daemon is not None:
            self.sr_daemon(wait_for_stop)
            self.sr_daemon = None

    def start_capture(self, message=None):
        """
        Activates background listening daemonic thread while continuously records phrases in the background
        and processes them
        """
        try:
            # Set idle to false since robin is listening in background
            self.robin.idle = False
            # Start bg listener daemon
            if self.sr_daemon is None:
                print("Starting bg listener daemon")
                listener = sr.Recognizer()
                self.sr_daemon = listener.listen_in_background(
                    sr.Microphone(),
                    self.capture_activation_phrase, 3
                )

            # If the app waa just launched...
            if self.first_run is True:
                self.robin.config["last_launched_at"] = datetime.now()
                self.robin.talk(self.startup_message())
                # Set is_first_launch to False
                if eval(self.robin.config["is_first_launch"]):
                    self.robin.config["is_first_launch"] = False

                conf = Config()
                conf.save_config(conf.path, self.robin.config)

            # Else randomly decide to tell the user the app is listening in the background
            elif ai_should_proceed_with_action():
                message = self.startup_message() if message is None else message
                self.robin.talk(message, display_message=False)

        except Exception as ex:
            print(ex)
            print('Exiting...')
            self.exit(self.ui)

    def exit(self, ui=None):
        notification.notify(
            title='Robin has stopped listening',
            message="An error occurred while listening in the background and listener has been paused. "
                    "Tap the mic button to restart background listener",
            app_name='Robin Virtual Assistant', app_icon='', timeout=3600,
            toast=True
        )
        self.should_exit = True
        conf = Config()
        conf.save_config(conf.path, self.robin.config)

    def run(self):
        """ Entry point for app background listening engine """
        if self.robin.idle is True and self.should_exit is False:
            # Start listening in background
            self.start_capture()

        # Keep the main thread running while app hasn't exited
        while self.should_exit is False:
            if self.robin.idle is True:
                if self.first_run:
                    self.first_run = False
                else:
                    random_activities = [
                        "Going back to sleep",
                        "Talk later boss",
                        "Off to do my thing"
                    ]
                    random_catchphrase = [
                        "Holla at me if you need anything",
                        f"Just say \"hello {self.robin.config['name']}\" whenever you need me",
                        "Just say the magic word and i'd be right with you!",
                        f"Hot word is \"hello {self.robin.config['name']}\""
                    ]

                    if ai_should_proceed_with_action():
                        message = f"{random.choice(random_activities)}. {random.choice(random_catchphrase)}."
                    else:
                        message = "..."
                    self.start_capture(message)

            self.idleness_count += 1
            if self.idleness_count > 160 and self.robin is not None:
                if ai_should_proceed_with_action():
                    message_index = random.randint(0, len(self.__idleness_reminders) - 1)
                    notification.notify(
                        title='Robin Reminder', message=self.__idleness_reminders[message_index],
                        app_name='Robin Virtual Assistant', app_icon='', timeout=40
                    )
                    self.robin.talk(self.__idleness_reminders[message_index])
                self.idleness_count = 0

            time.sleep(2)

        print("stopped bg")
        self.pause_capture(True)

# r = Robin()
# RobinBackgroundService(r, AppBgListener(robin_instance=r), None).run()
