"""
Startup Performance Dashboard
Provides a visual interface for monitoring and debugging startup performance
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QProgressBar, QGroupBox, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QPalette
from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, PrimaryPushButton,
    InfoBar, InfoBarPosition, FluentIcon
)

from src.heal.common.logging_config import get_logger
from src.heal.common.startup_performance_monitor import (
    startup_performance_monitor, get_startup_performance_summary
)
from src.heal.common.startup_benchmarking import (
    startup_benchmarking_system, get_performance_report
)
from src.heal.common.workflow_optimizer import (
    get_all_workflow_performance, get_workflow_performance_report
)

logger = get_logger(__name__)


class PerformanceMetricsCard(CardWidget):
    """性能指标卡片"""
    
    def __init__(self, title: str, value: str, unit: str = "", status: str = "normal"):
        super().__init__()
        self.setFixedSize(200, 120)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        title_label = BodyLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Value
        value_label = TitleLabel(f"{value} {unit}")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set color based on status
        if status == "good":
            value_label.setStyleSheet("color: #10B981;")  # Green
        elif status == "warning":
            value_label.setStyleSheet("color: #F59E0B;")  # Orange
        elif status == "error":
            value_label.setStyleSheet("color: #EF4444;")  # Red
        
        layout.addWidget(value_label)
        layout.addStretch()


class BottleneckAnalysisWidget(QWidget):
    """瓶颈分析组件"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = TitleLabel("性能瓶颈分析")
        layout.addWidget(title)
        
        # Bottleneck table
        self.bottleneck_table = QTableWidget()
        self.bottleneck_table.setColumnCount(4)
        self.bottleneck_table.setHorizontalHeaderLabels(["阶段", "平均耗时", "频率", "建议"])
        self.bottleneck_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.bottleneck_table)
    
    def update_bottlenecks(self, bottlenecks: List[Dict[str, Any]]):
        """更新瓶颈数据"""
        self.bottleneck_table.setRowCount(len(bottlenecks))
        
        for row, bottleneck in enumerate(bottlenecks):
            self.bottleneck_table.setItem(row, 0, QTableWidgetItem(bottleneck.get("step_name", "Unknown")))
            self.bottleneck_table.setItem(row, 1, QTableWidgetItem(f"{bottleneck.get('average_time', 0):.2f}s"))
            self.bottleneck_table.setItem(row, 2, QTableWidgetItem(f"{bottleneck.get('executions', 0)} 次"))
            
            # Generate suggestion based on time
            avg_time = bottleneck.get('average_time', 0)
            if avg_time > 3.0:
                suggestion = "考虑异步处理或优化算法"
            elif avg_time > 1.0:
                suggestion = "可以进一步优化"
            else:
                suggestion = "性能良好"
            
            self.bottleneck_table.setItem(row, 3, QTableWidgetItem(suggestion))


class WorkflowPerformanceWidget(QWidget):
    """工作流性能组件"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = TitleLabel("工作流性能详情")
        layout.addWidget(title)
        
        # Performance text area
        self.performance_text = QTextEdit()
        self.performance_text.setReadOnly(True)
        self.performance_text.setMaximumHeight(300)
        layout.addWidget(self.performance_text)
        
        # Refresh button
        refresh_btn = PrimaryPushButton("刷新数据")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
    
    def refresh_data(self):
        """刷新工作流性能数据"""
        try:
            workflow_data = get_all_workflow_performance()
            
            # Format the data for display
            formatted_text = "=== 工作流性能概览 ===\n\n"
            formatted_text += f"总工作流数量: {workflow_data.get('total_workflows', 0)}\n\n"
            
            for workflow_name, performance in workflow_data.get('workflows', {}).items():
                if 'error' in performance:
                    formatted_text += f"工作流 {workflow_name}: 错误 - {performance['error']}\n"
                    continue
                
                formatted_text += f"工作流: {workflow_name}\n"
                formatted_text += f"  最近执行次数: {performance.get('recent_executions', 0)}\n"
                formatted_text += f"  平均总时间: {performance.get('average_total_time', 0):.2f}s\n"
                formatted_text += f"  最快时间: {performance.get('min_total_time', 0):.2f}s\n"
                formatted_text += f"  最慢时间: {performance.get('max_total_time', 0):.2f}s\n"
                formatted_text += f"  成功率: {performance.get('success_rate', 0):.1%}\n"
                formatted_text += f"  性能趋势: {performance.get('performance_trend', 'unknown')}\n"
                
                bottlenecks = performance.get('bottleneck_steps', [])
                if bottlenecks:
                    formatted_text += "  瓶颈步骤:\n"
                    for bottleneck in bottlenecks[:3]:  # Top 3
                        formatted_text += f"    - {bottleneck.get('step_name', 'Unknown')}: {bottleneck.get('average_time', 0):.2f}s\n"
                
                formatted_text += "\n"
            
            self.performance_text.setPlainText(formatted_text)
            
        except Exception as e:
            logger.error(f"刷新工作流性能数据失败: {e}")
            self.performance_text.setPlainText(f"数据加载失败: {e}")


class StartupPerformanceDashboard(QWidget):
    """启动性能仪表板"""
    
    refresh_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("启动性能仪表板")
        self.setMinimumSize(1000, 700)
        self._init_ui()
        self._setup_auto_refresh()
        self.refresh_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = TitleLabel("启动性能监控仪表板")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = PrimaryPushButton("刷新数据")
        refresh_btn.setIcon(FluentIcon.SYNC)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Metrics cards
        self.metrics_layout = QHBoxLayout()
        layout.addLayout(self.metrics_layout)
        
        # Tab widget for detailed views
        self.tab_widget = QTabWidget()
        
        # Overview tab
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "概览")
        
        # Bottleneck analysis tab
        self.bottleneck_widget = BottleneckAnalysisWidget()
        self.tab_widget.addTab(self.bottleneck_widget, "瓶颈分析")
        
        # Workflow performance tab
        self.workflow_widget = WorkflowPerformanceWidget()
        self.tab_widget.addTab(self.workflow_widget, "工作流性能")
        
        # Benchmark results tab
        self.benchmark_tab = self._create_benchmark_tab()
        self.tab_widget.addTab(self.benchmark_tab, "基准测试")
        
        layout.addWidget(self.tab_widget)
    
    def _create_overview_tab(self) -> QWidget:
        """创建概览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance summary
        summary_group = QGroupBox("性能摘要")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        # Recent performance history
        history_group = QGroupBox("最近性能历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["时间", "启动时间", "内存使用", "成功", "瓶颈"])
        history_layout.addWidget(self.history_table)
        
        layout.addWidget(history_group)
        
        return widget
    
    def _create_benchmark_tab(self) -> QWidget:
        """创建基准测试标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Benchmark controls
        controls_layout = QHBoxLayout()
        
        run_benchmark_btn = PrimaryPushButton("运行基准测试")
        run_benchmark_btn.clicked.connect(self.run_benchmark)
        controls_layout.addWidget(run_benchmark_btn)
        
        set_baseline_btn = QPushButton("设置基线")
        set_baseline_btn.clicked.connect(self.set_baseline)
        controls_layout.addWidget(set_baseline_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Benchmark results
        self.benchmark_text = QTextEdit()
        self.benchmark_text.setReadOnly(True)
        layout.addWidget(self.benchmark_text)
        
        return widget
    
    def _setup_auto_refresh(self):
        """设置自动刷新"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_data(self):
        """刷新所有数据"""
        try:
            self._update_metrics_cards()
            self._update_overview_tab()
            self._update_bottleneck_analysis()
            self._update_benchmark_results()
            
            logger.debug("性能仪表板数据已刷新")
            
        except Exception as e:
            logger.error(f"刷新仪表板数据失败: {e}")
            InfoBar.error(
                title="数据刷新失败",
                content=f"无法刷新性能数据: {e}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def _update_metrics_cards(self):
        """更新指标卡片"""
        # Clear existing cards
        for i in reversed(range(self.metrics_layout.count())):
            child = self.metrics_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        try:
            # Get performance summary
            summary = get_startup_performance_summary()
            
            if "error" in summary:
                # Show error card
                error_card = PerformanceMetricsCard("状态", "无数据", "", "error")
                self.metrics_layout.addWidget(error_card)
                return
            
            # Startup time card
            avg_time = summary.get("average_startup_time", 0)
            time_status = "good" if avg_time < 3.0 else "warning" if avg_time < 6.0 else "error"
            time_card = PerformanceMetricsCard("平均启动时间", f"{avg_time:.2f}", "秒", time_status)
            self.metrics_layout.addWidget(time_card)
            
            # Memory usage card
            avg_memory = summary.get("average_memory_usage", 0)
            memory_status = "good" if avg_memory < 150 else "warning" if avg_memory < 250 else "error"
            memory_card = PerformanceMetricsCard("平均内存使用", f"{avg_memory:.1f}", "MB", memory_status)
            self.metrics_layout.addWidget(memory_card)
            
            # Success rate card
            success_rate = summary.get("success_rate", 0)
            success_status = "good" if success_rate > 0.95 else "warning" if success_rate > 0.8 else "error"
            success_card = PerformanceMetricsCard("成功率", f"{success_rate:.1%}", "", success_status)
            self.metrics_layout.addWidget(success_card)
            
            # Total startups card
            total_startups = summary.get("total_startups_recorded", 0)
            startups_card = PerformanceMetricsCard("记录启动次数", str(total_startups), "次", "normal")
            self.metrics_layout.addWidget(startups_card)
            
        except Exception as e:
            logger.error(f"更新指标卡片失败: {e}")
    
    def _update_overview_tab(self):
        """更新概览标签页"""
        try:
            summary = get_startup_performance_summary()
            
            # Update summary text
            if "error" in summary:
                self.summary_text.setPlainText(f"错误: {summary['error']}")
                return
            
            summary_text = f"""
启动性能概览:
- 应用名称: {summary.get('app_name', 'Unknown')}
- 总记录启动次数: {summary.get('total_startups_recorded', 0)}
- 最近启动次数: {summary.get('recent_startups', 0)}
- 平均启动时间: {summary.get('average_startup_time', 0):.2f} 秒
- 最快启动时间: {summary.get('fastest_startup', 0):.2f} 秒
- 最慢启动时间: {summary.get('slowest_startup', 0):.2f} 秒
- 平均内存使用: {summary.get('average_memory_usage', 0):.1f} MB
- 成功率: {summary.get('success_rate', 0):.1%}

最新启动信息:
- 总时间: {summary.get('latest_startup', {}).get('total_time', 0):.2f} 秒
- 内存使用: {summary.get('latest_startup', {}).get('memory_end', 0):.1f} MB
- 成功: {'是' if summary.get('latest_startup', {}).get('success', False) else '否'}
"""
            
            self.summary_text.setPlainText(summary_text)
            
        except Exception as e:
            logger.error(f"更新概览标签页失败: {e}")
    
    def _update_bottleneck_analysis(self):
        """更新瓶颈分析"""
        try:
            # Get workflow performance data
            workflow_data = get_workflow_performance_report("main_app_initialization")
            
            if "error" not in workflow_data:
                bottlenecks = workflow_data.get("bottleneck_steps", [])
                self.bottleneck_widget.update_bottlenecks(bottlenecks)
            
        except Exception as e:
            logger.error(f"更新瓶颈分析失败: {e}")
    
    def _update_benchmark_results(self):
        """更新基准测试结果"""
        try:
            report = get_performance_report()
            
            if "error" in report:
                self.benchmark_text.setPlainText(f"基准测试数据不可用: {report['error']}")
                return
            
            # Format benchmark report
            formatted_report = "=== 基准测试报告 ===\n\n"
            
            summary = report.get("summary", {})
            formatted_report += f"总基准测试次数: {summary.get('total_benchmarks', 0)}\n"
            formatted_report += f"性能趋势: {summary.get('trend', 'unknown')}\n\n"
            
            latest = summary.get("latest_performance", {})
            if latest:
                formatted_report += "最新性能:\n"
                formatted_report += f"  启动时间: {latest.get('startup_time', 0):.2f} 秒\n"
                formatted_report += f"  内存使用: {latest.get('memory_usage', 0):.1f} MB\n"
                formatted_report += f"  优化分数: {latest.get('optimization_score', 0):.1f}/100\n"
                formatted_report += f"  成功率: {latest.get('success_rate', 0):.1%}\n\n"
            
            recommendations = report.get("recommendations", [])
            if recommendations:
                formatted_report += "优化建议:\n"
                for i, rec in enumerate(recommendations, 1):
                    formatted_report += f"  {i}. {rec}\n"
            
            self.benchmark_text.setPlainText(formatted_report)
            
        except Exception as e:
            logger.error(f"更新基准测试结果失败: {e}")
    
    def run_benchmark(self):
        """运行基准测试"""
        try:
            InfoBar.info(
                title="基准测试",
                content="正在运行基准测试，请稍候...",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
            # Run benchmark with 5 runs for quick testing
            result = startup_benchmarking_system.run_benchmark(num_runs=5)
            
            InfoBar.success(
                title="基准测试完成",
                content=f"平均启动时间: {result.average_startup_time:.2f}s",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            
            # Refresh benchmark results
            self._update_benchmark_results()
            
        except Exception as e:
            logger.error(f"运行基准测试失败: {e}")
            InfoBar.error(
                title="基准测试失败",
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def set_baseline(self):
        """设置性能基线"""
        try:
            startup_benchmarking_system.set_baseline()
            
            InfoBar.success(
                title="基线设置成功",
                content="当前性能已设置为基线",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            logger.error(f"设置基线失败: {e}")
            InfoBar.error(
                title="设置基线失败",
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )


def show_startup_performance_dashboard() -> StartupPerformanceDashboard:
    """显示启动性能仪表板"""
    dashboard = StartupPerformanceDashboard()
    dashboard.show()
    return dashboard
