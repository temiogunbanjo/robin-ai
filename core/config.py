from datetime import datetime
import pyttsx3 as tts
from kivy.config import ConfigParser

settings_sections = {
    "user": {
        "language": "en-us",
    },
    "assistant": {
        "name": "Robin",
        "default_voice": 0,
        "wake_phrase": "hello robin"
    }
}

setting_panels = {
    "User Preferences": [
        {
            "type": "title",
            "title": "Language"
        },
        {
            "type": "options",
            "title": "Language",
            "key": "language",
            "section": "user",
            "desc": "The language you speak",
            "options": ["en-us", "en-fr"]
        }
    ],
    "Assistant": [
        {
            "type": "title",
            "title": "Voice Settings"
        },
        {
            "type": "options",
            "title": "AI Voice",
            "key": "default_voice",
            "section": "assistant",
            "desc": "Voice used by Assistant to speak",
            "options": ["0", "1"]
        },
        {
            "type": "title",
            "title": "Settings"
        },
        {
            "type": "string",
            "title": "Wake up phrase",
            "key": "wake_phrase",
            "section": "assistant",
            "desc": "Size of shape"
        },
    ]
}


class Config:
    def __init__(self):
        self.path = 'ai_pref.txt'
        self.default_config = {
            "name": 'robin',
            "language": "en-us",
            "default_voice": 0,
            "is_first_launch": True,
            "last_launched_at": datetime.now()
        }
        self.parser = ConfigParser()
        print(self.parser.read("robin.ini"))

    @staticmethod
    def config_exist(path):
        from os import path as p
        return p.isfile(path)

    def load_config(self, config_path=None):
        voices = self.get_tts_engine().getProperty('voices')
        path = config_path if config_path is not None else self.path

        # Load preferences if not first time
        if self.config_exist(path) is True:
            return {
                "voices": voices,
                **self.read_config(path)
            }
        # Else save default preferences
        else:
            self.save_config(path, self.default_config)
            self.default_config["voices"] = voices
            return self.default_config

    def save_config(self, path, config=None):
        config = self.default_config if config is None else config
        with open(path, 'w') as ai_pref_file:
            # Operations
            print('saving configurations...')
            for param in config:
                if param is not 'voices':
                    ai_pref_file.write(str(param) + "=" + str(config[param]) + "\n")
            print('Saved!')
            return

    def read_config(self, path):
        with open(path, 'r') as ai_pref_file:
            # Operations
            for line in ai_pref_file:
                param_value = line.split('=')
                self.default_config[param_value[0]] = param_value[1].replace('\n', '').strip()
        return self.default_config

    def get_tts_engine(self, **kwargs):
        engine = tts.init()
        voices = engine.getProperty('voices')
        voice_index_to_use = self.default_config["default_voice"] if 'voice_index' not in kwargs else int(
            kwargs["voice_index"])
        volume = 1 if 'volume' not in kwargs else int(kwargs["volume"])
        rate = 180 if 'rate' not in kwargs else int(kwargs["rate"])

        engine.setProperty('voice', voices[int(voice_index_to_use)].id)
        engine.setProperty('volume', volume)
        engine.setProperty('rate', rate)
        return engine
