import sys
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QDialog, QMessageBox, QLabel, QStyle
)
from PySide6.QtGui import QIcon, QPixmap, Qt
from qfluentwidgets import TitleLabel, PrimaryPushButton, InfoBar, FluentIcon, PushButton


class CustomMessageBox(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Custom MessageBox")
        self.setFixedSize(400, 200)
        self.setWindowIcon(QIcon.fromTheme("dialog-information"))

        self.layout = QVBoxLayout(self)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(True)  # 确保图标自适应大小

        self.message_label = TitleLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20)
        self.button_layout.addStretch()

        self.layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.message_label)
        self.layout.addLayout(self.button_layout)

        self.result = None

    def setText(self, text: str) -> None:
        self.message_label.setText(text)

    def setIconType(self, icon_type: str) -> None:
        icon_mapping = {
            "Information": FluentIcon.INFO,
            "Warning": FluentIcon.INFO,      # 使用合适的图标
            "Critical": FluentIcon.INFO,     # 使用ERROR图标代替不存在的EMBED
            "Question": FluentIcon.INFO
        }
        icon = icon_mapping.get(icon_type, FluentIcon.INFO)
        svg_icon = self.style().standardIcon(getattr(QStyle, f"SP_MessageBox{icon_type}Icon", QStyle.SP_MessageBoxInformation))
        pixmap = svg_icon.pixmap(64, 64)
        self.icon_label.setPixmap(pixmap)
        self.setWindowIcon(QIcon.fromTheme(f"dialog-{icon_type.lower()}"))

    def addButton(self, button_text: str, role: int) -> None:
        button = PrimaryPushButton(button_text)
        button.clicked.connect(lambda: self.buttonClicked(role))
        self.button_layout.addWidget(button)

    def buttonClicked(self, role: int) -> None:
        self.result = role
        self.accept()

    def exec_(self) -> int:
        super().exec_()
        return self.result

    @staticmethod
    def information(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Information")
        box.addButton("OK", QMessageBox.AcceptRole)
        return box.exec_()

    @staticmethod
    def warning(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Warning")
        box.addButton("OK", QMessageBox.AcceptRole)
        box.addButton("Cancel", QMessageBox.RejectRole)
        return box.exec_()

    @staticmethod
    def critical(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Critical")
        box.addButton("OK", QMessageBox.AcceptRole)
        return box.exec_()

    @staticmethod
    def question(parent: Optional[QWidget], title: str, text: str) -> int:
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIconType("Question")
        box.addButton("Yes", QMessageBox.YesRole)
        box.addButton("No", QMessageBox.NoRole)
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