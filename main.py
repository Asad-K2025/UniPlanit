from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
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
        self.subjects_marks_dictionary = {}  # Dictionary used to store subject, mark and credit values
        self.semester_labels_dictionary = {}  # Store labels to access them and change their values
        self.semester_marks_sections_dictionary = {}  # Stores sections were semester marks are displayed

    def build(self):  # Function defines main properties of app
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"  # Main themes of app
        self.root = WidgetsUI()  # Passing widgets class as UI of this app (this allows easier referencing of widgets)
        self.init_dropdown_menu()
        Window.bind(on_resize=self.on_window_resize)  # Call function every time window resizes
        self.on_window_resize(Window, Window.width, Window.height)  # Call once to initially set according to screen size
        return self.root

    def on_window_resize(self, window, width, height):  # Adapt marks output box according to screen size
        if width < 600:
            cols = 1
        elif width < 900:
            cols = 2
        else:
            cols = 3
        self.root.ids.degree_marks_output_box.cols = cols  # Setting columns of gpa output box to adapt to screen sizes
        for semester in self.semester_marks_sections_dictionary.values():
            semester.cols = cols

    def init_dropdown_menu(self):  # Function creates the menu for the dropdown for selecting semesters with its options
        options = [str(i) for i in range(1, 8 + 1)]  # Add option 1 to 8 in dropdown menu
        items = [{"text": opt, "viewclass": "OneLineListItem", "on_release": lambda x=opt: self.display_main_section(x)} for opt in options]
        self.menu = MDDropdownMenu(caller=self.root.ids.semester_dropdown, items=items, width_mult=4)  # Add menu to dropdown

    def display_main_section(self, semesters_in_degree):  # Function displays current_section with subject, mark and credit based on dropdown
        self.root.ids.semester_dropdown.set_item(semesters_in_degree)  # Set value of dropdown to selected value from menu
        self.menu.dismiss()  # Close the menu after number was selected
        self.root.ids.scroll_container.clear_widgets()  # Empty out scroll container in case of previous selection
        self.subjects_marks_dictionary.clear()  # Clear dictionary as widgets have been reset after semester selection

        for semester in range(1, int(semesters_in_degree) + 1):
            section_for_semester = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
            section_for_semester.bind(minimum_height=section_for_semester.setter("height"))  # Set height of this layout to its contents height

            semester_label = f"Semester {semester}"  # Labels for semester 1 to Last semester
            section_for_semester.add_widget(MDLabel(text=semester_label, font_style="H6", theme_text_color="Primary"))
            section_for_semester.add_widget(MDLabel(height=dp(1)))  # Add gap between semester title and widgets

            rows = []
            for _ in range(4):  # Creates 4 subjects for each semester in a box layout representing each semester
                row = self.create_subject_row(section_for_semester, semester_label)
                section_for_semester.add_widget(row)
                rows.append(row)

            self.subjects_marks_dictionary[semester_label] = rows  # Initialise dictionary with semester labels to use

            section_for_semester.add_widget(MDLabel(height=dp(1)))  # Add gap between widgets and semester marks section
            semester_marks_section = MDGridLayout(
                cols=3,  # Used to adjust for mobile
                size_hint_x=1,
                size_hint_y=None,
                adaptive_height=True,
                spacing=dp(10),
                padding=dp(10)
            )  # Section showcasing semester marks
            self.semester_marks_sections_dictionary[semester_label] = semester_marks_section  # Add section to dict to track

            section_for_semester.add_widget(MDLabel(text="[b]Semester marks summary:[/b]",
                                                    theme_text_color="Primary",
                                                    markup="True"))
            # Create semester summary labels
            wam_sem_label = MDLabel(text="[b]WAM: -- --[/b]", markup=True,
                                    height=dp(10), size_hint_y=None, text_size=(None, None), halign="center")
            gpa4_sem_label = MDLabel(text="[b]GPA (4-point scale): --[/b]", markup=True,
                                     height=dp(10), size_hint_y=None, text_size=(None, None), halign="center")
            gpa7_sem_label = MDLabel(text="[b]GPA (7-point scale): --[/b]", markup=True,
                                     height=dp(10), size_hint_y=None, text_size=(None, None), halign="center")

            # Add them to the layout
            semester_marks_section.add_widget(wam_sem_label)
            semester_marks_section.add_widget(gpa4_sem_label)
            semester_marks_section.add_widget(gpa7_sem_label)

            # Store them for future access
            self.semester_labels_dictionary[semester_label] = {
                "wam": wam_sem_label,
                "gpa4": gpa4_sem_label,
                "gpa7": gpa7_sem_label
            }
            section_for_semester.add_widget(semester_marks_section)  # Add section to scroll widget for each semester

            add_btn = MDRectangleFlatButton(  # Button to add subject to each semester
                text="Add Subject",
                size_hint=(None, None),
                size=("140dp", "36dp"),
                pos_hint={"center_x": 0.5},
                on_release=lambda _, sl=semester_label, sec=section_for_semester: self.add_subject_row(sl, sec)
            )
            section_for_semester.add_widget(add_btn)

            self.root.ids.scroll_container.add_widget(section_for_semester)  # Add current_section for each semester to interface

    def create_subject_row(self, parent, semester_label):
        # Function creates subject rows when value for semesters selected in dropdown
        row = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))  # Use boxlayout for each row for formatting
        black = (0, 0, 0, 1)
        row.add_widget(MDTextField(hint_text="Subject", mode="rectangle",
                                   text_color_normal=black, text_color_focus=black))
        row.add_widget(MDTextField(hint_text="Mark (%)", input_filter="float", mode="rectangle",
                                   text_color_normal=black, text_color_focus=black))
        row.add_widget(MDTextField(hint_text="Credit", input_filter="int", mode="rectangle", text="6",
                                   text_color_normal=black, text_color_focus=black))  # 3 textboxes for input
        bin_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0, 0, 1))
        bin_btn.bind(on_release=lambda _, r=row: self.remove_subject_row(semester_label, r, parent))  # Provide button functionality
        row.add_widget(bin_btn)
        return row

    def add_subject_row(self, semester_label, current_section):  # Functional called by add subject button
        row = self.create_subject_row(current_section, semester_label)  # Create a new row using predefined function
        current_section.add_widget(row, index=len(current_section.children) - 1)  # Insert row before Add button (the last index item)
        self.subjects_marks_dictionary[semester_label].append(row)  # Add row to dictionary as well
        Clock.schedule_once(lambda dt: current_section.do_layout())  # Reformat the current section with new widget
        # Clock used to ensure this executes after the widget has been added

    def remove_subject_row(self, semester_label, row, section):
        if row in self.subjects_marks_dictionary[semester_label]:
            self.subjects_marks_dictionary[semester_label].remove(row)
            section.remove_widget(row)
            Clock.schedule_once(lambda dt: section.do_layout())

    def display_marks_to_interface(self):  # Function adds calculated WAMs and GPAs for degree and semesters to interface

        def calculate_marks(total_credits, total_weight):  # Nested function calculates wam, gpa, grade and returns them
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

            return wam, grade, gpa_4, gpa_7

        # Initialise variables to pass to nested function calculate_marks() for calculation
        degree_total_weight = 0
        degree_total_credits = 0
        for semester_name, semester_subjects in self.subjects_marks_dictionary.items():  # Loop over each semester
            sem_weight = 0
            sem_credits = 0
            for subject in semester_subjects:  # Loop over each subject for the semester
                try:
                    mark = float(subject.children[2].text)
                    credit = float(subject.children[1].text)

                    degree_total_weight += mark * credit
                    degree_total_credits += credit

                    sem_weight += mark * credit
                    sem_credits += credit
                except:  # try except used in case of invalid empty values for a subject (subject is ignored)
                    continue
            # Section for calculating and adding semester marks to UI
            sem_wam, sem_grade, sem_gpa4, sem_gpa7 = calculate_marks(sem_credits, sem_weight)
            self.semester_labels_dictionary[semester_name]["wam"].text = f"WAM: {sem_wam} {sem_grade}"
            self.semester_labels_dictionary[semester_name]["gpa4"].text = f"GPA (4-point scale): {sem_gpa4}"
            self.semester_labels_dictionary[semester_name]["gpa7"].text = f"GPA (7-point scale): {sem_gpa7}"

        degree_wam, degree_grade, degree_gpa4, degree_gpa7 = calculate_marks(degree_total_credits, degree_total_weight)

        # Add degree GPA and WAM to the interface
        self.root.ids.wam_label.text = f"WAM: {degree_wam} {degree_grade}"
        self.root.ids.gpa4_label.text = f"GPA (4-point scale): {degree_gpa4}"
        self.root.ids.gpa7_label.text = f"GPA (7-point scale): {degree_gpa7}"


MarksApp().run()  # Main execution of class
