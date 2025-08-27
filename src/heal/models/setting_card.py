from typing import Any, List, Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPaintEvent
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    ExpandLayout,
    FluentIconBase,
    FluentStyleSheet,
    IconWidget,
    LineEdit,
    PushButton,
    drawIcon,
    isDarkTheme,
)

from src.heal.common.logging_config import get_logger

# 使用统一日志配置
logger = get_logger("setting_card")


class SettingCardGroup(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = ExpandLayout()

        self._setup_layout()

    def _setup_layout(self) -> None:
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)
        self.vBoxLayout.addLayout(self.cardLayout, 1)
        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)

    def addSettingCard(self, card: QWidget) -> None:
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    def addSettingCards(self, cards: List[QWidget]) -> None:
        for card in cards:
            self.addSettingCard(card)

    def adjustSize(self) -> None:
        height = self.cardLayout.heightForWidth(self.width()) + 46
        self.resize(self.width(), height)


class SettingCard(QFrame):
    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: Optional[str] = None,
        content: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)
        self.iconLabel = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title or "", self)
        self.contentLabel = QLabel(content or "", self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self._setup_layout(content)

    def _setup_layout(self, content: Optional[str]) -> None:
        if not content:
            self.contentLabel.hide()

        self.setFixedHeight(70 if content else 50)
        self.iconLabel.setFixedSize(16, 16)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._add_widgets_to_layout()

        self.contentLabel.setObjectName("contentLabel")
        FluentStyleSheet.SETTING_CARD.apply(self)

    def _add_widgets_to_layout(self) -> None:
        self.hBoxLayout.addWidget(
            self.iconLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(
            self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(
            self.contentLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)

    def setTitle(self, title: str) -> None:
        self.titleLabel.setText(title)

    def setContent(self, content: str) -> None:
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setValue(self, value: Any) -> None:
        # Placeholder method - subclasses can override
        _ = value  # To avoid unused parameter warning

    def paintEvent(self, e: QPaintEvent) -> None:
        _ = e  # To avoid unused parameter warning
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class SettingIconWidget(IconWidget):
    def paintEvent(self, e: QPaintEvent) -> None:
        _ = e  # To avoid unused parameter warning
        painter = QPainter(self)
        if not self.isEnabled():
            painter.setOpacity(0.36)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        drawIcon(self._icon, painter, self.rect())


class CustomFrame(QFrame):
    def __init__(
        self,
        title: str,
        icon: Union[str, QIcon, FluentIconBase],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent=parent)
        self.iconLabel = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)

        self.hBoxLayout = QHBoxLayout(self)

        self._setup_layout()

    def _setup_layout(self) -> None:
        self.iconLabel.setFixedSize(16, 16)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout.addWidget(
            self.iconLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(
            self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.hBoxLayout.addStretch(1)


class CustomFrameGroup(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.frameLayout = ExpandLayout()

        self._setup_layout()

    def _setup_layout(self) -> None:
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.frameLayout.setContentsMargins(0, 0, 0, 0)
        self.frameLayout.setSpacing(2)
        self.vBoxLayout.addLayout(self.frameLayout, 1)
        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)

    def addCustomFrame(self, frame: QFrame) -> None:
        frame.setParent(self)
        self.frameLayout.addWidget(frame)
        self.adjustSize()

    def addCustomFrames(self, frames: List[QFrame]) -> None:
        for frame in frames:
            self.addCustomFrame(frame)

    def createAndAddFrame(self, title: str, icon: Union[str, QIcon, FluentIconBase]) -> None:
        frame = CustomFrame(title, icon, self)
        self.addCustomFrame(frame)

    def adjustSize(self) -> None:
        height = self.frameLayout.heightForWidth(self.width()) + 46
        self.resize(self.width(), height)


class CustomDialog(QDialog):
    def __init__(self, widget: QWidget, title: str = "Dialog", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(widget)

        # Optional: Add standard buttons (OK/Cancel)
        button_layout = QHBoxLayout()
        ok_button = PushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = PushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)


class CustomInputDialog(QDialog):
    def __init__(self, title: str, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)

        # Use a different name to avoid conflict with layout() method
        main_layout = QVBoxLayout()
        self.label = QLabel(label)
        self.input = LineEdit()
        self.buttons_layout = QHBoxLayout()
        self.ok_button = PushButton("确认")
        self.cancel_button = PushButton("取消")

        self.buttons_layout.addWidget(self.ok_button)
        self.buttons_layout.addWidget(self.cancel_button)
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.input)
        main_layout.addLayout(self.buttons_layout)
        self.setLayout(main_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_text(self) -> Optional[str]:
        if self.exec() == QDialog.DialogCode.Accepted:
            return str(self.input.text())
        return None
