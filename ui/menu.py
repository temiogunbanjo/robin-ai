from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen


class MenuNavigationBar(BoxLayout):
    pass


class MenuBody(BoxLayout):
    pass


Builder.load_file('ui/menu.kv')


class Menu(Screen):
    def __init__(self, **kwargs):
        super(Menu, self).__init__(**kwargs)
        screen_layout = BoxLayout()
        header = MenuNavigationBar()
        body = MenuBody()

        screen_layout.orientation = 'vertical'
        screen_layout.add_widget(header)
        screen_layout.add_widget(body)

        self.add_widget(screen_layout)

    def __reduce__(self):
        """ helper for pickle """
        return self.__class__, ()
