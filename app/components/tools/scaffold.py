import os
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,  QFormLayout, QStackedWidget, QHBoxLayout)
from qfluentwidgets import TitleLabel, SubtitleLabel, LineEdit, TextEdit, PushButton
from app.components.utils.scaffold import (confirm_details, create_cmakelists, create_header, create_source, create_package_json,
                                           create_readme, create_gitignore, create_component_main, create_component_hpp, create_component_cpp)
from app.model.custom_messagebox import CustomMessageBox


class ScaffoldApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Module Scaffold Generator")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.stacked_widget = QStackedWidget()

        self.module_details = {}

        self.create_intro_page()
        self.create_form_pages()

        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)

    def create_intro_page(self):
        self.intro_page = QWidget()
        intro_layout = QVBoxLayout()
        intro_label = TitleLabel(
            "Welcome to the Module Scaffold Generator.\nClick 'Next' to start.")
        self.next_button = PushButton("Next")
        self.next_button.clicked.connect(self.show_next_page)
        intro_layout.addWidget(intro_label)
        intro_layout.addWidget(self.next_button)
        self.intro_page.setLayout(intro_layout)
        self.stacked_widget.addWidget(self.intro_page)

    def create_form_pages(self):
        self.pages = []
        fields = [
            ("Module Name (e.g., atom.utils):", "module_name"),
            ("Component Name (e.g., SystemComponent):", "component_name"),
            ("Version (e.g., 1.0.0):", "version"),
            ("Description:", "description"),
            ("Author:", "author"),
            ("License (e.g., GPL-3.0-or-later):", "license"),
            ("Repository URL (e.g., https://github.com/ElementAstro/Lithium):", "repo_url"),
            ("C++ Standard (e.g., 20):", "cpp_standard"),
            ("Additional source files (comma-separated, e.g., utils.cpp,math.cpp):",
             "additional_sources"),
            ("Additional header files (comma-separated, e.g., utils.hpp,math.hpp):",
             "additional_headers")
        ]

        for label_text, key in fields:
            page = QWidget()
            layout = QVBoxLayout()
            form_layout = QFormLayout()
            label = SubtitleLabel(label_text)
            input_widget = LineEdit()
            if key == "description":
                input_widget = TextEdit()
            form_layout.addRow(label, input_widget)
            layout.addLayout(form_layout)

            button_layout = QHBoxLayout()
            back_button = PushButton("Back")
            next_button = PushButton("Next")
            back_button.clicked.connect(self.show_previous_page)
            next_button.clicked.connect(self.show_next_page)
            button_layout.addWidget(back_button)
            button_layout.addWidget(next_button)

            layout.addLayout(button_layout)
            page.setLayout(layout)
            self.stacked_widget.addWidget(page)
            self.pages.append((page, input_widget, key))

        self.summary_page = QWidget()
        self.summary_layout = QVBoxLayout()
        self.summary_label = SubtitleLabel()
        self.summary_layout.addWidget(self.summary_label)
        self.confirm_button = PushButton("Confirm")
        self.confirm_button.clicked.connect(self.confirm_details)
        self.summary_layout.addWidget(self.confirm_button)
        self.summary_page.setLayout(self.summary_layout)
        self.stacked_widget.addWidget(self.summary_page)

    def show_next_page(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index < len(self.pages):
            page, input_widget, key = self.pages[current_index]
            self.module_details[key] = input_widget.toPlainText(
            ) if key == "description" else input_widget.text()

            if key == "cpp_standard" and not self.module_details[key]:
                self.module_details[key] = "20"

            if current_index == len(self.pages) - 1:
                self.show_summary()
            else:
                self.stacked_widget.setCurrentIndex(current_index + 1)

    def show_previous_page(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)

    def show_summary(self):
        details = self.module_details.copy()
        self.summary_label.setText(
            "\n".join([f"{key}: {value}" for key, value in details.items()]))
        self.stacked_widget.setCurrentIndex(self.stacked_widget.count() - 1)

    def confirm_details(self):
        confirmed, edit = confirm_details(self.module_details)
        if not confirmed:
            CustomMessageBox.warning(
                self, "Warning", "Please check your input and try again.")
            self.stacked_widget.setCurrentIndex(0)
            return

        module_name = self.module_details["module_name"]
        component_name = self.module_details["component_name"]
        version = self.module_details["version"]
        description = self.module_details["description"]
        author = self.module_details["author"]
        license = self.module_details["license"]
        repo_url = self.module_details["repo_url"]
        cpp_standard = self.module_details["cpp_standard"]
        additional_sources = self.module_details["additional_sources"]
        additional_headers = self.module_details["additional_headers"]

        module_dir = os.path.join(os.getcwd(), module_name)

        # Create the directory structure
        os.makedirs(module_dir, exist_ok=True)
        os.makedirs(os.path.join(module_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(module_dir, "include"), exist_ok=True)

        base_name = module_name.split('.')[-1]

        # Create _main.cpp
        main_cpp_path = os.path.join(module_dir, f"_main.cpp")
        with open(main_cpp_path, "w") as f:
            f.write(create_component_main(author, module_name, component_name))

        # Create _component.cpp
        component_cpp_path = os.path.join(module_dir, f"_component.cpp")
        with open(component_cpp_path, "w") as f:
            f.write(create_component_cpp(
                author, description, module_name, component_name))

        # Create _component.hpp
        component_hpp_path = os.path.join(module_dir, f"_component.hpp")
        with open(component_hpp_path, "w") as f:
            f.write(create_component_hpp(
                author, description, module_name, component_name))

        # Create CMakeLists.txt
        with open(os.path.join(module_dir, 'CMakeLists.txt'), 'w') as f:
            f.write(create_cmakelists(module_name, cpp_standard,
                    additional_sources, additional_headers))

        # Create module_name.hpp
        with open(os.path.join(module_dir, f'include/{base_name}.hpp'), 'w') as f:
            f.write(create_header(module_name))

        # Create module_name.cpp
        with open(os.path.join(module_dir, f'src/{base_name}.cpp'), 'w') as f:
            f.write(create_source(module_name))

        # Create additional source and header files
        for src in filter(None, additional_sources.split(',')):
            with open(os.path.join(module_dir, f'src/{src}'), 'w') as f:
                f.write(f"// {src}\n")
        for hdr in filter(None, additional_headers.split(',')):
            with open(os.path.join(module_dir, f'include/{hdr}'), 'w') as f:
                f.write(f"// {hdr}\n")

        # Create package.json
        with open(os.path.join(module_dir, 'package.json'), 'w') as f:
            f.write(create_package_json(module_name, version,
                    description, author, license, repo_url))

        # Create README.md
        with open(os.path.join(module_dir, 'README.md'), 'w') as f:
            f.write(create_readme(module_name, description, author, version))

        # Create .gitignore
        with open(os.path.join(module_dir, '.gitignore'), 'w') as f:
            f.write(create_gitignore())

        CustomMessageBox.information(self, "Success", f"Module {
                                     module_name} has been created successfully in {module_dir}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScaffoldApp()
    window.show()
    sys.exit(app.exec())
