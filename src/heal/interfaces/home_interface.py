import os
import random
from typing import List, Optional, Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QWidget
from qfluentwidgets import FluentIcon, PrimaryPushButton, TogglePushButton

from src.heal.common.exception_handler import ExceptionHandler
from src.heal.common.logging_config import get_logger, log_performance, with_correlation_id
from src.heal.common.resource_manager import register_timer
from src.heal.common.ui_utils import create_responsive_operation, batch_ui_update
from src.heal.components.home import (
    CompactBannerWidget,
    CustomFlipItemDelegate,
    DialogManager,
    HomeLayoutManager,
    QuickActionBar,
    ServerButton,
    ServerManager,
    ServerStatusCard,
    StatusOverviewWidget,
)
from src.heal.models.config import Info, cfg
from src.heal.models.process_manager import ProcessManager

# 定义常量避免重复
ONE_CLICK_START_TEXT = " 一键启动"
STOP_ALL_TEXT = " 停止全部"

# 使用统一日志配置
logger = get_logger(__name__)


class Home(QWidget):
    def __init__(self, text: str, parent: Any = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName(text)
        self._parent_widget = parent

        logger.info(f"初始化Home界面: {text}")

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
        if hasattr(self.process_manager, "process_restarted"):
            self.process_manager.process_restarted.connect(
                self.on_process_restarted)

        logger.debug("Home界面初始化完成")

        # Initialize status tracking for optimized layout
        if self.layout_manager.use_optimized_layout:
            self._update_optimized_status_displays()

    def initWidgets(self) -> None:
        # Check if we should use optimized layout
        if self.layout_manager.use_optimized_layout:
            self._init_optimized_widgets()
        else:
            self._init_legacy_widgets()

        self.initLayout()
        self.connectSignalToSlot()

    def _init_optimized_widgets(self) -> None:
        """Initialize widgets for optimized layout"""
        # Create new optimized components
        self.compact_banner: Any = self.layout_manager.create_compact_banner()
        self.status_overview: Any = self.layout_manager.create_status_overview()
        self.quick_action_bar: Any = self.layout_manager.create_quick_action_bar()

        # Create server status cards instead of buttons
        self.server_status_cards: list[Any] = self.layout_manager.create_server_status_cards(
            cfg.SERVER
        )

        # Create toolbar (still needed for compatibility)
        self.toolbar = self.layout_manager.create_toolbar()

        # Keep legacy components for backward compatibility but don't use them in layout
        self.flipView: Any = None
        self.server_buttons: list[Any] = []
        self.button_toggle: Any = None

    def _init_legacy_widgets(self) -> None:
        """Initialize widgets for legacy layout"""
        # Create flip view using layout manager
        self.flipView = self.layout_manager.create_flip_view()
        self.flipView.setCurrentIndex(random.randint(0, 2))

        # Create server buttons using server manager
        self.server_buttons = self.server_manager.create_server_buttons()

        # Create toggle button using layout manager
        self.button_toggle = self.layout_manager.create_toggle_button()

        # Create toolbar using layout manager
        self.toolbar = self.layout_manager.create_toolbar()

        # Set new components to None for legacy mode
        if not hasattr(self, 'compact_banner'):
            self.compact_banner = None
        if not hasattr(self, 'status_overview'):
            self.status_overview = None
        if not hasattr(self, 'quick_action_bar'):
            self.quick_action_bar = None
        if not hasattr(self, 'server_status_cards'):
            self.server_status_cards = []

    def initLayout(self) -> None:
        # Use appropriate layout based on configuration
        if self.layout_manager.use_optimized_layout:
            self.layout_manager.setup_optimized_layout(
                self.compact_banner,
                self.status_overview,
                self.server_status_cards,
                self.quick_action_bar,
                self.toolbar,
            )
        else:
            # Use legacy layout
            self.layout_manager.setup_main_layout(
                self.flipView, self.server_buttons, self.button_toggle, self.toolbar
            )

    def connectSignalToSlot(self) -> None:
        if self.layout_manager.use_optimized_layout:
            self._connect_optimized_signals()
        else:
            self._connect_legacy_signals()

    def _connect_optimized_signals(self) -> None:
        """Connect signals for optimized layout"""
        # Connect server status card signals
        for card in self.server_status_cards:
            card.start_requested.connect(self._handle_server_start_request)
            card.stop_requested.connect(self._handle_server_stop_request)
            card.restart_requested.connect(self._handle_server_restart_request)
            card.settings_requested.connect(
                self._handle_server_settings_request)

        # Connect quick action bar signals
        if self.quick_action_bar:
            self.quick_action_bar.start_all_requested.connect(
                self.handleServerLaunch)
            self.quick_action_bar.stop_all_requested.connect(
                self.handleStopAllServers)
            self.quick_action_bar.refresh_requested.connect(
                self._handle_refresh_request
            )
            self.quick_action_bar.view_logs_requested.connect(
                self._handle_view_logs_request
            )
            self.quick_action_bar.settings_requested.connect(
                self._handle_settings_request
            )

        # Connect compact banner signals
        if self.compact_banner:
            self.compact_banner.banner_clicked.connect(
                self._handle_banner_click)

        # Connect status overview signals
        if self.status_overview:
            self.status_overview.refresh_requested.connect(
                self._handle_refresh_request)

    def _connect_legacy_signals(self) -> None:
        """Connect signals for legacy layout"""
        if self.flipView:
            self.scrollTimer = QTimer(self)
            self.scrollTimer.timeout.connect(
                lambda: self.flipView.setCurrentIndex(random.randint(0, 2))
            )
            self.scrollTimer.start(5000)

            # 注册定时器到资源管理器
            register_timer(
                f"home_scroll_timer_{id(self)}", self.scrollTimer, "首页滚动定时器"
            )

        if self.button_toggle:
            self.button_toggle.clicked.connect(self.handleToggle)

    def handleToggle(self) -> None:
        if self.launched_servers:
            self.handleStopAllServers()
        else:
            self.handleServerLaunch()

    @log_performance("server_launch")
    def handleServerLaunch(self) -> None:
        """修复：降低认知复杂度，分解为更小的函数 - 使用响应式操作"""
        def launch_servers_operation() -> list[str]:
            """服务器启动操作"""
            with with_correlation_id() as cid:
                logger.info("开始批量启动服务器")
                selected_servers = self.server_manager.get_selected_servers()
                launched_servers_this_run = []

                logger.debug(f"选中的服务器数量: {len(selected_servers)}")

                for server_button in selected_servers:
                    if self.server_manager.should_launch_server(server_button):
                        server_name = server_button.objectName()
                        logger.info(f"启动服务器: {server_name}")
                        success = self.server_manager.launch_single_server(
                            server_button)
                        if success:
                            launched_servers_this_run.append(server_name)
                            logger.info(f"服务器 {server_name} 启动成功")
                        else:
                            logger.error(f"服务器 {server_name} 启动失败")

                return launched_servers_this_run

        def on_launch_completed(launched_servers: list[str]) -> None:
            """启动完成回调"""
            if launched_servers:
                logger.info(
                    f"成功启动 {len(launched_servers)} 个服务器: {launched_servers}"
                )
                self._update_ui_after_launch(launched_servers)
            else:
                logger.warning("没有服务器被启动")

        def on_launch_failed(error_msg: str) -> None:
            """启动失败回调"""
            logger.error(f"服务器启动失败: {error_msg}")

        # 创建响应式操作
        operation = create_responsive_operation(
            "server_launch",
            launch_servers_operation,
            completion_callback=on_launch_completed,
            error_callback=on_launch_failed
        )

        # 在后台线程执行以避免UI阻塞
        operation.execute_in_thread()

    def _get_selected_servers(self) -> List[TogglePushButton]:
        """获取选中的服务器按钮"""
        return [
            button
            for button in self.server_manager.button_group.buttons()
            if isinstance(button, TogglePushButton) and button.isChecked()
        ]

    def _should_launch_server(self, server: TogglePushButton) -> bool:
        """检查是否应该启动服务器"""
        return server.objectName() not in self.launched_servers

    def _launch_single_server(self, server: TogglePushButton) -> bool:
        """启动单个服务器"""
        name = server.objectName()
        server_path = f"./server/{name}"

        if not os.path.exists(server_path):
            self.showErrorInfoBar(name)
            return False

        try:
            # 修复：使用这些变量，即使只是日志记录
            server_config = cfg.SERVER[name]
            command = server_config.get("COMMAND", "")
            working_dir = server_path

            # 记录启动信息
            logger.info(f"启动服务器 {name}，命令: {command}，工作目录: {working_dir}")

            success = self.process_manager.start_process(
                name
            )  # Assuming start_process only takes process name

            if not success:
                self._handle_server_start_failure(server, name)
                return False

            return True

        except Exception as e:
            self._handle_server_start_exception(server, name, e)
            return False

    def _handle_server_start_failure(self, server: TogglePushButton, name: str) -> None:
        """处理服务器启动失败"""
        self.exception_handler.handle_known_exception(
            RuntimeError(f"Failed to start server {name}"),
            exc_type="process_error",
            severity="medium",
            user_message=f"无法启动服务器 {name}",
            parent_widget=self,
        )
        server.setChecked(False)

    def _handle_server_start_exception(
        self, server: TogglePushButton, name: str, exception: Exception
    ) -> None:
        """处理服务器启动异常"""
        self.exception_handler.handle_known_exception(
            exception,
            exc_type="process_error",
            severity="medium",
            user_message=f"启动服务器 {name} 时发生错误",
            parent_widget=self,
        )
        server.setChecked(False)

    def _update_ui_after_launch(self, launched_servers: List[str]) -> None:
        """启动后更新UI - 使用批处理优化"""
        # 使用批处理更新UI以提高性能
        def update_info() -> None:
            Info(
                self, "S", 1000, self.tr(
                    f"服务端 {', '.join(launched_servers)} 启动中...")
            )

        def update_button() -> None:
            self.button_toggle.setText(self.tr(STOP_ALL_TEXT))
            self.button_toggle.setIcon(FluentIcon.CLOSE)

        def update_toolbar() -> None:
            self.toolbar.setVisible(True)

        # 批量处理UI更新
        batch_ui_update(update_info)
        batch_ui_update(update_button)
        batch_ui_update(update_toolbar)

    @log_performance("stop_all_servers")
    def handleStopAllServers(self) -> None:
        """Stop all servers using ServerManager"""
        logger.info("开始停止所有服务器")
        # Use ServerManager to stop all launched servers
        self.server_manager.stop_all_servers()

        # UI updates will be handled by on_process_stopped signal
        # Reset toggle button immediately for responsiveness
        self.button_toggle.setText(self.tr(ONE_CLICK_START_TEXT))
        self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
        self.toolbar.clear()
        self.toolbar.setVisible(False)
        Info(self, "S", 1000, self.tr("正在停止所有服务端..."))
        logger.info("所有服务器停止命令已发送")

    def stopServer(self, server_name: str) -> None:
        """Stop a specific server using ServerManager"""
        self.server_manager.stop_server(server_name)

    def showErrorInfoBar(self, name: str) -> None:
        """显示错误信息栏"""
        self.dialog_manager.show_error_info_bar(
            name, self._parent_widget.stackedWidget if self._parent_widget else None
        )

    def addToolBarActions(self, server_name: str) -> None:
        action_log = QAction(self.tr(f"{server_name} 日志"), self)
        action_log.triggered.connect(
            lambda checked=False, s=server_name: self.showLog(s)
        )
        self.toolbar.addAction(action_log)

        action_stop = QAction(self.tr(f"停止 {server_name}"), self)
        action_stop.triggered.connect(
            lambda checked=False, s=server_name: self.stopSingleServer(s)
        )
        self.toolbar.addAction(action_stop)

        action_config = QAction(self.tr(f"配置 {server_name}"), self)
        action_config.triggered.connect(
            lambda checked=False, s=server_name: self.modifyConfig(s)
        )
        self.toolbar.addAction(action_config)

    def showLog(self, server_name: str) -> None:
        """显示服务器日志"""
        self.dialog_manager.show_log_dialog(server_name)

    def readLog(self, server_name: str) -> str:
        """读取服务器日志文件"""
        return self.dialog_manager.read_log(server_name)

    def stopSingleServer(self, server_name: str) -> None:
        if server_name in self.launched_servers:
            self.stopServer(server_name)

    def modifyConfig(self, server_name: str) -> None:
        """修改服务器配置"""
        self.dialog_manager.show_config_dialog(server_name)

    def saveConfig(self, server_name: str, config_path: str, dialog_to_close: Any) -> None:
        """保存服务器配置"""
        self.dialog_manager.save_config(
            server_name, config_path, dialog_to_close)

    def restartServer(self, server_name: str) -> None:
        """Restart a server using ServerManager"""
        self.server_manager.restart_server(server_name)

    # ProcessManager signal handlers
    def on_process_started(self, process_name: str) -> None:
        """Handle process started signal from ProcessManager"""
        logger.info(f"进程启动事件: {process_name}")

        if process_name in cfg.SERVER:
            # Update button state using server manager
            self.server_manager.update_button_state(process_name, "started")

            if process_name not in self.launched_servers:
                self.launched_servers.append(process_name)
                self.addToolBarActions(process_name)
                logger.debug(f"添加工具栏操作: {process_name}")

            Info(self, "S", 1000, self.tr(f"服务端 {process_name} 已启动!"))
            logger.info(f"服务端 {process_name} 启动完成，UI已更新")

            # Update optimized layout components
            if self.layout_manager.use_optimized_layout:
                # Update server status card
                for card in self.server_status_cards:
                    if card.server_name == process_name:
                        card.update_status("running")
                        break

                # Update status overview
                if self.status_overview:
                    self.status_overview.update_server_status(
                        process_name, "running")
                    self.status_overview.add_activity(
                        f"Started {process_name}")

                # Update displays
                self._update_optimized_status_displays()

    def on_process_stopped(self, process_name: str, exit_code: Optional[int] = None) -> None:
        """Handle process stopped signal from ProcessManager"""
        logger.info(f"进程停止事件: {process_name}, 退出码: {exit_code}")

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

            Info(self, "S", 1000, self.tr(stop_message))
            logger.info(f"服务端 {process_name} 停止完成，UI已更新")

            # Update UI if no servers are running
            if not self.launched_servers:
                if self.button_toggle:  # Legacy layout
                    self.button_toggle.setText(self.tr(ONE_CLICK_START_TEXT))
                    self.button_toggle.setIcon(FluentIcon.PLAY_SOLID)
                self.toolbar.clear()
                self.toolbar.setVisible(False)
                logger.debug("所有服务器已停止，重置UI状态")

            # Update optimized layout components
            if self.layout_manager.use_optimized_layout:
                # Update server status card
                for card in self.server_status_cards:
                    if card.server_name == process_name:
                        card.update_status("stopped")
                        break

                # Update status overview
                if self.status_overview:
                    self.status_overview.update_server_status(
                        process_name, "stopped")
                    self.status_overview.add_activity(
                        f"Stopped {process_name}")

                # Update displays
                self._update_optimized_status_displays()

    def on_process_crashed(self, process_name: str, exit_code: int) -> None:
        """Handle process crashed signal from ProcessManager"""
        Info(self, "E", 3000, self.tr(
            f"{process_name} 异常退出 (代码: {exit_code})"))

        # Update button state to show error using server manager
        self.server_manager.update_button_state(process_name, "crashed")

        # Also call on_process_stopped to clean up UI elements like toolbar
        self.on_process_stopped(process_name, exit_code)

    def on_process_restarted(self, process_name: str) -> None:
        """Handle process restarted signal from ProcessManager"""
        Info(self, "S", 1000, self.tr(f"{process_name} 已自动重启!"))

        # Update button state using server manager
        self.server_manager.update_button_state(process_name, "started")

    # New methods for optimized layout
    def _update_optimized_status_displays(self) -> None:
        """Update status displays for optimized layout"""
        if not self.layout_manager.use_optimized_layout:
            return

        # Update server counts in quick action bar
        if self.quick_action_bar:
            running_count = len(self.launched_servers)
            total_count = len(cfg.SERVER)
            self.quick_action_bar.update_server_counts(
                running_count, total_count)

        # Update status overview
        if self.status_overview:
            for server_name in cfg.SERVER.keys():
                status = (
                    "running" if server_name in self.launched_servers else "stopped"
                )
                self.status_overview.update_server_status(server_name, status)

        # Update compact banner stats
        if self.compact_banner:
            stats_text = f"{len(cfg.SERVER)} servers configured"
            self.compact_banner.update_stats(stats_text)

    def _handle_server_start_request(self, server_name: str) -> None:
        """Handle server start request from status card"""
        logger.info(f"Start request for server: {server_name}")
        # Find the corresponding server button and trigger start
        for card in self.server_status_cards:
            if card.server_name == server_name:
                card.update_status("starting")
                break

        # Use existing server launch logic
        if self.server_manager.launch_single_server(
            type(
                "MockButton",
                (),
                {"objectName": lambda: server_name, "setChecked": lambda x: None},
            )()
        ):
            self.launched_servers.append(server_name)
            self._update_optimized_status_displays()

    def _handle_server_stop_request(self, server_name: str) -> None:
        """Handle server stop request from status card"""
        logger.info(f"Stop request for server: {server_name}")
        # Find the corresponding card and update status
        for card in self.server_status_cards:
            if card.server_name == server_name:
                card.update_status("stopping")
                break

        # Use existing server stop logic
        self.server_manager.stop_server(server_name)
        if server_name in self.launched_servers:
            self.launched_servers.remove(server_name)
        self._update_optimized_status_displays()

    def _handle_server_restart_request(self, server_name: str) -> None:
        """Handle server restart request from status card"""
        logger.info(f"Restart request for server: {server_name}")
        self.server_manager.restart_server(server_name)

    def _handle_server_settings_request(self, server_name: str) -> None:
        """Handle server settings request from status card"""
        logger.info(f"Settings request for server: {server_name}")
        # This would open server-specific settings dialog
        # Implementation depends on your settings system

    def _handle_refresh_request(self) -> None:
        """Handle refresh request from quick action bar or status overview"""
        logger.info("Refresh request received")
        self._update_optimized_status_displays()

    def _handle_view_logs_request(self) -> None:
        """Handle view logs request from quick action bar"""
        logger.info("View logs request received")
        # This would open the logs interface
        # You might want to switch to the logs tab in the main navigation

    def _handle_settings_request(self) -> None:
        """Handle settings request from quick action bar"""
        logger.info("Settings request received")
        # This would open the settings interface
        # You might want to switch to the settings tab in the main navigation

    def _handle_banner_click(self) -> None:
        """Handle banner click event"""
        logger.info("Banner clicked")
        # This could show additional information or perform some action
