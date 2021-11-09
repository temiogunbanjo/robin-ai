from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.actionbar import ActionBar
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextFieldRound

all_sounds = {
    'mic_on': SoundLoader.load('resources/audio/beep1.wav'),
    'mic_off': SoundLoader.load('resources/audio/beep4 (5).mp3')
}


class NavigationBar(ActionBar):
    pass


class Body(BoxLayout):
    pass


class ResponseDisplay(ScrollView):
    pass


class InputSectionLayout(BoxLayout):
    pass


class AppTextField(MDTextFieldRound):
    def on_focus(self, instance, value):
        # print(self.get_root_window().ids)
        if value:
            self.icon_left_color = [139 / 255, 195 / 255, 75 / 255, 1]
            self.icon_right_color = [139 / 255, 195 / 255, 75 / 255, 1]

        else:
            self.icon_left_color = self.theme_cls.text_color
            self.icon_right_color = self.theme_cls.text_color


class RoundedButton(Button):
    pass


class RoundedToggleButton(ToggleButton):
    pass


class MicButton(RoundedToggleButton):
    status = 'normal'
    is_listening = False
    font_name = "Poppins-Medium"
    size = (dp(100), dp(100))
    size_hint = (None, None)
    pos_hint = {"center_x": 0.5, "center_y": 0.5}

    def on_state(self, *args):
        widget = args[0]
        self.status = widget.state


class AudioVisualizer(BoxLayout):
    pass


Builder.load_file('ui/home.kv')


class HomeLayout(MDScreen):
    message = StringProperty("Hey there!")
    input_box_value = StringProperty('')

    def __init__(self, **kwargs):
        super(HomeLayout, self).__init__(**kwargs)

        self.app_ui_handlers = None
        screen_layout = BoxLayout()
        header = NavigationBar()
        body = Body()

        response_section = ResponseDisplay()
        visualizer_section = AnchorLayout()
        mic_button_section = AnchorLayout()
        self.input_section = InputSectionLayout()

        # Widgets
        self.visualizer = AudioVisualizer()

        self.response_text_display = response_section.ids.response_label
        self.response_text_display.text = self.message

        self.mic = MicButton(text="Speak", color=(1, 1, 1),
                             on_press=lambda instance: self.activate_mic_widget_handler(instance))

        self.input_box = self.input_section.ids.command_input
        self.input_box.bind(text=self.on_text)

        self.post_button = self.input_section.ids.post_button
        self.post_button.bind(on_press=lambda instance: self.post_button_widget_handler(instance))

        self.input_section.height = self.post_button.height

        visualizer_section.add_widget(self.visualizer)
        mic_button_section.add_widget(self.mic)

        body.add_widget(response_section)
        body.add_widget(mic_button_section)
        body.add_widget(visualizer_section)
        body.add_widget(self.input_section)

        screen_layout.orientation = 'vertical'
        screen_layout.add_widget(header)
        screen_layout.add_widget(body)

        self.add_widget(screen_layout)

    def __reduce__(self):
        """ helper for pickle """
        return self.__class__, ()

    def on_text(self, *args):
        """ Gets called on key press in text box """
        value = args[1]
        self.input_box_value = value

    def on_input_box_value(self, *args):
        """ Gets called when the input_box_value changes """
        value = args[1]
        if value is not '':
            self.update_screen_value("[color=#77FF77]You:[/color] [color=#FFF]typing...[/color]")
        else:
            self.update_screen_value("[color=#FFF]...[/color]")

    def on_message(self, *args):
        value = args[1]
        self.update_screen_value(value)

    def update_screen_value(self, message):
        self.response_text_display.text = message
        self.response_text_display.height = self.response_text_display.texture_size[1]

    # WIDGET HANDLERS ==================================================================
    def activate_mic_widget_handler(self, instance):
        self.app_ui_handlers.robin_listen_action()

    def ui_screen_widget_handler(self, message):
        self.message = f"{message}"

    def post_button_widget_handler(self, instance):
        print('Send command button pressed')
        command = self.input_box_value
        if command is not '':
            self.response_text_display.text = f"[color=#77FF77]You:[/color] {command}"
            self.input_box.text = ''
            self.app_ui_handlers.robin_read_action(command)

    def save_app_ui_handlers(self, app_ui_handlers):
        self.app_ui_handlers = app_ui_handlers

    # ANIMATIONS ==========================================================================
    def do_mic_animation(self):
        if self.mic.status is 'down':
            self.mic.text = '• • •'
            self.mic.canvas_bg_color = self.mic.down_state_color
            all_sounds['mic_on'].play()
            Clock.schedule_interval(self.start_mic_animation, 2)
        else:
            self.stop_mic_animation()

    def start_mic_animation(self, *args):
        self.mic.is_listening = True
        anim = Animation(animated_color=(144 / 255, 164 / 255, 174 / 255, 0.5), size_increase_factor=0.4, t='out_cubic')
        anim += Animation(animated_color=(144 / 255, 164 / 255, 174 / 255, 0), size_increase_factor=0, t='in_cubic')
        anim.start(self.mic)

    def stop_mic_animation(self):
        if self.mic.status is not 'down' or self.mic.is_listening is True:
            self.mic.is_listening = False
            Animation().stop_all(self.mic)
            self.mic.state = 'normal'
            self.mic.text = 'Speak'
            self.mic.canvas_bg_color = self.mic.up_state_color
            self.mic.animated_color = (30 / 255, 144 / 255, 1, 0)
            self.mic.size_increase_factor = 0
            all_sounds['mic_off'].play()
        Clock.unschedule(self.start_mic_animation)

    @staticmethod
    def do_audio_visualizer_animation():
        print('visualizing audio')
