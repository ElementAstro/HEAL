import sys
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QDialog, QMessageBox, QLabel, QStyle
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from qfluentwidgets import TitleLabel, PrimaryPushButton  # 移除了未使用的FluentIcon


class CustomMessageBox(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Custom MessageBox")
        self.setFixedSize(400, 200)
        self.setWindowIcon(QIcon.fromTheme("dialog-information"))

        self._main_layout = QVBoxLayout(self)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setScaledContents(True)  # 确保图标自适应大小

        self.message_label = TitleLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20)
        self.button_layout.addStretch()

        self._main_layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addWidget(self.message_label)
        self._main_layout.addLayout(self.button_layout)

        self._result: Optional[int] = None

    def setText(self, text: str) -> None:
        self.message_label.setText(text)

    def setIconType(self, icon_type: str) -> None:
        svg_icon = self.style().standardIcon(getattr(QStyle.StandardPixmap, f"SP_MessageBox{icon_type}", QStyle.StandardPixmap.SP_MessageBoxInformation))
        pixmap = svg_icon.pixmap(64, 64)
        self.icon_label.setPixmap(pixmap)
        self.setWindowIcon(QIcon.fromTheme(f"dialog-{icon_type.lower()}"))

    def addButton(self, button_text: str, role: QMessageBox.ButtonRole) -> None:
        button = PrimaryPushButton(button_text)
        # 直接传递role对象，不尝试将其转换为int
        button.clicked.connect(lambda: self.buttonClicked(role))
        self.button_layout.addWidget(button)

    def buttonClicked(self, role: QMessageBox.ButtonRole) -> None:
        # 存储ButtonRole的枚举值
        self._result = role.value  # type: ignore
        self.accept()

    def exec_(self) -> int:
        super().exec()
        if self._result is not None:
            return self._result
        return 0

    @staticmethod
    def information(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Information")
        box.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        return box.exec_()

    @staticmethod
    def warning(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Warning")
        box.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        return box.exec_()

    @staticmethod
    def critical(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Critical")
        box.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        return box.exec_()

    @staticmethod
    def question(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Question")
        box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        box.addButton("No", QMessageBox.ButtonRole.NoRole)
        return box.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()
    main_window.setWindowTitle("Custom MessageBox Demo")
    main_layout = QVBoxLayout(main_window)
    main_layout.setSpacing(10)

    info_button = PrimaryPushButton("Show Information")
    warning_button = PrimaryPushButton("Show Warning")
    critical_button = PrimaryPushButton("Show Critical")
    question_button = PrimaryPushButton("Show Question")

    main_layout.addWidget(info_button)
    main_layout.addWidget(warning_button)
    main_layout.addWidget(critical_button)
    main_layout.addWidget(question_button)

    info_button.clicked.connect(
        lambda: CustomMessageBox.information(
            main_window, "Information", "This is an information message."
        )
    )
    warning_button.clicked.connect(
        lambda: CustomMessageBox.warning(
            main_window, "Warning", "This is a warning message."
        )
    )
    critical_button.clicked.connect(
        lambda: CustomMessageBox.critical(
            main_window, "Critical", "This is a critical message."
        )
    )
    question_button.clicked.connect(
        lambda: CustomMessageBox.question(
            main_window, "Question", "Is this a question message?"
        )
    )

    main_window.setLayout(main_layout)
    main_window.show()

    sys.exit(app.exec())