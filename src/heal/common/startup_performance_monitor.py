"""
Startup Performance Monitor
Provides detailed monitoring and analysis of application startup performance
"""

import time
import psutil
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import json

from .logging_config import get_logger
from .workflow_optimizer import WorkflowOptimizer, get_workflow_performance_report

logger = get_logger(__name__)


@dataclass
class StartupPhase:
    """启动阶段定义"""
    name: str
    description: str
    critical: bool = True
    expected_duration: float = 1.0  # seconds
    max_memory_increase: float = 50.0  # MB


@dataclass
class StartupMetrics:
    """启动性能指标"""
    total_startup_time: float = 0.0
    memory_usage_start: float = 0.0
    memory_usage_end: float = 0.0
    memory_peak: float = 0.0
    cpu_usage_average: float = 0.0
    phase_timings: Dict[str, float] = field(default_factory=dict)
    phase_memory_deltas: Dict[str, float] = field(default_factory=dict)
    bottleneck_phases: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)
    startup_success: bool = True
    error_details: Optional[str] = None


class StartupPerformanceMonitor:
    """启动性能监控器"""
    
    def __init__(self, app_name: str = "HEAL"):
        self.app_name = app_name
        self.logger = logger.bind(component="StartupPerformanceMonitor")
        self._monitoring_active = False
        self._startup_start_time = 0.0
        self._current_metrics = StartupMetrics()
        self._performance_history: List[StartupMetrics] = []
        self._lock = threading.Lock()
        
        # Define standard startup phases
        self.startup_phases = {
            "config_validation": StartupPhase(
                "配置验证", "验证和加载配置文件", True, 0.5, 10.0
            ),
            "logging_setup": StartupPhase(
                "日志初始化", "设置日志系统", True, 0.2, 5.0
            ),
            "i18n_setup": StartupPhase(
                "国际化设置", "设置语言和翻译", True, 0.3, 10.0
            ),
            "qt_application": StartupPhase(
                "Qt应用创建", "创建Qt应用实例", True, 0.5, 20.0
            ),
            "theme_init": StartupPhase(
                "主题初始化", "初始化应用主题", False, 0.3, 15.0
            ),
            "window_init": StartupPhase(
                "窗口初始化", "创建主窗口", True, 1.0, 30.0
            ),
            "navigation_init": StartupPhase(
                "导航初始化", "设置导航系统", True, 0.5, 20.0
            ),
            "font_check": StartupPhase(
                "字体检查", "检查和加载字体", False, 2.0, 10.0
            ),
            "splash_finish": StartupPhase(
                "启动画面完成", "关闭启动画面", False, 0.1, 5.0
            ),
            "signal_connection": StartupPhase(
                "信号连接", "连接应用信号", True, 0.2, 5.0
            ),
            "initial_setup": StartupPhase(
                "初始设置", "处理登录和初始配置", False, 1.0, 15.0
            ),
            "onboarding_init": StartupPhase(
                "引导系统初始化", "初始化用户引导系统", False, 0.5, 25.0
            )
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            "total_startup_time": 10.0,  # seconds
            "memory_increase": 200.0,    # MB
            "phase_timeout_multiplier": 3.0  # times expected duration
        }
    
    def start_monitoring(self) -> None:
        """开始监控启动过程"""
        with self._lock:
            if self._monitoring_active:
                self.logger.warning("启动监控已经在运行")
                return
                
            self._monitoring_active = True
            self._startup_start_time = time.time()
            self._current_metrics = StartupMetrics()
            
            # Capture initial system state
            try:
                process = psutil.Process()
                self._current_metrics.memory_usage_start = process.memory_info().rss / 1024 / 1024
                self._current_metrics.memory_peak = self._current_metrics.memory_usage_start
            except Exception as e:
                self.logger.warning(f"无法获取初始内存使用量: {e}")
                
            self.logger.info(f"开始监控 {self.app_name} 启动性能")
    
    def record_phase_start(self, phase_name: str) -> None:
        """记录阶段开始"""
        if not self._monitoring_active:
            return
            
        current_time = time.time()
        phase_key = f"{phase_name}_start"
        self._current_metrics.phase_timings[phase_key] = current_time
        
        self.logger.debug(f"启动阶段开始: {phase_name}")
    
    def record_phase_end(self, phase_name: str, success: bool = True, error: Optional[str] = None) -> None:
        """记录阶段结束"""
        if not self._monitoring_active:
            return
            
        current_time = time.time()
        start_key = f"{phase_name}_start"
        duration_key = f"{phase_name}_duration"
        
        if start_key in self._current_metrics.phase_timings:
            duration = current_time - self._current_metrics.phase_timings[start_key]
            self._current_metrics.phase_timings[duration_key] = duration
            
            # Record memory usage for this phase
            try:
                process = psutil.Process()
                current_memory = process.memory_info().rss / 1024 / 1024
                
                if phase_name in self._current_metrics.phase_memory_deltas:
                    memory_delta = current_memory - self._current_metrics.phase_memory_deltas[phase_name]
                else:
                    memory_delta = current_memory - self._current_metrics.memory_usage_start
                    
                self._current_metrics.phase_memory_deltas[phase_name] = memory_delta
                self._current_metrics.memory_peak = max(self._current_metrics.memory_peak, current_memory)
                
            except Exception as e:
                self.logger.warning(f"无法记录阶段 {phase_name} 的内存使用: {e}")
            
            # Check for performance issues
            self._analyze_phase_performance(phase_name, duration, success, error)
            
            self.logger.debug(f"启动阶段完成: {phase_name}, 耗时: {duration:.3f}s")
        else:
            self.logger.warning(f"阶段 {phase_name} 没有记录开始时间")
    
    def _analyze_phase_performance(self, phase_name: str, duration: float, 
                                 success: bool, error: Optional[str]) -> None:
        """分析阶段性能"""
        phase_info = self.startup_phases.get(phase_name)
        if not phase_info:
            return
            
        # Check duration against expected time
        if duration > phase_info.expected_duration * self.performance_thresholds["phase_timeout_multiplier"]:
            self._current_metrics.bottleneck_phases.append(phase_name)
            self._current_metrics.optimization_opportunities.append(
                f"阶段 {phase_name} 耗时 {duration:.2f}s，超过预期 {phase_info.expected_duration}s"
            )
        
        # Check memory usage
        memory_delta = self._current_metrics.phase_memory_deltas.get(phase_name, 0)
        if memory_delta > phase_info.max_memory_increase:
            self._current_metrics.optimization_opportunities.append(
                f"阶段 {phase_name} 内存增加 {memory_delta:.1f}MB，超过预期 {phase_info.max_memory_increase}MB"
            )
        
        # Record errors
        if not success and error:
            self._current_metrics.startup_success = False
            if self._current_metrics.error_details:
                self._current_metrics.error_details += f"; {phase_name}: {error}"
            else:
                self._current_metrics.error_details = f"{phase_name}: {error}"
    
    def finish_monitoring(self) -> StartupMetrics:
        """完成监控并返回结果"""
        with self._lock:
            if not self._monitoring_active:
                self.logger.warning("启动监控未在运行")
                return StartupMetrics()
                
            self._monitoring_active = False
            
            # Calculate total startup time
            self._current_metrics.total_startup_time = time.time() - self._startup_start_time
            
            # Capture final memory state
            try:
                process = psutil.Process()
                self._current_metrics.memory_usage_end = process.memory_info().rss / 1024 / 1024
            except Exception as e:
                self.logger.warning(f"无法获取最终内存使用量: {e}")
            
            # Store in history
            self._performance_history.append(self._current_metrics)
            if len(self._performance_history) > 50:  # Keep last 50 startup records
                self._performance_history.pop(0)
            
            # Generate final analysis
            self._generate_startup_analysis()
            
            self.logger.info(
                f"{self.app_name} 启动监控完成: "
                f"总耗时 {self._current_metrics.total_startup_time:.2f}s, "
                f"内存使用 {self._current_metrics.memory_usage_end:.1f}MB"
            )
            
            return self._current_metrics
    
    def _generate_startup_analysis(self) -> None:
        """生成启动分析报告"""
        metrics = self._current_metrics
        
        # Check overall performance
        if metrics.total_startup_time > self.performance_thresholds["total_startup_time"]:
            metrics.optimization_opportunities.append(
                f"总启动时间 {metrics.total_startup_time:.2f}s 超过阈值 "
                f"{self.performance_thresholds['total_startup_time']}s"
            )
        
        memory_increase = metrics.memory_usage_end - metrics.memory_usage_start
        if memory_increase > self.performance_thresholds["memory_increase"]:
            metrics.optimization_opportunities.append(
                f"启动过程内存增加 {memory_increase:.1f}MB 超过阈值 "
                f"{self.performance_thresholds['memory_increase']}MB"
            )
        
        # Identify top bottlenecks
        phase_durations = {
            phase: duration for phase, duration in metrics.phase_timings.items()
            if phase.endswith("_duration")
        }
        
        if phase_durations:
            sorted_phases = sorted(phase_durations.items(), key=lambda x: x[1], reverse=True)
            top_bottlenecks = [phase.replace("_duration", "") for phase, _ in sorted_phases[:3]]
            metrics.bottleneck_phases.extend(top_bottlenecks)
            
        # Remove duplicates
        metrics.bottleneck_phases = list(set(metrics.bottleneck_phases))
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self._performance_history:
            return {"error": "No performance data available"}
        
        recent_metrics = self._performance_history[-10:]  # Last 10 startups
        
        return {
            "app_name": self.app_name,
            "total_startups_recorded": len(self._performance_history),
            "recent_startups": len(recent_metrics),
            "average_startup_time": sum(m.total_startup_time for m in recent_metrics) / len(recent_metrics),
            "fastest_startup": min(m.total_startup_time for m in recent_metrics),
            "slowest_startup": max(m.total_startup_time for m in recent_metrics),
            "average_memory_usage": sum(m.memory_usage_end for m in recent_metrics) / len(recent_metrics),
            "common_bottlenecks": self._get_common_bottlenecks(recent_metrics),
            "success_rate": sum(1 for m in recent_metrics if m.startup_success) / len(recent_metrics),
            "latest_startup": {
                "total_time": self._current_metrics.total_startup_time,
                "memory_end": self._current_metrics.memory_usage_end,
                "success": self._current_metrics.startup_success,
                "bottlenecks": self._current_metrics.bottleneck_phases
            }
        }
    
    def _get_common_bottlenecks(self, metrics_list: List[StartupMetrics]) -> List[Dict[str, Any]]:
        """获取常见瓶颈"""
        bottleneck_counts = {}
        for metrics in metrics_list:
            for bottleneck in metrics.bottleneck_phases:
                bottleneck_counts[bottleneck] = bottleneck_counts.get(bottleneck, 0) + 1
        
        return [
            {"phase": phase, "frequency": count, "percentage": count / len(metrics_list) * 100}
            for phase, count in sorted(bottleneck_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def save_performance_data(self, file_path: Optional[Path] = None) -> bool:
        """保存性能数据到文件"""
        if not file_path:
            file_path = Path("logs") / "startup_performance.json"
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "app_name": self.app_name,
                "performance_history": [
                    {
                        "total_startup_time": m.total_startup_time,
                        "memory_usage_start": m.memory_usage_start,
                        "memory_usage_end": m.memory_usage_end,
                        "memory_peak": m.memory_peak,
                        "phase_timings": m.phase_timings,
                        "phase_memory_deltas": m.phase_memory_deltas,
                        "bottleneck_phases": m.bottleneck_phases,
                        "optimization_opportunities": m.optimization_opportunities,
                        "startup_success": m.startup_success,
                        "error_details": m.error_details
                    }
                    for m in self._performance_history
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"性能数据已保存到 {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存性能数据失败: {e}")
            return False


# Global startup performance monitor instance
startup_performance_monitor = StartupPerformanceMonitor()


# Convenience functions
def start_startup_monitoring() -> None:
    """开始启动监控"""
    startup_performance_monitor.start_monitoring()


def record_startup_phase(phase_name: str, start: bool = True, success: bool = True, error: Optional[str] = None) -> None:
    """记录启动阶段"""
    if start:
        startup_performance_monitor.record_phase_start(phase_name)
    else:
        startup_performance_monitor.record_phase_end(phase_name, success, error)


def finish_startup_monitoring() -> StartupMetrics:
    """完成启动监控"""
    return startup_performance_monitor.finish_monitoring()


def get_startup_performance_summary() -> Dict[str, Any]:
    """获取启动性能摘要"""
    return startup_performance_monitor.get_performance_summary()
