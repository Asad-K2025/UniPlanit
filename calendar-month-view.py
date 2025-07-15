from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window

import calendar
from datetime import date

import os
import json


calendar_data = {
    "07-2025": {
        "14": ["COMP1230 Lab", "Buy books"],
        "16": ["STAT1042 Exam"]
    },
    "08-2025": {
        "03": ["MATH2020 assignment"],
        "08": ["PHYS1001 prac"],
        "14": ["COMP1230 Lab", "Buy books"]
    }
}


class TaskPopup(Popup):  # Modal popup for creating or reviewing tasks on a specific date
    def __init__(self, day, month_key, **kwargs):
        super().__init__(title=f"Tasks for {day.zfill(2)}-{month_key}", size_hint=(0.8, 0.6), **kwargs)
        self.day = day
        self.month_key = month_key
        self.layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)
        self.task_input = TextInput(hint_text="New task...", multiline=False)

        self.task_list = MDBoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        self.task_list.bind(minimum_height=self.task_list.setter("height"))

        # Populate existing tasks for the selected date
        tasks = calendar_data.get(month_key, {}).get(self.day, [])
        for task in tasks:
            self.task_list.add_widget(Label(text=f"• {task}", font_size=14, size_hint_y=None, height=20))

        scroll = ScrollView()
        scroll.add_widget(self.task_list)  # Ensure tasks are scrollable

        add_btn = MDRaisedButton(text="Add Task", on_release=self.add_task)

        # Append widgets to interface
        self.layout.add_widget(scroll)
        self.layout.add_widget(self.task_input)
        self.layout.add_widget(add_btn)
        self.content = self.layout

    def add_task(self, *_args):  # Function appends new entry to UI and backend
        text = self.task_input.text.strip()
        if text:
            self.task_list.add_widget(Label(text=f"• {text}", font_size=14, size_hint_y=None, height=20))
            calendar_data.setdefault(self.month_key, {}).setdefault(self.day, []).append(text)  # Ensure month_key and day exist in calendar_data, otherwise add them in
            self.task_input.text = ""
            MDApp.get_running_app().root.show_month(self.month_key)  # Call show month function to reload interface when a new task is added
        MDApp.get_running_app().save_data()  # Save the data to a json file for storage


class DayCell(MDBoxLayout):  # Represents a single day box which is clickable
    def __init__(self, day, month_key, **kwargs):
        super().__init__(orientation="vertical", padding=5, spacing=3, size_hint_y=None, height=100, **kwargs)
        self.day = str(day)
        self.month_key = month_key

        # Retrieve task list for this date
        tasks = calendar_data.get(month_key, {}).get(self.day, [])
        has_tasks = bool(tasks)

        # Change colour if a task exists for a specific date
        if has_tasks:
            self.md_bg_color = MDApp.get_running_app().theme_cls.primary_light
        else:
            self.md_bg_color = MDApp.get_running_app().theme_cls.bg_light

        self.add_widget(MDLabel(text=f"[b]{self.day}[/b]", markup=True, halign="left", theme_text_color="Secondary"))

        preview = tasks[:2]  # Only show the first two tasks in preview to avoid cluttering the day box
        for task in preview:
            self.add_widget(Label(text=f"• {task}", font_size=12, size_hint_y=None, height=14))

        if len(tasks) > 2:
            self.add_widget(Label(text="…", font_size=12, size_hint_y=None, height=14))

    def on_touch_down(self, touch, *args):  # Function opens task editor popup if a day box/cell is clicked on
        if self.collide_point(*touch.pos):
            TaskPopup(day=self.day, month_key=self.month_key).open()  # Create instance of TaskPopup
            return True
        return super().on_touch_down(touch, *args)


class CalendarGrid(GridLayout):  # Defined a month grid container with 7 day structure, padding and all the dates
    def __init__(self, month_key, **kwargs):
        super().__init__(cols=7, spacing=4, padding=6, size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        self.build_month(month_key)

    def build_month(self, month_key):  # Function called whenever a month is selected to build the new month
        year, month = map(int, month_key.split("-"))
        _, days_in_month = calendar.monthrange(month, year)
        start_day = date(month, year, 1).weekday()  # Getting first day of the month of that year. Mon = 0, Tue = 1 ...

        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:  # Header labels for week
            self.add_widget(MDLabel(text=day, halign="center", theme_text_color="Primary", size_hint_y=None, height=28))

        for _ in range(start_day):  # Blank cells to offset the first day to correct weekday column
            self.add_widget(Label(text="", size_hint_y=None, height=60))

        for day in range(1, days_in_month + 1):  # Create instances of DayCells to populate the month
            new_widget = DayCell(day=day, month_key=month_key)
            self.add_widget(new_widget)


class CalendarScreenDisplay(MDScreen):  # Main interface combining all classes such as calendar grid, side widgets, year dropdown
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialising empty variables
        self.year_menu = None
        self.month_buttons_container = None
        self.year_selector = None
        self.selected_year = None
        self.active_grid_container = None
        self.navigation = None
        self.root = None
        self.current_index = 0

        self.year_range = list(range(2025, 2027 + 1))  # Defines years for which this calendar shows dates
        self.month_keys = [f"{month:02d}-{year}" for year in self.year_range for month in range(1, 12 + 1)]
        self.current_month_key = self.month_keys[self.current_index]

        self._start_y = None  # Determine y position before a gesture, used for swiping gesture to change months
        Window.bind(on_key_down=self.on_key_down)
        Clock.schedule_once(self.build_layout)

    def build_layout(self, _dt):  # Adds widgets to interface
        # Dropdown widget
        self.year_selector = MDRaisedButton(
            text="Select Year",
            size_hint_x=1,
            on_release=lambda *args: self.year_menu.open()
        )
        year_options = [str(year) for year in self.year_range]
        menu_items = [
            {"text": year, "on_release": lambda selected_year=year: self.select_year(selected_year)} for year in year_options
        ]
        self.year_menu = MDDropdownMenu(
            caller=self.year_selector,
            items=menu_items,
            width_mult=3
        )

        # Layout partition for sidebar and content area
        self.root = MDBoxLayout(orientation="horizontal", spacing=8, padding=8)
        self.navigation = MDBoxLayout(orientation="vertical", size_hint_x=0.25, spacing=6)
        self.active_grid_container = MDBoxLayout(orientation="vertical")

        # Sidebar for year selector and month buttons
        self.navigation.add_widget(self.year_selector)
        self.month_buttons_container = MDBoxLayout(orientation="vertical", spacing=6)
        self.navigation.add_widget(self.month_buttons_container)

        self.select_year(str(self.year_range[0]))  # Default year is first year in range

        self.root.add_widget(self.navigation)
        self.root.add_widget(self.active_grid_container)
        self.add_widget(self.root)

        self.show_month(self.current_month_key)

    def select_year(self, year):  # Called when a year is picked from dropdown
        self.selected_year = year
        self.year_selector.text = f"Year: {year}"
        self.year_menu.dismiss()
        self.refresh_month_buttons(year)

        # Automatically show January when year is selected
        january_key = f"01-{year}"
        self.current_index = self.month_keys.index(january_key)
        self.show_month(january_key)

    def refresh_month_buttons(self, year):  # Update sidebar buttons for each month when a new year is selected
        self.month_buttons_container.clear_widgets()
        for month in range(1, 12 + 1):
            month_key = f"{month:02d}-{year}"
            button_text = date(int(year), month, 1).strftime("%B")
            label = button_text[:3]  # Buttons show first 3 letters of a month
            btn = MDRaisedButton(
                text=label,
                on_release=lambda _, x=month_key: self.change_month(x, self.month_keys.index(x)),
                size_hint_y=None,
                height=46
            )
            self.month_buttons_container.add_widget(btn)

    def change_month(self, month_key, index):  # Function called for changing month when swiping or pressing arrow keys
        self.current_index = index
        self.current_month_key = month_key
        self.show_month(month_key)

    def show_month(self, month_key):  # For loading in a month
        self.current_month_key = month_key
        self.active_grid_container.clear_widgets()

        month, year = map(int, month_key.split('-'))

        header = MDLabel(
            text=f"[b]{date(year, month, 1).strftime('%B %Y')}[/b]",
            markup=True,
            halign="center",
            size_hint_y=None,
            height=40
        )

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)

        grid = CalendarGrid(month_key=month_key)  # Used for creating an instance of month
        scroll.add_widget(grid)

        self.active_grid_container.add_widget(header)
        self.active_grid_container.add_widget(scroll)

        # Update month buttons on left sidebar for the year
        if self.selected_year != year:
            self.selected_year = year
            self.year_selector.text = f"Year: {year}"
            self.refresh_month_buttons(year)

    def show_next_month(self):
        if self.current_index < len(self.month_keys) - 1:  # Ensure it isn't at December
            self.current_index += 1
            self.show_month(self.month_keys[self.current_index])
        else:
            self.current_index = 0  # Set back to January
            self.show_month(self.month_keys[0])

    def show_previous_month(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_month(self.month_keys[self.current_index])

    def on_touch_down(self, touch):  # Swiping down enables viewing next month
        self._start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):  # Swiping up enables viewing of previous month
        delta_y = touch.y - getattr(self, "_start_y", touch.y)
        if abs(delta_y) > 50:
            if delta_y > 0:
                self.show_next_month()
            else:
                self.show_previous_month()
        return super().on_touch_up(touch)

    def on_key_down(self, _window, key, _scancode, _codepoint, _modifiers):  # Using arrow keys to change months
        if key == 273:  # Up arrow
            self.show_previous_month()
        elif key == 274:  # Down arrow
            self.show_next_month()


class CalendarApp(MDApp):  # Class defines the main app
    def build(self):
        self.title = "Ultimate Task Calendar"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"  # Main themes of app
        Window.clearcolor = (0.98, 0.98, 0.98, 1)
        self.load_data()  # Load saved data from json
        return CalendarScreenDisplay()

    def save_data(self):  # Function saves the entered data to a json file in Users/AppData/Roaming/calendar
        save_path = os.path.join(self.user_data_dir, "saved_state.json")  # Compatible file path for all platforms
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(save_path, "w") as file:
                json.dump(calendar_data, file, indent=2)  # Indent used for readability of json
        except Exception as e:
            print(f"Failed to save data: {e}")  # Used in event of any errors, then they will be printed

    def load_data(self):  # Function runs to load all data saved in json
        global calendar_data  # Using global calendar data
        try:
            save_path = os.path.join(self.user_data_dir, "saved_state.json")
            if not os.path.exists(save_path):
                return  # If first time launch, json does not exist, so end execution

            with open(save_path, "r") as file:
                calendar_data = json.load(file)  # Retrieve data from json

        except Exception as e:  # In case of an error
            print(f"Error loading saved data: {e}")


CalendarApp().run()
