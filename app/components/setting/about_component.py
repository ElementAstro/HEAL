from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QPainter, QPainterPath, QPixmap, QFont, QClipboard
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication
from qfluentwidgets import PushButton, FluentIcon, setCustomStyleSheet
from app.model.config import cfg, Info


class AboutBackground(QWidget):
    """Background widget for the about section with rounded corners and app info."""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pixmap = QPixmap("./src/image/bg_about.png")
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 20, 20)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)

        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont(cfg.APP_FONT, 45))
        painter.drawText(self.rect().adjusted(0, -30, 0, 0),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, cfg.APP_NAME)
        painter.setFont(QFont(cfg.APP_FONT, 30))
        painter.drawText(self.rect().adjusted(0, 120, 0, 0),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, cfg.APP_VERSION)


class About(QWidget):
    """About section widget with links and version info."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text)
        self.__initWidget()

    def __initWidget(self):
        self.about_image = AboutBackground()
        self.about_image.setFixedSize(1100, 500)

        self.link_writer = PushButton(FluentIcon.HOME, self.tr('   作者主页'))
        self.link_repo = PushButton(FluentIcon.GITHUB, self.tr('   项目仓库'))
        self.link_releases = PushButton(FluentIcon.MESSAGE, self.tr('   版本发布'))
        self.link_issues = PushButton(FluentIcon.HELP, self.tr('   反馈交流'))

        for link_button in [self.link_writer, self.link_repo, self.link_releases, self.link_issues]:
            link_button.setFixedSize(260, 70)
            link_button.setIconSize(QSize(16, 16))
            link_button.setFont(QFont(cfg.APP_FONT, 12))
            setCustomStyleSheet(
                link_button, 'PushButton{border-radius: 12px}', 'PushButton{border-radius: 12px}')

        # 增加复制按钮
        self.copyButton = QPushButton(self.tr('复制版本信息'), self)
        self.copyButton.setFixedSize(200, 50)
        self.copyButton.setFont(QFont(cfg.APP_FONT, 12))
        self.copyButton.clicked.connect(self.copy_version_info)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.image_layout = QVBoxLayout()
        self.image_layout.addWidget(
            self.about_image, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.info_button_layout = QHBoxLayout()
        self.info_button_layout.addWidget(self.link_writer)
        self.info_button_layout.addWidget(self.link_repo)
        self.info_button_layout.addWidget(self.link_releases)
        self.info_button_layout.addWidget(self.link_issues)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.image_layout)
        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(self.info_button_layout)
        self.main_layout.addWidget(
            self.copyButton, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.main_layout)

    def __connectSignalToSlot(self):
        self.link_writer.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(cfg.URL_WRITER)))
        self.link_repo.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(cfg.URL_REPO)))
        self.link_releases.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(cfg.URL_RELEASES)))
        self.link_issues.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(cfg.URL_ISSUES)))

    def copy_version_info(self):
        clipboard: QClipboard = QApplication.clipboard()
        version_info = f"{cfg.APP_NAME} - {cfg.APP_VERSION}"
        clipboard.setText(version_info)
        Info(self, 'S', 1000, self.tr('版本信息已复制到剪贴板!'))
