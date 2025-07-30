from kivy.metrics import dp
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

calendar_data = {}  # Loads in data from json file
settings_dict = {}  # Saves timetable url link and filter preferences


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
        

class DayCell(MDBoxLayout):  # Represents a single day box which is clickable
    def __init__(self, day, month_key, **kwargs):
        super().__init__(orientation="vertical", padding=5, spacing=3, size_hint_y=None, height=100, **kwargs)
        self.day = str(day)
        self.month_key = month_key

        # Retrieve task list for this date
        tasks_dictionaries = calendar_data.get(month_key, {}).get(self.day.zfill(2), [])  # zfill for retrieving 07 format
        tasks = []
        for task in tasks_dictionaries:
            tasks.append(task['text'])
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

    def on_touch_down(self, touch, *args):  # Function opens week view when a day cell is pressed
        if self.collide_point(*touch.pos):
            MDApp.get_running_app().root.get_screen("month").show_week_view(self.month_key, self.day)
            return True
        return super().on_touch_down(touch)


class WeekViewScreen(MDScreen):  # Week calendar view class
    def __init__(self, week_dates, **kwargs):
        super().__init__(**kwargs)
        self.week_dates = week_dates
        self.build_week()

    def build_week(self):
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)

        top_row = MDBoxLayout(spacing=10, padding=5, size_hint_y=None, height=60)

        back_btn = MDRaisedButton(
            text="Back",
            size_hint=(None, None),
            size=(140, 40),
            on_release=self.back_to_month_view,
            md_bg_color=(0.8, 0, 0.1, 1)  # Red
        )

        # Text input for iCal link
        self.link_input = MDTextField(
            hint_text="Timetable Link",
            mode="rectangle",
            size_hint_x=0.1,
            size_hint_y=None,
            font_size=12
        )
        top_row.add_widget(back_btn)
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

    def back_to_month_view(self, *_):  # Function for returning to month view
        app = MDApp.get_running_app()
        month_screen = app.root.get_screen("month")
        month_screen.show_month(month_screen.current_month_key)
        app.root.current = "month"

    def show_add_task_dialog(self):
        content = TaskDialogContent()

        self.dialog = MDDialog(
            title="Add Task",
            text="",
            type="custom",
            content_cls=content,
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

    def save_task(self, *args):
        task_name = self.task_content.text_input.text
        task_date = self.task_content.date
        print(f"Task saved: {task_name} on {task_date}")
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


class MonthCalendarGrid(GridLayout):  # Defined a month grid container with 7 day structure, padding and all the dates
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


class CalendarScreenDisplay(
    MDScreen):  # Main interface combining all classes such as calendar grid, side widgets, year dropdown
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
            {"text": year, "on_release": lambda selected_year=year: self.select_year(selected_year)} for year in
            year_options
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

        grid = MonthCalendarGrid(month_key=month_key)  # Used for creating an instance of month
        scroll.add_widget(grid)

        self.active_grid_container.add_widget(header)
        self.active_grid_container.add_widget(scroll)

        # Update month buttons on left sidebar for the year
        if self.selected_year != year:
            self.selected_year = year
            self.year_selector.text = f"Year: {year}"
            self.refresh_month_buttons(year)

    def show_week_view(self, month_key, day):
        target_date = date(int(month_key.split("-")[1]), int(month_key.split("-")[0]), int(day))
        week_start = target_date - timedelta(days=target_date.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]

        screen_manager = MDApp.get_running_app().root  # ScreenManager instance

        if screen_manager.has_screen("week"):
            screen_manager.remove_widget(screen_manager.get_screen("week"))

        week_screen = WeekViewScreen(week_dates=week_dates, name="week")
        screen_manager.add_widget(week_screen)
        screen_manager.current = "week"

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.month_screen = None

    def build(self):
        self.title = "Ultimate Task Calendar"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        Window.clearcolor = (0.98, 0.98, 0.98, 1)
        self.load_data()

        screen_manager = ScreenManager()
        self.month_screen = CalendarScreenDisplay(name="month")
        screen_manager.add_widget(self.month_screen)

        # WeekViewScreen added dynamically when needed
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


CalendarApp().run()
