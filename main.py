from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
Window.clearcolor = get_color_from_hex("#0A000F")
class BigBrainApp(App):
    def build(self):
        self.title = "Big Brain AI"
        root = BoxLayout(orientation="vertical")
        root.add_widget(Label(text="[b][color=9B30FF]BIG[/color] [color=00FF88]BRAIN[/color] [color=E8D5FF]AI[/color][/b]\nOnline.",markup=True,font_size="28sp",halign="center"))
        return root
if __name__ == "__main__":
    BigBrainApp().run()
