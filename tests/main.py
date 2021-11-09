from kivy.lang import Builder
from kivymd.app import MDApp

# from kivymd.theming import ThemeManager

kv = '''
FloatLayout:

    MDContextMenu:
        menu: app.menu
        pos_hint: {'top': 1}
        on_enter: app.on_enter(*args)

        MDContextMenuItem:
            text: 'File'

        MDContextMenuItem:
            text: 'Edit'
'''

MENU = [
    [
        "File",
        [
            {"Item 1": []},
            {
                "Item 2": [
                    "Item 1",
                    "Item 2",
                    "Separator",
                    ["language-python", "Item 3"],
                ]
            },
            "Separator",
            {"Item 3": []},
            {
                "Item 4": [
                    ["language-python", "Item 1"],
                    ["language-cpp", "Item 2"],
                    "Separator",
                    ["language-swift", "Item 3"],
                ]
            },
            "Separator",
            {"Item 5": []},
        ],
    ],

    [
        "Edit",
        [
            {"Item 1": []},
            ["language-swift", "Item 3"]
        ]
    ]

]


class Test(MDApp):
    context_menu = None
    menu = MENU

    @staticmethod
    def on_enter(instance):
        """
        :type instance: <kivymd.context_menu.MDContextMenu object>

        """
        print(instance.current_selected_menu.text)

    def build(self):
        root = Builder.load_string(kv)
        return root


Test().run()
