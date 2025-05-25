import os
import random
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QStyleOptionViewItem, QLabel, QToolBar,  QDialog, QFormLayout
from PySide6.QtCore import Qt, QSize, QModelIndex, QRect, QTimer
from PySide6.QtGui import QPainter, QFont, QAction
from qfluentwidgets import (TogglePushButton, PrimaryPushButton, setCustomStyleSheet, InfoBarPosition, PushButton, TextEdit, LineEdit,
                            InfoBarIcon, InfoBar, FlowLayout, HorizontalFlipView, FlipImageDelegate, FluentIcon, RoundMenu, Action)
from app.model.config import cfg, Info
from src.icon.astro import AstroIcon


class CustomFlipItemDelegate(FlipImageDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        self.setBorderRadius(35)
        painter.save()
        rect = option.rect()
        rect = QRect(rect.x(), rect.y(), rect.width(), rect.height())
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont(cfg.APP_FONT, 35))
        painter.drawText(rect.adjusted(0, -20, 0, 0),
                         Qt.AlignmentFlag.AlignCenter, cfg.APP_NAME)
        painter.setFont(QFont(cfg.APP_FONT, 20))
        painter.drawText(rect.adjusted(0, 90, 0, 0),
                         Qt.AlignmentFlag.AlignCenter, cfg.APP_VERSION)
        painter.restore()


class ServerButton(TogglePushButton):
    def __init__(self, icon=None, text: str = '', parent=None, **kwargs):  # Added __init__
        super().__init__(icon=icon, text=text, parent=parent, **kwargs)
        self.context_menu_widgets = []  # Initialize context_menu_widgets

    def add_widget(self, widget):
        self.context_menu_widgets.append(widget)

    def remove_widget(self, widget):
        if widget in self.context_menu_widgets:
            self.context_menu_widgets.remove(widget)

    def contextMenuEvent(self, event) -> None:
        menu = RoundMenu(parent=self)
        for widget in self.context_menu_widgets:
            menu.addWidget(widget, selectable=False)

        self.add_custom_actions(menu)
        menu.exec(event.globalPos())

    def add_custom_actions(self, menu):
        """ Override this method to add custom server actions to the menu """
        menu.addSeparator()
        settings_action = Action(FluentIcon.SETTING, '设置')
        restart_action = QAction("重启服务器", self)
        restart_action.triggered.connect(self.restart_server)
        stop_action = QAction("停止服务器", self)
        stop_action.triggered.connect(self.stop_server)
        start_action = QAction("启动服务器", self)
        start_action.triggered.connect(self.start_server)
        menu.addAction(settings_action)
        menu.addAction(restart_action)
        menu.addAction(stop_action)
        menu.addAction(start_action)

    def restart_server(self):
        # 服务器重启逻辑
        print("服务器正在重启...")

    def stop_server(self):
        # 服务器停止逻辑
        print("服务器已停止。")

    def start_server(self):
        # 服务器启动逻辑
        print("服务器已启动。")


class Home(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text)
        self._parent_widget = parent  # Changed: self.parent -> self._parent_widget

        self.initWidgets()
        self.launched_servers = []
        self.monitorTimer = QTimer(self)  # Initialize monitorTimer

    def initWidgets(self):
        self.flipView = HorizontalFlipView()
        self.flipView.addImages(
            ["./src/image/bg_home_1.png", "./src/image/bg_home_2.png", "./src/image/bg_home_3.png"])
        self.flipView.setItemSize(QSize(1160, 350))
        self.flipView.setFixedSize(QSize(1160, 350))
        self.flipView.setCurrentIndex(random.randint(0, 2))
        self.flipView.setItemDelegate(CustomFlipItemDelegate(self.flipView))

        self.button_group = QButtonGroup()
        self.button_group.setExclusive(False)
        for name, details in cfg.SERVER.items():
            icon = FluentIcon.TAG
            if 'ICON' in details and details['ICON']:
                if 'ICON_TYPE' in details and details['ICON_TYPE'] == 'PATH':
                    icon = details['ICON']
                elif 'ICON_TYPE' in details and details['ICON_TYPE'] == 'FLUENT':
                    icon = getattr(FluentIcon, details['ICON'], FluentIcon.TAG)
                elif 'ICON_TYPE' in details and details['ICON_TYPE'] == 'ASTRO':
                    icon = getattr(AstroIcon, details['ICON'], FluentIcon.TAG)
                else:
                    # If ICON_TYPE is missing or unknown, but ICON is present, this might be an issue.
                    # For now, assuming it falls through or ICON is not set.
                    pass  # Or set a default icon if ICON is present but type is wrong
            button_server = ServerButton(icon, '   ' + name, self)
            button_server.setObjectName(name)
            button_server.setFixedSize(270, 70)
            button_server.setIconSize(QSize(24, 24))
            button_server.setFont(QFont(f'{cfg.APP_FONT}', 12))
            setCustomStyleSheet(
                button_server, 'PushButton{border-radius: 12px}', 'PushButton{border-radius: 12px}')

            # profile_card = ProfileCard(
            #     details['ICON'], name, details['COMMAND'], self)
            # button_server.add_widget(profile_card)

            self.button_group.addButton(button_server)

        self.button_toggle = PrimaryPushButton(
            FluentIcon.PLAY_SOLID, self.tr(' 一键启动'))
        self.button_toggle.setFixedSize(200, 65)
        self.button_toggle.setIconSize(QSize(20, 20))
        self.button_toggle.setFont(QFont(f'{cfg.APP_FONT}', 18))
        setCustomStyleSheet(
            self.button_toggle, 'PushButton{border-radius: 12px}', 'PushButton{border-radius: 12px}')

        self.toolbar = QToolBar(self)
        self.toolbar.setVisible(False)

        self.initLayout()
        self.connectSignalToSlot()

    def initLayout(self):
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.flipView)
        # Changed: Qt.AlignHCenter -> Qt.AlignmentFlag.AlignHCenter
        image_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        button_layout = FlowLayout(needAni=True)
        button_layout.setVerticalSpacing(30)
        button_layout.setHorizontalSpacing(30)
        for button in self.button_group.buttons():
            button_layout.addWidget(button)

        play_layout = QHBoxLayout()
        play_layout.addSpacing(15)
        play_layout.addLayout(button_layout)
        play_layout.addSpacing(300)

        button_toggle_layout = QHBoxLayout()
        # Changed: Qt.AlignRight -> Qt.AlignmentFlag.AlignRight
        button_toggle_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        button_toggle_layout.addWidget(self.button_toggle)
        button_toggle_layout.setContentsMargins(0, 0, 25, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 30, 10, 10)
        main_layout.addLayout(image_layout)
        main_layout.addSpacing(25)
        main_layout.addLayout(play_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(button_toggle_layout)
        main_layout.addSpacing(25)
        main_layout.addWidget(self.toolbar)

    def connectSignalToSlot(self):
        self.scrollTimer = QTimer(self)
        self.scrollTimer.timeout.connect(
            lambda: self.flipView.setCurrentIndex(random.randint(0, 2)))
        self.scrollTimer.start(5000)
        self.button_toggle.clicked.connect(self.handleToggle)

    def handleToggle(self):
        if self.launched_servers:
            self.handleStopAllServers()
        else:
            self.handleServerLaunch()

    def handleServerLaunch(self):
        selected_servers = self.button_group.buttons()
        launched_servers_this_run = []
        for server in selected_servers:
            if server.isChecked() and server.objectName() not in self.launched_servers:
                name = server.objectName()
                if os.path.exists(f'./server/{name}'):
                    command = cfg.SERVER[name]['COMMAND']
                    subprocess.run(command, shell=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.launched_servers.append(name)
                    launched_servers_this_run.append(name)
                    server.setStyleSheet(
                        'background-color: #4CAF50; color: white;')
                    self.addToolBarActions(name)
                else:
                    self.showErrorInfoBar(name)

        if launched_servers_this_run:
            Info(self, 'S', 1000, self.tr(
                f"服务端 {', '.join(launched_servers_this_run)} 已启动!"))
            self.button_toggle.setText(self.tr(' 停止全部'))
            self.button_toggle.setIcon(FluentIcon.CLOSE)
            self.toolbar.setVisible(True)

            # Start monitoring server status
            if not self.monitorTimer.isActive():
                self.monitorTimer.timeout.connect(self.monitorServerStatus)
                self.monitorTimer.start(10000)  # Every 10 seconds

    def handleStopAllServers(self):
        for server_name in list(self.launched_servers):  # Iterate over a copy
            self.stopServer(server_name)
        self.launched_servers.clear()
        for button in self.button_group.buttons():
            button.setChecked(False)
            button.setStyleSheet('')

        Info(self, 'S', 1000, self.tr("所有服务端已停止!"))
        self.button_toggle.setText(self.tr(' 一键启动'))
        self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
        self.toolbar.clear()
        self.toolbar.setVisible(False)

        if self.monitorTimer.isActive():
            self.monitorTimer.stop()
            # Disconnect to prevent multiple connections if started again
            try:
                self.monitorTimer.timeout.disconnect(self.monitorServerStatus)
            except RuntimeError:  # disconnect may fail if not connected or already disconnected
                pass

    def stopServer(self, server_name):
        if server_name in cfg.SERVER and 'STOP_COMMAND' in cfg.SERVER[server_name]:
            command = cfg.SERVER[server_name]['STOP_COMMAND']
            subprocess.run(command, shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print(f"Warning: No STOP_COMMAND configured for {server_name}")

    def showErrorInfoBar(self, name):
        server_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.tr('找不到服务端') + name + '!',
            content='',
            # Changed: Qt.Horizontal -> Qt.Orientation.Horizontal
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # Example, ensure this matches your actual page indices
        server_page = {'LunarCore': 3}
        if name in server_page and self._parent_widget and hasattr(self._parent_widget, 'stackedWidget'):
            page_index = server_page[name]
            server_error_button = PrimaryPushButton(
                self.tr('前往下载'))
            server_error_button.clicked.connect(
                lambda: self._parent_widget.stackedWidget.setCurrentIndex(page_index))  # Changed: self.parent -> self._parent_widget
            server_error.addWidget(server_error_button)
            server_error.show()
        else:
            server_error.show()

    def addToolBarActions(self, server_name):
        # Clear existing actions for this server_name to prevent duplicates if called multiple times
        # This requires actions to be identifiable or manage them in a dictionary
        # For simplicity, current code might add duplicate actions if this method is called again for the same server.
        # A more robust solution would be to store actions and remove old ones before adding.

        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(lambda s=server_name: self.showLog(s))
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda s=server_name: self.stopSingleServer(s))
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(
            lambda s=server_name: self.modifyConfig(s))
        self.toolbar.addAction(action_config)

    def showLog(self, server_name):
        log_dialog = QDialog(self)
        log_dialog.setWindowTitle(self.tr(f"{server_name} 日志"))
        log_layout = QVBoxLayout(log_dialog)
        log_text = TextEdit(log_dialog)
        log_text.setReadOnly(True)
        log_text.setText(self.readLog(server_name))
        log_layout.addWidget(log_text)
        log_dialog.setLayout(log_layout)
        log_dialog.exec()

    def readLog(self, server_name):
        log_path = f'./logs/{server_name}.log'
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as file:  # Added encoding
                    return file.read()
            except Exception as e:
                return self.tr("读取日志文件失败: ") + str(e)
        else:
            return self.tr("日志文件不存在")

    def stopSingleServer(self, server_name):
        if server_name in self.launched_servers:
            self.stopServer(server_name)
            self.launched_servers.remove(server_name)

            # Update button state
            for button in self.button_group.buttons():
                if button.objectName() == server_name:
                    button.setChecked(False)
                    button.setStyleSheet('')
                    break

            Info(self, 'S', 1000, self.tr(f"{server_name} 已停止!"))

            # Remove actions for this server from toolbar
            actions_to_remove = []
            for action in self.toolbar.actions():
                if server_name in action.text():  # Simple check, might need refinement
                    actions_to_remove.append(action)
            for action in actions_to_remove:
                self.toolbar.removeAction(action)

            if not self.launched_servers:
                self.button_toggle.setText(self.tr(' 一键启动'))
                self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
                self.toolbar.clear()  # Clear all if no servers are running
                self.toolbar.setVisible(False)
                if self.monitorTimer.isActive():
                    self.monitorTimer.stop()
                    try:
                        self.monitorTimer.timeout.disconnect(
                            self.monitorServerStatus)
                    except RuntimeError:
                        pass

    def modifyConfig(self, server_name):
        config_dialog = QDialog(self)
        config_dialog.setWindowTitle(self.tr(f"{server_name} 配置"))
        config_layout = QVBoxLayout(config_dialog)

        form_layout = QFormLayout()
        config_path = f'./config/{server_name}.cfg'
        self.config_fields = {}  # Initialize here to ensure it's fresh for this dialog

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as file:  # Added encoding
                    lines = file.readlines()
                    for line in lines:
                        line = line.strip()
                        # Check for '=' and ignore comments
                        if '=' in line and not line.startswith('#'):
                            # Split only on first '='
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            line_edit = LineEdit(value)
                            self.config_fields[key] = line_edit
                            form_layout.addRow(QLabel(key), line_edit)
            except Exception as e:
                Info(self, 'E', 3000, self.tr(f"读取配置文件失败: {e}"))

        save_button = PushButton(self.tr("保存"))
        save_button.clicked.connect(
            lambda: self.saveConfig(server_name, config_path, config_dialog))  # Pass dialog to close it

        config_layout.addLayout(form_layout)
        config_layout.addWidget(save_button)
        config_dialog.setLayout(config_layout)
        config_dialog.exec()

    def saveConfig(self, server_name, config_path, dialog_to_close):
        try:
            with open(config_path, 'w', encoding='utf-8') as file:  # Added encoding
                for key, line_edit in self.config_fields.items():
                    file.write(f"{key}={line_edit.text()}\n")
            Info(self, 'S', 1000, self.tr(f"{server_name} 配置已保存!"))
            if dialog_to_close:
                dialog_to_close.accept()
        except Exception as e:
            Info(self, 'E', 3000, self.tr(f"保存配置失败: {e}"))

    def monitorServerStatus(self):
        # Iterate over a copy as restartServer might be called
        for server_name in list(self.launched_servers):
            status = self.checkServerStatus(server_name)
            if not status:
                Info(self, 'E', 3000, self.tr(f"{server_name} 崩溃，正在重启..."))
                self.restartServer(server_name)

    # Changed: server_name -> _server_name
    def checkServerStatus(self, _server_name):
        # Placeholder: Implement actual server status check logic.
        # For example, ping the server, check if a port is open, or query a status endpoint.
        # _server_name can be used to get specific server details (e.g., port, host) from cfg.SERVER
        # print(f"Checking status for {_server_name}") # Debug print
        return True  # Defaulting to True, replace with actual logic

    def restartServer(self, server_name):
        if server_name in cfg.SERVER and 'COMMAND' in cfg.SERVER[server_name]:
            command = cfg.SERVER[server_name]['COMMAND']
            subprocess.run(command, shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            Info(self, 'S', 1000, self.tr(f"{server_name} 已重启!"))
        else:
            Info(self, 'E', 3000, self.tr(f"无法重启 {server_name}: 未找到命令配置"))
