from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty


class WidgetsUI(MDBoxLayout):  # Class needed to define the user interface, cannot be created in kv as app requires backend python
    degree_marks_text_font_size = StringProperty("18sp")


class MarksApp(MDApp):  # Class used to define backend logic
    def __init__(self):
        super().__init__()
        self.is_small_view = False  # Used to adjust mobile view
        self.subjects_marks_dictionary = {}  # Dictionary used to store subject, mark and credit values for calculating gpa and wam
        self.semester_labels_dictionary = {}  # Store labels to access them and change their values
        self.semester_marks_sections_dictionary = {}  # Stores sections where semester marks are displayed
        self.subject_input_rows_array = []  # Each row will be a dict with fields such as (subject_field, mark_field, parent, container, etc.) used for formatting interface between mobile and desktop
        self.focusable_fields_grid = []  # Stores textboxes in order to be movable with keyboard button presses
        self.rows_count_dictionary = {}  # Used to store how many widgets there are for each semester
        self.menu = None  # Used to initially define the menu widget for dropdown

    def build(self):  # Function defines main properties of app
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"  # Main themes of app
        self.root = WidgetsUI()  # Passing widgets class as UI of this app (this allows easier referencing of widgets)
        self.init_dropdown_menu()
        Window.bind(on_resize=self.on_window_resize)  # Call function every time window resizes
        Window.bind(on_key_down=self._on_key_down)  # Define behaviour when certain keys are pressed
        self.on_window_resize(Window, Window.width, Window.height)  # Call once to initially set according to screen size
        return self.root

    def on_window_resize(self, _1, width, _2):  # Adapt marks output box according to screen size (_1 and _2 not used)
        self.is_small_view = (width < 700)  # If small view, track flag as true to make UI changes to input boxes

        if width < 600:
            cols = 1
            font_size = "16sp"
        elif width < 900:
            cols = 2
            font_size = "18sp"
        else:
            cols = 3
            font_size = "20sp"

        self.root.ids.degree_marks_output_box.cols = cols  # Setting columns of marks output box to adapt to screen sizes

        for semester in self.semester_marks_sections_dictionary.values():  # Setting cols of semester mark output boxes
            semester.cols = cols

        self.root.degree_marks_text_font_size = font_size  # Change font size at bottom of screen based on screen size

        self.refresh_subject_row_layouts()  # Refresh subject rows layout

    def _on_key_down(self, _window, key, _scancode, _codepoint, modifiers):  # Define behaviour for using tab and arrow keys to move across textboxes
        # Find focused field
        field_found = False  # Flag to check if focused field ahs been found
        row, col = 0, 0  # Incase these values are not assigned during loop for any reason
        for row_index, fields_row in enumerate(self.focusable_fields_grid):  # Loop over every row
            for col_index, field in enumerate(fields_row):  # Loop over every field in the row
                if field.focus:  # If field has cursor then store its position
                    field_found = True
                    row = row_index
                    col = col_index
                    break
            if field_found:  # If field found, do not loop over other rows
                break

        if not field_found:
            return False  # No focused field found, hence perform no actions
        else:
            current_field = self.focusable_fields_grid[row][col]
            flat_list = [item for row in self.focusable_fields_grid for item in row]  # Merged version of list of lists
            flat_index = flat_list.index(current_field)
            cursor_position = current_field.cursor_index()  # Used so arrow keys can still traverse a word in textbox
            text_len = len(current_field.text)

        if key == 9 and "shift" not in modifiers:  # Tab
            next_field = flat_list[(flat_index + 1) % len(flat_list)]  # Head to index 0 if it reaches end of array
            current_field.focus = False
            next_field.focus = True
            return True

        if key == 9 and "shift" in modifiers:  # Shift + Tab
            prev_field = flat_list[(flat_index - 1) % len(flat_list)]  # Head to last index if it reaches start of array
            current_field.focus = False
            prev_field.focus = True
            return True

        if key == 276 and cursor_position == 0:  # Left
            current_field.focus = False
            prev_field = self.focusable_fields_grid[row][col - 1]
            prev_field.focus = True
            text_field_end_index = len(prev_field.text or "")
            Clock.schedule_once(lambda dt: setattr(prev_field, 'cursor', (text_field_end_index, 0)), 0)
            return True

        if key == 275 and cursor_position == text_len:  # Right
            current_field.focus = False
            if col == 2:
                next_field = self.focusable_fields_grid[row][0]
            else:
                next_field = self.focusable_fields_grid[row][col + 1]
            next_field.focus = True
            Clock.schedule_once(lambda dt: setattr(next_field, 'cursor', (0, 0)), 0)
            return True

        if key == 273:  # Up
            current_field.focus = False
            if row > 0:
                self.focusable_fields_grid[row - 1][col].focus = True  # If not first row, go up
            else:
                self.focusable_fields_grid[-1][col].focus = True  # If first row, move to bottom row
            return True

        if key == 274:  # Down
            current_field.focus = False
            if row < len(self.focusable_fields_grid) - 1:
                self.focusable_fields_grid[row + 1][col].focus = True
            else:
                self.focusable_fields_grid[0][col].focus = True
            return True

        return False  # otherwise let default behavior happen such as text editing

    def init_dropdown_menu(self):  # Function creates the menu for the dropdown for selecting semesters with its options
        options = [str(i) for i in range(1, 14 + 1)]  # Add option 1 to 14 in dropdown menu
        items = [{"text": opt, "viewclass": "OneLineListItem", "on_release": lambda x=opt: self.display_main_section(x)} for opt in options]
        self.menu = MDDropdownMenu(caller=self.root.ids.semester_dropdown, items=items)  # Add menu to dropdown

    def display_main_section(self, semesters_in_degree):  # Function displays current_section with subject, mark and credit based on dropdown
        self.root.ids.semester_dropdown.set_item(semesters_in_degree)  # Set value of dropdown to selected value from menu
        self.menu.dismiss()  # Close the menu after number was selected
        self.root.ids.scroll_container.clear_widgets()  # Empty out scroll container in case of previous selection
        self.subjects_marks_dictionary.clear()  # Clear dictionary as widgets have been reset after semester selection
        self.focusable_fields_grid.clear()   # Clear array as entry widget rows have been reset after semester selection

        for semester in range(1, int(semesters_in_degree) + 1):
            section_for_semester = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
            section_for_semester.bind(minimum_height=section_for_semester.setter("height"))  # Set height of this layout to its contents height

            year = int((semester + 1) / 2)  # Calculate Year for the semester
            semester_label = f"Semester {semester} (Year {year})"  # Labels for semester 1 to Last semester
            section_for_semester.add_widget(MDLabel(text=semester_label, font_style="H6", theme_text_color="Primary"))
            section_for_semester.add_widget(MDLabel(height=dp(1)))  # Add gap between semester title and widgets

            rows = []
            for _ in range(4):  # Creates 4 subjects for each semester in a box layout representing each semester
                row = self.create_subject_row(section_for_semester, semester_label)
                section_for_semester.add_widget(row)
                rows.append(row)

            add_btn = MDIconButton(  # Button to add subject to each semester
                icon="plus",
                theme_text_color="Custom",
                text_color=self.theme_cls.primary_color,
                on_release=lambda _, sl=semester_label, sec=section_for_semester: self.add_subject_row(sl, sec)
            )
            section_for_semester.add_widget(add_btn)

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
                                    height=dp(10), size_hint_y=None, text_size=(None, None))
            gpa4_sem_label = MDLabel(text="[b]GPA (4-point scale): --[/b]", markup=True,
                                     height=dp(10), size_hint_y=None, text_size=(None, None))
            gpa7_sem_label = MDLabel(text="[b]GPA (7-point scale): --[/b]", markup=True,
                                     height=dp(10), size_hint_y=None, text_size=(None, None))

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

            self.root.ids.scroll_container.add_widget(section_for_semester)  # Add current_section for each semester to interface

    def create_subject_row(self, parent, semester_label):
        # Function creates subject rows when value for semesters selected in dropdown
        black = (0, 0, 0, 1)

        subject_field = MDTextField(hint_text="Subject",
                                    mode="rectangle",
                                    text_color_normal=black,
                                    text_color_focus=black,
                                    size_hint_x="0.6")  # Take up 60% of the screen size
        mark_field = MDTextField(hint_text="Mark",
                                 input_filter="float",
                                 mode="rectangle",
                                 width=dp(70),
                                 text_color_normal=black,
                                 text_color_focus=black,
                                 size_hint_x=None)
        credit_field = MDTextField(hint_text="Credit",
                                   input_filter="int",
                                   mode="rectangle",
                                   text="6",
                                   size_hint_x=None,
                                   width=dp(70),
                                   text_color_normal=black,
                                   text_color_focus=black)  # 3 textboxes for input

        for field in (subject_field, mark_field, credit_field):  # Append the 3 textboxes to array to track them for allowing tab and arrow keys over textboxes
            field.multiline = False  # Ensure tab doesnt insert a tab character

        if semester_label in self.rows_count_dictionary.keys():  # Track widgets in row_count dictionary
            self.rows_count_dictionary[semester_label] += 1
        else:
            self.rows_count_dictionary[semester_label] = 1

        # Insert the widget in the array at appropriate point based on which semester it belongs to
        widget_index = 0
        for key, value in self.rows_count_dictionary.items():
            widget_index += value  # Store how many widgets are present before the new added widget
            if key == semester_label:
                break  # If the semester which the widget belongs to is reached, stop increasing the widget_index value
        self.focusable_fields_grid.insert(widget_index - 1, [subject_field, mark_field, credit_field])

        bin_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0, 0, 1))

        row_container = self.build_subject_row_layout(subject_field, mark_field, credit_field, bin_btn)  # Pass widgets to store in layout

        bin_btn.bind(on_release=lambda _, r=row_container: self.remove_subject_row(semester_label, r, parent))  # Provide button functionality

        # Track components for re-layout later
        self.subject_input_rows_array.append({
            "container": row_container,
            "parent": parent,
            "semester_label": semester_label,
            "subject": subject_field,
            "mark": mark_field,
            "credit": credit_field,
            "bin": bin_btn
        })

        return row_container

    def build_subject_row_layout(self, subject, mark, credit, bin_btn):
        if self.is_small_view:
            row = MDBoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(100))

            top = MDBoxLayout(size_hint_y=None, height=dp(48))
            top.add_widget(subject)  # Add subject widget separately for smaller screen sizes

            bottom = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
            bottom.add_widget(mark)  # Add other 3 input text fields below the subject input text field
            bottom.add_widget(credit)
            bottom.add_widget(bin_btn)

            row.add_widget(top)
            row.add_widget(bottom)
        else:
            row = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))  # Use boxlayout for each row for formatting
            row.add_widget(subject)  # Add all widgets in one line for desktop
            row.add_widget(mark)
            row.add_widget(credit)
            row.add_widget(bin_btn)

        return row  # Return row with formatting and widgets

    def refresh_subject_row_layouts(self):  # Dynamically adjust screen size based on resizing

        for row_info_dict in self.subject_input_rows_array:  # Lopping over every row's dictionary to retrieve widgets
            parent = row_info_dict["parent"]  # Section for semester
            old_container = row_info_dict["container"]  # Layout for a row

            if old_container in parent.children:  # Check if row_container is in section for semester
                index = parent.children.index(old_container) if old_container in parent.children else 0  # Store index to tracker where to place widgets
                parent.remove_widget(old_container)  # If it exists, remove it as new container will be added

                # Detach children to avoid any parent conflicts
                row_info_dict["subject"].parent.remove_widget(row_info_dict["subject"])
                row_info_dict["mark"].parent.remove_widget(row_info_dict["mark"])
                row_info_dict["credit"].parent.remove_widget(row_info_dict["credit"])
                row_info_dict["bin"].parent.remove_widget(row_info_dict["bin"])

                # Rebuild with new layout mode
                new_container = self.build_subject_row_layout(
                    row_info_dict["subject"], row_info_dict["mark"], row_info_dict["credit"], row_info_dict["bin"]
                )
                row_info_dict["container"] = new_container
                parent.add_widget(new_container, index=index)

    def add_subject_row(self, semester_label, current_section):  # Function called by add subject button
        row = self.create_subject_row(current_section, semester_label)  # Create a new row using predefined function

        current_section.add_widget(row, index=4)  # Insert row before add button, 4 skips mark labels and add button

        self.subjects_marks_dictionary[semester_label].append(row)  # Add row to dictionary as well
        Clock.schedule_once(lambda dt: current_section.do_layout())  # Reformat the current section with new widget
        # Clock used to ensure this executes after the widget has been added

    def remove_subject_row(self, semester_label, row, section):  # Functionality of red bin button

        subject = row.children[3]
        mark = row.children[2]
        credit = row.children[1]
        for fields_row in self.focusable_fields_grid:  # Remove widgets from fields_grid_array to ensure correct navigation with arrow keys
            if subject in fields_row and mark in fields_row and credit in fields_row:
                self.focusable_fields_grid.remove(fields_row)
                break

        if row in self.subjects_marks_dictionary[semester_label]:  # Remove from dictionary for calculating GPA
            self.subjects_marks_dictionary[semester_label].remove(row)
            section.remove_widget(row)  # Remove widget form interface
            Clock.schedule_once(lambda dt: section.do_layout())  # Restructure the interface after ensuring widget is removed with a delay

        self.subject_input_rows_array = [  # Remove the rows dictionary from the input row tracking array containing layout information
            row_dictionary for row_dictionary in self.subject_input_rows_array if row_dictionary["container"] != row
        ]

        if semester_label in self.rows_count_dictionary:
            self.rows_count_dictionary[semester_label] -= 1  # Decrement count of widgets in the semester

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
                except ValueError:  # try except used in case of invalid empty values for a subject (subject is ignored)
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
