from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.clock import Clock
from kivy.core.window import Window

# Managing dates
import calendar
from datetime import date, timedelta, datetime

# File management
import os
import json

# Managing ics link
import requests
from ics import Calendar

from collections import defaultdict

calendar_data = {}
settings_dict = {}


class TaskDialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.size_hint_y = None
        self.height = "400dp"

        self.text_input = MDTextField(
            hint_text="Task Name",
            mode="rectangle",
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.text_input)

        self.date = datetime.now().date()

        self.date_label = MDLabel(
            text=self.date.strftime("%A, %d %B %Y"),
            halign="center",
            theme_text_color="Primary"
        )
        self.add_widget(self.date_label)

        self.date_button = MDRaisedButton(
            text="Change Date",
            on_release=self.open_date_picker
        )
        self.add_widget(self.date_button)

        self.radio_group = MDBoxLayout(orientation='horizontal', spacing=20, padding=10)

        self.untimed_radio = MDCheckbox(group="task_time", active=True)
        self.untimed_radio.bind(active=self.toggle_time_fields)
        self.radio_group.add_widget(self.untimed_radio)
        self.radio_group.add_widget(MDLabel(text="Untimed / All-Day", theme_text_color="Primary"))

        self.timed_radio = MDCheckbox(group="task_time")
        self.timed_radio.bind(active=self.toggle_time_fields)
        self.radio_group.add_widget(self.timed_radio)
        self.radio_group.add_widget(MDLabel(text="Timed", theme_text_color="Primary"))

        self.add_widget(self.radio_group)

        self.start_time_btn = MDRaisedButton(
            text="Select Start Time",
            on_release=self.open_start_time_picker,
            opacity=0,
            disabled=True
        )
        self.end_time_btn = MDRaisedButton(
            text="Select End Time",
            on_release=self.open_end_time_picker,
            opacity=0,
            disabled=True
        )
        self.add_widget(self.start_time_btn)
        self.add_widget(self.end_time_btn)

    def toggle_time_fields(self, instance, value):
        is_timed = self.timed_radio.active
        self.start_time_btn.disabled = not is_timed
        self.end_time_btn.disabled = not is_timed
        self.start_time_btn.opacity = 1 if is_timed else 0
        self.end_time_btn.opacity = 1 if is_timed else 0

    def open_date_picker(self, *_):
        date_picker = MDDatePicker(on_save=self.on_date_selected)
        date_picker.open()

    def on_date_selected(self, instance, value, date_range):
        self.date = value
        self.date_label.text = value.strftime("%A, %d %B %Y")

    def open_start_time_picker(self, *args):
        picker = MDTimePicker()
        picker.bind(time=self.set_start_time)
        picker.open()

    def open_end_time_picker(self, *args):
        picker = MDTimePicker()
        picker.bind(time=self.set_end_time)
        picker.open()

    def set_start_time(self, instance, time_obj):
        self.start_time_btn.text = f"Start: {time_obj.strftime('%H:%M')}"

    def set_end_time(self, instance, time_obj):
        self.end_time_btn.text = f"End: {time_obj.strftime('%H:%M')}"


class AllWeekViewScreen(MDScreen):  # Week calendar view class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_all_week()

    def build_all_week(self):
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)

        top_row = MDBoxLayout(spacing=10, padding=5, size_hint_y=None, height=60)

        # Text input for iCal link
        self.link_input = MDTextField(
            hint_text="Timetable Link",
            mode="rectangle",
            size_hint_x=0.1,
            size_hint_y=None,
            font_size=12
        )
        top_row.add_widget(self.link_input)

        save_btn = MDRaisedButton(
            text="Save",
            size_hint=(None, None),
            on_release=self.save_settings
        )
        top_row.add_widget(save_btn)

        gen_btn = MDRaisedButton(
            text="Generate Timetable",
            size_hint=(None, None),
        )
        top_row.add_widget(gen_btn)

        self.uni_checkbox = MDCheckbox(active=True)
        uni_box = MDBoxLayout(orientation="horizontal", spacing=6, size_hint_x=None, width=140)
        uni_box.add_widget(self.uni_checkbox)
        uni_box.add_widget(MDLabel(text="Timetable", halign="left", font_style="Caption"))
        top_row.add_widget(uni_box)

        self.other_checkbox = MDCheckbox(active=True)
        other_box = MDBoxLayout(orientation="horizontal", spacing=6, size_hint_x=None, width=100)
        other_box.add_widget(self.other_checkbox)
        other_box.add_widget(MDLabel(text="Other", halign="left", font_style="Caption"))
        top_row.add_widget(other_box)

        add_btn = MDIconButton(
            icon="plus",
            pos_hint={"center_y": 0.5},
            on_release=lambda *args: self.show_add_task_dialog(),
            theme_text_color="Custom",
            text_color=MDApp.get_running_app().theme_cls.primary_color
        )
        top_row.add_widget(add_btn)

        layout.add_widget(top_row)

        # Weekday header
        header = GridLayout(cols=8, size_hint_y=None, height=36)
        header.add_widget(MDLabel(text="Time", halign="center"))
        for day in self.week_dates:
            header.add_widget(MDLabel(text=day.strftime("%a\n%d %b"), markup=True, halign="center"))
        layout.add_widget(header)

        # Untimed task row
        untimed_row = GridLayout(cols=8, size_hint_y=None, height=60, spacing=4)
        untimed_row.add_widget(MDLabel(text="Untimed/All-Day", halign="center", theme_text_color="Secondary"))

        for d in self.week_dates:
            month_key, day = d.strftime("%m-%Y"), d.strftime("%d")
            tasks = calendar_data.get(month_key, {}).get(day, [])

            untimed_cell = MDBoxLayout(
                orientation="vertical",
                spacing=2,
                padding=4,
                md_bg_color=(0.92, 0.92, 0.92, 1)
            )

            for task in tasks:
                if not ("start_time" in task and "end_time" in task):
                    untimed_cell.add_widget(Label(text=f"• {task['text']}", font_size=10))
                    untimed_cell.md_bg_color = MDApp.get_running_app().theme_cls.primary_light

            untimed_row.add_widget(untimed_cell)

        layout.add_widget(untimed_row)

        # Time grid
        grid = GridLayout(cols=8, spacing=4, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        # Build 30 min intervals
        interval_times = []
        time = datetime.strptime("06:00", "%H:%M")
        while time <= datetime.strptime("21:30", "%H:%M"):
            interval_times.append(time.strftime("%H:%M"))
            time += timedelta(minutes=30)

        # Render time slots
        for interval in interval_times:
            show_label = interval.endswith(":00")  # Show only on full hour
            grid.add_widget(MDLabel(text=interval if show_label else "", halign="center", theme_text_color="Secondary"))

            for d in self.week_dates:
                month_key, day = d.strftime("%m-%Y"), d.strftime("%d")
                tasks = calendar_data.get(month_key, {}).get(day, [])

                # Filter tasks active at this interval
                active_tasks = []
                current_time = datetime.strptime(interval, "%H:%M")

                for task in tasks:
                    if "start_time" in task and "end_time" in task:
                        start = datetime.strptime(task["start_time"], "%H:%M")
                        end = datetime.strptime(task["end_time"], "%H:%M")
                        if start <= current_time < end:
                            active_tasks.append(task)

                # Create cell and split vertically if needed
                cell = MDBoxLayout(
                    orientation="horizontal",
                    spacing=1,
                    padding=2,
                    height=30,
                    size_hint_y=None,
                    md_bg_color=(0.95, 0.95, 0.95, 1)
                )

                if active_tasks:
                    for task in active_tasks:
                        task_box = MDBoxLayout(
                            orientation="vertical",
                            size_hint_x=(1 / len(active_tasks)),
                            md_bg_color=MDApp.get_running_app().theme_cls.primary_light,
                            padding=2
                        )
                        task_box.add_widget(Label(
                            text=f"{task['text']}\n{task['start_time']}-{task['end_time']}",
                            font_size=9
                        ))
                        cell.add_widget(task_box)

                grid.add_widget(cell)

        scroll = ScrollView()
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def show_add_task_dialog(self):
        self.task_content = TaskDialogContent()

        self.dialog = MDDialog(
            title="Add Task",
            text="",
            type="custom",
            content_cls=self.task_content,
            buttons=[
                MDRaisedButton(
                    text="Save",
                    on_release=self.save_task
                ),
                MDFlatButton(
                    text="Cancel",
                    on_release=self.dismiss_dialog
                )
            ]
        )
        self.dialog.open()

    def dismiss_dialog(self, *args):
        self.dialog.dismiss()

    def save_settings(self, _):
        global settings_dict
        link = self.link_input.text.strip()
        settings_dict['ics_url'] = link
        save_path = os.path.join(MDApp.get_running_app().user_data_dir, "settings.json")  # Compatible file path for all platforms
        try:
            with open(save_path, "w") as file:
                json.dump(settings_dict, file)
        except Exception as e:
            print(f"Failed to save link: {e}")  # Used in event of any errors, then they will be printed

    def save_task(self, *args):
        global calendar_data

        task_name = self.task_content.text_input.text.strip()
        if not task_name:
            print("Task name is required.")
            return

        date_str_day = self.task_content.date.strftime("%d")  # e.g. "31"
        date_str_month = self.task_content.date.strftime("%m-%Y")  # e.g. "07-2025"

        # Initialise nested dicts if necessary
        if date_str_month not in calendar_data:
            calendar_data[date_str_month] = {}
        if date_str_day not in calendar_data[date_str_month]:
            calendar_data[date_str_month][date_str_day] = []

        # Build task dictionary
        task = {
            "text": task_name,
            "type": "other"
        }

        if self.task_content.timed_radio.active:
            try:
                task["start_time"] = self.task_content.start_time_btn.text.split("Start: ")[1]
                task["end_time"] = self.task_content.end_time_btn.text.split("End: ")[1]
            except IndexError:
                print("Missing time selection")
                return

        # Add task to calendar
        calendar_data[date_str_month][date_str_day].append(task)
        self.dialog.dismiss()
        MDApp.get_running_app().save_data()

    def get_all_week_tasks(self):
        all_tasks_by_weekday = defaultdict(list)

        for month_key in calendar_data:
            for day_key in calendar_data[month_key]:
                try:
                    day_date = datetime.strptime(f"{day_key}-{month_key}", "%d-%m-%Y")
                    weekday = calendar.day_name[day_date.weekday()]  # e.g., "Monday"

                    for task in calendar_data[month_key][day_key]:
                        all_tasks_by_weekday[weekday].append(task)
                except ValueError:
                    continue  # Skip invalid dates

        return all_tasks_by_weekday


class AllWeekTimetableApp(MDApp):  # Class defines the main app
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.title = "All Week Timetable"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        Window.clearcolor = (0.98, 0.98, 0.98, 1)
        self.load_data()

        screen_manager = ScreenManager()
        self.week_screen = AllWeekViewScreen(name="week")
        screen_manager.add_widget(self.week_screen)

        return screen_manager

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
                self.save_data()
                return  # If first time launch, json does not exist, so end execution

            with open(save_path, "r") as file:
                calendar_data = json.load(file)  # Retrieve data from json

            self.import_ics_to_calendar_data()  # Load in uni timetable data

        except Exception as e:  # In case of an error
            print(f"Error loading saved data: {e}")

    def import_ics_to_calendar_data(self):
        global settings_dict
        global calendar_data
        settings_path = os.path.join(self.user_data_dir, "settings.json")  # Load link
        if not os.path.exists(settings_path):
            print("No link saved.")
            return False

        try:
            with open(settings_path) as file:
                settings_dict = json.load(file)

            # Fetch and parse
            calendar_request = Calendar(requests.get(settings_dict['ics_url']).text)

            if len(calendar_request.events) > 0:  # Remove all previously loaded uni tasks if link works
                for month_key in list(calendar_data.keys()):
                    for day_key in list(calendar_data[month_key].keys()):
                        calendar_data[month_key][day_key] = [
                            task for task in calendar_data[month_key][day_key]
                            if task.get("type") != "uni"
                        ]

            for event in calendar_request.events:
                request_date = event.begin.strftime("%d")
                month_key = event.begin.strftime("%m-%Y")
                start = event.begin.strftime("%H:%M")
                end = event.end.strftime("%H:%M")

                entry = {
                    "text": event.name,
                    "start_time": start,
                    "end_time": end,
                    "type": "uni"
                }

                calendar_data.setdefault(month_key, {}).setdefault(request_date, []).append(entry)
            return True
        except Exception as e:
            print(f"Failed to import: {e}")
            return False


AllWeekTimetableApp().run()