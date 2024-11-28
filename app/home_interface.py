import os
import random
import subprocess
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QStyleOptionViewItem, QLabel, QToolBar,  QDialog, QFormLayout
from PySide6.QtCore import Qt, QSize, QModelIndex, QRect, QTimer
from PySide6.QtGui import QPainter, QFont, QAction, QClipboard
from qfluentwidgets import (TogglePushButton, PrimaryPushButton, setCustomStyleSheet, InfoBarPosition, PushButton,TextEdit,LineEdit,
                            InfoBarIcon, InfoBar, FlowLayout, HorizontalFlipView, FlipImageDelegate, FluentIcon, RoundMenu, Action,
                            AvatarWidget)
from app.model.config import cfg, Info
from src.icon.astro import AstroIcon

class CustomFlipItemDelegate(FlipImageDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        self.setBorderRadius(35)
        painter.save()
        rect = option.rect
        rect = QRect(rect.x(), rect.y(), rect.width(), rect.height())
        painter.setPen(Qt.white)
        painter.setFont(QFont(cfg.APP_FONT, 35))
        painter.drawText(rect.adjusted(0, -20, 0, 0),
                         Qt.AlignCenter, cfg.APP_NAME)
        painter.setFont(QFont(cfg.APP_FONT, 20))
        painter.drawText(rect.adjusted(0, 90, 0, 0),
                         Qt.AlignCenter, cfg.APP_VERSION)
        painter.restore()

class ServerButton(TogglePushButton):

    def ensure_variable(self, var_name, default_value=None):
        if not hasattr(self, var_name):
            setattr(self, var_name, default_value)

    def add_widget(self, widget):
        self.ensure_variable('context_menu_widgets', [])
        self.context_menu_widgets.append(widget)

    def remove_widget(self, widget):
        self.ensure_variable('context_menu_widgets', [])
        if widget in self.context_menu_widgets:
            self.context_menu_widgets.remove(widget)

    def contextMenuEvent(self, event) -> None:
        self.ensure_variable('context_menu_widgets', [])
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
        self.parent = parent

        self.initWidgets()
        self.launched_servers = []

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
                    continue
            button_server = ServerButton(icon, '   ' + name, self)
            button_server.setObjectName(name)
            button_server.setFixedSize(270, 70)
            button_server.setIconSize(QSize(24, 24))
            button_server.setFont(QFont(f'{cfg.APP_FONT}', 12))
            setCustomStyleSheet(
                button_server, 'PushButton{border-radius: 12px}', 'PushButton{border-radius: 12px}')
            
            #profile_card = ProfileCard(
           #     details['ICON'], name, details['COMMAND'], self)
            #button_server.add_widget(profile_card)

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
        image_layout.setAlignment(Qt.AlignHCenter)

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
        button_toggle_layout.setAlignment(Qt.AlignRight)
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
        launched_servers = []
        for server in selected_servers:
            if server.isChecked() and server.objectName() not in self.launched_servers:
                name = server.objectName()
                if os.path.exists(f'./server/{name}'):
                    command = cfg.SERVER[name]['COMMAND']
                    subprocess.run(command, shell=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.launched_servers.append(name)
                    launched_servers.append(name)
                    server.setStyleSheet(
                        'background-color: #4CAF50; color: white;')
                    self.addToolBarActions(name)
                else:
                    self.showErrorInfoBar(name)

        if launched_servers:
            Info(self, 'S', 1000, self.tr(
                f"服务端 {', '.join(launched_servers)} 已启动!"))
            self.button_toggle.setText(self.tr(' 停止全部'))
            self.button_toggle.setIcon(FluentIcon.CLOSE)
            self.toolbar.setVisible(True)

    def handleStopAllServers(self):
        for server_name in self.launched_servers:
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

    def stopServer(self, server_name):
        command = cfg.SERVER[server_name]['STOP_COMMAND']
        subprocess.run(command, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)

    def showErrorInfoBar(self, name):
        server_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.tr('找不到服务端') + name + '!',
            content='',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        server_page = {'LunarCore': 3}
        if name in server_page:
            page_index = server_page[name]
            server_error_button = PrimaryPushButton(
                self.tr('前往下载'))
            server_error_button.clicked.connect(
                lambda: self.parent.stackedWidget.setCurrentIndex(page_index))
            server_error.addWidget(server_error_button)
            server_error.show()
        else:
            server_error.show()

    def addToolBarActions(self, server_name):
        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(lambda: self.showLog(server_name))
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda: self.stopSingleServer(server_name))
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(lambda: self.modifyConfig(server_name))
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
            with open(log_path, 'r') as file:
                return file.read()
        else:
            return self.tr("日志文件不存在")

    def stopSingleServer(self, server_name):
        if server_name in self.launched_servers:
            self.stopServer(server_name)
            self.launched_servers.remove(server_name)
            for button in self.button_group.buttons():
                if button.objectName() == server_name:
                    button.setChecked(False)
                    button.setStyleSheet('')
            Info(self, 'S', 1000, self.tr(f"{server_name} 已停止!"))
            if not self.launched_servers:
                self.button_toggle.setText(self.tr(' 一键启动'))
                self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
                self.toolbar.clear()
                self.toolbar.setVisible(False)

    def modifyConfig(self, server_name):
        config_dialog = QDialog(self)
        config_dialog.setWindowTitle(self.tr(f"{server_name} 配置"))
        config_layout = QVBoxLayout(config_dialog)

        form_layout = QFormLayout()
        config_path = f'./config/{server_name}.cfg'
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                lines = file.readlines()
                self.config_fields = {}
                for line in lines:
                    key, value = line.strip().split('=')
                    line_edit = LineEdit(value)
                    self.config_fields[key] = line_edit
                    form_layout.addRow(QLabel(key), line_edit)

        save_button = PushButton(self.tr("保存"))
        save_button.clicked.connect(
            lambda: self.saveConfig(server_name, config_path))

        config_layout.addLayout(form_layout)
        config_layout.addWidget(save_button)
        config_dialog.setLayout(config_layout)
        config_dialog.exec()

    def saveConfig(self, server_name, config_path):
        with open(config_path, 'w') as file:
            for key, line_edit in self.config_fields.items():
                file.write(f"{key}={line_edit.text()}\n")
        Info(self, 'S', 1000, self.tr(f"{server_name} 配置已保存!"))

    def monitorServerStatus(self):
        for server_name in self.launched_servers:
            status = self.checkServerStatus(server_name)
            if not status:
                Info(self, 'E', 1000, self.tr(f"{server_name} 崩溃，正在重启..."))
                self.restartServer(server_name)

    def checkServerStatus(self, server_name):
        # 实现服务器状态检查逻辑，返回 True 表示运行中，False 表示已停止。
        # 这里可以使用 ping 命令、端口检查等方式实现。
        return True

    def restartServer(self, server_name):
        command = cfg.SERVER[server_name]['COMMAND']
        subprocess.run(command, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        Info(self, 'S', 1000, self.tr(f"{server_name} 已重启!"))

    def handleToggle(self):
        if self.launched_servers:
            self.handleStopAllServers()
        else:
            self.handleServerLaunch()

    def handleServerLaunch(self):
        selected_servers = self.button_group.buttons()
        launched_servers = []
        for server in selected_servers:
            if server.isChecked() and server.objectName() not in self.launched_servers:
                name = server.objectName()
                if os.path.exists(f'./server/{name}'):
                    command = cfg.SERVER[name]['COMMAND']
                    subprocess.run(command, shell=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.launched_servers.append(name)
                    launched_servers.append(name)
                    server.setStyleSheet(
                        'background-color: #4CAF50; color: white;')
                    self.addToolBarActions(name)
                else:
                    self.showErrorInfoBar(name)

        if launched_servers:
            Info(self, 'S', 1000, self.tr(
                f"服务端 {', '.join(launched_servers)} 已启动!"))
            self.button_toggle.setText(self.tr(' 停止全部'))
            self.button_toggle.setIcon(FluentIcon.CLOSE)
            self.toolbar.setVisible(True)

    def handleStopAllServers(self):
        for server_name in self.launched_servers:
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

    def stopServer(self, server_name):
        command = cfg.SERVER[server_name]['STOP_COMMAND']
        subprocess.run(command, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)

    def showErrorInfoBar(self, name):
        server_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.tr('找不到服务端') + name + '!',
            content='',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        server_page = {'LunarCore': 3}
        if name in server_page:
            page_index = server_page[name]
            server_error_button = PrimaryPushButton(
                self.tr('前往下载'))
            server_error_button.clicked.connect(
                lambda: self.parent.stackedWidget.setCurrentIndex(page_index))
            server_error.addWidget(server_error_button)
            server_error.show()
        else:
            server_error.show()

    def addToolBarActions(self, server_name):
        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(lambda: self.showLog(server_name))
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda: self.stopSingleServer(server_name))
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(lambda: self.modifyConfig(server_name))
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
            with open(log_path, 'r') as file:
                return file.read()
        else:
            return self.tr("日志文件不存在")

    def stopSingleServer(self, server_name):
        if server_name in self.launched_servers:
            self.stopServer(server_name)
            self.launched_servers.remove(server_name)
            for button in self.button_group.buttons():
                if button.objectName() == server_name:
                    button.setChecked(False)
                    button.setStyleSheet('')
            Info(self, 'S', 1000, self.tr(f"{server_name} 已停止!"))
            if not self.launched_servers:
                self.button_toggle.setText(self.tr(' 一键启动'))
                self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
                self.toolbar.clear()
                self.toolbar.setVisible(False)

    def modifyConfig(self, server_name):
        config_dialog = QDialog(self)
        config_dialog.setWindowTitle(self.tr(f"{server_name} 配置"))
        config_layout = QVBoxLayout(config_dialog)

        form_layout = QFormLayout()
        config_path = f'./config/{server_name}.cfg'
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                lines = file.readlines()
                self.config_fields = {}
                for line in lines:
                    key, value = line.strip().split('=')
                    line_edit = LineEdit(value)
                    self.config_fields[key] = line_edit
                    form_layout.addRow(QLabel(key), line_edit)

        save_button = PushButton(self.tr("保存"))
        save_button.clicked.connect(
            lambda: self.saveConfig(server_name, config_path))

        config_layout.addLayout(form_layout)
        config_layout.addWidget(save_button)
        config_dialog.setLayout(config_layout)
        config_dialog.exec()

    def saveConfig(self, server_name, config_path):
        with open(config_path, 'w') as file:
            for key, line_edit in self.config_fields.items():
                file.write(f"{key}={line_edit.text()}\n")
        Info(self, 'S', 1000, self.tr(f"{server_name} 配置已保存!"))

    def monitorServerStatus(self):
        for server_name in self.launched_servers:
            status = self.checkServerStatus(server_name)
            if not status:
                Info(self, 'E', 1000, self.tr(f"{server_name} 崩溃，正在重启..."))
                self.restartServer(server_name)

    def checkServerStatus(self, server_name):
        # 实现服务器状态检查逻辑，返回 True 表示运行中，False 表示已停止。
        # 这里可以使用 ping 命令、端口检查等方式实现。
        return True

    def restartServer(self, server_name):
        command = cfg.SERVER[server_name]['COMMAND']
        subprocess.run(command, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        Info(self, 'S', 1000, self.tr(f"{server_name} 已重启!"))

    def handleToggle(self):
        if self.launched_servers:
            self.handleStopAllServers()
        else:
            self.handleServerLaunch()

    def handleServerLaunch(self):
        selected_servers = self.button_group.buttons()
        launched_servers = []
        for server in selected_servers:
            if server.isChecked() and server.objectName() not in self.launched_servers:
                name = server.objectName()
                if os.path.exists(f'./server/{name}'):
                    command = cfg.SERVER[name]['COMMAND']
                    subprocess.run(command, shell=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.launched_servers.append(name)
                    launched_servers.append(name)
                    server.setStyleSheet(
                        'background-color: #4CAF50; color: white;')
                    self.addToolBarActions(name)
                else:
                    self.showErrorInfoBar(name)

        if launched_servers:
            Info(self, 'S', 1000, self.tr(
                f"服务端 {', '.join(launched_servers)} 已启动!"))
            self.button_toggle.setText(self.tr(' 停止全部'))
            self.button_toggle.setIcon(FluentIcon.CLOSE)
            self.toolbar.setVisible(True)

            # 开始监控服务器状态
            self.monitorTimer = QTimer(self)
            self.monitorTimer.timeout.connect(self.monitorServerStatus)
            self.monitorTimer.start(10000)  # 每10秒检查一次

    def handleStopAllServers(self):
        for server_name in self.launched_servers:
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

        if hasattr(self, 'monitorTimer'):
            self.monitorTimer.stop()

    def stopServer(self, server_name):
        command = cfg.SERVER[server_name]['STOP_COMMAND']
        subprocess.run(command, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)

    def showErrorInfoBar(self, name):
        server_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.tr('找不到服务端') + name + '!',
            content='',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        server_page = {'LunarCore': 3}
        if name in server_page:
            page_index = server_page[name]
            server_error_button = PrimaryPushButton(
                self.tr('前往下载'))
            server_error_button.clicked.connect(
                lambda: self.parent.stackedWidget.setCurrentIndex(page_index))
            server_error.addWidget(server_error_button)
            server_error.show()
        else:
            server_error.show()

    def addToolBarActions(self, server_name):
        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(lambda: self.showLog(server_name))
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda: self.stopSingleServer(server_name))
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(lambda: self.modifyConfig(server_name))
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
            with open(log_path, 'r') as file:
                return file.read()
        else:
            return self.tr("日志文件不存在")

    def stopSingleServer(self, server_name):
        if server_name in self.launched_servers:
            self.stopServer(server_name)
            self.launched_servers.remove(server_name)
            for button in self.button_group.buttons():
                if button.objectName() == server_name:
                    button.setChecked(False)
                    button.setStyleSheet('')
            Info(self, 'S', 1000, self.tr(f"{server_name} 已停止!"))
            if not self.launched_servers:
                self.button_toggle.setText(self.tr(' 一键启动'))
                self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
                self.toolbar.clear()
                self.toolbar.setVisible(False)

    def modifyConfig(self, server_name):
        config_dialog = QDialog(self)
        config_dialog.setWindowTitle(self.tr(f"{server_name} 配置"))
        config_layout = QVBoxLayout(config_dialog)

        form_layout = QFormLayout()
        config_path = f'./config/{server_name}.cfg'
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                lines = file.readlines()
                self.config_fields = {}
                for line in lines:
                    key, value = line.strip().split('=')
                    line_edit = LineEdit(value)
                    self.config_fields[key] = line_edit
                    form_layout.addRow(QLabel(key), line_edit)

        save_button = PushButton(self.tr("保存"))
        save_button.clicked.connect(
            lambda: self.saveConfig(server_name, config_path))

        config_layout.addLayout(form_layout)
        config_layout.addWidget(save_button)
        config_dialog.setLayout(config_layout)
        config_dialog.exec()

    def saveConfig(self, server_name, config_path):
        with open(config_path, 'w') as file:
            for key, line_edit in self.config_fields.items():
                file.write(f"{key}={line_edit.text()}\n")
        Info(self, 'S', 1000, self.tr(f"{server_name} 配置已保存!"))

    def monitorServerStatus(self):
        for server_name in self.launched_servers:
            status = self.checkServerStatus(server_name)
            if not status:
                Info(self, 'E', 1000, self.tr(f"{server_name} 崩溃，正在重启..."))
                self.restartServer(server_name)

    def checkServerStatus(self, server_name):
        # 实现服务器状态检查逻辑，返回 True 表示运行中，False 表示已停止。
        # 这里可以使用 ping 命令、端口检查等方式实现。
        return True

    def restartServer(self, server_name):
        command = cfg.SERVER[server_name]['COMMAND']
        subprocess.run(command, shell=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        Info(self, 'S', 1000, self.tr(f"{server_name} 已重启!"))
