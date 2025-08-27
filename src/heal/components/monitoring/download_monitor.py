"""
下载进度监控UI组件
提供实时下载进度显示、控制和管理功能
"""

from pathlib import Path
from typing import Any, Dict  # List, Optional removed as per error

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont  # QColor removed as per error
from PySide6.QtWidgets import QHBoxLayout  # QGroupBox, QLabel, removed as per error
from PySide6.QtWidgets import (  # QProgressBar, QListWidget, QListWidgetItem removed as per error
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (  # InfoBarIcon removed as per error; BodyLabel removed as per error
    CaptionLabel,
    CardWidget,
    FluentIcon,
    IndeterminateProgressBar,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    TransparentToolButton,
)

# global_exception_handler removed as per error
from ...common.exception_handler import download_exception_handler
from ...common.logging_config import get_logger, log_download, log_performance
from ...models.download_manager import DownloadItem, DownloadManager, DownloadStatus

# 使用统一日志配置
logger = get_logger("download_monitor")


class DownloadItemCard(CardWidget):
    """单个下载项卡片"""

    pause_requested = Signal(str)  # download_id
    resume_requested = Signal(str)  # download_id
    cancel_requested = Signal(str)  # download_id
    retry_requested = Signal(str)  # download_id

    def __init__(self, download_item: DownloadItem, parent: Any = None) -> None:
        super().__init__(parent)
        self.download_item = download_item
        self.init_ui()
        self.update_progress(download_item)

    def init_ui(self) -> None:
        """初始化UI"""
        self.setFixedHeight(140)
        main_layout = QVBoxLayout(self)  # Changed variable name for clarity
        self.setLayout(main_layout)  # Explicitly set layout
        main_layout.setContentsMargins(16, 12, 16, 12)

        # 顶部：文件名和状态
        top_layout = QHBoxLayout()

        self.filename_label = StrongBodyLabel(
            Path(self.download_item.file_path).name
        )  # Use file_path
        self.filename_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))

        self.status_label = CaptionLabel("状态")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        top_layout.addWidget(self.filename_label)
        top_layout.addStretch()
        top_layout.addWidget(self.status_label)

        # 中部：进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        # 进度信息
        progress_info_layout = QHBoxLayout()

        self.size_label = CaptionLabel("大小: --")
        self.speed_label = CaptionLabel("速度: --")
        self.eta_label = CaptionLabel("剩余时间: --")
        self.percentage_label = CaptionLabel("0%")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        progress_info_layout.addWidget(self.size_label)
        progress_info_layout.addWidget(self.speed_label)
        progress_info_layout.addWidget(self.eta_label)
        progress_info_layout.addStretch()
        progress_info_layout.addWidget(self.percentage_label)

        # 底部：控制按钮
        button_layout = QHBoxLayout()

        self.pause_btn = TransparentToolButton(FluentIcon.PAUSE, self)
        self.pause_btn.setToolTip("暂停下载")
        self.pause_btn.clicked.connect(
            lambda: self.pause_requested.emit(self.download_item.id)
        )

        self.resume_btn = TransparentToolButton(FluentIcon.PLAY, self)
        self.resume_btn.setToolTip("恢复下载")
        self.resume_btn.clicked.connect(
            lambda: self.resume_requested.emit(self.download_item.id)
        )

        self.retry_btn = TransparentToolButton(FluentIcon.SYNC, self)
        self.retry_btn.setToolTip("重试下载")
        self.retry_btn.clicked.connect(
            lambda: self.retry_requested.emit(self.download_item.id)
        )

        self.cancel_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        self.cancel_btn.setToolTip("取消下载")
        self.cancel_btn.clicked.connect(
            lambda: self.cancel_requested.emit(self.download_item.id)
        )

        button_layout.addStretch()
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.resume_btn)
        button_layout.addWidget(self.retry_btn)
        button_layout.addWidget(self.cancel_btn)

        # 添加到主布局
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.progress_bar)  # Index 1
        # Indeterminate bar will be inserted at index 2 if needed
        main_layout.addLayout(progress_info_layout)  # Becomes index 2 or 3
        main_layout.addLayout(button_layout)  # Becomes index 3 or 4

    def update_progress(self, download_item: DownloadItem) -> None:
        """更新下载进度显示"""
        self.download_item = download_item

        # 更新状态标签和颜色
        status_text = {
            DownloadStatus.PENDING: "等待中",
            DownloadStatus.DOWNLOADING: "下载中",
            DownloadStatus.PAUSED: "已暂停",
            DownloadStatus.COMPLETED: "已完成",
            DownloadStatus.FAILED: "失败",
            DownloadStatus.CANCELLED: "已取消",
        }.get(download_item.status, "未知")

        status_color = {
            DownloadStatus.PENDING: "#FFA500",
            DownloadStatus.DOWNLOADING: "#0078D4",
            DownloadStatus.PAUSED: "#666666",
            DownloadStatus.COMPLETED: "#00AA00",
            DownloadStatus.FAILED: "#FF0000",
            DownloadStatus.CANCELLED: "#666666",
        }.get(download_item.status, "#666666")

        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"color: {status_color};")

        # 更新进度条
        card_layout = self.layout()  # Get the layout, should be QVBoxLayout
        if (
            download_item.status == DownloadStatus.DOWNLOADING
            and download_item.file_size == 0
        ):  # Use file_size
            # 未知大小的下载，使用无限进度条
            self.progress_bar.setVisible(False)
            if not hasattr(self, "indeterminate_bar"):
                self.indeterminate_bar = IndeterminateProgressBar(self)
                if isinstance(
                    card_layout, QVBoxLayout
                ):  # Check if layout is QVBoxLayout
                    # Insert after progress_bar
                    card_layout.insertWidget(2, self.indeterminate_bar)
                else:
                    logger.error(
                        f"下载项卡片布局错误: 布局不是QVBoxLayout类型，下载ID: {download_item.id}"
                    )
            if hasattr(
                self, "indeterminate_bar"
            ):  # Check again in case insertion failed
                self.indeterminate_bar.setVisible(True)
        else:
            # 已知大小的下载
            if hasattr(self, "indeterminate_bar"):
                self.indeterminate_bar.setVisible(False)
            self.progress_bar.setVisible(True)

            if download_item.file_size > 0:  # Use file_size
                progress = int(
                    (download_item.downloaded_size / download_item.file_size) * 100
                )  # Use file_size
                self.progress_bar.setValue(progress)
                self.percentage_label.setText(f"{progress}%")
            else:
                self.progress_bar.setValue(0)
                self.percentage_label.setText("0%")

        # 更新大小信息
        if download_item.file_size > 0:  # Use file_size
            total_mb = download_item.file_size / (1024 * 1024)  # Use file_size
            downloaded_mb = download_item.downloaded_size / (1024 * 1024)
            self.size_label.setText(f"大小: {downloaded_mb:.1f}/{total_mb:.1f} MB")
        else:
            downloaded_mb = download_item.downloaded_size / (1024 * 1024)
            self.size_label.setText(f"已下载: {downloaded_mb:.1f} MB")

        # 更新速度
        if hasattr(download_item, "speed") and download_item.speed > 0:  # Use speed
            speed_mb = download_item.speed / (1024 * 1024)  # Use speed
            if speed_mb >= 1:
                self.speed_label.setText(f"速度: {speed_mb:.1f} MB/s")
            else:
                speed_kb = download_item.speed / 1024  # Use speed
                self.speed_label.setText(f"速度: {speed_kb:.1f} KB/s")
        else:
            self.speed_label.setText("速度: --")

        # 更新预计剩余时间
        if hasattr(download_item, "eta") and download_item.eta > 0:  # Use eta
            eta_val = download_item.eta  # Use eta
            if eta_val > 3600:
                hours = int(eta_val // 3600)
                minutes = int((eta_val % 3600) // 60)
                self.eta_label.setText(f"剩余: {hours}h{minutes}m")
            elif eta_val > 60:
                minutes = int(eta_val // 60)
                seconds = int(eta_val % 60)
                self.eta_label.setText(f"剩余: {minutes}m{seconds}s")
            else:
                self.eta_label.setText(f"剩余: {int(eta_val)}s")
        else:
            self.eta_label.setText("剩余时间: --")

        # 根据状态更新按钮可用性
        self.pause_btn.setVisible(download_item.status == DownloadStatus.DOWNLOADING)
        self.resume_btn.setVisible(download_item.status == DownloadStatus.PAUSED)
        self.retry_btn.setVisible(download_item.status == DownloadStatus.FAILED)
        self.cancel_btn.setEnabled(
            download_item.status
            in [
                DownloadStatus.PENDING,
                DownloadStatus.DOWNLOADING,
                DownloadStatus.PAUSED,
            ]
        )


class DownloadManagerWidget(QWidget):
    """下载管理主窗口部件"""

    # download_id ; Renamed to avoid conflict with method name
    download_added_signal = Signal(str)
    download_completed_signal = Signal(str)  # download_id ; Renamed
    download_failed_signal = Signal(str)  # download_id ; Renamed

    def __init__(self, download_manager: DownloadManager, parent: Any = None) -> None:
        super().__init__(parent)
        self.download_manager = download_manager
        self.download_cards: Dict[str, DownloadItemCard] = {}
        self.update_timer = QTimer()

        self.init_ui()
        self.connect_signals()
        self.start_monitoring()

    def init_ui(self) -> None:
        """初始化UI"""
        main_layout = QVBoxLayout(self)  # Changed variable name
        self.setLayout(main_layout)  # Explicitly set layout
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 标题和控制按钮
        header_layout = QHBoxLayout()

        title_label = StrongBodyLabel("下载管理")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))

        self.refresh_btn = PrimaryPushButton("刷新列表")
        self.refresh_btn.setIcon(FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self.refresh_downloads)

        self.pause_all_btn = PushButton("暂停全部")
        self.pause_all_btn.setIcon(FluentIcon.PAUSE)
        self.pause_all_btn.clicked.connect(self.pause_all_downloads)

        self.resume_all_btn = PrimaryPushButton("恢复全部")
        self.resume_all_btn.setIcon(FluentIcon.PLAY)
        self.resume_all_btn.clicked.connect(self.resume_all_downloads)

        self.clear_completed_btn = PushButton("清除已完成")
        self.clear_completed_btn.setIcon(FluentIcon.DELETE)
        self.clear_completed_btn.clicked.connect(self.clear_completed_downloads)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.pause_all_btn)
        header_layout.addWidget(self.resume_all_btn)
        header_layout.addWidget(self.clear_completed_btn)

        # 统计信息
        stats_layout = QHBoxLayout()

        self.total_label = CaptionLabel("总下载: 0")
        self.active_label = CaptionLabel("进行中: 0")
        self.completed_label = CaptionLabel("已完成: 0")
        self.failed_label = CaptionLabel("失败: 0")
        self.speed_label = CaptionLabel("总速度: 0 KB/s")

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.active_label)
        stats_layout.addWidget(self.completed_label)
        stats_layout.addWidget(self.failed_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.speed_label)

        # 下载列表容器
        self.download_container = QWidget()
        self.download_layout = QVBoxLayout(self.download_container)
        self.download_layout.setContentsMargins(0, 0, 0, 0)
        self.download_layout.setSpacing(8)

        # 滚动区域
        scroll_area = ScrollArea()
        scroll_area.setWidget(self.download_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 状态栏
        self.status_label = CaptionLabel("就绪")

        # 添加到主布局
        main_layout.addLayout(header_layout)
        main_layout.addLayout(stats_layout)
        main_layout.addWidget(scroll_area, 1)
        main_layout.addWidget(self.status_label)

    def connect_signals(self) -> None:
        """连接信号"""
        # 连接下载管理器信号
        self.download_manager.download_started.connect(self.on_download_started)
        self.download_manager.download_completed.connect(self.on_download_completed)
        self.download_manager.download_failed.connect(self.on_download_failed)
        # Use download_status_changed for pause, resume, cancel InfoBars
        self.download_manager.download_status_changed.connect(
            self._on_download_status_changed_for_infobar
        )

        # 设置定时更新
        self.update_timer.timeout.connect(self.update_download_progress)

    def _on_download_status_changed_for_infobar(
        self, download_id: str, status: DownloadStatus
    ) -> None:
        """Handles status changes to show specific InfoBars for pause/cancel."""
        if status == DownloadStatus.PAUSED:
            # This method shows the InfoBar
            self.on_download_paused(download_id)
        elif status == DownloadStatus.CANCELLED:
            # This method shows the InfoBar
            self.on_download_cancelled(download_id)
        # Resumed InfoBar is handled in resume_download method

    def start_monitoring(self) -> None:
        """开始监控"""
        self.refresh_downloads()
        self.update_timer.start(1000)  # 每秒更新一次

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.update_timer.stop()

    @download_exception_handler
    def refresh_downloads(self) -> None:
        """刷新下载列表"""
        self.status_label.setText("刷新下载列表...")

        # 获取所有下载项
        downloads_dict = self.download_manager.list_downloads()  # Use list_downloads

        # Clear old cards that are no longer in the download manager's list
        current_card_ids = set(self.download_cards.keys())
        manager_ids = set(downloads_dict.keys())

        ids_to_remove = current_card_ids - manager_ids
        for download_id in ids_to_remove:
            if download_id in self.download_cards:
                self.download_cards[download_id].deleteLater()
                del self.download_cards[download_id]

        # Update existing cards and add new ones
        for download_id, download_item in downloads_dict.items():
            if download_id in self.download_cards:
                self.download_cards[download_id].update_progress(download_item)
            else:
                self.add_download_card(download_item)

        self.update_statistics()
        self.status_label.setText(f"共 {len(downloads_dict)} 个下载任务")

    def add_download_card(self, download_item: DownloadItem) -> None:
        """添加下载卡片"""
        if (
            download_item.id in self.download_cards
        ):  # Avoid duplicates if refresh logic changes
            self.download_cards[download_item.id].update_progress(download_item)
            return

        # Parent to container
        card = DownloadItemCard(download_item, self.download_container)
        card.pause_requested.connect(self.pause_download)
        card.resume_requested.connect(self.resume_download)
        card.cancel_requested.connect(self.cancel_download)
        card.retry_requested.connect(self.retry_download)

        self.download_cards[download_item.id] = card
        self.download_layout.addWidget(card)

    @download_exception_handler
    def update_download_progress(self) -> None:
        """更新下载进度"""
        active_ids_in_manager = self.download_manager.list_downloads().keys()

        # Update existing cards
        # Iterate copy for safe removal
        for download_id, card in list(self.download_cards.items()):
            if download_id not in active_ids_in_manager:
                # Item removed from manager (e.g. cleared completed)
                card.deleteLater()
                del self.download_cards[download_id]
                continue
            try:
                download_item = self.download_manager.get_download_info(download_id)
                if download_item:
                    card.update_progress(download_item)
            except Exception:  # pylint: disable=broad-except
                # Log error or handle, e can be logged if needed
                continue  # Keep UI responsive

        self.update_statistics()

    def update_statistics(self) -> None:
        """更新统计信息"""
        stats = self.download_manager.get_download_statistics()

        self.total_label.setText(f"总下载: {stats.get('total', 0)}")
        self.active_label.setText(f"进行中: {stats.get('downloading', 0)}")
        self.completed_label.setText(f"已完成: {stats.get('completed', 0)}")
        self.failed_label.setText(f"失败: {stats.get('failed', 0)}")

        total_speed = stats.get("total_speed", 0)

        if total_speed >= 1024 * 1024:  # MB/s
            speed_mb = total_speed / (1024 * 1024)
            self.speed_label.setText(f"总速度: {speed_mb:.1f} MB/s")
        else:  # KB/s
            speed_kb = total_speed / 1024
            self.speed_label.setText(f"总速度: {speed_kb:.1f} KB/s")

    @download_exception_handler
    def pause_download(self, download_id: str) -> None:
        """暂停下载"""
        if self.download_manager.pause_download(download_id):
            self.status_label.setText(f"下载 {download_id} 已暂停")
            # InfoBar will be shown by _on_download_status_changed_for_infobar
        else:
            self.status_label.setText(f"暂停下载 {download_id} 失败")

    @download_exception_handler
    def resume_download(self, download_id: str) -> None:
        """恢复下载"""
        if self.download_manager.resume_download(download_id):
            self.status_label.setText(f"下载 {download_id} 已恢复")
            self.on_download_resumed(download_id)  # Show InfoBar directly
        else:
            self.status_label.setText(f"恢复下载 {download_id} 失败")

    @download_exception_handler
    def cancel_download(self, download_id: str) -> None:
        """取消下载"""
        if self.download_manager.cancel_download(
            download_id
        ):  # Manager will set status to CANCELLED
            self.status_label.setText(f"下载 {download_id} 已取消")
            # Card removal and InfoBar will be handled by on_download_cancelled via status change
            if download_id in self.download_cards:  # Ensure card still exists
                download_info = self.download_manager.get_download_info(download_id)
                if download_info:
                    self.download_cards[download_id].update_progress(download_info)

        else:
            self.status_label.setText(f"取消下载 {download_id} 失败")

    @download_exception_handler
    def retry_download(self, download_id: str) -> None:
        """重试下载"""
        # Retry is essentially resuming a failed download
        # Use resume_download for retry
        if self.download_manager.resume_download(download_id):
            self.status_label.setText(f"下载 {download_id} 开始重试")
            # InfoBar for "resumed" or "started" will be shown
        else:
            self.status_label.setText(f"重试下载 {download_id} 失败")

    @download_exception_handler
    def pause_all_downloads(self) -> None:
        """暂停所有下载"""
        paused_count = 0
        for download_id in list(self.download_cards.keys()):  # Iterate copy
            item = self.download_manager.get_download_info(download_id)
            if item and item.status == DownloadStatus.DOWNLOADING:
                if self.download_manager.pause_download(download_id):
                    paused_count += 1

        self.status_label.setText(f"已暂停 {paused_count} 个下载")

    @download_exception_handler
    def resume_all_downloads(self) -> None:
        """恢复所有下载"""
        resumed_count = 0
        for download_id in list(self.download_cards.keys()):  # Iterate copy
            item = self.download_manager.get_download_info(download_id)
            if item and item.status == DownloadStatus.PAUSED:
                if self.download_manager.resume_download(download_id):
                    resumed_count += 1

        self.status_label.setText(f"已恢复 {resumed_count} 个下载")

    @download_exception_handler
    def clear_completed_downloads(self) -> None:
        """清除已完成的下载"""
        ids_to_remove = []
        for download_id, card_widget in list(self.download_cards.items()):
            item = card_widget.download_item  # Use the item stored in the card
            if item and item.status in [
                DownloadStatus.COMPLETED,
                DownloadStatus.CANCELLED,
                DownloadStatus.FAILED,
            ]:
                ids_to_remove.append(download_id)

        cleared_count = 0
        for download_id in ids_to_remove:
            # Remove from manager first (deletes file if specified in manager's logic)
            # Let manager handle file deletion policy
            if self.download_manager.remove_download(download_id, delete_file=False):
                # Then remove card from UI
                if download_id in self.download_cards:
                    self.download_cards[download_id].deleteLater()
                    del self.download_cards[download_id]
                cleared_count += 1

        self.status_label.setText(f"已清除 {cleared_count} 个任务")
        self.update_statistics()  # Refresh stats after clearing

    def on_download_started(self, download_id: str) -> None:
        """下载开始事件"""
        InfoBar.info(  # Changed to info
            title="下载开始",
            content=f"下载 {download_id} 已开始",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
        self.download_added_signal.emit(download_id)
        # If the card doesn't exist, add it
        if download_id not in self.download_cards:
            item = self.download_manager.get_download_info(download_id)
            if item:
                self.add_download_card(item)
        self.update_statistics()

    def on_download_completed(self, download_id: str) -> None:
        """下载完成事件"""
        InfoBar.success(
            title="下载完成",
            content=f"下载 {download_id} 已完成",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self,
        )
        self.download_completed_signal.emit(download_id)
        self.update_statistics()

    def on_download_failed(self, download_id: str, error: str) -> None:
        """下载失败事件"""
        InfoBar.error(
            title="下载失败",
            content=f"下载 {download_id} 失败: {error}",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=8000,
            parent=self,
        )
        self.download_failed_signal.emit(download_id)
        self.update_statistics()

    def on_download_paused(self, download_id: str) -> None:
        """下载暂停事件 - shows InfoBar"""
        InfoBar.info(  # Changed to info
            title="下载暂停",
            content=f"下载 {download_id} 已暂停",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
        self.update_statistics()

    def on_download_resumed(self, download_id: str) -> None:
        """下载恢复事件 - shows InfoBar"""
        InfoBar.info(  # Changed to info
            title="下载恢复",
            content=f"下载 {download_id} 已恢复",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
        self.update_statistics()

    def on_download_cancelled(self, download_id: str) -> None:
        """下载取消事件 - shows InfoBar and removes card"""
        InfoBar.info(  # Changed to info
            title="下载取消",
            content=f"下载 {download_id} 已取消",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
        # Card removal should be handled when status becomes CANCELLED and progress is updated
        if download_id in self.download_cards:
            # Optionally, make the card reflect "Cancelled" state before potential removal by clear_completed
            item_info = self.download_manager.get_download_info(download_id)
            if item_info:
                self.download_cards[download_id].update_progress(item_info)
            else:  # If removed from manager already
                self.download_cards[download_id].deleteLater()
                del self.download_cards[download_id]

        self.update_statistics()
