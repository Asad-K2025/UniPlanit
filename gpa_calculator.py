from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivymd.toast import toast
import json
import os


class WidgetsUI(MDBoxLayout):  # Class needed to define the user interface, cannot be created in kv as app requires backend python
    degree_marks_text_font_size = StringProperty("18sp")
    degree_marks_title_font_size = StringProperty("22sp")


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
        self.on_window_resize(Window, Window.width,
                              Window.height)  # Call once to initially set according to screen size
        return self.root

    def on_start(self):
        self.load_data()  # Load in pre-entered values by user. On start used as running this in build is too early and slow

    def on_window_resize(self, _1, width, _2):  # Adapt marks output box according to screen size (_1 and _2 not used)
        self.is_small_view = (width < 700)  # If small view, track flag as true to make UI changes to input boxes
        if width < 600:
            cols = 1
            font_size = 16
        elif width < 900:
            cols = 2
            font_size = 18
        else:
            cols = 3
            font_size = 20

        self.root.ids.degree_marks_output_box.cols = cols  # Setting columns of marks output box to adapt to screen sizes

        for semester in self.semester_marks_sections_dictionary.values():  # Setting cols of semester mark output boxes
            semester.cols = cols

        self.root.degree_marks_text_font_size = f'{font_size}sp'  # Change font size at bottom of screen based on screen size
        self.root.degree_marks_title_font_size = f'{font_size + 4}sp'  # Change font size at bottom of screen based on screen size

        self.refresh_subject_row_layouts()  # Refresh subject rows static_layout

    def _on_key_down(self, _window, key, _scancode, _codepoint,
                     modifiers):  # Define behaviour for using tab and arrow keys to move across textboxes
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

        if key == 13:  # Enter key
            for row in self.subject_input_rows_array:  # Find which semester the focused field belongs to
                if any(field.focus for field in (row["subject"], row["mark"], row["credit"])):
                    semester = row["semester_label"]
                    parent = row["parent"]
                    self.add_subject_row(semester, parent)  # Add a row if the semester is focused on
                    break
            return True

        return False  # otherwise let default behavior happen such as text editing

    def save_data(self):  # Function saves the entered data to a json file in Users/AppData/Roaming/marks
        data = {
            "num_semesters": len(self.subjects_marks_dictionary),
            "semesters": {}
        }

        for row in self.subject_input_rows_array:  # Retrieve all entered data in textboxes
            semester = row["semester_label"]
            if semester not in data["semesters"]:
                data["semesters"][semester] = []

            subject = row["subject"].text.strip()
            mark = row["mark"].text.strip()
            credit = row["credit"].text.strip()

            data["semesters"][semester].append({
                "subject": subject,
                "mark": mark,
                "credit": credit
            })

        save_path = os.path.join(self.user_data_dir, "saved_state.json")  # Compatible file path for all platforms
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            with open(save_path, "w") as file:
                json.dump(data, file, indent=2)  # Indent used for readability of json
        except Exception as e:
            print(f"Failed to save data: {e}")  # Used in event of any errors, then they will be printed

    def load_data(self):  # Function runs to load all data saved in json
        try:
            save_path = os.path.join(self.user_data_dir, "saved_state.json")
            if not os.path.exists(save_path):
                return  # If first time launch, json does not exist, so end execution

            with open(save_path, "r") as file:
                data = json.load(file)  # Retrieve data from json

            semesters = data.get("semesters", {})
            for semester_label, subjects in semesters.items():
                section = self.recreate_semester_section(semester_label,
                                                         subjects)  # Reload all widgets back using helper function
                self.root.ids.scroll_container.add_widget(section)

            self.display_marks_to_interface()  # Have calculated wam and gpa on interface when app loads in

            if self.menu:
                self.root.ids.semester_dropdown.text = f"{len(semesters)}"  # Load in selected value form dropdown when app loads

        except Exception as e:  # In case of an error
            print(f"Error loading saved data: {e}")

    def auto_update(self, *args):  # Run _do_update automatically whenever something is typed
        Clock.unschedule(self._do_update)
        Clock.schedule_once(self._do_update,
                            0.3)  # Add 0.3-second delay before calculating marks, in case of rapid typing

        for _ in args:  # Args used as function is passed extra 3 parameters by kivy which are not needed
            pass

    def _do_update(self, _dt):  # After 0.3 seconds, this runs and saves data to json as well as calculating marks
        self.display_marks_to_interface()
        self.save_data()

    @staticmethod  # Function does not require self
    def show_message(message):  # A message is passed which is then displayed by kivy on screen
        toast(message)

    def validate_textbox(self, instance, value, max_val):  # Validates textbox input value with a max value
        try:
            val = int(value)
            if val > max_val:
                instance.text = str(max_val)  # or whatever your max is
                self.show_message(f"Maximum value is {max_val}")
            elif val < 0:
                instance.text = "0"
                self.show_message("Value can't be negative")
        except ValueError:
            pass  # User may still be typing, ignore the error

    def init_dropdown_menu(self):  # Function creates the menu for the dropdown for selecting semesters with its options
        options = [str(i) for i in range(1, 14 + 1)]  # Add option 1 to 14 in dropdown menu
        items = [{"text": opt, "viewclass": "OneLineListItem", "on_release": lambda x=opt: self.display_main_section(x)}
                 for opt in options]
        self.menu = MDDropdownMenu(caller=self.root.ids.semester_dropdown, items=items)  # Add menu to dropdown

    def display_main_section(self,
                             semesters_in_degree):  # Function displays current_section with subject, mark and credit based on dropdown
        self.root.ids.semester_dropdown.set_item(
            semesters_in_degree)  # Set value of dropdown to selected value from menu
        self.menu.dismiss()  # Close the menu after number was selected
        self.root.ids.scroll_container.clear_widgets()  # Empty out scroll container in case of previous selection
        self.subjects_marks_dictionary.clear()  # Clear dictionary as widgets have been reset after semester selection
        self.focusable_fields_grid.clear()  # Clear array as entry widget rows have been reset after semester selection
        self.semester_labels_dictionary.clear()  # Clear labels stored for semesters
        self.semester_marks_sections_dictionary.clear()  # Clear dictionary storing sections for semester marks
        self.subject_input_rows_array.clear()  # Clear the array storing dictionaries for each row
        self.rows_count_dictionary.clear()  # Clear dictionary storing semester count

        for semester in range(1, int(semesters_in_degree) + 1):
            section_for_semester = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
            section_for_semester.bind(minimum_height=section_for_semester.setter(
                "height"))  # Set height of this static_layout to its contents height

            year = int((semester + 1) / 2)  # Calculate Year for the semester
            semester_label = f"Semester {semester} (Year {year})"  # Labels for semester 1 to Last semester
            section_for_semester.add_widget(MDLabel(text=semester_label, font_style="H6", theme_text_color="Primary"))
            section_for_semester.add_widget(MDLabel(height=dp(1)))  # Add gap between semester title and widgets

            rows = []
            for _ in range(4):  # Creates 4 subjects for each semester in a box static_layout representing each semester
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
            self.semester_marks_sections_dictionary[
                semester_label] = semester_marks_section  # Add section to dict to track

            section_for_semester.add_widget(MDLabel(text="[b]Semester marks summary:[/b]",
                                                    theme_text_color="Primary",
                                                    markup="True"))
            # Create semester summary labels
            wam_sem_label = MDLabel(text="[b]WAM: 0.0 F[/b]", markup=True,
                                    height=dp(10), size_hint_y=None, text_size=(None, None))
            gpa4_sem_label = MDLabel(text="[b]GPA (4-point scale): 0.0[/b]", markup=True,
                                     height=dp(10), size_hint_y=None, text_size=(None, None))
            gpa7_sem_label = MDLabel(text="[b]GPA (7-point scale): 0.0[/b]", markup=True,
                                     height=dp(10), size_hint_y=None, text_size=(None, None))

            # Add them to the static_layout
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

            self.root.ids.scroll_container.add_widget(
                section_for_semester)  # Add current_section for each semester to interface

            self.auto_update()  # Ensure to update json with new changes

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

        for field in (subject_field, mark_field, credit_field):
            field.fbind("text", self.auto_update)

        mark_field.fbind("text", lambda instance, val: self.validate_textbox(instance, val, 100))
        credit_field.fbind("text", lambda instance, val: self.validate_textbox(instance, val, 500))

        for field in (subject_field, mark_field,
                      credit_field):  # Append the 3 textboxes to array to track them for allowing tab and arrow keys over textboxes
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

        row_container = self.build_subject_row_layout(subject_field, mark_field, credit_field,
                                                      bin_btn)  # Pass widgets to store in static_layout

        bin_btn.bind(on_release=lambda _, r=row_container: self.remove_subject_row(semester_label, r,
                                                                                   parent))  # Provide button functionality

        # Track components for re-static_layout later
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

    def build_subject_row_layout(self, subject, mark, credit, bin_btn):  # Build app static_layout based on mobile or pc
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
            row = MDBoxLayout(spacing=dp(10), size_hint_y=None,
                              height=dp(48))  # Use boxlayout for each row for formatting
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
                index = parent.children.index(
                    old_container) if old_container in parent.children else 0  # Store index to tracker where to place widgets
                parent.remove_widget(old_container)  # If it exists, remove it as new container will be added

                # Detach children to avoid any parent conflicts
                row_info_dict["subject"].parent.remove_widget(row_info_dict["subject"])
                row_info_dict["mark"].parent.remove_widget(row_info_dict["mark"])
                row_info_dict["credit"].parent.remove_widget(row_info_dict["credit"])
                row_info_dict["bin"].parent.remove_widget(row_info_dict["bin"])

                # Rebuild with new static_layout mode
                new_container = self.build_subject_row_layout(
                    row_info_dict["subject"], row_info_dict["mark"], row_info_dict["credit"], row_info_dict["bin"]
                )

                # Section binds bin functionality again for new static_layout mode
                row_info_dict["bin"].unbind(on_release=None)  # Avoid duplicate bindings
                row_info_dict["bin"].bind(
                    on_release=lambda _, r=new_container, sl=row_info_dict['semester_label'], s=parent: self.remove_subject_row(sl, r, s)
                )

                row_info_dict["container"] = new_container
                parent.add_widget(new_container, index=index)

                # Update container reference in subjects_marks_dictionary
                semester = row_info_dict["semester_label"]
                if semester in self.subjects_marks_dictionary:
                    rows_list = self.subjects_marks_dictionary[semester]
                    for i, old_row in enumerate(rows_list):
                        if old_row == old_container:
                            rows_list[i] = new_container
                            break

    def add_subject_row(self, semester_label, current_section):  # Function called by add subject button
        row = self.create_subject_row(current_section, semester_label)  # Create a new row using predefined function

        current_section.add_widget(row, index=4)  # Insert row before add button, index 4 skips mark labels and add button (index 0 starts at bottom in kivy)

        self.subjects_marks_dictionary[semester_label].append(row)  # Add row to dictionary as well
        Clock.schedule_once(lambda dt: current_section.do_layout())  # Reformat the current section with new widget
        # Clock used to ensure this executes after the widget has been added

        self.auto_update()  # As a row was added, save this in json file

        for row_info in reversed(self.subject_input_rows_array):  # Search for the added row in array
            if row_info["container"] == row:
                Clock.schedule_once(lambda dt: setattr(row_info["subject"], "focus", True), 0)  # Set focus to subject field in new added row
                break

    def remove_subject_row(self, semester_label, row, section):  # Functionality of red bin button

        subject_widget, mark_widget, credit_widget = 0, 0, 0  # Initialise variables to prevent any undefined variable searches

        for input_row in self.subject_input_rows_array:
            if input_row["container"] == row:
                mark_widget = input_row["mark"]
                credit_widget = input_row["credit"]
                subject_widget = input_row["subject"]
                break  # Stop searching for more fields and save the correct variables

        for fields_row in self.focusable_fields_grid:  # Remove widgets of row from fields_grid_array to ensure correct navigation with arrow keys
            if subject_widget in fields_row and mark_widget in fields_row and credit_widget in fields_row:
                self.focusable_fields_grid.remove(fields_row)
                break

        if row in self.subjects_marks_dictionary[semester_label]:  # Remove from dictionary for calculating GPA
            self.subjects_marks_dictionary[semester_label].remove(row)
            section.remove_widget(row)  # Remove widget form interface

            def refresh_layout(_):
                section.do_layout()
                if isinstance(section.parent, ScrollView):
                    section.parent.do_layout()
                elif section.parent:
                    section.parent.do_layout()

            Clock.schedule_once(refresh_layout)  # Restructure the interface after ensuring widget is removed with a delay

        self.subject_input_rows_array = [
            # Remove the rows dictionary from the input row tracking array containing static_layout information
            row_dictionary for row_dictionary in self.subject_input_rows_array if row_dictionary["container"] != row
        ]

        if semester_label in self.rows_count_dictionary:
            self.rows_count_dictionary[semester_label] -= 1  # Decrement count of widgets in the semester

        self.auto_update()  # Recalculate marks as a row was deleted, and save in the json file

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
            for row in self.subject_input_rows_array:
                if row["semester_label"] != semester_name:
                    continue  # Skip rows from other semesters

                mark_text = row["mark"].text.strip()
                credit_text = row["credit"].text.strip()

                if not mark_text or not credit_text:
                    continue  # Skip incomplete rows and negative values to avoid throwing errors

                try:
                    mark = float(mark_text)
                    credit = float(credit_text)

                    degree_total_weight += mark * credit
                    degree_total_credits += credit

                    sem_weight += mark * credit
                    sem_credits += credit
                except Exception as e:  # try except used in case of invalid empty values for a subject (subject is ignored)
                    print(f'Failed to calculate marks: {e}')
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

    def recreate_semester_section(self, semester_label, subjects):  # Function recreates interface with saved data
        section = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        section.bind(minimum_height=section.setter("height"))

        # Add semester title
        section.add_widget(MDLabel(text=semester_label, font_style="H6", theme_text_color="Primary"))
        section.add_widget(MDLabel(height=dp(1)))  # Spacer

        rows = []
        for subject in subjects:
            # Create and prefill text fields
            subject_field = MDTextField(
                hint_text="Subject",
                text=subject.get("subject", ""),  # Fill textboxes with values loaded from json file
                size_hint_x=0.6,
                mode="rectangle",
                text_color_normal=(0, 0, 0, 1),
                text_color_focus=(0, 0, 0, 1)
            )

            mark_field = MDTextField(
                hint_text="Mark",
                text=subject.get("mark", ""),
                input_filter="float",
                size_hint_x=None,
                width=dp(70),
                mode="rectangle",
                text_color_normal=(0, 0, 0, 1),
                text_color_focus=(0, 0, 0, 1)
            )

            credit_field = MDTextField(
                hint_text="Credit",
                text=subject.get("credit", "6"),
                input_filter="int",
                size_hint_x=None,
                width=dp(70),
                mode="rectangle",
                text_color_normal=(0, 0, 0, 1),
                text_color_focus=(0, 0, 0, 1)
            )

            # Style and logic bindings
            for field in (subject_field, mark_field, credit_field):
                field.multiline = False
                field.fbind("text", self.auto_update)

            mark_field.fbind("text", lambda instance, val: self.validate_textbox(instance, val, 100))
            credit_field.fbind("text", lambda instance, val: self.validate_textbox(instance, val, 500))

            # Add to grid for keyboard navigation
            self.focusable_fields_grid.append([subject_field, mark_field, credit_field])

            bin_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0, 0, 1))
            row_container = self.build_subject_row_layout(subject_field, mark_field, credit_field, bin_btn)
            bin_btn.bind(on_release=lambda _, r=row_container: self.remove_subject_row(semester_label, r, section))

            rows.append(row_container)
            section.add_widget(row_container)

            self.subject_input_rows_array.append({
                "container": row_container,
                "parent": section,
                "semester_label": semester_label,
                "subject": subject_field,
                "mark": mark_field,
                "credit": credit_field,
                "bin": bin_btn
            })

            if semester_label in self.rows_count_dictionary.keys():  # Track widgets in row_count dictionary
                self.rows_count_dictionary[semester_label] += 1
            else:
                self.rows_count_dictionary[semester_label] = 1

        # Save to dict for recalculation
        self.subjects_marks_dictionary[semester_label] = rows

        # Add "+" button
        add_btn = MDIconButton(
            icon="plus",
            theme_text_color="Custom",
            text_color=self.theme_cls.primary_color,
            on_release=lambda _, sl=semester_label, sec=section: self.add_subject_row(sl, sec)
        )
        section.add_widget(add_btn)

        # Add summary section (WAM, GPA labels)
        section.add_widget(MDLabel(height=dp(1)))
        section.add_widget(MDLabel(text="[b]Semester marks summary:[/b]", theme_text_color="Primary", markup=True))

        marks_section = MDGridLayout(cols=3, size_hint_x=1, size_hint_y=None, adaptive_height=True, spacing=dp(10),
                                     padding=dp(10))
        wam_label = MDLabel(text="[b]WAM: 0.0 F[/b]", markup=True, height=dp(10), size_hint_y=None)
        gpa4_label = MDLabel(text="[b]GPA (4-point scale): 0.0[/b]", markup=True, height=dp(10), size_hint_y=None)
        gpa7_label = MDLabel(text="[b]GPA (7-point scale): 0.0[/b]", markup=True, height=dp(10), size_hint_y=None)

        marks_section.add_widget(wam_label)
        marks_section.add_widget(gpa4_label)
        marks_section.add_widget(gpa7_label)

        section.add_widget(marks_section)
        self.semester_labels_dictionary[semester_label] = {
            "wam": wam_label,
            "gpa4": gpa4_label,
            "gpa7": gpa7_label
        }
        self.semester_marks_sections_dictionary[semester_label] = marks_section

        return section


MarksApp().run()  # Main execution of class
