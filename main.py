from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRectangleFlatButton, MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window


class WidgetsUI(MDBoxLayout):  # Class needed to define the user interface as a BoxLayout format (widgets in kv file)
    pass  # Cannot be created purely in kv as python requires backend logic for this app


class MarksApp(MDApp):  # Class used to define backend logic
    def __init__(self):
        super().__init__()
        self.subject_mark_dictionary = {}  # Dictionary used to store subject, mark and credit values

    def build(self):  # Function defines main properties fo app
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"  # Main themes of app
        self.root = WidgetsUI()  # Passing widgets class as UI of this app (this allows easier referencing of widgets)
        self.init_dropdown_menu()
        Window.bind(on_resize=self.on_window_resize)  # Call function every time window resizes
        self.on_window_resize(Window, Window.width, Window.height)  # Call once to initially set according to screen size
        return self.root

    def on_window_resize(self, window, width, height):  # Adapt gpa output box according to screen size
        if width < 400:
            cols = 1
        elif width < 700:
            cols = 2
        else:
            cols = 3
        self.root.ids.gpa_output_box.cols = cols  # Setting columns of gpa output box to adapt to screen sizes

    def init_dropdown_menu(self):  # Function creates the menu for the dropdown for selecting years with its options
        options = [str(i) for i in range(1, 8 + 1)]  # Add option 1 to 8 in dropdown menu
        items = [{"text": opt, "viewclass": "OneLineListItem", "on_release": lambda x=opt: self.display_main_section(x)} for opt in options]
        self.menu = MDDropdownMenu(caller=self.root.ids.year_dropdown, items=items, width_mult=4)  # Add menu to dropdown

    def display_main_section(self, years_in_degree):  # Function displays current_section with subject, mark and credit based on dropdown
        self.root.ids.year_dropdown.set_item(years_in_degree)  # Set value of dropdown to selected value from menu
        self.menu.dismiss()  # Close the menu after number was selected
        self.root.ids.scroll_container.clear_widgets()  # Empty out scroll container in case of previous selection
        self.subject_mark_dictionary.clear()  # Clear dictionary as widgets have been reset after year selection

        for year in range(1, int(years_in_degree) + 1):
            section_for_year = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
            section_for_year.bind(minimum_height=section_for_year.setter("height"))  # Set height of this layout to its contents height

            year_label = f"Year {year}"  # Labels for Year 1 to Last Year
            section_for_year.add_widget(MDLabel(text=year_label, font_style="H6", theme_text_color="Primary"))

            section_for_year.add_widget(MDLabel(height=dp(1)))  # Add gap between year title and widgets

            rows = []
            for _ in range(4):  # Creates 4 subjects for each year in a box layout representing each year
                row = self.create_subject_row(section_for_year, year_label)
                section_for_year.add_widget(row)
                rows.append(row)

            self.subject_mark_dictionary[year_label] = rows  # Initialise dictionary with year labels to use

            add_btn = MDRectangleFlatButton(  # Button to add subject to each year
                text="Add Subject",
                size_hint=(None, None),
                size=("140dp", "36dp"),
                pos_hint={"center_x": 0.5},
                on_release=lambda _, yl=year_label, sec=section_for_year: self.add_subject_row(yl, sec)
            )
            section_for_year.add_widget(add_btn)

            self.root.ids.scroll_container.add_widget(section_for_year)  # Add current_section for each year to interface

    def create_subject_row(self, parent, year_label):
        # Function creates subject rows when value for years selected in dropdown
        row = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))  # Use boxlayout for each row for formatting
        black = (0, 0, 0, 1)
        row.add_widget(MDTextField(hint_text="Subject", mode="rectangle",
                                   text_color_normal=black, text_color_focus=black))
        row.add_widget(MDTextField(hint_text="Mark (%)", input_filter="float", mode="rectangle",
                                   text_color_normal=black, text_color_focus=black))
        row.add_widget(MDTextField(hint_text="Credit", input_filter="int", mode="rectangle", text="6",
                                   text_color_normal=black, text_color_focus=black))  # 3 textboxes for input
        bin_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0, 0, 1))
        bin_btn.bind(on_release=lambda _, r=row: self.remove_subject_row(year_label, r, parent))  # Provide button functionality
        row.add_widget(bin_btn)
        return row

    def add_subject_row(self, year_label, current_section):  # Functional called by add subject button
        row = self.create_subject_row(current_section, year_label)  # Create a new row using predefined function
        current_section.add_widget(row, index=len(current_section.children) - 1)  # Insert row before Add button (the last index item)
        self.subject_mark_dictionary[year_label].append(row)  # Add row to dictionary as well
        Clock.schedule_once(lambda dt: current_section.do_layout())  # Reformat the current section with new widget
        # Clock used to ensure this executes after the widget has been added

    def remove_subject_row(self, year_label, row, section):
        if row in self.subject_mark_dictionary[year_label]:
            self.subject_mark_dictionary[year_label].remove(row)
            section.remove_widget(row)
            Clock.schedule_once(lambda dt: section.do_layout())

    def calculate_gpa(self):  # Function calculate WAM and GPAs and adds to interface
        total_weight = 0
        total_credits = 0
        for subject_sections in self.subject_mark_dictionary.values():
            for subject in subject_sections:
                try:
                    mark = float(subject.children[2].text)
                    credit = float(subject.children[1].text)
                    total_weight += mark * credit
                    total_credits += credit
                except:  # try except used in case of invalid empty values (they are ignored)
                    continue
        wam = round(total_weight / total_credits, 2) if total_credits else 0
        if wam >= 85:
            grade = 'HD'
            gpa_7 = 7.0
            gpa_4 = 4.0
        elif 85 > wam >= 75:
            grade = 'D'
            gpa_7 = 6.0
            gpa_4 = 3.5
        elif 75 > wam >= 65:
            grade = 'C'
            gpa_7 = 5.0
            gpa_4 = 3.0
        elif 65 > wam >= 50:
            grade = 'P'
            gpa_7 = 4.0
            gpa_4 = 2.0
        else:
            grade = 'F'
            gpa_7 = 0.0
            gpa_4 = 0.0

        # Add GPA and WAM to the interface
        self.root.ids.wam_label.text = f"Predicted WAM: {wam} {grade}"
        self.root.ids.gpa4_label.text = f"GPA (4-point scale): {gpa_4}"
        self.root.ids.gpa7_label.text = f"GPA (7-point scale): {gpa_7}"


MarksApp().run()  # Main execution of class
