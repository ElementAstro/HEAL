import sys
from dataclasses import dataclass, field
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QMessageBox
)
from qfluentwidgets import (
    TitleLabel, PasswordLineEdit, PrimaryPushButton, FluentStyleSheet
)
from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase


@dataclass
class MessageBoxBase(MaskDialogBase):
    # 重命名Signal以避免与QDialog的方法冲突
    acceptedSignal: Signal = field(default_factory=Signal)
    rejectedSignal: Signal = field(default_factory=Signal)

    def __post_init__(self):
        super().__init__()
        self.buttonGroup = QFrame(self.widget)
        self.yesButton = PrimaryPushButton(self.tr('登录'), self.buttonGroup)
        self.cancelButton = QPushButton(self.tr('退出'), self.buttonGroup)

        self.vBoxLayout = QVBoxLayout(self.widget)
        self.viewLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout(self.buttonGroup)

        self.__initWidget()

    def __initWidget(self) -> None:
        self.__setQss()
        self.__initLayout()

        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))

        # 使用正确的枚举类型
        self.yesButton.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)
        self.cancelButton.setAttribute(
            Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)

        self.yesButton.setFocus()
        self.buttonGroup.setFixedHeight(81)

        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)

    def __initLayout(self) -> None:
        self._hBoxLayout.removeWidget(self.widget)
        # 使用正确的枚举类型
        self._hBoxLayout.addWidget(
            self.widget, 1, Qt.AlignmentFlag.AlignCenter)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.viewLayout, 1)
        # 使用正确的枚举类型
        self.vBoxLayout.addWidget(
            self.buttonGroup, 0, Qt.AlignmentFlag.AlignBottom)

        self.viewLayout.setSpacing(12)
        self.viewLayout.setContentsMargins(24, 24, 24, 24)

        self.buttonLayout.setSpacing(12)
        self.buttonLayout.setContentsMargins(24, 24, 24, 24)
        # 使用正确的枚举类型
        self.buttonLayout.addWidget(
            self.yesButton, 1, Qt.AlignmentFlag.AlignVCenter)
        self.buttonLayout.addWidget(
            self.cancelButton, 1, Qt.AlignmentFlag.AlignVCenter)

    def __onCancelButtonClicked(self) -> None:
        self.reject()
        self.rejectedSignal.emit()

    def __onYesButtonClicked(self) -> None:
        self.acceptedSignal.emit()

    def __setQss(self) -> None:
        self.buttonGroup.setObjectName('buttonGroup')
        self.cancelButton.setObjectName('cancelButton')
        FluentStyleSheet.DIALOG.apply(self)

    def hideYesButton(self) -> None:
        self.yesButton.hide()
        self.buttonLayout.insertStretch(0, 1)

    def hideCancelButton(self) -> None:
        self.cancelButton.hide()
        self.buttonLayout.insertStretch(0, 1)


@dataclass
class MessageLogin(MessageBoxBase):
    passwordEntered: Signal = field(default_factory=Signal)

    def __post_init__(self):
        super().__post_init__()
        self.titleLabel = TitleLabel(self.tr('你的老婆是?    '))
        self.passwordLabel = PasswordLineEdit(self)
        self.passwordLabel.setFixedWidth(300)
        self.passwordLabel.setPlaceholderText(self.tr('请输入TA的英文名'))

        # 新增组件
        self.rememberCheckBox = QCheckBox(self.tr('记住密码'), self)
        self.forgotPasswordLabel = QLabel(
            f"<a href='#'>{self.tr('忘记密码?')}</a>", self)
        self.forgotPasswordLabel.setOpenExternalLinks(False)
        self.forgotPasswordLabel.linkActivated.connect(self.onForgotPassword)

        self.yesButton.clicked.connect(self.emitPassword)
        self.cancelButton.clicked.connect(lambda: sys.exit())

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.passwordLabel)
        self.viewLayout.addWidget(self.rememberCheckBox)
        self.viewLayout.addWidget(self.forgotPasswordLabel)

    def emitPassword(self) -> None:
        password = self.passwordLabel.text()
        if self.rememberCheckBox.isChecked():
            # 实现记住密码的逻辑
            pass
        self.passwordEntered.emit(password)

    def onForgotPassword(self):
        QMessageBox.information(self, self.tr('忘记密码'), self.tr('请联系管理员重置密码。'))
