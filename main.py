from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import ListProperty
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.card import MDCard
from bs4 import BeautifulSoup
import zipfile
import requests
from threading import Thread
import os
import webbrowser

# Android imports
from android.permissions import request_permissions, Permission
from android.storage import app_storage_path
from android import mActivity
from jnius import autoclass, cast

Environment = autoclass('android.os.Environment')
Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Context = autoclass('android.content.Context')

KV = '''
<RoundedButton@MDRaisedButton>:
    md_bg_color: app.theme_cls.primary_color
    text_color: 1, 1, 1, 1
    radius: [24,]

ScreenManager:
    SelectionScreen:
    ResultsScreen:

<SelectionScreen>:
    name: "select"
    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 20

        RoundedButton:
            text: "Select ZIP"
            on_release: root.open_file_picker()
            size_hint_y: None
            height: "50dp"

        MDLabel:
            id: file_label
            text: ""
            halign: "center"
            theme_text_color: "Secondary"

        BoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: 10

            MDCheckbox:
                id: checkbox
                size_hint: None, None
                size: "48dp", "48dp"

            MDLabel:
                text: "I Agree to the Terms and Conditions."
                theme_text_color: "Secondary"
                halign: "left"

        RoundedButton:
            text: "Continue"
            on_release: root.check_and_continue()
            size_hint_y: None
            height: "50dp"

<ResultsScreen>:
    name: "results"
    BoxLayout:
        orientation: "vertical"

        MDDropDownItem:
            id: filter_dropdown
            text: "Accounts Don’t Follow You"
            pos_hint: {"center_x": 0.5}
            on_release: root.menu.open()

        ScrollView:
            GridLayout:
                id: results_grid
                cols: 1
                spacing: dp(10)
                padding: dp(10)
                size_hint_y: None
                height: self.minimum_height
'''

Builder.load_string(KV)

class SelectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_path = None
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE, Permission.INTERNET])

    def open_file_picker(self):
        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("*/*")
        mActivity.startActivityForResult(intent, 123)

    def on_activity_result(self, request_code, result_code, data):
        if request_code == 123 and data:
            uri = data.getData()
            file_uri = cast(Uri, uri)
            file_path = self.get_real_path(file_uri)
            if file_path and file_path.endswith('.zip'):
                self.file_path = file_path
                self.ids.file_label.text = "File selected!"
            else:
                self.ids.file_label.text = "Please select a ZIP file."

    def get_real_path(self, uri):
        content_resolver = mActivity.getContentResolver()
        input_stream = content_resolver.openInputStream(uri)
        file_name = self.get_file_name(uri)
        temp_path = os.path.join(app_storage_path(), file_name)
        
        with open(temp_path, 'wb') as f:
            while True:
                chunk = input_stream.read(4096)
                if not chunk:
                    break
                f.write(chunk)
        input_stream.close()
        return temp_path

    def get_file_name(self, uri):
        cursor = mActivity.getContentResolver().query(uri, None, None, None, None)
        name_index = cursor.getColumnIndex(Environment.DISPLAY_NAME)
        cursor.moveToFirst()
        name = cursor.getString(name_index)
        cursor.close()
        return name

    def check_and_continue(self):
        if not self.file_path:
            self.ids.file_label.text = "Please select a file first!"
            return
        if not self.ids.checkbox.active:
            self.ids.file_label.text = "Please accept the terms!"
            return
        self.manager.current = "results"
        self.manager.get_screen("results").load_data(self.file_path)

class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.followers = []
        self.following = []
        self.menu = None
        self.setup_menu()

    def setup_menu(self):
        self.menu = MDDropdownMenu(
            caller=self.ids.filter_dropdown,
            items=[
                {"text": "Accounts Don’t Follow You", "on_release": lambda x="Accounts Don’t Follow You": self.set_filter(x)},
                {"text": "Accounts You Don’t Follow", "on_release": lambda x="Accounts You Don’t Follow": self.set_filter(x)},
            ],
            width_mult=4,
        )

    def set_filter(self, text):
        self.ids.filter_dropdown.set_item(text)
        self.menu.dismiss()
        self.show_profiles()

    def load_data(self, file_path):
        Thread(target=self._extract_zip, args=(file_path,), daemon=True).start()

    def _extract_zip(self, file_path):
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                for file in z.namelist():
                    if 'followers_1.html' in file:
                        with z.open(file) as f:
                            soup = BeautifulSoup(f.read(), 'html.parser')
                            self.followers = [a['href'] for a in soup.find_all('a', href=True)]
                    elif 'following.html' in file:
                        with z.open(file) as f:
                            soup = BeautifulSoup(f.read(), 'html.parser')
                            self.following = [a['href'] for a in soup.find_all('a', href=True)]
        except Exception as e:
            print("ZIP load error:", e)

        Clock.schedule_once(lambda dt: self.show_profiles())

    def show_profiles(self):
        self.ids.results_grid.clear_widgets()
        selected = self.ids.filter_dropdown.current_item
        if selected == "Accounts Don’t Follow You":
            urls = [url for url in self.following if url not in self.followers]
        else:
            urls = [url for url in self.followers if url not in self.following]

        for url in urls:
            Thread(target=self.add_profile, args=(url,), daemon=True).start()

    def add_profile(self, url):
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            img_url = soup.find("meta", property="og:image")
            name_tag = soup.find("title")
            photo = img_url['content'] if img_url else ""
            name = name_tag.text.strip().split("(")[0] if name_tag else url.split("/")[-1]
        except:
            photo, name = "", url.split("/")[-1]

        Clock.schedule_once(lambda dt: self.add_card(url, name, photo))

    def add_card(self, url, name, img_url):
        card = MDCard(orientation='horizontal', size_hint_y=None, height="140dp", padding="10dp", spacing=10)
        
        img = AsyncImage(source=img_url, size_hint=(None, None), size=("100dp", "100dp"))
        card.add_widget(img)

        box = BoxLayout(orientation='vertical', spacing=5)
        box.add_widget(MDLabel(text=f"[b]{name}[/b]", markup=True, font_style="H6"))
        username = url.strip('/').split("/")[-1]
        box.add_widget(MDLabel(text=f"@{username}", theme_text_color="Secondary"))
        card.add_widget(box)

        btn = MDRaisedButton(text="Open", on_release=lambda x: self.open_profile(url), size_hint=(None, None))
        card.add_widget(btn)

        self.ids.results_grid.add_widget(card)

    def open_profile(self, url):
        intent = Intent(Intent.ACTION_VIEW)
        intent.setData(Uri.parse(url))
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.startActivity(intent)

class InstaApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.theme_style = "Dark"
        Window.size = (400, 700)
        return Builder.load_string(KV)

if __name__ == "__main__":
    InstaApp().run()
