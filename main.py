from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from datetime import datetime
import threading
import requests

# Android voice imports
from jnius import autoclass
from android import activity

Window.softinput_mode = "below_target"


# =========================
# SPLASH SCREEN
# =========================
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout()

        with layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = RoundedRectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self.update_bg, size=self.update_bg)

        self.logo = Label(
            text="J.A.R.V.I.S",
            font_size=sp(42),
            color=(0.2, 0.9, 1, 0)
        )

        layout.add_widget(self.logo)
        self.add_widget(layout)

        anim = Animation(color=(0.2, 0.9, 1, 1), duration=1)
        anim.start(self.logo)

        Clock.schedule_once(self.go_main, 2)

    def update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

    def go_main(self, dt):
        self.manager.current = "main"


# =========================
# AI FUNCTION
# =========================
API_KEY = "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"  # Put key if needed
API_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def ask_ai(prompt):

    if "time" in prompt.lower():
        return datetime.now().strftime("Current time: %I:%M %p")

    if "date" in prompt.lower():
        return datetime.now().strftime("Today is %A, %B %d, %Y")

    if not API_KEY:
        return "No API key connected."

    try:
        payload = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Jarvis. Be intelligent and cool."
                },
                {"role": "user", "content": prompt}
            ]
        }

        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
        data = r.json()
        return data["choices"][0]["message"]["content"]

    except:
        return "Connection error."


# =========================
# CHAT BUBBLE
# =========================
class ChatBubble(BoxLayout):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None)
        self.padding = dp(12)
        self.size_hint_x = 0.8

        self.label = Label(
            text=text,
            font_size=sp(16),
            size_hint_y=None,
            halign="left",
            valign="top",
            color=(1, 1, 1, 1)
        )

        self.label.bind(
            width=lambda *x: self.label.setter('text_size')(self.label, (self.label.width, None)),
            texture_size=self.update_height
        )

        self.add_widget(self.label)

        with self.canvas.before:
            if is_user:
                Color(0.2, 0.6, 1, 1)
            else:
                Color(0.18, 0.18, 0.18, 1)

            self.bg = RoundedRectangle(radius=[25])

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_height(self, instance, size):
        self.label.height = size[1]
        self.height = size[1] + dp(24)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


# =========================
# MAIN UI
# =========================
class JarvisUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical")

        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
            padding=dp(10)
        )

        self.chat_layout.bind(minimum_height=self.chat_layout.setter("height"))
        self.scroll.add_widget(self.chat_layout)
        self.add_widget(self.scroll)

        # Bottom bar container (rounded)
        bottom_container = BoxLayout(
            size_hint=(1, None),
            height=dp(70),
            padding=dp(10)
        )

        with bottom_container.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bottom_bg = RoundedRectangle(radius=[30])

        bottom_container.bind(
            pos=lambda i, v: setattr(self.bottom_bg, "pos", i.pos),
            size=lambda i, v: setattr(self.bottom_bg, "size", i.size)
        )

        self.input_box = TextInput(
            hint_text="Message Jarvis...",
            multiline=False,
            font_size=sp(18),
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.2, 0.9, 1, 1)
        )

        self.input_box.bind(on_text_validate=self.send_message)

        self.send_btn = Button(
            text="Send",
            size_hint=(None, 1),
            width=dp(70),
            background_normal="",
            background_color=(0.2, 0.6, 1, 1)
        )
        self.send_btn.bind(on_press=self.send_message)

        self.mic_btn = Button(
            text="🎤",
            size_hint=(None, 1),
            width=dp(60),
            background_normal="",
            background_color=(0.2, 0.9, 1, 1)
        )
        self.mic_btn.bind(on_press=self.start_voice_input)

        bottom_container.add_widget(self.mic_btn)
        bottom_container.add_widget(self.input_box)
        bottom_container.add_widget(self.send_btn)

        self.add_widget(bottom_container)

        self.add_message("Jarvis ready. How may I assist you?", False)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def add_message(self, message, is_user):
        container = BoxLayout(orientation="horizontal", size_hint_y=None)

        bubble = ChatBubble(message, is_user)

        def update_container(instance, value):
            container.height = value + dp(10)

        bubble.bind(height=update_container)

        if is_user:
            container.add_widget(Widget(size_hint_x=0.2))
            container.add_widget(bubble)
        else:
            container.add_widget(bubble)
            container.add_widget(Widget(size_hint_x=0.2))

        self.chat_layout.add_widget(container)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1)

        return bubble

    def send_message(self, instance):
        text = self.input_box.text.strip()
        if not text:
            return

        self.add_message(text, True)
        self.input_box.text = ""

        thinking = self.add_message("Jarvis is thinking...", False)

        threading.Thread(
            target=self.get_response,
            args=(text, thinking),
            daemon=True
        ).start()

    def get_response(self, text, bubble):
        reply = ask_ai(text)
        Clock.schedule_once(lambda dt: self.update_bubble(bubble, reply))

    def update_bubble(self, bubble, new_text):
        bubble.label.text = new_text

    # =========================
    # ANDROID NATIVE VOICE
    # =========================
    def start_voice_input(self, instance):
        Intent = autoclass('android.content.Intent')
        RecognizerIntent = autoclass('android.speech.RecognizerIntent')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')

        intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now...")

        currentActivity = PythonActivity.mActivity
        currentActivity.startActivityForResult(intent, 1001)

        activity.bind(on_activity_result=self.on_activity_result)

    def on_activity_result(self, requestCode, resultCode, intent):
        if requestCode == 1001 and resultCode == -1:
            results = intent.getStringArrayListExtra(
                autoclass('android.speech.RecognizerIntent').EXTRA_RESULTS
            )
            spoken_text = results.get(0)
            self.input_box.text = spoken_text


# =========================
# APP
# =========================
class JarvisApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.4))
        sm.add_widget(SplashScreen(name="splash"))

        main = Screen(name="main")
        main.add_widget(JarvisUI())
        sm.add_widget(main)

        sm.current = "splash"
        return sm


if __name__ == "__main__":
    JarvisApp().run()