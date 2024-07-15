import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QDialog, QMessageBox)
from PySide6.QtGui import QIcon

from qfluentwidgets import TitleLabel, PushButton

class CustomMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom MessageBox")
        self.setFixedSize(300, 150)
        self.layout = QVBoxLayout()
        
        self.message_label = TitleLabel("")
        self.layout.addWidget(self.message_label)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        self.result = None

    def setText(self, text):
        self.message_label.setText(text)

    def setIcon(self, icon):
        if icon == "Information":
            self.setWindowIcon(QIcon.fromTheme("dialog-information"))
        elif icon == "Warning":
            self.setWindowIcon(QIcon.fromTheme("dialog-warning"))
        elif icon == "Critical":
            self.setWindowIcon(QIcon.fromTheme("dialog-critical"))
        elif icon == "Question":
            self.setWindowIcon(QIcon.fromTheme("dialog-question"))

    def addButton(self, button, role):
        self.button_layout.addWidget(button)
        button.clicked.connect(lambda: self.buttonClicked(role))

    def buttonClicked(self, role):
        self.result = role
        self.accept()

    def exec_(self):
        super().exec_()
        return self.result

    @staticmethod
    def information(parent, title, text):
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon("Information")
        ok_button = PushButton("OK")
        box.addButton(ok_button, QMessageBox.AcceptRole)
        return box.exec_()

    @staticmethod
    def warning(parent, title, text):
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon("Warning")
        ok_button = PushButton("OK")
        cancel_button = PushButton("Cancel")
        box.addButton(ok_button, QMessageBox.AcceptRole)
        box.addButton(cancel_button, QMessageBox.RejectRole)
        return box.exec_()

    @staticmethod
    def critical(parent, title, text):
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon("Critical")
        ok_button = PushButton("OK")
        box.addButton(ok_button, QMessageBox.AcceptRole)
        return box.exec_()

    @staticmethod
    def question(parent, title, text):
        box = CustomMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon("Question")
        yes_button = PushButton("Yes")
        no_button = PushButton("No")
        box.addButton(yes_button, QMessageBox.YesRole)
        box.addButton(no_button, QMessageBox.NoRole)
        return box.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    
    info_button = PushButton("Show Information")
    warning_button = PushButton("Show Warning")
    critical_button = PushButton("Show Critical")
    question_button = PushButton("Show Question")
    
    layout.addWidget(info_button)
    layout.addWidget(warning_button)
    layout.addWidget(critical_button)
    layout.addWidget(question_button)

    info_button.clicked.connect(lambda: CustomMessageBox.information(main_window, "Information", "This is an information message."))
    warning_button.clicked.connect(lambda: CustomMessageBox.warning(main_window, "Warning", "This is a warning message."))
    critical_button.clicked.connect(lambda: CustomMessageBox.critical(main_window, "Critical", "This is a critical message."))
    question_button.clicked.connect(lambda: CustomMessageBox.question(main_window, "Question", "This is a question message."))
    
    main_window.setLayout(layout)
    main_window.show()
    
    sys.exit(app.exec())
