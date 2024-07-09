from typing import Union, List
from PySide6.QtGui import QIcon, QPainter, QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget
from qfluentwidgets import (FluentIconBase, IconWidget,
                            FluentStyleSheet, isDarkTheme, drawIcon, ExpandLayout)


class SettingCardGroup(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = ExpandLayout()

        self._setup_layout()

    def _setup_layout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)
        self.vBoxLayout.addLayout(self.cardLayout, 1)
        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)

    def addSettingCard(self, card: QWidget):
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    def addSettingCards(self, cards: List[QWidget]):
        for card in cards:
            self.addSettingCard(card)

    def adjustSize(self):
        height = self.cardLayout.heightForWidth(self.width()) + 46
        self.resize(self.width(), height)


class SettingCard(QFrame):
    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str = None, content: str = None, parent: QWidget = None):
        super().__init__(parent=parent)
        self.iconLabel = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content or '', self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self._setup_layout(content)

    def _setup_layout(self, content: str):
        if not content:
            self.contentLabel.hide()

        self.setFixedHeight(70 if content else 50)
        self.iconLabel.setFixedSize(16, 16)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self._add_widgets_to_layout()

        self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.SETTING_CARD.apply(self)

    def _add_widgets_to_layout(self):
        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)

    def setTitle(self, title: str):
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setValue(self, value):
        pass

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class SettingIconWidget(IconWidget):
    def paintEvent(self, e):
        painter = QPainter(self)
        if not self.isEnabled():
            painter.setOpacity(0.36)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        drawIcon(self._icon, painter, self.rect())


class CustomFrame(QFrame):
    def __init__(self, title: str, icon: Union[str, QIcon, FluentIconBase], parent: QWidget = None):
        super().__init__(parent=parent)
        self.iconLabel = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)

        self.hBoxLayout = QHBoxLayout(self)

        self._setup_layout()

    def _setup_layout(self):
        self.iconLabel.setFixedSize(16, 16)
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addStretch(1)


class CustomFrameGroup(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.frameLayout = ExpandLayout()

        self._setup_layout()

    def _setup_layout(self):
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.frameLayout.setContentsMargins(0, 0, 0, 0)
        self.frameLayout.setSpacing(2)
        self.vBoxLayout.addLayout(self.frameLayout, 1)
        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)

    def addCustomFrame(self, frame: QFrame):
        frame.setParent(self)
        self.frameLayout.addWidget(frame)
        self.adjustSize()

    def addCustomFrames(self, frames: List[QFrame]):
        for frame in frames:
            self.addCustomFrame(frame)

    def createAndAddFrame(self, title: str, icon: Union[str, QIcon, FluentIconBase]):
        frame = CustomFrame(title, icon, self)
        self.addCustomFrame(frame)

    def adjustSize(self):
        height = self.frameLayout.heightForWidth(self.width()) + 46
        self.resize(self.width(), height)


class SettingCard(QFrame):
    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title: str = None, content: str = None, parent: QWidget = None):
        super().__init__(parent=parent)
        self.iconLabel = SettingIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content or '', self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self._setup_layout(content)

    def _setup_layout(self, content: str):
        if not content:
            self.contentLabel.hide()

        self.setFixedHeight(70 if content else 50)
        self.iconLabel.setFixedSize(16, 16)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self._add_widgets_to_layout()

        self.contentLabel.setObjectName('contentLabel')
        FluentStyleSheet.SETTING_CARD.apply(self)

    def _add_widgets_to_layout(self):
        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)

    def setTitle(self, title: str):
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setValue(self, value):
        pass

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class SettingIconWidget(IconWidget):
    def paintEvent(self, e):
        painter = QPainter(self)
        if not self.isEnabled():
            painter.setOpacity(0.36)
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.SmoothPixmapTransform)
        drawIcon(self._icon, painter, self.rect())
