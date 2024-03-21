import importlib
import os
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QMessageBox, QTextEdit, QLabel
from PySide6.QtCore import QThread, Signal
from qfluentwidgets import PrimaryPushButton

class ScriptLoaderThread(QThread):
    script_loaded = Signal(list)

    def __init__(self, script_directory):
        super().__init__()
        self.script_directory = script_directory

    def run(self):
        scripts = []
        script_files = [file for file in os.listdir(self.script_directory) if file.endswith(".py")]
        for script_file in script_files:
            module_name = os.path.splitext(script_file)[0]
            script_path = os.path.join(self.script_directory, script_file)

            try:
                spec = importlib.util.spec_from_file_location(module_name, script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                functions = [func for func in dir(module) if callable(getattr(module, func))]
                scripts.append((module_name, functions))
            except Exception as e:
                print(f"Failed to load {script_file}: {str(e)}")

        self.script_loaded.emit(scripts)

class DynamicScriptLoader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Script Loader")
        self.layout = QVBoxLayout(self)

        self.script_functions = []
        self.script_directory = ""
        self.loaded_scripts = []

        self.toolbar_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Select Directory")
        self.select_button.clicked.connect(self.select_directory_and_load_scripts)
        self.toolbar_layout.addWidget(self.select_button)

        self.unload_button = QPushButton("Unload Scripts")
        self.unload_button.clicked.connect(self.unload_scripts)
        self.unload_button.setEnabled(False)
        self.toolbar_layout.addWidget(self.unload_button)

        self.layout.addLayout(self.toolbar_layout)

        self.directory_label = QLabel("Selected Directory: ")
        self.layout.addWidget(self.directory_label)

        self.function_list = QListWidget()
        self.layout.addWidget(self.function_list)

        self.load_button = QPushButton("Load Selected Script")
        self.load_button.clicked.connect(self.load_selected_script)
        self.layout.addWidget(self.load_button)

        self.output_display = QTextEdit()
        self.layout.addWidget(self.output_display)

    def select_directory_and_load_scripts(self):
        selected_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if selected_directory:
            self.script_directory = selected_directory
            self.directory_label.setText(f"Selected Directory: {self.script_directory}")
            self.load_scripts()

    def load_scripts(self):
        self.thread = ScriptLoaderThread(self.script_directory)
        self.thread.script_loaded.connect(self.handle_scripts_loaded)
        self.thread.start()

    def unload_scripts(self):
        # Clear the loaded scripts and update the function list
        self.loaded_scripts = []
        self.update_function_list()
        self.unload_button.setEnabled(False)

    def handle_scripts_loaded(self, scripts):
        self.loaded_scripts = scripts
        self.update_function_list()
        self.unload_button.setEnabled(True)

    def load_selected_script(self):
        selected_item = self.function_list.currentItem()
        if selected_item:
            script_name = selected_item.text()
            # Add logic to load or unload the selected script
            if self.load_button.text() == "Load Selected Script":
                # Add logic to load the selected script
                self.output_display.append(f"Loading script: {script_name}")
                # TODO: Implement the script loading logic
                self.load_button.setText("Unload Selected Script")
            else:
                # Add logic to unload the selected script
                self.output_display.append(f"Unloading script: {script_name}")
                # TODO: Implement the script unloading logic
                self.load_button.setText("Load Selected Script")

    def update_function_list(self):
        self.function_list.clear()
        for script_name, _ in self.loaded_scripts:
            self.function_list.addItem(script_name)

if __name__ == "__main__":
    app = QApplication([])
    script_loader = DynamicScriptLoader()
    script_loader.show()
    app.exec()
