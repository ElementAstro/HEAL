import asyncio
import inspect
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    Action,
    LineEdit,
    ListWidget,
    MessageBox,
    PushButton,
    SubtitleLabel,
    TextEdit,
    Theme,
    TitleLabel,
    isDarkTheme,
    setTheme,
)

from src.heal.components.utils.dispatch import command_dispatcher


@dataclass
class Command:
    name: str
    description: str
    handler: Any


class CommandExecutionThread(QThread):
    result_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(
        self, command_name: str, *args: Any, user_permissions: List[str], **kwargs: Any
    ) -> None:
        super().__init__()
        self.command_name = command_name
        self.args = args
        self.user_permissions = user_permissions
        self.kwargs = kwargs

    async def _execute(self) -> None:
        try:
            result = await command_dispatcher.execute_command(
                self.command_name,
                *self.args,
                user_permissions=self.user_permissions,
                **self.kwargs,
            )
            self.result_signal.emit(str(result))
        except Exception as e:
            self.error_signal.emit(str(e))

    def run(self) -> None:
        asyncio.run(self._execute())


class CommandCenter(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Command Center")
        self.setGeometry(100, 100, 900, 700)

        self.command_history: List[str] = []
        self.param_inputs: Dict[str, QLineEdit] = {}

        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # 左侧布局
        left_widget = self._create_left_panel()
        splitter.addWidget(left_widget)

        # 右侧布局
        right_widget = self._create_right_panel()
        splitter.addWidget(right_widget)

        splitter.setSizes([300, 600])
        main_layout.addWidget(splitter)

        # 设置主题
        setTheme(Theme.DARK if isDarkTheme() else Theme.LIGHT)

    def _create_left_panel(self) -> QWidget:
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

        left_container = QWidget()
        left_container.setLayout(left_layout)
        return left_container

    def _create_right_panel(self) -> QWidget:
        right_layout = QVBoxLayout()

        # 参数输入区域
        self.param_layout = QFormLayout()
        param_group = QGroupBox("Command Parameters")
        param_group.setLayout(self.param_layout)
        right_layout.addWidget(param_group)

        # 输入和执行按钮
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

        # 结果输出
        self.result_output = TextEdit()
        self.result_output.setReadOnly(True)
        right_layout.addWidget(QLabel("Execution Result"))
        right_layout.addWidget(self.result_output)

        # 历史记录
        self.history_list = ListWidget()
        self.history_list.setMaximumHeight(150)
        self.history_list.itemClicked.connect(self.load_from_history)
        right_layout.addWidget(QLabel("Command History"))
        right_layout.addWidget(self.history_list)

        # 历史操作按钮
        history_buttons_layout = QHBoxLayout()
        save_history_button = PushButton("Save History")
        save_history_button.clicked.connect(self.save_history)
        load_history_button = PushButton("Load History")
        load_history_button.clicked.connect(self.load_history)
        history_buttons_layout.addWidget(save_history_button)
        history_buttons_layout.addWidget(load_history_button)
        right_layout.addLayout(history_buttons_layout)

        right_container = QWidget()
        right_container.setLayout(right_layout)
        return right_container

    def update_command_list(self) -> None:
        self.command_list.clear()
        commands = command_dispatcher.list_commands()
        for name, description in commands.items():
            item = QListWidgetItem(f"{name}: {description}")
            self.command_list.addItem(item)

    def load_command(self, item: QListWidgetItem) -> None:
        command_name = item.text().split(":")[0]
        self.command_input.setText(command_name)
        command_info = command_dispatcher.get_command_info(command_name)
        if command_info:
            self.clear_param_layout()
            signature = inspect.signature(command_info.handler)
            for param_name, param in signature.parameters.items():
                if param_name in ["args", "kwargs"]:
                    continue
                input_widget = LineEdit()
                input_widget.setObjectName(param_name)
                input_widget.setPlaceholderText(str(param.annotation.__name__))
                if param.default != inspect.Parameter.empty:
                    input_widget.setText(str(param.default))
                self.param_layout.addRow(
                    QLabel(f"{param_name}:"), input_widget)
                self.param_inputs[param_name] = input_widget

    def show_command_description(self, item: QListWidgetItem) -> None:
        command_name = item.text().split(":")[0]
        command_info = command_dispatcher.get_command_info(command_name)
        if command_info:
            self.command_description.setText(command_info.description)

    def clear_param_layout(self) -> None:
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)
        self.param_inputs.clear()

    def execute_command(self) -> None:
        command_text = self.command_input.text().strip()
        if not command_text:
            MessageBox.warning(self, "Error", "Please enter a command").exec()
            return

        parts = command_text.split()
        command_name = parts[0]
        args = parts[1:]

        self.command_history.append(command_text)
        self.update_history_list()

        kwargs = {key: widget.text()
                  for key, widget in self.param_inputs.items()}

        self.execution_thread = CommandExecutionThread(
            command_name, *args, user_permissions=["basic"], **kwargs
        )
        self.execution_thread.result_signal.connect(self.display_result)
        self.execution_thread.error_signal.connect(self.display_error)
        self.execution_thread.start()

    def batch_execute_commands(self) -> None:
        commands, ok = QInputDialog.getMultiLineText(
            self, "Batch Execute", "Enter commands separated by new lines:"
        )
        if ok:
            commands = commands.strip().split("\n")
            results = []
            for command_text in commands:
                parts = command_text.split()
                command_name = parts[0]
                args = parts[1:]
                try:
                    result = asyncio.run(
                        command_dispatcher.execute_command(
                            command_name, *args, user_permissions=["basic"]
                        )
                    )
                    results.append(f"{command_name}: {result}")
                except Exception as e:
                    results.append(f"{command_name}: Error - {e}")
            self.display_result("\n".join(results))

    def load_from_history(self, item: QListWidgetItem) -> None:
        self.command_input.setText(item.text())

    def update_history_list(self) -> None:
        self.history_list.clear()
        for cmd in self.command_history[-50:]:
            item = QListWidgetItem(cmd)
            self.history_list.addItem(item)

    def save_history(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Command History", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(self.command_history, file,
                          ensure_ascii=False, indent=4)

    def load_history(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Command History", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            with open(file_name, "r", encoding="utf-8") as file:
                self.command_history = json.load(file)
                self.update_history_list()

    def display_result(self, result: str) -> None:
        self.result_output.append(f"Result: {result}")

    def display_error(self, error: str) -> None:
        self.result_output.append(f"Error: {error}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Command Dispatcher GUI")
        self.setGeometry(100, 100, 900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.command_center = CommandCenter()
        layout.addWidget(self.command_center)

        self.create_menu()

    def create_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        settings_menu = menubar.addMenu("Settings")

        save_history_action = QAction("Save History", self)
        save_history_action.triggered.connect(self.command_center.save_history)
        file_menu.addAction(save_history_action)

        load_history_action = QAction("Load History", self)
        load_history_action.triggered.connect(self.command_center.load_history)
        file_menu.addAction(load_history_action)

        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.clear_history)
        file_menu.addAction(clear_history_action)

    def clear_history(self) -> None:
        self.command_center.command_history.clear()
        self.command_center.update_history_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
