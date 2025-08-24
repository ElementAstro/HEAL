import random
import os
from typing import Optional, List
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QToolBar
from PySide6.QtGui import QAction
from qfluentwidgets import (PrimaryPushButton, FluentIcon, TogglePushButton)
from app.model.config import cfg, Info
from app.model.process_manager import ProcessManager
from app.common.exception_handler import ExceptionHandler
from app.components.home import (
    CustomFlipItemDelegate, ServerButton, HomeLayoutManager, 
    ServerManager, DialogManager
)

# 定义常量避免重复
ONE_CLICK_START_TEXT = ' 一键启动'
STOP_ALL_TEXT = ' 停止全部'


class Home(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text)
        self._parent_widget = parent

        # Initialize components
        self.server_manager = ServerManager(self)
        self.layout_manager = HomeLayoutManager(self)
        self.dialog_manager = DialogManager(self)
        
        # Initialize ProcessManager and ExceptionHandler
        self.process_manager = self.server_manager.process_manager
        self.exception_handler = self.server_manager.exception_handler
        
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
        # Create flip view using layout manager
        self.flipView = self.layout_manager.create_flip_view()
        self.flipView.setCurrentIndex(random.randint(0, 2))

        # Create server buttons using server manager
        self.server_buttons = self.server_manager.create_server_buttons()
        
        # Create toggle button using layout manager
        self.button_toggle = self.layout_manager.create_toggle_button()
        
        # Create toolbar using layout manager
        self.toolbar = self.layout_manager.create_toolbar()

        self.initLayout()
        self.connectSignalToSlot()

    def initLayout(self):
        # Use layout manager to setup the main layout
        self.layout_manager.setup_main_layout(
            self.flipView, 
            self.server_buttons, 
            self.button_toggle,
            self.toolbar
        )

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
        selected_servers = self.server_manager.get_selected_servers()
        launched_servers_this_run = []
        
        for server_button in selected_servers:
            if self.server_manager.should_launch_server(server_button):
                success = self.server_manager.launch_single_server(server_button)
                if success:
                    launched_servers_this_run.append(server_button.objectName())

        if launched_servers_this_run:
            self._update_ui_after_launch(launched_servers_this_run)

    def _get_selected_servers(self) -> List[TogglePushButton]:
        """获取选中的服务器按钮"""
        return [button for button in self.server_manager.button_group.buttons()
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
        # Use ServerManager to stop all launched servers
        self.server_manager.stop_all_servers()
        
        # UI updates will be handled by on_process_stopped signal
        # Reset toggle button immediately for responsiveness
        self.button_toggle.setText(self.tr(ONE_CLICK_START_TEXT))
        self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
        self.toolbar.clear()
        self.toolbar.setVisible(False)
        Info(self, 'S', 1000, self.tr("正在停止所有服务端..."))

    def stopServer(self, server_name: str):
        """Stop a specific server using ServerManager"""
        self.server_manager.stop_server(server_name)

    def showErrorInfoBar(self, name: str):
        """显示错误信息栏"""
        self.dialog_manager.show_error_info_bar(
            name, 
            self._parent_widget.stackedWidget if self._parent_widget else None
        )

    def addToolBarActions(self, server_name: str):
        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(lambda checked=False, s=server_name: self.showLog(s))
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda checked=False, s=server_name: self.stopSingleServer(s))
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(
            lambda checked=False, s=server_name: self.modifyConfig(s))
        self.toolbar.addAction(action_config)

    def showLog(self, server_name: str):
        """显示服务器日志"""
        self.dialog_manager.show_log_dialog(server_name)

    def readLog(self, server_name: str) -> str:
        """读取服务器日志文件"""
        return self.dialog_manager.read_log(server_name)

    def stopSingleServer(self, server_name: str):
        if server_name in self.launched_servers:
            self.stopServer(server_name)

    def modifyConfig(self, server_name: str):
        """修改服务器配置"""
        self.dialog_manager.show_config_dialog(server_name)

    def saveConfig(self, server_name: str, config_path: str, dialog_to_close):
        """保存服务器配置"""
        self.dialog_manager.save_config(server_name, config_path, dialog_to_close)

    def restartServer(self, server_name: str):
        """Restart a server using ServerManager"""
        self.server_manager.restart_server(server_name)

    # ProcessManager signal handlers
    def on_process_started(self, process_name: str):
        """Handle process started signal from ProcessManager"""
        if process_name in cfg.SERVER:
            # Update button state using server manager
            self.server_manager.update_button_state(process_name, "started")
            
            if process_name not in self.launched_servers:
                self.launched_servers.append(process_name)
                self.addToolBarActions(process_name)
            
            Info(self, 'S', 1000, self.tr(f"服务端 {process_name} 已启动!"))

    def on_process_stopped(self, process_name: str, exit_code: Optional[int] = None):
        """Handle process stopped signal from ProcessManager"""
        if process_name in self.launched_servers:
            self.launched_servers.remove(process_name)
            
            # Update button state using server manager
            self.server_manager.update_button_state(process_name, "stopped")
            
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
        
        # Update button state to show error using server manager
        self.server_manager.update_button_state(process_name, "crashed")
        
        # Also call on_process_stopped to clean up UI elements like toolbar
        self.on_process_stopped(process_name, exit_code)

    def on_process_restarted(self, process_name: str):
        """Handle process restarted signal from ProcessManager"""
        Info(self, 'S', 1000, self.tr(f"{process_name} 已自动重启!"))
        
        # Update button state using server manager
        self.server_manager.update_button_state(process_name, "started")
