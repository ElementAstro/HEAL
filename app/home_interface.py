import os
import random
from typing import Optional, List, Dict, Any, Union
from PySide6.QtCore import Qt, QSize, QModelIndex, QTimer, QRect
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QStyleOptionViewItem, QLabel, QToolBar, QDialog, QFormLayout
from PySide6.QtCore import Qt, QSize, QModelIndex, QTimer
from PySide6.QtGui import QPainter, QFont, QAction
from qfluentwidgets import (TogglePushButton, PrimaryPushButton, setCustomStyleSheet, InfoBarPosition, PushButton, TextEdit, LineEdit,
                            InfoBarIcon, InfoBar, FlowLayout, HorizontalFlipView, FlipImageDelegate, FluentIcon, RoundMenu, Action)
from app.model.config import cfg, Info
from app.model.process_manager import ProcessManager
from app.common.exception_handler import ExceptionHandler
from src.icon.astro import AstroIcon

# 定义常量避免重复
BUTTON_BORDER_RADIUS_STYLE = 'PushButton{border-radius: 12px}'
ONE_CLICK_START_TEXT = ' 一键启动'
STOP_ALL_TEXT = ' 停止全部'


class CustomFlipItemDelegate(FlipImageDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # Draw using parent's implementation first
        super().paint(painter, option, index)
        self.setBorderRadius(35)
        
        painter.save()
        
        # Create rect without accessing device properties
        viewport = painter.viewport()
        item_rect = QRect(0, 0, viewport.width(), viewport.height())

        painter.setPen(Qt.GlobalColor.white)

        # 绘制应用程序名称
        painter.setFont(QFont(cfg.APP_FONT, 35))
        # QRect.adjusted() 方法返回一个新的 QRect，因此 item_rect 本身不会被修改。
        painter.drawText(item_rect.adjusted(0, -20, 0, 0),
                         Qt.AlignmentFlag.AlignCenter, cfg.APP_NAME)

        # 绘制应用程序版本
        painter.setFont(QFont(cfg.APP_FONT, 20))
        painter.drawText(item_rect.adjusted(0, 90, 0, 0),
                         Qt.AlignmentFlag.AlignCenter, cfg.APP_VERSION)

        painter.restore()


class ServerButton(TogglePushButton):
    """Custom server control button."""
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        if args and isinstance(args[0], QWidget):
            instance.setParent(args[0])
        elif 'parent' in kwargs and kwargs['parent']:
            instance.setParent(kwargs['parent'])
        return instance

    def contextMenuEvent(self, event) -> None:  # type: ignore
        """Handle context menu event."""
        menu = RoundMenu(parent=self)
        menu.addSeparator()
        
        settings = Action(FluentIcon.SETTING, '设置', parent=self)
        restart = Action(icon=None, text="重启服务器", parent=self)
        stop = Action(icon=None, text="停止服务器", parent=self)
        start = Action(icon=None, text="启动服务器", parent=self)
        
        restart.triggered.connect(lambda: self._print_status("正在重启"))
        stop.triggered.connect(lambda: self._print_status("已停止"))
        start.triggered.connect(lambda: self._print_status("已启动"))
        
        menu.addActions([settings, restart, stop, start])
        menu.exec(event.globalPos())

    def _print_status(self, status: str) -> None:
        print(f"服务器 {self.objectName()} {status}。")
        self.context_menu_widgets: List[QWidget] = []

    def add_widget(self, widget: QWidget):
        """添加组件到上下文菜单"""
        self.context_menu_widgets.append(widget)

    def remove_widget(self, widget: QWidget):
        """从上下文菜单移除组件"""
        if widget in self.context_menu_widgets:
            self.context_menu_widgets.remove(widget)

    def contextMenuEvent(self, event) -> None:
        """显示上下文菜单"""
        menu = RoundMenu(parent=self)
        for widget in self.context_menu_widgets:
            menu.addWidget(widget, selectable=False)

        self.add_custom_actions(menu)
        menu.exec(event.globalPos())

    def add_custom_actions(self, menu: RoundMenu):
        """添加自定义服务器操作到菜单"""
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
        """重启服务器"""
        print(f"服务器 {self.objectName()} 正在重启...")

    def stop_server(self):
        """停止服务器"""
        print(f"服务器 {self.objectName()} 已停止。")

    def start_server(self):
        """启动服务器"""
        print(f"服务器 {self.objectName()} 已启动。")


class Home(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text)
        self._parent_widget = parent

        # Initialize ProcessManager and ExceptionHandler
        self.process_manager = ProcessManager()
        self.exception_handler = ExceptionHandler()
        
        self.initWidgets()
        self.launched_servers: List[str] = []
        self.monitorTimer = QTimer(self)
        
        # Connect ProcessManager signals
        self.process_manager.process_started.connect(self.on_process_started)
        self.process_manager.process_stopped.connect(self.on_process_stopped)
        self.process_manager.process_crashed.connect(self.on_process_crashed)
        
        # 修复：检查是否存在 process_restarted 信号
        if hasattr(self.process_manager, 'process_restarted'):
            self.process_manager.process_restarted.connect(self.on_process_restarted)

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
        
        self._create_server_buttons()
        self._create_toggle_button()
        
        self.toolbar = QToolBar(self)
        self.toolbar.setVisible(False)

        self.initLayout()
        self.connectSignalToSlot()

    def _create_server_buttons(self):
        """创建服务器按钮"""
        for name, details in cfg.SERVER.items():
            icon = self._get_server_icon(details)
            
            button_server = ServerButton(self)
            button_server.setIcon(icon)
            button_server.setText('   ' + name)
            button_server.setObjectName(name)
            button_server.setFixedSize(270, 70)
            button_server.setIconSize(QSize(24, 24))
            button_server.setFont(QFont(f'{cfg.APP_FONT}', 12))
            setCustomStyleSheet(
                button_server, BUTTON_BORDER_RADIUS_STYLE, BUTTON_BORDER_RADIUS_STYLE)

            self.button_group.addButton(button_server)

    def _get_server_icon(self, details: Dict[str, Any]):
        """获取服务器图标"""
        icon = FluentIcon.TAG
        # 修复：合并if语句
        if 'ICON' in details and details['ICON'] and 'ICON_TYPE' in details:
            icon_type = details['ICON_TYPE']
            if icon_type == 'PATH':
                icon = details['ICON']
            elif icon_type == 'FLUENT':
                icon = getattr(FluentIcon, details['ICON'], FluentIcon.TAG)
            elif icon_type == 'ASTRO':
                icon = getattr(AstroIcon, details['ICON'], FluentIcon.TAG)
            # 移除空的 else 块，提供默认处理
        elif 'ICON' in details and details['ICON']: # 处理只有 ICON 没有 ICON_TYPE 的情况
            icon = details['ICON']
        return icon

    def _create_toggle_button(self):
        """创建切换按钮"""
        self.button_toggle = PrimaryPushButton(
            FluentIcon.PLAY_SOLID, self.tr(ONE_CLICK_START_TEXT))
        self.button_toggle.setFixedSize(200, 65)
        self.button_toggle.setIconSize(QSize(20, 20))
        self.button_toggle.setFont(QFont(f'{cfg.APP_FONT}', 18))
        setCustomStyleSheet(
            self.button_toggle, BUTTON_BORDER_RADIUS_STYLE, BUTTON_BORDER_RADIUS_STYLE)

    def initLayout(self):
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.flipView)
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
        """修复：降低认知复杂度，分解为更小的函数"""
        selected_servers = self._get_selected_servers()
        launched_servers_this_run = []
        
        for server_button in selected_servers: # Renamed server to server_button for clarity
            if self._should_launch_server(server_button):
                success = self._launch_single_server(server_button)
                if success:
                    launched_servers_this_run.append(server_button.objectName())

        if launched_servers_this_run:
            self._update_ui_after_launch(launched_servers_this_run)

    def _get_selected_servers(self) -> List[TogglePushButton]:
        """获取选中的服务器按钮"""
        return [button for button in self.button_group.buttons()
                if isinstance(button, TogglePushButton) and button.isChecked()]

    def _should_launch_server(self, server: TogglePushButton) -> bool:
        """检查是否应该启动服务器"""
        return server.objectName() not in self.launched_servers

    def _launch_single_server(self, server: TogglePushButton) -> bool:
        """启动单个服务器"""
        name = server.objectName()
        server_path = f'./server/{name}'
        
        if not os.path.exists(server_path):
            self.showErrorInfoBar(name)
            return False
            
        try:
            # 修复：使用这些变量，即使只是日志记录
            server_config = cfg.SERVER[name]
            command = server_config.get('COMMAND', '')
            working_dir = server_path
            
            # 记录启动信息
            print(f"Starting server {name} with command: {command} in directory: {working_dir}")
            
            success = self.process_manager.start_process(name)  # Assuming start_process only takes process name
            
            if not success:
                self._handle_server_start_failure(server, name)
                return False
                
            return True
            
        except Exception as e:
            self._handle_server_start_exception(server, name, e)
            return False

    def _handle_server_start_failure(self, server: TogglePushButton, name: str):
        """处理服务器启动失败"""
        self.exception_handler.handle_known_exception(
            RuntimeError(f"Failed to start server {name}"),
            exc_type="process_error",
            severity="medium",
            user_message=f"无法启动服务器 {name}",
            parent_widget=self
        )
        server.setChecked(False)

    def _handle_server_start_exception(self, server: TogglePushButton, name: str, exception: Exception):
        """处理服务器启动异常"""
        self.exception_handler.handle_known_exception(
            exception,
            exc_type="process_error",
            severity="medium",
            user_message=f"启动服务器 {name} 时发生错误",
            parent_widget=self
        )
        server.setChecked(False)

    def _update_ui_after_launch(self, launched_servers: List[str]):
        """启动后更新UI"""
        Info(self, 'S', 1000, self.tr(
            f"服务端 {', '.join(launched_servers)} 启动中..."))
        self.button_toggle.setText(self.tr(STOP_ALL_TEXT))
        self.button_toggle.setIcon(FluentIcon.CLOSE)
        self.toolbar.setVisible(True)

    def handleStopAllServers(self):
        # Use ProcessManager to stop all launched servers
        for server_name in list(self.launched_servers): # Iterate over a copy
            self.process_manager.stop_process(server_name)
        
        # UI updates will be handled by on_process_stopped signal
        # Reset toggle button immediately for responsiveness
        self.button_toggle.setText(self.tr(ONE_CLICK_START_TEXT))
        self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
        self.toolbar.clear()
        self.toolbar.setVisible(False)
        Info(self, 'S', 1000, self.tr("正在停止所有服务端..."))


    def stopServer(self, server_name: str):
        """Stop a specific server using ProcessManager"""
        try:
            self.process_manager.stop_process(server_name)
        except Exception as e:
            self.exception_handler.handle_known_exception(
                e,
                exc_type="process_error",
                severity="medium",
                user_message=f"停止服务器 {server_name} 时发生错误",
                parent_widget=self
            )

    def showErrorInfoBar(self, name: str):
        server_error = InfoBar(
            icon=InfoBarIcon.ERROR,
            title=self.tr('找不到服务端') + name + '!',
            content='',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        server_page = {'LunarCore': 3} # Example, adjust as needed
        # 修复：添加完整的类型检查
        if (name in server_page and
                self._parent_widget is not None and
                hasattr(self._parent_widget, 'stackedWidget') and
                self._parent_widget.stackedWidget is not None):
            
            page_index = server_page[name]
            server_error_button = PrimaryPushButton(self.tr('前往下载'))
            # Ensure _parent_widget and its stackedWidget are valid before connecting
            current_parent_widget = self._parent_widget # Capture for lambda
            server_error_button.clicked.connect(
                lambda: current_parent_widget.stackedWidget.setCurrentIndex(page_index)
                if current_parent_widget and hasattr(current_parent_widget, 'stackedWidget') and current_parent_widget.stackedWidget
                else None # Or some error handling
            )
            server_error.addWidget(server_error_button)
        
        server_error.show()

    def addToolBarActions(self, server_name: str):
        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(lambda checked=False, s=server_name: self.showLog(s)) # Add checked for QAction
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda checked=False, s=server_name: self.stopSingleServer(s)) # Add checked
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(
            lambda checked=False, s=server_name: self.modifyConfig(s)) # Add checked
        self.toolbar.addAction(action_config)

    def showLog(self, server_name: str):
        log_dialog = QDialog(self)
        log_dialog.setWindowTitle(self.tr(f"{server_name} 日志"))
        log_layout = QVBoxLayout(log_dialog)
        log_text = TextEdit(log_dialog)
        log_text.setReadOnly(True)
        log_text.setText(self.readLog(server_name))
        log_layout.addWidget(log_text)
        log_dialog.setLayout(log_layout)
        log_dialog.exec()

    def readLog(self, server_name: str) -> str:
        log_path = f'./logs/{server_name}.log'
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except Exception as e:
                return self.tr("读取日志文件失败: ") + str(e)
        else:
            return self.tr("日志文件不存在")

    def stopSingleServer(self, server_name: str):
        if server_name in self.launched_servers:
            self.stopServer(server_name)

    def modifyConfig(self, server_name: str):
        config_dialog = QDialog(self)
        config_dialog.setWindowTitle(self.tr(f"{server_name} 配置"))
        config_layout = QVBoxLayout(config_dialog)

        form_layout = QFormLayout()
        config_path = f'./config/{server_name}.cfg' # This should likely be .json or other structured format
        self.config_fields = {}

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    for line in lines:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'): # Basic parsing for key=value
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            line_edit = LineEdit(value)
                            self.config_fields[key] = line_edit
                            form_layout.addRow(QLabel(key), line_edit)
            except Exception as e:
                Info(self, 'E', 3000, self.tr(f"读取配置文件失败: {e}"))
        else:
            Info(self, 'W', 3000, self.tr(f"配置文件 {config_path} 不存在"))


        save_button = PushButton(self.tr("保存"))
        save_button.clicked.connect(
            lambda: self.saveConfig(server_name, config_path, config_dialog))

        config_layout.addLayout(form_layout)
        config_layout.addWidget(save_button)
        config_dialog.setLayout(config_layout)
        config_dialog.exec()

    def saveConfig(self, server_name: str, config_path: str, dialog_to_close: QDialog):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as file:
                for key, line_edit in self.config_fields.items():
                    file.write(f"{key}={line_edit.text()}\n")
            Info(self, 'S', 1000, self.tr(f"{server_name} 配置已保存!"))
            if dialog_to_close:
                dialog_to_close.accept()
        except Exception as e:
            Info(self, 'E', 3000, self.tr(f"保存配置失败: {e}"))

    def monitorServerStatus(self):
        """监控服务器状态 - 现在由ProcessManager处理"""
        # This method is now redundant as ProcessManager handles monitoring
        pass

    def checkServerStatus(self) -> bool:
        """检查服务器状态 - 现在由ProcessManager处理"""
        # This method is now redundant as ProcessManager handles status checking
        return True

    def restartServer(self, server_name: str):
        """Restart a server using ProcessManager"""
        try:
            self.process_manager.restart_process(server_name)
        except Exception as e:
            self.exception_handler.handle_known_exception(
                e,
                exc_type="process_error",
                severity="medium",
                user_message=f"重启服务器 {server_name} 时发生错误",
                parent_widget=self
            )

    # ProcessManager signal handlers
    def on_process_started(self, process_name: str):
        """Handle process started signal from ProcessManager"""
        if process_name in cfg.SERVER:
            # Update button state
            for button_widget in self.button_group.buttons(): # Use a different variable name
                if button_widget.objectName() == process_name:
                    button_widget.setChecked(True)
                    button_widget.setStyleSheet('background-color: #4CAF50; color: white;') # Example style
                    break
            
            if process_name not in self.launched_servers:
                self.launched_servers.append(process_name)
                self.addToolBarActions(process_name)
            
            Info(self, 'S', 1000, self.tr(f"服务端 {process_name} 已启动!"))

    def on_process_stopped(self, process_name: str, exit_code: Optional[int] = None): # Add exit_code
        """Handle process stopped signal from ProcessManager"""
        if process_name in self.launched_servers:
            self.launched_servers.remove(process_name)
            
            # Update button state
            for button_widget in self.button_group.buttons(): # Use a different variable name
                if button_widget.objectName() == process_name:
                    button_widget.setChecked(False)
                    button_widget.setStyleSheet('') # Reset style
                    break
            
            # Remove toolbar actions for this server
            actions_to_remove = []
            for action in self.toolbar.actions():
                if process_name in action.text():
                    actions_to_remove.append(action)
            for action in actions_to_remove:
                self.toolbar.removeAction(action)
            
            stop_message = f"{process_name} 已停止!"
            if exit_code is not None:
                stop_message += f" (退出码: {exit_code})"

            Info(self, 'S', 1000, self.tr(stop_message))
            
            # Update UI if no servers are running
            if not self.launched_servers:
                self.button_toggle.setText(self.tr(ONE_CLICK_START_TEXT))
                self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
                self.toolbar.clear()
                self.toolbar.setVisible(False)

    def on_process_crashed(self, process_name: str, exit_code: int):
        """Handle process crashed signal from ProcessManager"""
        Info(self, 'E', 3000, self.tr(f"{process_name} 异常退出 (代码: {exit_code})"))
        
        # Update button state to show error
        for button_widget in self.button_group.buttons(): # Use a different variable name
            if button_widget.objectName() == process_name:
                button_widget.setStyleSheet('background-color: #F44336; color: white;') # Example error style
                break
        # Also call on_process_stopped to clean up UI elements like toolbar
        self.on_process_stopped(process_name, exit_code)


    def on_process_restarted(self, process_name: str):
        """Handle process restarted signal from ProcessManager"""
        Info(self, 'S', 1000, self.tr(f"{process_name} 已自动重启!"))
        
        # Update button state
        for button_widget in self.button_group.buttons(): # Use a different variable name
            if button_widget.objectName() == process_name:
                button_widget.setStyleSheet('background-color: #4CAF50; color: white;') # Example style
                break
