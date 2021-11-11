import json
import threading
from multiprocessing import active_children

from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.settings import SettingsWithSidebar
from kivymd.app import MDApp

from core.robin import RobinInterface, Robin
from core.config import setting_panels, settings_sections

bg_listener_thread = None
universal_db = {}


def update_universal_db(key, value):
    universal_db[key] = value


# create the layout class
class FileChooser(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__()
        self.files = StringProperty('')
        self.callback = None if 'callback' not in kwargs else kwargs['callback']
        # print(kwargs)

    def select(self, *args):
        file_list = args[1]
        try:
            self.ids.file_input_box.text = ';'.join(file_list)
            self.files = ';'.join(file_list)
        except:
            pass

    def confirm_select(self, app, *args):
        print(type(self.files).__name__)
        if type(self.files).__name__ == 'str' and self.files is not '':
            if self.callback is not None and type(self.callback).__name__ == 'function':
                threading.Thread(
                    target=self.callback,
                    args=(self.files.split(';'),),
                    daemon=True
                ).start()
            app.close_popup('filedialog')

    @staticmethod
    def cancel(*args):
        app = args[0]
        app.close_popup('filedialog')


class MainLayout(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from ui.home import HomeLayout
        from ui.preloader import Preloader
        from ui.menu import Menu

        self.app_ui_handlers = None
        self.preloader = Preloader()
        self.home = HomeLayout()
        self.app_menu = Menu()

        self.add_widget(self.preloader)
        self.add_widget(self.home)
        self.add_widget(self.app_menu)

    def save_app_ui_handlers(self, app_ui_handlers):
        self.app_ui_handlers = app_ui_handlers
        self.home.save_app_ui_handlers(app_ui_handlers)


class RobinApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.core.audio import SoundLoader
        self.title = 'Robin Virtual Assistant'
        self.icon = 'resources/images/Robin.png'
        self.app_ui_handlers = None
        self.sound_loader = SoundLoader
        self.ui_home = None
        self.popups = {}
        self.count = 0

    def __reduce__(self):
        """ helper for pickle """
        return self.__class__, ()

    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.root = MainLayout()
        self.root.save_app_ui_handlers(self.app_ui_handlers)
        self.ui_home = self.root.home
        return self.root

    def build_config(self, config):
        for section, options in settings_sections.items():
            config.setdefaults(section, options)

    def build_settings(self, settings):
        for panel, _setting in setting_panels.items():
            settings.add_json_panel(panel, self.config, data=json.dumps(_setting))

    def on_start(self):
        try:
            # Increase the progress bar
            Clock.schedule_interval(self.update_progress_value, 0.5)

            update_universal_db('progress_value', 30)
            update_universal_db('progress_message', "Starting bg listener process...")
        except Exception as e:
            print(e)

    def save_app_ui_instance_as_handlers(self, app_ui):
        self.app_ui_handlers = app_ui

    def play_sound(self, song_file):
        self.sound_loader.load(song_file).play()

    def create_popup(self, **kwargs):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        # name, content, title
        name = f"popup_{len(self.popups) + 1}" if 'name' not in kwargs else kwargs['name']
        title = "New Popup window" if 'title' not in kwargs else kwargs['title']
        size = (400, 400) if 'size' not in kwargs else kwargs['size']

        default_content = BoxLayout()
        default_content.orientation = 'vertical'
        default_content.add_widget(Label(text="Hello, this is a popup"))
        default_content.add_widget(Button(text="close", on_press=lambda instance: self.close_popup(name)))

        content = default_content if 'content' not in kwargs else kwargs['content']
        self.popups[name] = Popup(title=title, content=content, size_hint=(None, None), size=size)
        return self.popups[name]

    def close_popup(self, name, *args):
        self.popups[name].dismiss()
        del self.popups[name]

    def create_filedialog(self, **kwargs):
        content = FileChooser(**kwargs)
        filedialog = self.create_popup(name='filedialog', title="File Chooser", content=content, size=(600, 500))
        filedialog.open()
        return content

    def update_progress_value(self, dt):
        if universal_db is not None:
            value = int(universal_db['progress_value']) + self.count
            self.root.preloader.progress_value = value
            self.root.preloader.progress_message = universal_db['progress_message']

            self.count += 1
            update_universal_db('progress_value', value)

            # Go to dashboard or exit if loading failed
            if value >= 100:
                Clock.unschedule(self.update_progress_value)
                self.root.current = 'home'

                if bg_listener_thread is not None:
                    print("Starting bg listener process...")
                    bg_listener_thread.start()


# registering our new custom font style
LabelBase.register(name='Poppins', fn_regular='resources/fonts/poppins/Poppins-Regular.ttf')
LabelBase.register(name='Poppins-Medium', fn_regular='resources/fonts/poppins/Poppins-Medium.ttf')
LabelBase.register(name='Poppins-Bold', fn_regular='resources/fonts/poppins/Poppins-Bold.ttf')


class AppUI:
    def __init__(self):
        self.robin_interface_instance = None
        self.robinGUI = None
        self.robin_instance = None
        self.robin_background_service = None

    def launch(self):
        # Start background listener thread
        try:
            # Initialize Background Processes
            self.initialize_bg_processes()
            update_universal_db('progress_message', "Initializing BG Processes...")

            # Initialize RobinUIApp instance
            self.robinGUI = RobinApp()

            # Pass AppUI handlers to RobinUIApp instance
            self.robinGUI.save_app_ui_instance_as_handlers(app_ui=self)
            self.robinGUI.run()
        except Exception as ex:
            raise ex
            # print('Launch Error:', ex)
        finally:
            # Once app stops running, exit the app
            self.exit()

    def initialize_bg_processes(self):
        global universal_db, bg_listener_thread
        from utils.multitask import MyThread
        from service.robin_bg_service import RobinBackgroundService
        # Start background listener thread
        try:
            # Initialize Robin core
            self.robin_instance = Robin(ui=self) if self.robin_instance is None else self.robin_instance

            # Initialize Robin core
            self.robin_interface_instance = RobinInterface(
                robin_instance=self.robin_instance,
                ui_instance=self
            ) if self.robin_interface_instance is None else self.robin_interface_instance

            self.robin_background_service = RobinBackgroundService(
                self.robin_instance,
                self.robin_interface_instance,
                self
            ) if self.robin_background_service is None else self.robin_background_service

            # Initialize bg listener process
            bg_listener_thread = MyThread(name="bg", callback=self.robin_background_service.run, params=None)
            bg_listener_thread.daemon = True
        except Exception as ex:
            print(ex)

    def check_bg_processes_status(self, is_idle):
        try:
            global universal_db, bg_listener_thread
            print("bg_listener_thread is alive:", bg_listener_thread.is_alive())
            # If listener is not alive, restart listener
            if not bg_listener_thread.is_alive():
                self.robin_background_service.should_exit = False
                self.initialize_bg_processes()
        except Exception as ex:
            print(ex)

    def exit(self):
        from threading import current_thread, main_thread
        Clock.unschedule(self.robinGUI.update_progress_value)
        print('Stopping background processes...')
        self.robin_instance.exit()

        # Make all running threads daemonic, so it can be terminated at exit of program
        for thread in threading.enumerate():
            if thread.is_alive() and thread.isDaemon() is False and current_thread() is not main_thread():
                try:
                    thread.setDaemon(True)
                except Exception:
                    pass

        # Check for running processes and terminate processes
        for process in active_children():
            if process.is_alive() and process.daemon is False:
                process.terminate()
                print(f'{process} is alive:', process.is_alive())

    def update_ui_screen(self, message):
        if self.robinGUI and self.robinGUI.ui_home:
            self.robinGUI.ui_home.ui_screen_widget_handler(message)
        else:
            print('Printing on console:', message)

    def robin_listen_action(self):
        if self.robinGUI and self.robinGUI.ui_home:
            mic_is_pressed = self.robinGUI.ui_home.mic.state is 'down'
            if mic_is_pressed:
                self.robin_instance.idle = False
                self.robin_background_service.pause_capture(False)
                self.app_bg_instance.robin_listen_action(ui=self)
                self.robin_instance.idle = True
            else:
                self.app_bg_instance.robin_stop_listen_action(ui=self)
                self.robin_instance.idle = True

    def robin_read_action(self, command):
        self.app_bg_instance.robin_read_action(command, self)
        self.robin_instance.idle = False

    def audio_visualizer_action(self):
        if self.robinGUI and self.robinGUI.ui_home:
            self.robinGUI.ui_home.do_audio_visualizer_animation()

    # ANIMATIONS =================================================
    def start_mic_animation(self):
        if self.robinGUI and self.robinGUI.ui_home:
            self.robinGUI.ui_home.mic.state = 'down'
            self.robinGUI.ui_home.do_mic_animation()

    def stop_mic_animation(self):
        if self.robinGUI and self.robinGUI.ui_home:
            self.robinGUI.ui_home.stop_mic_animation()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Initialize UI
    AppUI().launch()
