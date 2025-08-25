"""
进程状态监控UI组件
提供实时进程状态显示、控制和监控功能
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    InfoBar,
    InfoBarIcon,
    InfoBarPosition,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    StrongBodyLabel,
    TransparentToolButton,
)

from ...common.exception_handler import (
    global_exception_handler,
    process_exception_handler,
)
from ...common.i18n_ui import setup_component_i18n, tr, tr_button, tr_label
from ...common.logging_config import get_logger, log_performance, with_correlation_id
from ...models.process_manager import ProcessInfo, ProcessManager, ProcessStatus

# 使用统一日志配置
logger = get_logger("process_monitor")


class ProcessStatusCard(CardWidget):
    """单个进程状态卡片"""

    restart_requested = Signal(str)  # process_name
    stop_requested = Signal(str)  # process_name
    log_requested = Signal(str)  # process_name

    def __init__(self, process_info: ProcessInfo, parent=None) -> None:
        super().__init__(parent)
        self.process_info = process_info
        logger.debug(f"创建进程状态卡片: {process_info.name}")
        self.init_ui()
        self.update_status(process_info)

    def init_ui(self) -> None:
        """初始化UI"""
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 顶部：进程名称和状态
        top_layout = QHBoxLayout()

        self.name_label = StrongBodyLabel(self.process_info.name)
        self.name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))

        self.status_label = CaptionLabel("状态")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        top_layout.addWidget(self.name_label)
        top_layout.addStretch()
        top_layout.addWidget(self.status_label)

        # 中部：进程信息
        middle_layout = QHBoxLayout()

        self.pid_label = CaptionLabel("PID: --")
        self.uptime_label = CaptionLabel("运行时间: --")
        self.cpu_label = CaptionLabel("CPU: --%")
        self.memory_label = CaptionLabel("内存: -- MB")

        middle_layout.addWidget(self.pid_label)
        middle_layout.addWidget(self.uptime_label)
        middle_layout.addWidget(self.cpu_label)
        middle_layout.addWidget(self.memory_label)
        middle_layout.addStretch()

        # 底部：控制按钮
        button_layout = QHBoxLayout()

        self.restart_btn = TransparentToolButton(FluentIcon.RESTART, self)
        self.restart_btn.setToolTip("重启进程")
        self.restart_btn.clicked.connect(
            lambda: self.restart_requested.emit(self.process_info.name)
        )

        self.stop_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.stop_btn.setToolTip("停止进程")
        self.stop_btn.clicked.connect(
            lambda: self.stop_requested.emit(self.process_info.name)
        )

        self.log_btn = TransparentToolButton(FluentIcon.DOCUMENT, self)
        self.log_btn.setToolTip("查看日志")
        self.log_btn.clicked.connect(
            lambda: self.log_requested.emit(self.process_info.name)
        )

        button_layout.addStretch()
        button_layout.addWidget(self.restart_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.log_btn)

        # 添加到主布局
        layout.addLayout(top_layout)
        layout.addLayout(middle_layout)
        layout.addLayout(button_layout)

    def update_status(self, process_info: ProcessInfo) -> None:
        """更新进程状态显示"""
        self.process_info = process_info

        # 更新状态标签和颜色
        status_text = {
            ProcessStatus.STOPPED: "已停止",
            ProcessStatus.STARTING: "启动中",
            ProcessStatus.RUNNING: "运行中",
            ProcessStatus.STOPPING: "停止中",
            ProcessStatus.CRASHED: "已崩溃",
            ProcessStatus.UNKNOWN: "未知",
        }.get(process_info.status, "未知")

        status_color = {
            ProcessStatus.STOPPED: "#666666",
            ProcessStatus.STARTING: "#FFA500",
            ProcessStatus.RUNNING: "#00AA00",
            ProcessStatus.STOPPING: "#FFA500",
            ProcessStatus.CRASHED: "#FF0000",
            ProcessStatus.UNKNOWN: "#666666",
        }.get(process_info.status, "#666666")

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"color: {status_color};")

        # 更新进程信息
        if process_info.pid:
            self.pid_label.setText(f"PID: {process_info.pid}")
        else:
            self.pid_label.setText("PID: --")

        if process_info.start_time:
            import time

            uptime = time.time() - process_info.start_time.timestamp()
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            self.uptime_label.setText(f"运行时间: {hours:02d}:{minutes:02d}")
        else:
            self.uptime_label.setText("运行时间: --")

        # CPU和内存使用率（如果有的话）
        if hasattr(process_info, "cpu_percent"):
            self.cpu_label.setText(f"CPU: {process_info.cpu_percent:.1f}%")
        else:
            self.cpu_label.setText("CPU: --%")

        if hasattr(process_info, "memory_mb"):
            self.memory_label.setText(f"内存: {process_info.memory_mb:.1f} MB")
        else:
            self.memory_label.setText("内存: -- MB")

        # 根据状态禁用/启用按钮
        can_control = process_info.status in [
            ProcessStatus.RUNNING,
            ProcessStatus.STOPPED,
            ProcessStatus.CRASHED,
        ]
        self.restart_btn.setEnabled(can_control)
        self.stop_btn.setEnabled(process_info.status == ProcessStatus.RUNNING)


class ProcessMonitorWidget(QWidget):
    """进程监控主窗口部件"""

    process_started = Signal(str)
    process_stopped = Signal(str)
    process_restarted = Signal(str)

    def __init__(self, process_manager: ProcessManager, parent=None) -> None:
        super().__init__(parent)
        self.process_manager = process_manager
        self.process_cards: Dict[str, ProcessStatusCard] = {}
        self.update_timer = QTimer()

        self.init_ui()
        self.connect_signals()
        self.start_monitoring()

    def init_ui(self) -> None:
        """初始化UI"""
        # 设置国际化支持
        self.i18n = setup_component_i18n(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题和控制按钮
        header_layout = QHBoxLayout()

        self.title_label = StrongBodyLabel(tr("process_monitor.title"))
        self.title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        self.i18n.register_text(self.title_label, "process_monitor.title")

        self.refresh_btn = tr_button(
            "process_monitor.refresh_status", FluentIcon.SYNC, primary=True
        )
        self.refresh_btn.clicked.connect(self.refresh_all_processes)

        self.start_all_btn = tr_button(
            "process_monitor.start_all", FluentIcon.PLAY, primary=True
        )
        self.start_all_btn.clicked.connect(self.start_all_processes)

        self.stop_all_btn = tr_button("process_monitor.stop_all", FluentIcon.PAUSE)
        self.stop_all_btn.clicked.connect(self.stop_all_processes)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.start_all_btn)
        header_layout.addWidget(self.stop_all_btn)

        # 进程列表容器
        self.process_container = QWidget()
        self.process_layout = QVBoxLayout(self.process_container)
        self.process_layout.setContentsMargins(0, 0, 0, 0)
        self.process_layout.setSpacing(8)

        # 滚动区域（如果需要的话）
        from qfluentwidgets import ScrollArea

        scroll_area = ScrollArea()
        scroll_area.setWidget(self.process_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 状态栏
        self.status_label = CaptionLabel(tr("ready"))
        self.i18n.register_text(self.status_label, "ready")

        # 添加到主布局
        layout.addLayout(header_layout)
        layout.addWidget(scroll_area, 1)
        layout.addWidget(self.status_label)

    def connect_signals(self) -> None:
        """连接信号"""
        # 连接进程管理器信号
        self.process_manager.process_started.connect(self.on_process_started)
        self.process_manager.process_stopped.connect(self.on_process_stopped)
        self.process_manager.process_crashed.connect(self.on_process_crashed)
        self.process_manager.process_restarted.connect(self.on_process_restarted)

        # 设置定时更新
        self.update_timer.timeout.connect(self.update_process_status)

    def start_monitoring(self) -> None:
        """开始监控"""
        self.refresh_all_processes()
        self.update_timer.start(2000)  # 每2秒更新一次

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.update_timer.stop()

    @process_exception_handler
    def refresh_all_processes(self) -> None:
        """刷新所有进程状态"""
        self.status_label.setText("刷新进程状态...")

        # 获取所有进程信息
        processes = self.process_manager.get_all_processes()

        # 清除旧的卡片
        for card in self.process_cards.values():
            card.deleteLater()
        self.process_cards.clear()

        # 创建新的卡片
        for process_info in processes:
            self.add_process_card(process_info)

        self.status_label.setText(f"共监控 {len(processes)} 个进程")

    def add_process_card(self, process_info: ProcessInfo) -> None:
        """添加进程卡片"""
        card = ProcessStatusCard(process_info, self)
        card.restart_requested.connect(self.restart_process)
        card.stop_requested.connect(self.stop_process)
        card.log_requested.connect(self.show_process_log)

        self.process_cards[process_info.name] = card
        self.process_layout.addWidget(card)

    @process_exception_handler
    def update_process_status(self) -> None:
        """更新进程状态"""
        for name, card in self.process_cards.items():
            try:
                process_info = self.process_manager.get_process_info(name)
                if process_info:
                    card.update_status(process_info)
            except Exception as e:
                # 进程可能已经被删除
                continue

    @process_exception_handler
    def start_all_processes(self) -> None:
        """启动所有进程"""
        self.status_label.setText("启动所有进程...")
        started_count = 0

        for name in self.process_cards.keys():
            try:
                if self.process_manager.start_process(name):
                    started_count += 1
            except Exception as e:
                continue

        self.status_label.setText(f"已启动 {started_count} 个进程")
        self.process_started.emit("all")

    @process_exception_handler
    def stop_all_processes(self) -> None:
        """停止所有进程"""
        self.status_label.setText("停止所有进程...")
        stopped_count = 0

        for name in self.process_cards.keys():
            try:
                if self.process_manager.stop_process(name):
                    stopped_count += 1
            except Exception as e:
                continue

        self.status_label.setText(f"已停止 {stopped_count} 个进程")
        self.process_stopped.emit("all")

    @process_exception_handler
    def restart_process(self, name: str) -> None:
        """重启进程"""
        self.status_label.setText(f"重启进程 {name}...")
        if self.process_manager.restart_process(name):
            self.status_label.setText(f"进程 {name} 重启成功")
            self.process_restarted.emit(name)
        else:
            self.status_label.setText(f"进程 {name} 重启失败")

    @process_exception_handler
    def stop_process(self, name: str) -> None:
        """停止进程"""
        self.status_label.setText(f"停止进程 {name}...")
        if self.process_manager.stop_process(name):
            self.status_label.setText(f"进程 {name} 已停止")
            self.process_stopped.emit(name)
        else:
            self.status_label.setText(f"进程 {name} 停止失败")

    def show_process_log(self, name: str) -> None:
        """显示进程日志 - 现在使用统一日志面板"""
        try:
            # 尝试使用统一日志面板
            from src.heal.components.logging import show_process_log

            show_process_log(name)
        except ImportError:
            # 如果统一日志面板不可用，回退到传统方式
            self._show_legacy_process_log(name)

    def _show_legacy_process_log(self, name: str) -> None:
        """显示传统的进程日志（备用方案）"""
        try:
            log_content = self.process_manager.get_process_output(name)
            if log_content:
                self._show_log_dialog(name, log_content)
            else:
                InfoBar.warning(
                    title="日志为空",
                    content=f"进程 {name} 暂无日志输出",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self,
                )
        except Exception as e:
            global_exception_handler.handle_known_exception(
                exception=e,
                user_message=f"获取进程 {name} 日志失败",
                parent_widget=self,
            )

    def _show_log_dialog(self, name: str, log_content: str) -> None:
        """显示日志对话框"""
        from qfluentwidgets import MessageBox

        # 限制日志长度
        if len(log_content) > 10000:
            log_content = log_content[-10000:] + "\n...(显示最后10000个字符)"

        dialog = MessageBox(title=f"{name} 进程日志", content=log_content, parent=self)
        dialog.contentLabel.setWordWrap(True)
        dialog.contentLabel.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        dialog.exec()

    def on_process_started(self, name: str) -> None:
        """进程启动事件"""
        InfoBar.success(
            title="进程启动",
            content=f"进程 {name} 已成功启动",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def on_process_stopped(self, name: str) -> None:
        """进程停止事件"""
        InfoBar.information(
            title="进程停止",
            content=f"进程 {name} 已停止",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def on_process_crashed(self, name: str, exit_code: int) -> None:
        """进程崩溃事件"""
        InfoBar.error(
            title="进程崩溃",
            content=f"进程 {name} 异常退出 (退出码: {exit_code})",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )

    def on_process_restarted(self, name: str) -> None:
        """进程重启事件"""
        InfoBar.success(
            title="进程重启",
            content=f"进程 {name} 已重新启动",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
