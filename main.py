from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRectangleFlatButton, MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget


class GPAWidget(MDBoxLayout):
    pass


class GPAApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.root = GPAWidget()
        self.subject_widgets = {}
        Clock.schedule_once(lambda dt: self.init_dropdown_menu())
        Window.bind(on_resize=self.on_window_resize)
        self.on_window_resize(Window, Window.width, Window.height)  # Triggers once at startup
        return self.root

    def on_window_resize(self, window, width, height):
        width = Window.width
        if width < 400:
            cols = 1
        elif width < 700:
            cols = 2
        else:
            cols = 3

        self.root.ids.gpa_output_box.cols = cols

    def init_dropdown_menu(self):
        options = [str(i) for i in range(1, 7)]
        items = [{"text": opt, "viewclass": "OneLineListItem", "on_release": lambda x=opt: self.on_select_years(x)} for opt in options]
        self.menu = MDDropdownMenu(caller=self.root.ids.year_dropdown, items=items, width_mult=4)

    def on_select_years(self, val):
        self.root.ids.year_dropdown.set_item(val)
        self.menu.dismiss()
        container = self.root.ids.year_container
        container.clear_widgets()
        self.subject_widgets.clear()

        for year in range(1, int(val) + 1):
            year_label = f"Year {year}"
            section = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
            section.bind(minimum_height=section.setter("height"))

            section.add_widget(MDLabel(text=year_label, font_style="H6", theme_text_color="Primary"))

            rows = []
            for _ in range(4):
                row = self.create_subject_row(section, year_label)
                section.add_widget(row)
                rows.append(row)

            add_btn = MDRectangleFlatButton(
                text="Add Subject",
                size_hint=(None, None),
                size=("140dp", "36dp"),
                pos_hint={"center_x": 0.5},
                on_release=lambda _, yl=year_label, sec=section: self.add_subject_row(yl, sec)
            )
            section.add_widget(add_btn)

            container.add_widget(section)
            self.subject_widgets[year_label] = rows

    def create_subject_row(self, parent, year_label):
        row = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(48))
        black = (0, 0, 0, 1)
        row.add_widget(MDTextField(hint_text="Subject", mode="rectangle",
                                   text_color_normal=black, text_color_focus=black))
        row.add_widget(MDTextField(hint_text="Mark (%)", input_filter="float", mode="rectangle",
                                   text_color_normal=black, text_color_focus=black))
        row.add_widget(MDTextField(hint_text="Credit", input_filter="int", mode="rectangle", text="6",
                                   text_color_normal=black, text_color_focus=black))
        bin_btn = MDIconButton(icon="trash-can", theme_text_color="Custom", text_color=(1, 0, 0, 1))
        bin_btn.bind(on_release=lambda _, r=row: self.remove_subject_row(year_label, r, parent))
        row.add_widget(bin_btn)
        return row

    def add_subject_row(self, year_label, section):
        row = self.create_subject_row(section, year_label)
        # Insert before the Add button (last child)
        section.add_widget(row, index=len(section.children) - 1)
        self.subject_widgets[year_label].append(row)
        Clock.schedule_once(lambda dt: section.do_layout())

    def remove_subject_row(self, year_label, row, section):
        if row in self.subject_widgets[year_label]:
            self.subject_widgets[year_label].remove(row)
            section.remove_widget(row)
            Clock.schedule_once(lambda dt: section.do_layout())

    def calculate_gpa(self):
        total_weighted = 0
        total_credits = 0
        for rows in self.subject_widgets.values():
            for row in rows:
                try:
                    mark = float(row.children[2].text)
                    credit = float(row.children[1].text)
                    total_weighted += mark * credit
                    total_credits += credit
                except:
                    continue
        wam = round(total_weighted / total_credits, 2) if total_credits else 0
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

        # self.root.ids.gpa_output_text.clear_widgets()

        self.root.ids.wam_label.text = f"Predicted WAM: {wam} {grade}"
        self.root.ids.gpa4_label.text = f"GPA (4-point scale): {gpa_4}"
        self.root.ids.gpa7_label.text = f"GPA (7-point scale): {gpa_7}"


if __name__ == "__main__":
    GPAApp().run()