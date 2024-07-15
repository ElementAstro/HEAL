import inspect
import sys
import asyncio
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel,
                               QListWidgetItem,  QFormLayout, QGroupBox, QInputDialog, QSplitter, QFileDialog)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
from qfluentwidgets import PushButton, LineEdit, TextEdit, ListWidget, Action, MessageBox, TitleLabel, SubtitleLabel, setTheme, Theme, isDarkTheme

from app.components.utils.dispatch import command_dispatcher


class CommandExecutionThread(QThread):
    result_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, command_name, *args, user_permissions, **kwargs):
        super().__init__()
        self.command_name = command_name
        self.args = args
        self.user_permissions = user_permissions
        self.kwargs = kwargs

    async def _execute(self):
        try:
            result = await command_dispatcher.execute_command(self.command_name, *self.args, user_permissions=self.user_permissions, **self.kwargs)
            self.result_signal.emit(str(result))
        except Exception as e:
            self.error_signal.emit(str(e))

    def run(self):
        asyncio.run(self._execute())


class CommandCenter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Center")
        self.setGeometry(100, 100, 800, 600)

        self.command_history = []

        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        left_layout = QVBoxLayout()
        self.command_list = ListWidget()
        self.command_list.itemDoubleClicked.connect(self.load_command)
        self.command_list.itemClicked.connect(self.show_command_description)
        self.update_command_list()
        left_layout.addWidget(SubtitleLabel("Available Commands"))
        left_layout.addWidget(self.command_list)
        self.command_description = TextEdit()
        self.command_description.setReadOnly(True)
        left_layout.addWidget(SubtitleLabel("Command Description"))
        left_layout.addWidget(self.command_description)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        right_layout = QVBoxLayout()
        self.param_layout = QFormLayout()
        param_group = QGroupBox("Command Parameters")
        param_group.setLayout(self.param_layout)
        right_layout.addWidget(param_group)

        input_layout = QHBoxLayout()
        self.command_input = LineEdit()
        self.command_input.setPlaceholderText("Enter command and arguments")
        execute_button = PushButton("Execute")
        execute_button.clicked.connect(self.execute_command)
        batch_execute_button = PushButton("Batch Execute")
        batch_execute_button.clicked.connect(self.batch_execute_commands)
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(execute_button)
        input_layout.addWidget(batch_execute_button)
        right_layout.addLayout(input_layout)

        self.result_output = TextEdit()
        self.result_output.setReadOnly(True)
        right_layout.addWidget(QLabel("Execution Result"))
        right_layout.addWidget(self.result_output)

        self.history_list = ListWidget()
        self.history_list.setMaximumHeight(100)
        self.history_list.itemClicked.connect(self.load_from_history)
        right_layout.addWidget(QLabel("Command History"))
        right_layout.addWidget(self.history_list)

        save_history_button = PushButton("Save History")
        save_history_button.clicked.connect(self.save_history)
        load_history_button = PushButton("Load History")
        load_history_button.clicked.connect(self.load_history)
        right_layout.addWidget(save_history_button)
        right_layout.addWidget(load_history_button)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        main_layout.addWidget(splitter)

        # Set theme based on system settings
        setTheme(Theme.DARK if isDarkTheme() else Theme.LIGHT)

    def update_command_list(self):
        self.command_list.clear()
        commands = command_dispatcher.list_commands()
        for name, description in commands.items():
            item = QListWidgetItem(f"{name}: {description}")
            self.command_list.addItem(item)

    def load_command(self, item):
        command_name = item.text().split(":")[0]
        self.command_input.setText(command_name)
        command_info = command_dispatcher.get_command_info(command_name)
        if command_info:
            self.clear_param_layout()
            signature = inspect.signature(command_info.handler)
            for param_name, param in signature.parameters.items():
                if param_name == 'args' or param_name == 'kwargs':
                    continue
                input_widget = LineEdit()
                input_widget.setObjectName(param_name)
                if param.default != inspect.Parameter.empty:
                    input_widget.setText(str(param.default))
                self.param_layout.addRow(
                    QLabel(f"{param_name} ({param.annotation.__name__}):"), input_widget)

    def show_command_description(self, item):
        command_name = item.text().split(":")[0]
        command_info = command_dispatcher.get_command_info(command_name)
        if command_info:
            self.command_description.setText(command_info.description)

    def clear_param_layout(self):
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)

    def execute_command(self):
        command_text = self.command_input.text().strip()
        if not command_text:
            w = MessageBox("Error", "Please enter a command", self)
            w.exec()
            return

        parts = command_text.split()
        command_name = parts[0]
        args = parts[1:]

        self.command_history.append(command_text)
        self.update_history_list()

        kwargs = {}
        for i in range(self.param_layout.rowCount()):
            label = self.param_layout.itemAt(i, QFormLayout.LabelRole).widget()
            input_widget = self.param_layout.itemAt(
                i, QFormLayout.FieldRole).widget()
            param_name = input_widget.objectName()
            param_value = input_widget.text()
            kwargs[param_name] = param_value

        self.execution_thread = CommandExecutionThread(
            command_name, *args, user_permissions=["basic"], **kwargs)
        self.execution_thread.result_signal.connect(self.display_result)
        self.execution_thread.error_signal.connect(self.display_error)
        self.execution_thread.start()

    def batch_execute_commands(self):
        commands, ok = QInputDialog.getMultiLineText(
            self, "Batch Execute", "Enter commands separated by new lines:")
        if ok:
            commands = commands.strip().split('\n')
            command_dicts = []
            for command_text in commands:
                parts = command_text.split()
                command_name = parts[0]
                args = parts[1:]
                command_dicts.append({
                    'name': command_name,
                    'args': args,
                    'permissions': ["basic"],
                    'kwargs': {key: input_widget.text() for key, input_widget in self.param_inputs.items()}
                })
            results = command_dispatcher.batch_execute(command_dicts)
            self.display_result(f"Batch Results: {results}")

    def load_from_history(self, item):
        self.command_input.setText(item.text())

    def update_history_list(self):
        self.history_list.clear()
        for cmd in self.command_history:
            item = QListWidgetItem(cmd)
            self.history_list.addItem(item)

    def save_history(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Command History", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'w') as file:
                json.dump(self.command_history, file)

    def load_history(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Command History", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r') as file:
                self.command_history = json.load(file)
                self.update_history_list()

    def display_result(self, result):
        self.result_output.append(f"Result: {result}")

    def display_error(self, error):
        self.result_output.append(f"Error: {error}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Dispatcher GUI")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.command_center = CommandCenter()
        layout.addWidget(self.command_center)

        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        settings_menu = menubar.addMenu('Settings')

        save_history_action = Action('Save History', self)
        save_history_action.triggered.connect(self.command_center.save_history)
        file_menu.addAction(save_history_action)

        load_history_action = Action('Load History', self)
        load_history_action.triggered.connect(self.command_center.load_history)
        file_menu.addAction(load_history_action)

        clear_history_action = Action('Clear History', self)
        clear_history_action.triggered.connect(self.clear_history)
        file_menu.addAction(clear_history_action)

    def clear_history(self):
        self.command_center.command_history = []
        self.command_center.update_history_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
