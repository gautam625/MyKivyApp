from kivy.app import App
from kivy.uix.button import Button

class MyApp(App):
    def build(self):
        return Button(text='Click Me!', on_press=self.say_hello)

    def say_hello(self, instance):
        print("Hello from Kivy!")

if __name__ == '__main__':
    MyApp().run()
