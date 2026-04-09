"""
main.py — Big Brain AI Stage 2 Step 1: Dark UI Shell
"""

import os
import sys
import datetime
import threading
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex

BLACK_VOID  = get_color_from_hex("#000000")
BLACK_SOFT  = get_color_from_hex("#0A0A0F")
VIOLET_DARK = get_color_from_hex("#0D0520")
VIOLET_GLOW = get_color_from_hex("#7B00CC")
GREEN_DARK  = get_color_from_hex("#001A0D")
GREEN_GLOW  = get_color_from_hex("#00AA44")
TEXT_DIM    = get_color_from_hex("#6B5A7E")
TEXT_SOFT   = get_color_from_hex("#C0A0D8")
TEXT_BRIGHT = get_color_from_hex("#FFFFFF")
TEXT_GREEN  = get_color_from_hex("#00CC55")

Window.clearcolor = BLACK_VOID

class MarqueeBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(26)
        self._full_text = ""
        self._char_pos = 0
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda i, v: setattr(self._bg, "pos", v))
        self.bind(size=lambda i, v: setattr(self._bg, "size", v))
        self.lbl = Label(text="", markup=True, font_size=dp(11),
                         halign="left", valign="middle", color=list(TEXT_DIM)+[1])
        self.add_widget(self.lbl)
        Clock.schedule_interval(self._update_content, 10)
        Clock.schedule_interval(self._scroll, 0.08)
        self._update_content(0)

    def _update_content(self, dt):
        now = datetime.datetime.now()
        t = now.strftime("%I:%M %p")
        d = now.strftime("%a %b %d")
        w = "-- °F"
        self._full_text = f"[color=7B00CC]{t}[/color]  [color=006633]{d}[/color]  [color=00AA44]{w}[/color]          "

    def _scroll(self, dt):
        if not self._full_text: return
        t = self._full_text
        pos = self._char_pos % len(t)
        self.lbl.text = (t + t)[pos:pos+60]
        self._char_pos += 1

class DarkButton(Button):
    def __init__(self, glow_color=None, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self._glow = glow_color or VIOLET_GLOW
        with self.canvas.before:
            self._c = Color(*VIOLET_DARK)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._rr.pos = self.pos
        self._rr.size = self.size

    def on_press(self):
        self._c.rgba = list(self._glow)+[1]
        self.color = list(TEXT_BRIGHT)+[1]

    def on_release(self):
        self._c.rgba = list(VIOLET_DARK)+[1]
        self.color = list(TEXT_DIM)+[1]

class MessageBubble(BoxLayout):
    def __init__(self, text, is_user=True, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(6), dp(4)]
        bg = VIOLET_DARK if is_user else GREEN_DARK
        tc = list(TEXT_SOFT) if is_user else list(TEXT_GREEN)
        with self.canvas.before:
            Color(*bg)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=lambda i, v: setattr(self._bg, "pos", v))
        self.bind(size=lambda i, v: setattr(self._bg, "size", v))
        lbl = Label(text=text, markup=True, size_hint_y=None,
                    text_size=(Window.width * 0.75, None),
                    halign="left", valign="top", color=tc,
                    font_size=dp(13), padding=[dp(10), dp(8)])
        lbl.bind(texture_size=lambda i, v: setattr(i, "height", v[1]+dp(16)))
        lbl.bind(height=lambda i, v: setattr(self, "height", v+dp(16)))
        self.add_widget(lbl)

class BigBrainChat(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 0
        self._build_ui()

    def _build_ui(self):
        self.add_widget(MarqueeBar())
        header = BoxLayout(size_hint_y=None, height=dp(46), padding=[dp(16), dp(8)])
        with header.canvas.before:
            Color(*BLACK_SOFT)
            hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hbg, "pos", v))
        header.bind(size=lambda i, v: setattr(hbg, "size", v))
        header.add_widget(Label(
            text="[b][color=4A0080]BIG[/color] [color=006633]BRAIN[/color][/b]",
            markup=True, font_size=dp(20), halign="left", valign="middle",
        ))
        self.add_widget(header)
        div = BoxLayout(size_hint_y=None, height=dp(1))
        with div.canvas.before:
            Color(*VIOLET_GLOW, 0.25)
            Rectangle(size=div.size, pos=div.pos)
        self.add_widget(div)
        self.scroll = ScrollView(size_hint_y=1)
        self.chat_layout = BoxLayout(orientation="vertical", size_hint_y=None,
                                     spacing=dp(6), padding=[dp(10), dp(10)])
        self.chat_layout.bind(minimum_height=self.chat_layout.setter("height"))
        self.scroll.add_widget(self.chat_layout)
        self.add_widget(self.scroll)
        self.status_lbl = Label(text="", size_hint_y=None, height=dp(20),
                                color=list(TEXT_DIM)+[1], font_size=dp(11))
        self.add_widget(self.status_lbl)
        input_row = BoxLayout(size_hint_y=None, height=dp(54),
                              spacing=dp(6), padding=[dp(8), dp(6)])
        with input_row.canvas.before:
            Color(*BLACK_SOFT)
            ibg = Rectangle(pos=input_row.pos, size=input_row.size)
        input_row.bind(pos=lambda i, v: setattr(ibg, "pos", v))
        input_row.bind(size=lambda i, v: setattr(ibg, "size", v))
        self.text_input = TextInput(
            hint_text="speak...", hint_text_color=list(TEXT_DIM)+[1],
            multiline=False, size_hint_y=None, height=dp(42),
            background_color=list(GREEN_DARK)+[1],
            foreground_color=list(TEXT_SOFT)+[1],
            cursor_color=list(GREEN_GLOW)+[1],
            font_size=dp(14), padding=[dp(12), dp(10)],
        )
        input_row.add_widget(self.text_input)
        send_btn = DarkButton(text="▶", glow_color=GREEN_GLOW,
                              size_hint_x=None, width=dp(44),
                              size_hint_y=None, height=dp(42),
                              color=list(TEXT_DIM)+[1], font_size=dp(18), bold=True)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)
        self._add_message("Big Brain online.", is_user=False)

    def _add_message(self, text, is_user=True):
        bubble = MessageBubble(text=text, is_user=is_user,
                               size_hint_x=0.82,
                               pos_hint={"right": 1} if is_user else {"x": 0})
        self.chat_layout.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1)

class BigBrainApp(App):
    def build(self):
        self.title = "Big Brain"
        return BigBrainChat()

from kivy.app import App as _App
import sys as _sys

IS_ANDROID = "ANDROID_ARGUMENT" in __import__("os").environ or "ANDROID_PRIVATE_PATH" in __import__("os").environ

def request_permissions():
    if not IS_ANDROID:
        return
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.READ_SMS, Permission.RECEIVE_SMS, Permission.SEND_SMS,
            Permission.READ_CALL_LOG, Permission.CALL_PHONE,
            Permission.READ_CONTACTS, Permission.WRITE_CONTACTS,
            Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION,
            Permission.CAMERA, Permission.RECORD_AUDIO,
            Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE,
            Permission.POST_NOTIFICATIONS, Permission.RECEIVE_BOOT_COMPLETED,
            Permission.FOREGROUND_SERVICE, Permission.VIBRATE,
        ])
    except Exception:
        pass

if __name__ == "__main__":
    BigBrainApp().run()
