"""
Unified Debug System
Consolidates all debug-related functionality into a single, cohesive system
that provides comprehensive debugging capabilities across the application.
"""

from typing import Any, Dict, List, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import traceback
import threading
from pathlib import Path
from collections import defaultdict, deque

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QWidget

from ...common.logging_config import get_logger

logger = get_logger(__name__)


class DebugLevel(Enum):
    """Debug information levels"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DebugCategory(Enum):
    """Debug categories"""
    PERFORMANCE = "performance"
    STARTUP = "startup"
    UI = "ui"
    NETWORK = "network"
    DATABASE = "database"
    COMPONENT = "component"
    SYSTEM = "system"
    USER_ACTION = "user_action"


@dataclass
class DebugEvent:
    """Debug event data structure"""
    event_id: str
    timestamp: float
    level: DebugLevel
    category: DebugCategory
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    thread_id: Optional[int] = None
    correlation_id: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    metric_id: str
    name: str
    value: Union[int, float]
    unit: str
    timestamp: float
    component: str
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedDebugSystem(QObject):
    """
    Unified debug system that consolidates:
    - Performance monitoring and analysis
    - Startup performance tracking
    - Component debugging
    - System diagnostics
    - Debug UI coordination
    """
    
    # Unified signals
    debug_event_logged = Signal(str)  # event_id
    performance_metric_recorded = Signal(str)  # metric_id
    debug_session_started = Signal(str)  # session_id
    debug_session_ended = Signal(str)  # session_id
    critical_issue_detected = Signal(str, str)  # component, issue
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger(f"{__name__}.UnifiedDebugSystem")
        
        # Debug data storage
        self.debug_events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.performance_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Component monitoring
        self.monitored_components: Set[str] = set()
        self.component_states: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.startup_phases: List[Dict[str, Any]] = []
        self.performance_benchmarks: Dict[str, float] = {}
        self.memory_snapshots: List[Dict[str, Any]] = []
        
        # Debug configuration
        self.debug_config = {
            'enabled': True,
            'log_level': DebugLevel.DEBUG,
            'categories_enabled': set(DebugCategory),
            'performance_monitoring': True,
            'memory_monitoring': True,
            'auto_save_interval': 300,  # 5 minutes
        }
        
        # Timers
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_debug_data)
        self.auto_save_timer.start(self.debug_config['auto_save_interval'] * 1000)
        
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._collect_performance_metrics)
        self.performance_timer.start(5000)  # Collect every 5 seconds
        
        # File paths
        self.debug_data_file = Path("debug/debug_events.json")
        self.performance_data_file = Path("debug/performance_metrics.json")
        
        # Initialize
        self._load_debug_configuration()
        
        self.logger.info("UnifiedDebugSystem initialized")
    
    def start_debug_session(self, session_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new debug session"""
        session_id = f"session_{int(time.time() * 1000)}"
        
        session_data = {
            'session_id': session_id,
            'name': session_name,
            'start_time': time.time(),
            'metadata': metadata or {},
            'events': [],
            'metrics': [],
            'active': True
        }
        
        self.active_sessions[session_id] = session_data
        self.debug_session_started.emit(session_id)
        
        self.logger.info(f"Debug session started: {session_name} ({session_id})")
        return session_id
    
    def end_debug_session(self, session_id: str) -> bool:
        """End a debug session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session['end_time'] = time.time()
        session['duration'] = session['end_time'] - session['start_time']
        session['active'] = False
        
        self.debug_session_ended.emit(session_id)
        
        self.logger.info(f"Debug session ended: {session['name']} ({session_id})")
        return True
    
    def log_debug_event(
        self,
        component: str,
        message: str,
        level: DebugLevel = DebugLevel.DEBUG,
        category: DebugCategory = DebugCategory.COMPONENT,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """Log a debug event"""
        
        if not self._should_log_event(level, category):
            return ""
        
        event_id = f"event_{int(time.time() * 1000000)}"
        
        # Create debug event
        event = DebugEvent(
            event_id=event_id,
            timestamp=time.time(),
            level=level,
            category=category,
            component=component,
            message=message,
            details=details or {},
            stack_trace=traceback.format_stack() if level in [DebugLevel.ERROR, DebugLevel.CRITICAL] else None,
            thread_id=threading.get_ident(),
            correlation_id=correlation_id
        )
        
        # Store event
        self.debug_events.append(event)
        
        # Add to active sessions
        for session in self.active_sessions.values():
            if session['active']:
                session['events'].append(event_id)
        
        # Check for critical issues
        if level == DebugLevel.CRITICAL:
            self.critical_issue_detected.emit(component, message)
        
        # Emit signal
        self.debug_event_logged.emit(event_id)
        
        return event_id
    
    def record_performance_metric(
        self,
        name: str,
        value: Union[int, float],
        unit: str,
        component: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record a performance metric"""
        
        metric_id = f"metric_{int(time.time() * 1000000)}"
        
        metric = PerformanceMetric(
            metric_id=metric_id,
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            component=component,
            category=category,
            metadata=metadata or {}
        )
        
        # Store metric
        self.performance_metrics[component].append(metric)
        
        # Limit metrics per component
        if len(self.performance_metrics[component]) > 1000:
            self.performance_metrics[component] = self.performance_metrics[component][-1000:]
        
        # Add to active sessions
        for session in self.active_sessions.values():
            if session['active']:
                session['metrics'].append(metric_id)
        
        # Emit signal
        self.performance_metric_recorded.emit(metric_id)
        
        return metric_id
    
    def monitor_component(self, component_name: str, widget: Optional[QWidget] = None) -> None:
        """Start monitoring a component"""
        self.monitored_components.add(component_name)
        
        if widget:
            # Setup widget monitoring
            self._setup_widget_monitoring(component_name, widget)
        
        # Initialize component state
        self.component_states[component_name] = {
            'start_time': time.time(),
            'widget': widget,
            'events': [],
            'metrics': [],
            'status': 'active'
        }
        
        self.logger.debug(f"Started monitoring component: {component_name}")
    
    def stop_monitoring_component(self, component_name: str) -> None:
        """Stop monitoring a component"""
        self.monitored_components.discard(component_name)
        
        if component_name in self.component_states:
            self.component_states[component_name]['status'] = 'inactive'
            self.component_states[component_name]['end_time'] = time.time()
        
        self.logger.debug(f"Stopped monitoring component: {component_name}")
    
    def get_debug_events(
        self,
        component: Optional[str] = None,
        level: Optional[DebugLevel] = None,
        category: Optional[DebugCategory] = None,
        limit: int = 100
    ) -> List[DebugEvent]:
        """Get debug events with optional filtering"""
        
        events = list(self.debug_events)
        
        # Apply filters
        if component:
            events = [e for e in events if e.component == component]
        if level:
            events = [e for e in events if e.level == level]
        if category:
            events = [e for e in events if e.category == category]
        
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]
    
    def get_performance_metrics(
        self,
        component: Optional[str] = None,
        metric_name: Optional[str] = None,
        time_range: Optional[tuple] = None
    ) -> List[PerformanceMetric]:
        """Get performance metrics with optional filtering"""
        
        all_metrics = []
        
        if component:
            all_metrics = self.performance_metrics.get(component, [])
        else:
            for component_metrics in self.performance_metrics.values():
                all_metrics.extend(component_metrics)
        
        # Apply filters
        if metric_name:
            all_metrics = [m for m in all_metrics if m.name == metric_name]
        
        if time_range:
            start_time, end_time = time_range
            all_metrics = [m for m in all_metrics if start_time <= m.timestamp <= end_time]
        
        # Sort by timestamp
        all_metrics.sort(key=lambda x: x.timestamp, reverse=True)
        return all_metrics
    
    def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics"""
        import psutil
        import platform
        
        diagnostics = {
            'timestamp': time.time(),
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
            },
            'application': {
                'monitored_components': len(self.monitored_components),
                'active_sessions': len([s for s in self.active_sessions.values() if s['active']]),
                'total_events': len(self.debug_events),
                'total_metrics': sum(len(metrics) for metrics in self.performance_metrics.values())
            },
            'performance': self._get_performance_summary(),
            'issues': self._detect_performance_issues()
        }
        
        return diagnostics
    
    def export_debug_data(self, file_path: Optional[str] = None) -> str:
        """Export debug data to file"""
        if not file_path:
            timestamp = int(time.time())
            file_path = f"debug/debug_export_{timestamp}.json"
        
        export_data = {
            'export_timestamp': time.time(),
            'debug_config': self.debug_config,
            'events': [self._serialize_event(event) for event in list(self.debug_events)[-1000:]],  # Last 1000 events
            'performance_metrics': self._serialize_metrics(),
            'sessions': self.active_sessions,
            'component_states': self.component_states,
            'system_diagnostics': self.get_system_diagnostics()
        }
        
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Debug data exported to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export debug data: {e}")
            return ""
    
    def clear_debug_data(self, older_than_hours: Optional[int] = None) -> int:
        """Clear debug data, optionally keeping recent data"""
        if older_than_hours is None:
            # Clear all data
            events_cleared = len(self.debug_events)
            self.debug_events.clear()
            
            metrics_cleared = sum(len(metrics) for metrics in self.performance_metrics.values())
            self.performance_metrics.clear()
            
            total_cleared = events_cleared + metrics_cleared
        else:
            # Clear data older than specified hours
            cutoff_time = time.time() - (older_than_hours * 3600)
            
            # Filter events
            original_event_count = len(self.debug_events)
            self.debug_events = deque(
                [event for event in self.debug_events if event.timestamp >= cutoff_time],
                maxlen=10000
            )
            events_cleared = original_event_count - len(self.debug_events)
            
            # Filter metrics
            metrics_cleared = 0
            for component, metrics in self.performance_metrics.items():
                original_count = len(metrics)
                self.performance_metrics[component] = [
                    metric for metric in metrics if metric.timestamp >= cutoff_time
                ]
                metrics_cleared += original_count - len(self.performance_metrics[component])
            
            total_cleared = events_cleared + metrics_cleared
        
        self.logger.info(f"Cleared {total_cleared} debug records")
        return total_cleared
    
    def enable_category(self, category: DebugCategory) -> None:
        """Enable debug logging for a category"""
        self.debug_config['categories_enabled'].add(category)
        self.logger.debug(f"Enabled debug category: {category.value}")
    
    def disable_category(self, category: DebugCategory) -> None:
        """Disable debug logging for a category"""
        self.debug_config['categories_enabled'].discard(category)
        self.logger.debug(f"Disabled debug category: {category.value}")
    
    def set_debug_level(self, level: DebugLevel) -> None:
        """Set minimum debug level"""
        self.debug_config['log_level'] = level
        self.logger.info(f"Debug level set to: {level.value}")
    
    def get_debug_statistics(self) -> Dict[str, Any]:
        """Get comprehensive debug statistics"""
        stats = {
            'events': {
                'total': len(self.debug_events),
                'by_level': defaultdict(int),
                'by_category': defaultdict(int),
                'by_component': defaultdict(int)
            },
            'performance': {
                'total_metrics': sum(len(metrics) for metrics in self.performance_metrics.values()),
                'components_monitored': len(self.performance_metrics),
                'avg_metrics_per_component': 0
            },
            'sessions': {
                'total': len(self.active_sessions),
                'active': len([s for s in self.active_sessions.values() if s['active']])
            },
            'monitoring': {
                'components': len(self.monitored_components),
                'startup_phases': len(self.startup_phases)
            }
        }
        
        # Calculate event statistics
        for event in self.debug_events:
            stats['events']['by_level'][event.level.value] += 1
            stats['events']['by_category'][event.category.value] += 1
            stats['events']['by_component'][event.component] += 1
        
        # Calculate performance statistics
        if self.performance_metrics:
            total_metrics = sum(len(metrics) for metrics in self.performance_metrics.values())
            stats['performance']['avg_metrics_per_component'] = total_metrics / len(self.performance_metrics)
        
        return stats
    
    def _should_log_event(self, level: DebugLevel, category: DebugCategory) -> bool:
        """Check if event should be logged"""
        if not self.debug_config['enabled']:
            return False
        
        if category not in self.debug_config['categories_enabled']:
            return False
        
        # Check level threshold
        level_values = {
            DebugLevel.TRACE: 0,
            DebugLevel.DEBUG: 1,
            DebugLevel.INFO: 2,
            DebugLevel.WARNING: 3,
            DebugLevel.ERROR: 4,
            DebugLevel.CRITICAL: 5
        }
        
        return level_values[level] >= level_values[self.debug_config['log_level']]
    
    def _setup_widget_monitoring(self, component_name: str, widget: QWidget) -> None:
        """Setup monitoring for a widget"""
        # Monitor widget events (simplified)
        if hasattr(widget, 'clicked'):
            widget.clicked.connect(
                lambda: self.log_debug_event(
                    component_name, 
                    f"Widget clicked: {widget.objectName()}", 
                    DebugLevel.DEBUG, 
                    DebugCategory.UI
                )
            )
    
    def _collect_performance_metrics(self) -> None:
        """Collect system performance metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.record_performance_metric(
                "cpu_usage", cpu_percent, "%", "system", "performance"
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_performance_metric(
                "memory_usage", memory.percent, "%", "system", "performance"
            )
            
            # Process-specific metrics
            process = psutil.Process()
            self.record_performance_metric(
                "process_memory", process.memory_info().rss / 1024 / 1024, "MB", "application", "performance"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {e}")
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {
            'components': {},
            'overall': {
                'avg_cpu': 0,
                'avg_memory': 0,
                'peak_memory': 0
            }
        }
        
        # Calculate component summaries
        for component, metrics in self.performance_metrics.items():
            if metrics:
                component_summary = {
                    'metric_count': len(metrics),
                    'latest_timestamp': max(m.timestamp for m in metrics),
                    'categories': set(m.category for m in metrics)
                }
                summary['components'][component] = component_summary
        
        return summary
    
    def _detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Detect potential performance issues"""
        issues = []
        
        # Check for high CPU usage
        cpu_metrics = [m for metrics in self.performance_metrics.values() 
                      for m in metrics if m.name == 'cpu_usage']
        if cpu_metrics:
            recent_cpu = [m.value for m in cpu_metrics[-10:]]  # Last 10 readings
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            if avg_cpu > 80:
                issues.append({
                    'type': 'high_cpu_usage',
                    'severity': 'warning',
                    'message': f'High CPU usage detected: {avg_cpu:.1f}%'
                })
        
        # Check for memory leaks
        memory_metrics = [m for metrics in self.performance_metrics.values() 
                         for m in metrics if m.name == 'process_memory']
        if len(memory_metrics) > 20:
            recent_memory = [m.value for m in memory_metrics[-20:]]
            if len(set(recent_memory)) > 1:  # Memory usage is changing
                trend = (recent_memory[-1] - recent_memory[0]) / len(recent_memory)
                if trend > 1:  # Growing by more than 1MB per reading
                    issues.append({
                        'type': 'potential_memory_leak',
                        'severity': 'warning',
                        'message': f'Memory usage trending upward: +{trend:.1f}MB per reading'
                    })
        
        return issues
    
    def _serialize_event(self, event: DebugEvent) -> Dict[str, Any]:
        """Serialize debug event for export"""
        return {
            'event_id': event.event_id,
            'timestamp': event.timestamp,
            'level': event.level.value,
            'category': event.category.value,
            'component': event.component,
            'message': event.message,
            'details': event.details,
            'thread_id': event.thread_id,
            'correlation_id': event.correlation_id
        }
    
    def _serialize_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Serialize performance metrics for export"""
        serialized = {}
        
        for component, metrics in self.performance_metrics.items():
            serialized[component] = [
                {
                    'metric_id': m.metric_id,
                    'name': m.name,
                    'value': m.value,
                    'unit': m.unit,
                    'timestamp': m.timestamp,
                    'category': m.category,
                    'metadata': m.metadata
                }
                for m in metrics[-100:]  # Last 100 metrics per component
            ]
        
        return serialized
    
    def _auto_save_debug_data(self) -> None:
        """Auto-save debug data periodically"""
        try:
            # Save recent events
            recent_events = list(self.debug_events)[-1000:]  # Last 1000 events
            events_data = [self._serialize_event(event) for event in recent_events]
            
            self.debug_data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.debug_data_file, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, indent=2)
            
            # Save performance metrics
            metrics_data = self._serialize_metrics()
            with open(self.performance_data_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2)
            
            self.logger.debug("Debug data auto-saved")
            
        except Exception as e:
            self.logger.error(f"Failed to auto-save debug data: {e}")
    
    def _load_debug_configuration(self) -> None:
        """Load debug configuration"""
        config_file = Path("config/debug.json")
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Update configuration
                self.debug_config.update(config_data)
                
                self.logger.info("Debug configuration loaded")
                
        except Exception as e:
            self.logger.error(f"Failed to load debug configuration: {e}")


# Convenience functions for backward compatibility
def log_performance(component: str, metric_name: str, value: float, unit: str = "ms") -> None:
    """Log performance metric (backward compatibility)"""
    # This would connect to the global debug system instance
    pass

def log_startup_phase(phase_name: str, duration: float) -> None:
    """Log startup phase (backward compatibility)"""
    # This would connect to the global debug system instance
    pass
