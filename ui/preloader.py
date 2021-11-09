from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen

Builder.load_file('ui/preloader.kv')


class Preloader(Screen):
    progress_value = NumericProperty(10)
    progress_message = StringProperty('Starting App...')

    def on_progress_value(self, instance, value):
        pass

    def on_progress_message(self, instance, value):
        pass
