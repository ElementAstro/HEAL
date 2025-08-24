from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import FluentIcon, LineEdit, PrimaryPushButton
from app.model.setting_card import SettingCard


class LineEditSettingCardPort(SettingCard):
    """Port setting card with line edit input."""
    set_port = Signal()

    def __init__(self, title, icon=FluentIcon.SETTING):
        super().__init__(icon, title)
        self.port_edit = LineEdit(self)
        self.port_edit.setFixedWidth(85)
        self.port_edit.setPlaceholderText(self.tr("端口"))
        self.port_edit.setValidator(QIntValidator(1, 99999, self))
        self.set_port_button = PrimaryPushButton(self.tr('设置'), self)

        self.hBoxLayout.addWidget(
            self.port_edit, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(
            self.set_port_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.set_port_button.clicked.connect(self.set_port.emit)
