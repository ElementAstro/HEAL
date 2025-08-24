import json
import sys
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QClipboard
from PySide6.QtCore import QProcess
from qfluentwidgets import (
    CustomColorSettingCard, ComboBoxSettingCard, PrimaryPushSettingCard,
    SwitchSettingCard, FluentIcon, setThemeColor
)
from app.model.setting_card import SettingCardGroup, CustomDialog
from app.model.check_update import check_update
from app.model.config import cfg, get_json, Info
from app.components.tools.editor import JsonEditor
from app.components.setting.setting_cards import LineEditSettingCardPort

if TYPE_CHECKING:
    from app.setting_interface import Setting


class SettingsManager:
    """Manages all setting cards and their operations."""
    
    def __init__(self, parent_widget: "Setting"):
        self.parent = parent_widget
        self.config_editor = JsonEditor()
        
    def create_personal_interface(self) -> SettingCardGroup:
        """Create personal settings interface."""
        personal_interface = SettingCardGroup(self.parent.scrollWidget)
        
        # Theme color card
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FluentIcon.PALETTE,
            self.parent.tr('主题色'),
            self.parent.tr('默认流萤主题色，开拓者你不会改的吧?')
        )
        
        # DPI scale card
        self.zoomCard = ComboBoxSettingCard(
            cfg.dpiScale,
            FluentIcon.ZOOM,
            "DPI",
            self.parent.tr("调整全局缩放"),
            texts=["100%", "125%", "150%", "175%", "200%", self.parent.tr("跟随系统设置")]
        )
        
        # Language card
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FluentIcon.LANGUAGE,
            self.parent.tr('语言'),
            self.parent.tr('界面显示语言'),
            texts=['简体中文', '繁體中文', 'English', self.parent.tr('跟随系统设置')]
        )
        
        # Update card
        self.updateOnStartUpCard = PrimaryPushSettingCard(
            self.parent.tr('检查更新'),
            FluentIcon.UPDATE,
            self.parent.tr('手动检查更新'),
            self.parent.tr('当前版本 : ') + cfg.APP_VERSION
        )
        
        # Restart card
        self.restartCard = PrimaryPushSettingCard(
            self.parent.tr('重启程序'),
            FluentIcon.ROTATE,
            self.parent.tr('重启程序'),
            self.parent.tr('无奖竞猜，存在即合理')
        )
        
        # Config editor card
        self.configEditorCard = PrimaryPushSettingCard(
            self.parent.tr('打开配置'),
            FluentIcon.PENCIL_INK,
            self.parent.tr('打开配置'),
            self.parent.tr('自实现Json编辑器')
        )
        
        # Add cards to interface
        personal_interface.addSettingCard(self.themeColorCard)
        personal_interface.addSettingCard(self.zoomCard)
        personal_interface.addSettingCard(self.languageCard)
        personal_interface.addSettingCard(self.updateOnStartUpCard)
        personal_interface.addSettingCard(self.restartCard)
        personal_interface.addSettingCard(self.configEditorCard)
        
        return personal_interface
    
    def create_function_interface(self) -> SettingCardGroup:
        """Create function settings interface."""
        function_interface = SettingCardGroup(self.parent.scrollWidget)
        
        # Auto copy card
        self.autoCopyCard = SwitchSettingCard(
            FluentIcon.COPY,
            self.parent.tr('命令自动复制'),
            self.parent.tr('选择命令时，自动复制命令到剪贴板'),
            configItem=cfg.autoCopy
        )
        
        # Login card
        self.useLoginCard = SwitchSettingCard(
            FluentIcon.PENCIL_INK,
            self.parent.tr('启用登录功能'),
            self.parent.tr('使用自定义登陆彩蛋'),
            configItem=cfg.useLogin
        )
        
        # Audio card
        self.useAudioCard = SwitchSettingCard(
            FluentIcon.MUSIC,
            self.parent.tr('启用流萤语音'),
            self.parent.tr('使用随机流萤语音彩蛋'),
            configItem=cfg.useAudio
        )
        
        # Add cards to interface
        function_interface.addSettingCard(self.autoCopyCard)
        function_interface.addSettingCard(self.useLoginCard)
        function_interface.addSettingCard(self.useAudioCard)
        
        return function_interface
    
    def create_proxy_interface(self) -> SettingCardGroup:
        """Create proxy settings interface."""
        proxy_interface = SettingCardGroup(self.parent.scrollWidget)
        
        # Proxy card
        self.proxyCard = SwitchSettingCard(
            FluentIcon.CERTIFICATE,
            self.parent.tr('使用代理端口'),
            self.parent.tr('启用代理，在配置文件里更改地址'),
            configItem=cfg.proxyStatus
        )
        
        # Proxy port card
        self.proxyPortCard = LineEditSettingCardPort(
            self.parent.tr('代理端口')
        )
        
        # China mirror card
        self.chinaCard = SwitchSettingCard(
            FluentIcon.CALORIES,
            self.parent.tr('使用国内镜像'),
            self.parent.tr('为Github下载启用国内镜像站链接'),
            configItem=cfg.chinaStatus
        )
        
        # Add cards to interface
        proxy_interface.addSettingCard(self.proxyCard)
        proxy_interface.addSettingCard(self.proxyPortCard)
        proxy_interface.addSettingCard(self.chinaCard)
        
        return proxy_interface
    
    def connect_signals(self):
        """Connect all setting card signals."""
        # Personal interface signals
        self.themeColorCard.colorChanged.connect(
            lambda c: setThemeColor(c, lazy=True))
        self.zoomCard.comboBox.currentIndexChanged.connect(
            self.restart_application)
        self.languageCard.comboBox.currentIndexChanged.connect(
            self.restart_application)
        self.updateOnStartUpCard.clicked.connect(
            lambda: check_update() if self.parent.parent_widget else check_update())
        self.restartCard.clicked.connect(self.restart_application)
        self.configEditorCard.clicked.connect(self.open_config_editor)

        # Function interface signals
        self.autoCopyCard.checkedChanged.connect(
            lambda: self.handle_choice_changed(cfg.autoCopy.value, 
                                              self.parent.tr('自动复制已开启!'), 
                                              self.parent.tr('自动复制已关闭!')))
        self.useLoginCard.checkedChanged.connect(
            lambda: self.handle_choice_changed(cfg.useLogin.value, 
                                              self.parent.tr('登录功能已开启!'), 
                                              self.parent.tr('登录功能已关闭!')))
        self.useAudioCard.checkedChanged.connect(
            lambda: self.handle_choice_changed(cfg.useAudio.value, 
                                              self.parent.tr('流萤语音已开启!'), 
                                              self.parent.tr('流萤语音已关闭!')))

        # Proxy interface signals
        self.proxyCard.checkedChanged.connect(
            lambda: self.handle_proxy_changed(cfg.proxyStatus.value, 
                                             self.parent.tr('代理端口已开启!'), 
                                             self.parent.tr('代理端口已关闭!')))
        self.chinaCard.checkedChanged.connect(
            lambda: self.handle_proxy_changed(cfg.chinaStatus.value, 
                                             self.parent.tr('国内镜像已开启!'), 
                                             self.parent.tr('国内镜像已关闭!')))
        self.proxyPortCard.set_port.connect(self.handle_set_proxy_port)
    
    def restart_application(self):
        """Restart the application."""
        current_process = QProcess()
        current_process.startDetached(sys.executable, sys.argv)
        sys.exit()

    def open_config_editor(self):
        """Open the configuration editor."""
        self.config_editor_dialog = CustomDialog(self.config_editor)
        self.config_editor_dialog.show()

    def handle_choice_changed(self, status, title_true, title_false):
        """Handle toggle setting changes."""
        if status:
            Info(self.parent, 'S', 1000, title_true)
        else:
            Info(self.parent, 'S', 1000, title_false)

    def handle_proxy_changed(self, status, title_true, title_false):
        """Handle proxy setting changes."""
        if status:
            Info(self.parent, 'S', 1000, title_true)
        else:
            Info(self.parent, 'S', 1000, title_false)

        if cfg.chinaStatus.value and cfg.proxyStatus.value:
            Info(self.parent, 'W', 3000, self.parent.tr("代理设置冲突,优先使用国内镜像!"))

        self.init_proxy_info()

    def handle_set_proxy_port(self):
        """Handle proxy port setting."""
        new_port = self.proxyPortCard.port_edit.text()
        if new_port:
            config_path = 'config/config.json'
            with open(config_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                data['PROXY_PORT'] = new_port
            with open(config_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)

            # 复制到剪贴板
            clipboard: QClipboard = QApplication.clipboard()
            clipboard.setText(new_port)
            Info(self.parent, 'S', 1000, self.parent.tr('代理端口已复制到剪贴板!'))

        self.init_proxy_info()

    def init_proxy_info(self):
        """Initialize proxy information display."""
        port = get_json('./config/config.json', 'PROXY_PORT')
        self.proxyPortCard.titleLabel.setText(self.parent.tr(f'代理端口 (当前: {port})'))
        self.proxyPortCard.setDisabled(not cfg.proxyStatus.value)
