from typing import Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, LineEdit, PrimaryPushButton

from ...common.i18n_ui import setup_component_i18n, tr
from ...models.setting_card import SettingCard


class LineEditSettingCardPort(SettingCard):
    """Port setting card with line edit input."""

    set_port = Signal()

    def __init__(self, title: str, icon: Union[FluentIcon, str] = FluentIcon.SETTING) -> None:
        super().__init__(icon, title)

        # 设置国际化支持
        self.i18n = setup_component_i18n(self)

        self.port_edit = LineEdit(self)
        self.port_edit.setFixedWidth(85)
        self.port_edit.setPlaceholderText(tr("setting_cards.port"))
        self.port_edit.setValidator(QIntValidator(1, 99999, self))
        self.set_port_button = PrimaryPushButton(tr("setting_cards.set"), self)

        # 注册国际化元素
        self.i18n.register_placeholder(self.port_edit, "setting_cards.port")
        self.i18n.register_text(self.set_port_button, "setting_cards.set")

        self.hBoxLayout.addWidget(
            self.port_edit, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(
            self.set_port_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.set_port_button.clicked.connect(self.set_port.emit)
