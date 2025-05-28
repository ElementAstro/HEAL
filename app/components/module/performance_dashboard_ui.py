"""
Performance Dashboard UI Component

Provides visual interface for real-time performance monitoring of modules
with charts, metrics, alerts, and detailed analytics.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import queue
from datetime import datetime
import json
from typing import Dict, Any
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import psutil
import os

from loguru import logger


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.settings = {
            'cpu_threshold': 80.0,
            'memory_threshold': 85.0,
            'update_interval': 1.0
        }
        self.alerts = []
        self.modules_data = {}
        self.history = []

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        try:
            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()

            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'active_modules': len(self.modules_data),
                'total_operations': sum(m.get('operations', 0) for m in self.modules_data.values()),
                'error_rate': self._calculate_error_rate(),
                'avg_response_time': self._calculate_avg_response_time(),
                'disk_io_mb': (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024 if disk_io else 0,
                'network_io_kb': (network_io.bytes_sent + network_io.bytes_recv) / 1024 if network_io else 0,
                'modules': self.modules_data.copy()
            }

            # 检查阈值并生成警报
            self._check_thresholds(metrics)

            return metrics

        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'active_modules': 0,
                'total_operations': 0,
                'error_rate': 0,
                'avg_response_time': 0,
                'modules': {}
            }

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                'platform': os.name,
                'cpu_count': psutil.cpu_count(),
                'memory_total': f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB",
                'disk_usage': {disk.device: f"{psutil.disk_usage(disk.mountpoint).percent:.1f}%"
                               for disk in psutil.disk_partitions()[:3]},
                'python_version': f"{sys.version.split()[0]}",
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {'error': str(e)}

    def get_active_alerts(self) -> list:
        """获取活动警报"""
        # 返回最近的警报
        recent_alerts = [alert for alert in self.alerts if
                         time.time() - alert.get('timestamp', 0) < 300]  # 5分钟内的警报
        return recent_alerts

    def get_module_details(self, module_name: str) -> Dict[str, Any]:
        """获取模块详细信息"""
        if module_name in self.modules_data:
            details = self.modules_data[module_name].copy()
            details.update({
                'uptime': f"{details.get('uptime', 0):.1f} seconds",
                'last_activity': datetime.fromtimestamp(details.get('last_activity', time.time())).strftime('%Y-%m-%d %H:%M:%S'),
                'error_count': details.get('errors', 0),
                'success_rate': f"{(1 - details.get('error_rate', 0)) * 100:.1f}%"
            })
            return details
        return {'error': 'Module not found'}

    def update_settings(self, settings: Dict[str, Any]):
        """更新设置"""
        self.settings.update(settings)
        logger.info(f"性能监控器设置已更新: {settings}")

    def export_data(self) -> Dict[str, Any]:
        """导出数据"""
        return {
            'timestamp': datetime.now().isoformat(),
            'settings': self.settings,
            'current_metrics': self.get_current_metrics(),
            'system_info': self.get_system_info(),
            'alerts_count': len(self.alerts),
            'modules_count': len(self.modules_data)
        }

    def _calculate_error_rate(self) -> float:
        """计算错误率"""
        total_ops = sum(m.get('operations', 0)
                        for m in self.modules_data.values())
        total_errors = sum(m.get('errors', 0)
                           for m in self.modules_data.values())
        return (total_errors / total_ops * 100) if total_ops > 0 else 0

    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        response_times = [m.get('response_time', 0)
                          for m in self.modules_data.values() if m.get('response_time')]
        return sum(response_times) / len(response_times) if response_times else 0

    def _check_thresholds(self, metrics: Dict[str, Any]):
        """检查阈值并生成警报"""
        current_time = time.time()

        # CPU阈值检查
        if metrics['cpu_percent'] > self.settings['cpu_threshold']:
            self.alerts.append({
                'timestamp': current_time,
                'severity': 'WARNING',
                'message': f"CPU使用率过高: {metrics['cpu_percent']:.1f}%"
            })

        # 内存阈值检查
        if metrics['memory_percent'] > self.settings['memory_threshold']:
            self.alerts.append({
                'timestamp': current_time,
                'severity': 'WARNING',
                'message': f"内存使用率过高: {metrics['memory_percent']:.1f}%"
            })

        # 限制警报数量
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]


class PerformanceChartWidget:
    """Real-time chart widget for performance metrics"""

    def __init__(self, parent, title: str, ylabel: str, max_points: int = 50):
        self.parent = parent
        self.title = title
        self.ylabel = ylabel
        self.max_points = max_points

        # Create figure and subplot
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True, alpha=0.3)

        # Data storage
        self.times = []
        self.values = []

        # Setup plot
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        self.ax.set_xlim(0, max_points)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Auto-adjust layout
        self.fig.tight_layout()

    def update_data(self, value: float):
        """Update chart with new data point"""
        try:
            current_time = datetime.now()
            self.times.append(current_time)
            self.values.append(value)

            # Limit data points
            if len(self.values) > self.max_points:
                self.times = self.times[-self.max_points:]
                self.values = self.values[-self.max_points:]

            # Update plot
            if len(self.values) > 1:
                x_data = list(range(len(self.values)))
                self.line.set_data(x_data, self.values)

                # Auto-scale
                self.ax.set_xlim(0, max(len(self.values), 10))
                if self.values:
                    y_min, y_max = min(self.values), max(self.values)
                    y_range = y_max - y_min if y_max != y_min else 1
                    self.ax.set_ylim(y_min - y_range * 0.1,
                                     y_max + y_range * 0.1)

                # Update x-axis labels with time
                if len(self.times) > 5:
                    step = max(1, len(self.times) // 5)
                    tick_positions = list(range(0, len(self.times), step))
                    tick_labels = [self.times[i].strftime(
                        '%H:%M:%S') for i in tick_positions]
                    self.ax.set_xticks(tick_positions)
                    self.ax.set_xticklabels(tick_labels, rotation=45)

                self.canvas.draw()

        except Exception as e:
            logger.error(f"Error updating chart data: {e}")

    def clear_data(self):
        """Clear all chart data"""
        self.times.clear()
        self.values.clear()
        self.line.set_data([], [])
        self.canvas.draw()


class MetricsDisplayWidget:
    """Widget for displaying current metrics values"""

    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.LabelFrame(parent, text="Current Metrics", padding=10)
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        # Metrics labels
        self.metrics_vars = {}
        self.create_metrics_display()

    def create_metrics_display(self):
        """Create metrics display layout"""
        metrics = [
            ("CPU Usage", "cpu_percent"),
            ("Memory Usage", "memory_percent"),
            ("Active Modules", "active_modules"),
            ("Total Operations", "total_operations"),
            ("Error Rate", "error_rate"),
            ("Avg Response Time", "avg_response_time")
        ]

        for i, (display_name, key) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2

            # Label
            ttk.Label(self.frame, text=f"{display_name}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 5), pady=2
            )

            # Value
            var = tk.StringVar(value="0")
            self.metrics_vars[key] = var
            value_label = ttk.Label(
                self.frame, textvariable=var, font=('TkDefaultFont', 9, 'bold'))
            value_label.grid(row=row, column=col+1,
                             sticky=tk.W, padx=(0, 20), pady=2)

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update displayed metrics"""
        try:
            for key, var in self.metrics_vars.items():
                if key in metrics:
                    value = metrics[key]
                    if key in ['cpu_percent', 'memory_percent', 'error_rate']:
                        var.set(f"{value:.1f}%")
                    elif key == 'avg_response_time':
                        var.set(f"{value:.2f}ms")
                    else:
                        var.set(str(value))
        except Exception as e:
            logger.error(f"Error updating metrics display: {e}")


class AlertsWidget:
    """Widget for displaying performance alerts"""

    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.LabelFrame(
            parent, text="Performance Alerts", padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create listbox for alerts
        self.alerts_listbox = tk.Listbox(self.frame, height=6)
        self.alerts_listbox.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.alerts_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.alerts_listbox.config(yscrollcommand=scrollbar.set)

        # Clear button
        ttk.Button(self.frame, text="Clear Alerts",
                   command=self.clear_alerts).pack(pady=(5, 0))

        self.alerts = []

    def add_alert(self, alert: Dict[str, Any]):
        """Add new alert to display"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            severity = alert.get('severity', 'INFO')
            message = alert.get('message', 'Unknown alert')

            alert_text = f"[{timestamp}] {severity}: {message}"
            self.alerts.append(alert_text)

            # Add to listbox
            self.alerts_listbox.insert(0, alert_text)

            # Color code by severity
            if severity == 'CRITICAL':
                self.alerts_listbox.itemconfig(0, {'bg': '#ffcccc'})
            elif severity == 'WARNING':
                self.alerts_listbox.itemconfig(0, {'bg': '#ffffcc'})
            elif severity == 'INFO':
                self.alerts_listbox.itemconfig(0, {'bg': '#ccffcc'})

            # Limit number of alerts
            if self.alerts_listbox.size() > 100:
                self.alerts_listbox.delete(99, tk.END)
                self.alerts = self.alerts[:100]

        except Exception as e:
            logger.error(f"Error adding alert: {e}")

    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts_listbox.delete(0, tk.END)
        self.alerts.clear()


class PerformanceDashboardUI:
    """Main Performance Dashboard UI Component"""

    def __init__(self, parent, performance_monitor: PerformanceMonitor):
        self.parent = parent
        self.performance_monitor = performance_monitor
        self.update_thread = None
        self.running = False
        self.update_queue = queue.Queue()

        # Setup UI
        self.setup_ui()

        # Start monitoring
        self.start_monitoring()

        logger.info("Performance Dashboard UI initialized")

    def setup_ui(self):
        """Setup the dashboard UI"""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Overview tab
        self.setup_overview_tab()

        # System tab
        self.setup_system_tab()

        # Modules tab
        self.setup_modules_tab()

        # Settings tab
        self.setup_settings_tab()

    def setup_overview_tab(self):
        """Setup overview tab with key metrics"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")

        # Top metrics panel
        self.metrics_widget = MetricsDisplayWidget(overview_frame)

        # Charts frame
        charts_frame = ttk.Frame(overview_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create chart widgets
        self.cpu_chart = PerformanceChartWidget(
            charts_frame, "CPU Usage (%)", "Usage %")
        self.memory_chart = PerformanceChartWidget(
            charts_frame, "Memory Usage (%)", "Usage %")

        # Alerts widget
        self.alerts_widget = AlertsWidget(overview_frame)

    def setup_system_tab(self):
        """Setup system monitoring tab"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="System")

        # System info
        info_frame = ttk.LabelFrame(
            system_frame, text="System Information", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.system_info_text = tk.Text(info_frame, height=8, wrap=tk.WORD)
        self.system_info_text.pack(fill=tk.BOTH, expand=True)

        # Resource usage charts
        resources_frame = ttk.LabelFrame(
            system_frame, text="Resource Usage", padding=10)
        resources_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.disk_chart = PerformanceChartWidget(
            resources_frame, "Disk I/O (MB/s)", "MB/s")
        self.network_chart = PerformanceChartWidget(
            resources_frame, "Network I/O (KB/s)", "KB/s")

    def setup_modules_tab(self):
        """Setup modules monitoring tab"""
        modules_frame = ttk.Frame(self.notebook)
        self.notebook.add(modules_frame, text="Modules")

        # Module list
        list_frame = ttk.LabelFrame(
            modules_frame, text="Active Modules", padding=10)
        list_frame.pack(fill=tk.X, padx=5, pady=5)

        # Treeview for modules
        columns = ('Module', 'Status', 'CPU %',
                   'Memory MB', 'Operations', 'Errors')
        self.modules_tree = ttk.Treeview(
            list_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.modules_tree.heading(col, text=col)
            self.modules_tree.column(col, width=100)

        self.modules_tree.pack(fill=tk.BOTH, expand=True)

        # Module details
        details_frame = ttk.LabelFrame(
            modules_frame, text="Module Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.module_details_text = tk.Text(
            details_frame, height=8, wrap=tk.WORD)
        self.module_details_text.pack(fill=tk.BOTH, expand=True)

        # Bind selection event
        self.modules_tree.bind('<<TreeviewSelect>>', self.on_module_select)

    def setup_settings_tab(self):
        """Setup settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Monitoring settings
        monitor_frame = ttk.LabelFrame(
            settings_frame, text="Monitoring Settings", padding=10)
        monitor_frame.pack(fill=tk.X, padx=5, pady=5)

        # Update interval
        ttk.Label(monitor_frame, text="Update Interval (seconds):").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.update_interval_var = tk.StringVar(value="1.0")
        update_entry = ttk.Entry(
            monitor_frame, textvariable=self.update_interval_var, width=10)
        update_entry.grid(row=0, column=1, sticky=tk.W)

        # Alert thresholds
        ttk.Label(monitor_frame, text="CPU Alert Threshold (%):").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.cpu_threshold_var = tk.StringVar(value="80")
        cpu_entry = ttk.Entry(
            monitor_frame, textvariable=self.cpu_threshold_var, width=10)
        cpu_entry.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        ttk.Label(monitor_frame, text="Memory Alert Threshold (%):").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.memory_threshold_var = tk.StringVar(value="85")
        memory_entry = ttk.Entry(
            monitor_frame, textvariable=self.memory_threshold_var, width=10)
        memory_entry.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))

        # Control buttons
        controls_frame = ttk.LabelFrame(
            settings_frame, text="Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(controls_frame, text="Apply Settings",
                   command=self.apply_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Reset Charts",
                   command=self.reset_charts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Export Data",
                   command=self.export_data).pack(side=tk.LEFT, padx=(0, 5))

        # Status
        self.status_var = tk.StringVar(value="Monitoring active")
        ttk.Label(controls_frame, textvariable=self.status_var).pack(
            side=tk.RIGHT)

    def start_monitoring(self):
        """Start the monitoring thread"""
        self.running = True
        self.update_thread = threading.Thread(
            target=self.monitoring_loop, daemon=True)
        self.update_thread.start()

        # Start UI update timer
        self.update_ui()

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)

    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current metrics
                metrics = self.performance_monitor.get_current_metrics()
                system_info = self.performance_monitor.get_system_info()
                alerts = self.performance_monitor.get_active_alerts()

                # Queue updates for UI thread
                self.update_queue.put({
                    'type': 'metrics',
                    'data': metrics
                })

                self.update_queue.put({
                    'type': 'system_info',
                    'data': system_info
                })

                if alerts:
                    for alert in alerts:
                        self.update_queue.put({
                            'type': 'alert',
                            'data': alert
                        })

                # Wait for next update
                interval = float(self.update_interval_var.get())
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)

    def update_ui(self):
        """Update UI with queued data"""
        try:
            # Process all queued updates
            while not self.update_queue.empty():
                update = self.update_queue.get_nowait()
                update_type = update['type']
                data = update['data']

                if update_type == 'metrics':
                    self.update_metrics_display(data)
                elif update_type == 'system_info':
                    self.update_system_info(data)
                elif update_type == 'alert':
                    self.alerts_widget.add_alert(data)

            # Schedule next update
            self.parent.after(500, self.update_ui)

        except queue.Empty:
            self.parent.after(500, self.update_ui)
        except Exception as e:
            logger.error(f"Error updating UI: {e}")
            self.parent.after(1000, self.update_ui)

    def update_metrics_display(self, metrics: Dict[str, Any]):
        """Update metrics display and charts"""
        try:
            # Update metrics widget
            self.metrics_widget.update_metrics(metrics)

            # Update charts
            if 'cpu_percent' in metrics:
                self.cpu_chart.update_data(metrics['cpu_percent'])

            if 'memory_percent' in metrics:
                self.memory_chart.update_data(metrics['memory_percent'])

            if 'disk_io_mb' in metrics:
                self.disk_chart.update_data(metrics['disk_io_mb'])

            if 'network_io_kb' in metrics:
                self.network_chart.update_data(metrics['network_io_kb'])

            # Update modules tree
            self.update_modules_tree(metrics.get('modules', {}))

        except Exception as e:
            logger.error(f"Error updating metrics display: {e}")

    def update_system_info(self, system_info: Dict[str, Any]):
        """Update system information display"""
        try:
            info_text = "System Information:\n\n"
            for key, value in system_info.items():
                if isinstance(value, dict):
                    info_text += f"{key.title()}:\n"
                    for sub_key, sub_value in value.items():
                        info_text += f"  {sub_key}: {sub_value}\n"
                else:
                    info_text += f"{key.title()}: {value}\n"

            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(1.0, info_text)

        except Exception as e:
            logger.error(f"Error updating system info: {e}")

    def update_modules_tree(self, modules_data: Dict[str, Any]):
        """Update modules treeview"""
        try:
            # Clear existing items
            for item in self.modules_tree.get_children():
                self.modules_tree.delete(item)

            # Add module data
            for module_name, module_info in modules_data.items():
                self.modules_tree.insert('', tk.END, values=(
                    module_name,
                    module_info.get('status', 'Unknown'),
                    f"{module_info.get('cpu_percent', 0):.1f}",
                    f"{module_info.get('memory_mb', 0):.1f}",
                    module_info.get('operations', 0),
                    module_info.get('errors', 0)
                ))

        except Exception as e:
            logger.error(f"Error updating modules tree: {e}")

    def on_module_select(self, _):
        """Handle module selection in tree"""
        try:
            selection = self.modules_tree.selection()
            if selection:
                item = self.modules_tree.item(selection[0])
                module_name = item['values'][0]

                # Get detailed module information
                module_details = self.performance_monitor.get_module_details(
                    module_name)

                details_text = f"Module: {module_name}\n\n"
                for key, value in module_details.items():
                    details_text += f"{key.title()}: {value}\n"

                self.module_details_text.delete(1.0, tk.END)
                self.module_details_text.insert(1.0, details_text)

        except Exception as e:
            logger.error(f"Error displaying module details: {e}")

    def apply_settings(self):
        """Apply monitoring settings"""
        try:
            # Validate settings
            update_interval = float(self.update_interval_var.get())
            cpu_threshold = float(self.cpu_threshold_var.get())
            memory_threshold = float(self.memory_threshold_var.get())

            if update_interval < 0.1:
                raise ValueError(
                    "Update interval must be at least 0.1 seconds")

            if not (0 <= cpu_threshold <= 100):
                raise ValueError("CPU threshold must be between 0 and 100")

            if not (0 <= memory_threshold <= 100):
                raise ValueError("Memory threshold must be between 0 and 100")

            # Apply settings to performance monitor
            settings = {
                'cpu_threshold': cpu_threshold,
                'memory_threshold': memory_threshold,
                'update_interval': update_interval
            }

            self.performance_monitor.update_settings(settings)
            self.status_var.set("Settings applied successfully")

            messagebox.showinfo("Settings", "Settings applied successfully!")

        except ValueError as e:
            messagebox.showerror("Invalid Settings", str(e))
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    def reset_charts(self):
        """Reset all chart data"""
        try:
            self.cpu_chart.clear_data()
            self.memory_chart.clear_data()
            self.disk_chart.clear_data()
            self.network_chart.clear_data()
            self.alerts_widget.clear_alerts()

            self.status_var.set("Charts reset")

        except Exception as e:
            logger.error(f"Error resetting charts: {e}")
            messagebox.showerror("Error", f"Failed to reset charts: {e}")

    def export_data(self):
        """Export performance data"""
        try:
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Performance Data"
            )

            if filename:
                data = self.performance_monitor.export_data()
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

                self.status_var.set(f"Data exported to {filename}")
                messagebox.showinfo(
                    "Export", f"Data exported successfully to {filename}")

        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def destroy(self):
        """Clean up resources"""
        self.stop_monitoring()
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()


def create_performance_dashboard(parent, performance_monitor: PerformanceMonitor) -> PerformanceDashboardUI:
    """Create and return a performance dashboard UI component"""
    return PerformanceDashboardUI(parent, performance_monitor)


if __name__ == "__main__":
    # Test the dashboard
    root = tk.Tk()
    root.title("Performance Dashboard Test")
    root.geometry("1200x800")

    # Create mock performance monitor
    monitor = PerformanceMonitor()

    # Create dashboard
    dashboard = create_performance_dashboard(root, monitor)

    root.mainloop()
