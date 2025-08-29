"""
Loading Progress Widget
Provides visual feedback system to show startup and loading progress to users
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QTextEdit, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen
from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, CaptionLabel,
    ProgressBar, IndeterminateProgressBar, FluentIcon,
    InfoBar, InfoBarPosition
)

from ...common.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class LoadingStep:
    """加载步骤"""
    step_id: str
    name: str
    description: str = ""
    estimated_time: float = 1.0  # seconds
    is_critical: bool = True
    
    # Runtime state
    is_started: bool = False
    is_completed: bool = False
    is_failed: bool = False
    actual_time: float = 0.0
    start_time: float = 0.0
    error_message: str = ""


class LoadingProgressWidget(CardWidget):
    """加载进度组件"""
    
    # Signals
    step_started = Signal(str)      # step_id
    step_completed = Signal(str)    # step_id
    step_failed = Signal(str, str)  # step_id, error_message
    loading_finished = Signal(bool) # success
    
    def __init__(self, title: str = "正在加载...", show_details: bool = True):
        super().__init__()
        self.title = title
        self.show_details = show_details
        self.logger = logger.bind(component="LoadingProgressWidget")
        
        # Loading state
        self.loading_steps: Dict[str, LoadingStep] = {}
        self.step_order: List[str] = []
        self.current_step_index = 0
        self.total_estimated_time = 0.0
        self.start_time = 0.0
        self.is_loading = False
        
        # UI components
        self.progress_bar: Optional[ProgressBar] = None
        self.current_step_label: Optional[BodyLabel] = None
        self.time_label: Optional[CaptionLabel] = None
        self.details_text: Optional[QTextEdit] = None
        
        # Animation
        self.fade_animation: Optional[QPropertyAnimation] = None
        
        self._init_ui()
        self._setup_timer()
    
    def _init_ui(self):
        """初始化UI"""
        self.setFixedSize(400, 300 if self.show_details else 150)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = TitleLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Progress bar
        self.progress_bar = ProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Current step info
        step_layout = QVBoxLayout()
        
        self.current_step_label = BodyLabel("准备中...")
        self.current_step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_layout.addWidget(self.current_step_label)
        
        self.time_label = CaptionLabel("预计时间: --")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_layout.addWidget(self.time_label)
        
        layout.addLayout(step_layout)
        
        # Details section (optional)
        if self.show_details:
            details_frame = QFrame()
            details_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            details_layout = QVBoxLayout(details_frame)
            
            details_title = BodyLabel("详细信息:")
            details_layout.addWidget(details_title)
            
            self.details_text = QTextEdit()
            self.details_text.setReadOnly(True)
            self.details_text.setMaximumHeight(100)
            self.details_text.setFont(QFont("Consolas", 9))
            details_layout.addWidget(self.details_text)
            
            layout.addWidget(details_frame)
        
        layout.addStretch()
    
    def _setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_time_display)
        self.update_timer.setInterval(100)  # Update every 100ms
    
    def add_loading_step(self, step_id: str, name: str, description: str = "",
                        estimated_time: float = 1.0, is_critical: bool = True) -> None:
        """添加加载步骤"""
        step = LoadingStep(
            step_id=step_id,
            name=name,
            description=description,
            estimated_time=estimated_time,
            is_critical=is_critical
        )
        
        self.loading_steps[step_id] = step
        self.step_order.append(step_id)
        self.total_estimated_time += estimated_time
        
        self.logger.debug(f"Added loading step: {step_id} ({name})")
    
    def start_loading(self) -> None:
        """开始加载"""
        if self.is_loading:
            self.logger.warning("Loading already in progress")
            return
        
        if not self.step_order:
            self.logger.warning("No loading steps defined")
            return
        
        self.is_loading = True
        self.start_time = time.time()
        self.current_step_index = 0
        
        # Reset all steps
        for step in self.loading_steps.values():
            step.is_started = False
            step.is_completed = False
            step.is_failed = False
            step.actual_time = 0.0
            step.start_time = 0.0
            step.error_message = ""
        
        # Start timer
        self.update_timer.start()
        
        # Update UI
        self.progress_bar.setValue(0)
        self._update_current_step_display()
        
        self.logger.info(f"Started loading with {len(self.step_order)} steps")
    
    def start_step(self, step_id: str) -> None:
        """开始执行步骤"""
        if step_id not in self.loading_steps:
            self.logger.error(f"Step {step_id} not found")
            return
        
        step = self.loading_steps[step_id]
        if step.is_started:
            self.logger.warning(f"Step {step_id} already started")
            return
        
        step.is_started = True
        step.start_time = time.time()
        
        # Update current step index
        if step_id in self.step_order:
            self.current_step_index = self.step_order.index(step_id)
        
        self._update_current_step_display()
        self._add_detail_message(f"开始: {step.name}")
        
        self.step_started.emit(step_id)
        self.logger.debug(f"Started step: {step_id}")
    
    def complete_step(self, step_id: str, success: bool = True, error_message: str = "") -> None:
        """完成步骤"""
        if step_id not in self.loading_steps:
            self.logger.error(f"Step {step_id} not found")
            return
        
        step = self.loading_steps[step_id]
        if not step.is_started:
            self.logger.warning(f"Step {step_id} not started")
            return
        
        if step.is_completed or step.is_failed:
            self.logger.warning(f"Step {step_id} already completed")
            return
        
        step.actual_time = time.time() - step.start_time
        
        if success:
            step.is_completed = True
            self._add_detail_message(f"完成: {step.name} ({step.actual_time:.2f}s)")
            self.step_completed.emit(step_id)
        else:
            step.is_failed = True
            step.error_message = error_message
            self._add_detail_message(f"失败: {step.name} - {error_message}")
            self.step_failed.emit(step_id, error_message)
        
        # Update progress
        self._update_progress()
        
        # Check if all steps are done
        if self._all_steps_done():
            self._finish_loading()
        else:
            # Move to next step
            self._advance_to_next_step()
        
        self.logger.debug(f"Completed step: {step_id} (success: {success})")
    
    def _update_current_step_display(self) -> None:
        """更新当前步骤显示"""
        if self.current_step_index >= len(self.step_order):
            return
        
        current_step_id = self.step_order[self.current_step_index]
        current_step = self.loading_steps[current_step_id]
        
        self.current_step_label.setText(current_step.name)
        
        # Update estimated time
        remaining_time = self._calculate_remaining_time()
        if remaining_time > 0:
            self.time_label.setText(f"预计剩余时间: {remaining_time:.1f}s")
        else:
            self.time_label.setText("计算中...")
    
    def _update_time_display(self) -> None:
        """更新时间显示"""
        if not self.is_loading:
            return
        
        elapsed_time = time.time() - self.start_time
        remaining_time = self._calculate_remaining_time()
        
        if remaining_time > 0:
            self.time_label.setText(f"已用时间: {elapsed_time:.1f}s | 预计剩余: {remaining_time:.1f}s")
        else:
            self.time_label.setText(f"已用时间: {elapsed_time:.1f}s")
    
    def _calculate_remaining_time(self) -> float:
        """计算剩余时间"""
        if not self.step_order:
            return 0.0
        
        total_remaining = 0.0
        
        for i in range(self.current_step_index, len(self.step_order)):
            step_id = self.step_order[i]
            step = self.loading_steps[step_id]
            
            if step.is_completed or step.is_failed:
                continue
            elif step.is_started:
                # Use remaining estimated time for current step
                elapsed = time.time() - step.start_time
                remaining = max(0, step.estimated_time - elapsed)
                total_remaining += remaining
            else:
                # Use full estimated time for future steps
                total_remaining += step.estimated_time
        
        return total_remaining
    
    def _update_progress(self) -> None:
        """更新进度条"""
        if not self.step_order:
            return
        
        completed_steps = sum(1 for step in self.loading_steps.values() 
                            if step.is_completed or step.is_failed)
        progress = int((completed_steps / len(self.step_order)) * 100)
        
        self.progress_bar.setValue(progress)
    
    def _advance_to_next_step(self) -> None:
        """前进到下一步"""
        self.current_step_index += 1
        if self.current_step_index < len(self.step_order):
            self._update_current_step_display()
    
    def _all_steps_done(self) -> bool:
        """检查是否所有步骤都完成"""
        return all(step.is_completed or step.is_failed 
                  for step in self.loading_steps.values())
    
    def _finish_loading(self) -> None:
        """完成加载"""
        self.is_loading = False
        self.update_timer.stop()
        
        # Calculate final statistics
        total_time = time.time() - self.start_time
        successful_steps = sum(1 for step in self.loading_steps.values() if step.is_completed)
        failed_steps = sum(1 for step in self.loading_steps.values() if step.is_failed)
        
        success = failed_steps == 0 or all(
            not step.is_critical for step in self.loading_steps.values() if step.is_failed
        )
        
        # Update UI
        self.progress_bar.setValue(100)
        if success:
            self.current_step_label.setText("加载完成!")
            self.time_label.setText(f"总用时: {total_time:.2f}s")
        else:
            self.current_step_label.setText("加载失败!")
            self.time_label.setText(f"失败于 {total_time:.2f}s")
        
        self._add_detail_message(f"加载完成: 成功 {successful_steps}, 失败 {failed_steps}")
        
        # Emit signal
        self.loading_finished.emit(success)
        
        self.logger.info(f"Loading finished: success={success}, time={total_time:.2f}s")
    
    def _add_detail_message(self, message: str) -> None:
        """添加详细信息"""
        if not self.details_text:
            return
        
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.details_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_indeterminate_progress(self, enabled: bool) -> None:
        """设置不确定进度模式"""
        if enabled:
            # Replace with indeterminate progress bar
            if isinstance(self.progress_bar, ProgressBar):
                layout = self.progress_bar.parent().layout()
                index = layout.indexOf(self.progress_bar)
                self.progress_bar.setParent(None)
                
                self.progress_bar = IndeterminateProgressBar()
                layout.insertWidget(index, self.progress_bar)
        else:
            # Replace with regular progress bar
            if isinstance(self.progress_bar, IndeterminateProgressBar):
                layout = self.progress_bar.parent().layout()
                index = layout.indexOf(self.progress_bar)
                self.progress_bar.setParent(None)
                
                self.progress_bar = ProgressBar()
                self.progress_bar.setMinimum(0)
                self.progress_bar.setMaximum(100)
                layout.insertWidget(index, self.progress_bar)
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """获取加载统计"""
        if not self.is_loading and self.start_time == 0:
            return {"status": "not_started"}
        
        elapsed_time = time.time() - self.start_time if self.start_time > 0 else 0
        
        step_details = []
        for step_id in self.step_order:
            step = self.loading_steps[step_id]
            step_details.append({
                "step_id": step_id,
                "name": step.name,
                "is_started": step.is_started,
                "is_completed": step.is_completed,
                "is_failed": step.is_failed,
                "actual_time": step.actual_time,
                "estimated_time": step.estimated_time,
                "error_message": step.error_message
            })
        
        return {
            "status": "loading" if self.is_loading else "finished",
            "elapsed_time": elapsed_time,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.step_order),
            "completed_steps": sum(1 for s in self.loading_steps.values() if s.is_completed),
            "failed_steps": sum(1 for s in self.loading_steps.values() if s.is_failed),
            "estimated_total_time": self.total_estimated_time,
            "remaining_time": self._calculate_remaining_time(),
            "step_details": step_details
        }
    
    def reset(self) -> None:
        """重置加载状态"""
        self.is_loading = False
        self.update_timer.stop()
        self.current_step_index = 0
        self.start_time = 0.0
        
        # Reset UI
        self.progress_bar.setValue(0)
        self.current_step_label.setText("准备中...")
        self.time_label.setText("预计时间: --")
        
        if self.details_text:
            self.details_text.clear()
        
        # Reset steps
        for step in self.loading_steps.values():
            step.is_started = False
            step.is_completed = False
            step.is_failed = False
            step.actual_time = 0.0
            step.start_time = 0.0
            step.error_message = ""
        
        self.logger.debug("Loading progress widget reset")


class StartupProgressWidget(LoadingProgressWidget):
    """启动进度组件"""
    
    def __init__(self):
        super().__init__("应用启动中...", show_details=True)
        self._setup_startup_steps()
    
    def _setup_startup_steps(self):
        """设置启动步骤"""
        startup_steps = [
            ("config_validation", "配置验证", "验证配置文件", 0.5, True),
            ("logging_setup", "日志初始化", "设置日志系统", 0.2, True),
            ("i18n_setup", "国际化设置", "加载语言文件", 0.3, True),
            ("qt_application", "Qt应用创建", "创建应用实例", 0.5, True),
            ("theme_init", "主题初始化", "加载应用主题", 0.3, False),
            ("window_init", "窗口初始化", "创建主窗口", 1.0, True),
            ("navigation_init", "导航初始化", "设置导航系统", 0.5, True),
            ("font_check", "字体检查", "检查系统字体", 2.0, False),
            ("splash_finish", "启动画面", "关闭启动画面", 0.1, False),
            ("signal_connection", "信号连接", "连接应用信号", 0.2, True),
            ("initial_setup", "初始设置", "处理初始配置", 1.0, False),
            ("onboarding_init", "引导系统", "初始化用户引导", 0.5, False),
        ]
        
        for step_id, name, description, estimated_time, is_critical in startup_steps:
            self.add_loading_step(step_id, name, description, estimated_time, is_critical)
