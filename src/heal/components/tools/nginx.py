import os
from dataclasses import dataclass
from typing import List, Optional, Any

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import PushButton, SpinBox, TableWidget

from src.heal.common.logging_config import get_logger, log_performance, with_correlation_id
from src.heal.models.setting_card import CustomInputDialog

# 使用统一日志配置
logger = get_logger("nginx_configurator")


@dataclass
class Route:
    path: str
    target: str


@dataclass
class Upstream:
    server: str
    weight: int


class NginxConfigurator(QFrame):
    def __init__(self) -> None:
        super().__init__()

        # 日志现在使用统一配置
        logger.info("NginxConfigurator initialized")

        # 设置布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # 路由配置页
        self.route_tab = QWidget()
        self.setup_route_tab()
        self.tabs.addTab(self.route_tab, "路由配置")

        # 全局配置页
        self.global_tab = QWidget()
        self.setup_global_tab()
        self.tabs.addTab(self.global_tab, "全局配置")

        # 日志配置页
        self.log_tab = QWidget()
        self.setup_log_tab()
        self.tabs.addTab(self.log_tab, "日志配置")

        # 静态文件缓存页
        self.cache_tab = QWidget()
        self.setup_cache_tab()
        self.tabs.addTab(self.cache_tab, "静态文件缓存")

        # 负载均衡配置页
        self.upstream_tab = QWidget()
        self.setup_upstream_tab()
        self.tabs.addTab(self.upstream_tab, "负载均衡")

        # 操作按钮页
        self.action_tab = QWidget()
        self.setup_action_tab()
        self.tabs.addTab(self.action_tab, "操作")

        # 日志监控页
        self.log_monitor_tab = QWidget()
        self.setup_log_monitor_tab()
        self.tabs.addTab(self.log_monitor_tab, "日志监控")

        # 初始化配置
        self.routes: List[Route] = []
        self.upstreams: List[Upstream] = []
        self.monitor_process: Optional[QProcess] = None

    def setup_route_tab(self) -> None:
        layout = QVBoxLayout()
        self.route_table = TableWidget(self)
        self.route_table.setColumnCount(3)
        self.route_table.setHorizontalHeaderLabels(["路径", "目标地址", "操作"])
        self.route_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.route_table.setEditTriggers(TableWidget.NoEditTriggers)

        self.add_route_button = PushButton("添加路由")
        self.add_route_button.clicked.connect(self.add_route)

        layout.addWidget(self.route_table)
        layout.addWidget(self.add_route_button)
        self.route_tab.setLayout(layout)

    def setup_global_tab(self) -> None:
        layout = QFormLayout()
        self.worker_processes_input = SpinBox()
        self.worker_processes_input.setRange(1, 64)
        self.worker_processes_input.setValue(1)

        self.worker_connections_input = SpinBox()
        self.worker_connections_input.setRange(1, 65535)
        self.worker_connections_input.setValue(1024)

        layout.addRow("Worker Processes:", self.worker_processes_input)
        layout.addRow("Worker Connections:", self.worker_connections_input)
        self.global_tab.setLayout(layout)

    def setup_log_tab(self) -> None:
        layout = QFormLayout()
        self.access_log_path_input = QLineEdit()
        self.error_log_path_input = QLineEdit()

        layout.addRow("访问日志路径:", self.access_log_path_input)
        layout.addRow("错误日志路径:", self.error_log_path_input)
        self.log_tab.setLayout(layout)

    def setup_cache_tab(self) -> None:
        layout = QFormLayout()
        self.cache_path_input = QLineEdit()
        self.cache_time_input = SpinBox()
        self.cache_time_input.setRange(0, 365)
        self.cache_time_input.setValue(30)

        layout.addRow("缓存路径:", self.cache_path_input)
        layout.addRow("缓存时间 (天):", self.cache_time_input)
        self.cache_tab.setLayout(layout)

    def setup_upstream_tab(self) -> None:
        layout = QVBoxLayout()
        self.upstream_table = TableWidget(self)
        self.upstream_table.setColumnCount(3)
        self.upstream_table.setHorizontalHeaderLabels(["服务器地址", "权重", "操作"])
        self.upstream_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.add_upstream_button = PushButton("添加负载均衡节点")
        self.add_upstream_button.clicked.connect(self.add_upstream)

        layout.addWidget(self.upstream_table)
        layout.addWidget(self.add_upstream_button)
        self.upstream_tab.setLayout(layout)

    def setup_action_tab(self) -> None:
        layout = QHBoxLayout()
        self.save_button = PushButton("保存配置")
        self.save_button.clicked.connect(self.save_config)

        self.validate_button = PushButton("校验配置")
        self.validate_button.clicked.connect(self.validate_config)

        self.reload_button = PushButton("重载 Nginx")
        self.reload_button.clicked.connect(self.reload_nginx)

        self.restart_button = PushButton("重启 Nginx")
        self.restart_button.clicked.connect(self.restart_nginx)

        self.import_button = PushButton("导入配置")
        self.import_button.clicked.connect(self.import_config)

        self.export_button = PushButton("导出配置")
        self.export_button.clicked.connect(self.export_config)

        layout.addWidget(self.save_button)
        layout.addWidget(self.validate_button)
        layout.addWidget(self.reload_button)
        layout.addWidget(self.restart_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.export_button)
        self.action_tab.setLayout(layout)

    def setup_log_monitor_tab(self) -> None:
        layout = QVBoxLayout()
        self.log_monitor = QTextEdit()
        self.log_monitor.setReadOnly(True)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入关键字过滤日志")
        self.filter_input.textChanged.connect(self.filter_logs)

        layout.addWidget(self.filter_input)
        layout.addWidget(self.log_monitor)
        self.log_monitor_tab.setLayout(layout)

    def filter_logs(self) -> None:
        keyword = self.filter_input.text()
        # 这里可以实现日志过滤逻辑
        pass

    def add_route(self) -> None:
        path_dialog = CustomInputDialog("添加路由", "路径（如 /api）:", self)
        path = path_dialog.get_text()
        if not path or not path.strip():
            return

        target_dialog = CustomInputDialog(
            "添加路由", "目标地址（如 http://127.0.0.1:5000）:", self)
        target = target_dialog.get_text()
        if not target or not target.strip():
            return

        route = Route(path=path.strip(), target=target.strip())
        self.routes.append(route)
        self.update_route_table()
        logger.info(f"添加路由: {route}")

    def update_route_table(self) -> None:
        self.route_table.setRowCount(len(self.routes))
        for i, route in enumerate(self.routes):
            self.route_table.setItem(i, 0, QTableWidgetItem(route.path))
            self.route_table.setItem(i, 1, QTableWidgetItem(route.target))
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, idx=i: self.delete_route(idx))
            self.route_table.setCellWidget(i, 2, delete_btn)

    def delete_route(self, index: int) -> None:
        if 0 <= index < len(self.routes):
            removed = self.routes.pop(index)
            self.update_route_table()
            logger.info(f"删除路由: {removed}")

    def add_upstream(self) -> None:
        server_dialog = CustomInputDialog(
            "添加节点", "服务器地址（如 127.0.0.1:8000）:", self)
        server = server_dialog.get_text()
        if not server or not server.strip():
            return

        # For weight, we'll use a simple input dialog and convert to int
        weight_dialog = CustomInputDialog("添加节点", "权重 (1-100):", self)
        weight_str = weight_dialog.get_text()
        if not weight_str:
            return

        try:
            weight = int(weight_str)
            if not (1 <= weight <= 100):
                return
        except ValueError:
            return

        upstream = Upstream(server=server.strip(), weight=weight)
        self.upstreams.append(upstream)
        self.update_upstream_table()
        logger.info(f"添加负载均衡节点: {upstream}")

    def update_upstream_table(self) -> None:
        self.upstream_table.setRowCount(len(self.upstreams))
        for i, upstream in enumerate(self.upstreams):
            self.upstream_table.setItem(
                i, 0, QTableWidgetItem(upstream.server))
            self.upstream_table.setItem(
                i, 1, QTableWidgetItem(str(upstream.weight)))
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(
                lambda _, idx=i: self.delete_upstream(idx))
            self.upstream_table.setCellWidget(i, 2, delete_btn)

    def delete_upstream(self, index: int) -> None:
        if 0 <= index < len(self.upstreams):
            removed = self.upstreams.pop(index)
            self.update_upstream_table()
            logger.info(f"删除负载均衡节点: {removed}")

    def save_config(self) -> None:
        config = self.generate_nginx_config()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "nginx.conf", "配置文件 (*.conf);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(config)
                QMessageBox.information(self, "成功", "配置已保存")
                logger.info(f"配置文件已保存: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
                logger.error(f"保存配置失败: {e}")

    def import_config(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置文件", "", "配置文件 (*.conf);;所有文件 (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    config = file.read()
                # 解析配置文件并更新界面
                # 此处需要实现配置解析逻辑
                QMessageBox.information(self, "成功", "配置已导入")
                logger.info(f"配置文件已导入: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置失败: {e}")
                logger.error(f"导入配置失败: {e}")

    def export_config(self) -> None:
        self.save_config()

    def generate_nginx_config(self) -> str:
        worker_processes = self.worker_processes_input.value()
        worker_connections = self.worker_connections_input.value()

        config = f"""
# 全局设置
worker_processes {worker_processes};
events {{
    worker_connections {worker_connections};
}}

http {{
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;
"""

        access_log = self.access_log_path_input.text() or "/var/log/nginx/access.log"
        error_log = self.error_log_path_input.text() or "/var/log/nginx/error.log"

        config += f"""
    access_log {access_log};
    error_log {error_log};
"""

        cache_path = self.cache_path_input.text().strip()
        cache_time = self.cache_time_input.value()
        if cache_path:
            config += f"""
    location /static {{
        root {cache_path};
        expires {cache_time}d;
    }}
"""

        if self.upstreams:
            config += """
    upstream backend {
"""
            for upstream in self.upstreams:
                config += (
                    f"        server {upstream.server} weight={upstream.weight};\n"
                )
            config += "    }\n"

        config += """
    server {
        listen 80;
        server_name localhost;

        location / {
            root   html;
            index  index.html index.htm;
        }
"""
        for route in self.routes:
            config += f"""
        location {route.path} {{
            proxy_pass {route.target};
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }}
"""
        config += """
    }
}
"""
        return config

    def validate_config(self) -> None:
        process = QProcess(self)
        process.start("nginx", ["-t"])
        process.waitForFinished()
        output = process.readAllStandardOutput().data().decode()
        error = process.readAllStandardError().data().decode()

        if "successful" in output:
            QMessageBox.information(self, "校验成功", output)
            logger.info("Nginx 配置校验成功")
        else:
            QMessageBox.critical(self, "校验失败", error or output)
            logger.error(f"Nginx 配置校验失败: {error or output}")

    def reload_nginx(self) -> None:
        process = QProcess(self)
        process.start("nginx", ["-s", "reload"])
        process.waitForFinished()
        output = process.readAllStandardOutput().data().decode()
        error = process.readAllStandardError().data().decode()

        if not error:
            QMessageBox.information(self, "重载成功", "Nginx 已成功重载！")
            logger.info("Nginx 已成功重载")
        else:
            QMessageBox.critical(self, "重载失败", error)
            logger.error(f"Nginx 重载失败: {error}")

    def restart_nginx(self) -> None:
        process = QProcess(self)
        process.start("nginx", ["-s", "stop"])
        process.waitForFinished()
        process.start("nginx")
        process.waitForFinished()
        output = process.readAllStandardOutput().data().decode()
        error = process.readAllStandardError().data().decode()

        if not error:
            QMessageBox.information(self, "重启成功", "Nginx 已成功重启！")
            logger.info("Nginx 已成功重启")
        else:
            QMessageBox.critical(self, "重启失败", error)
            logger.error(f"Nginx 重启失败: {error}")

    def start_log_monitor(self) -> None:
        log_file = self.access_log_path_input.text() or "/var/log/nginx/access.log"
        if not os.path.exists(log_file):
            QMessageBox.warning(self, "日志文件不存在", f"无法找到日志文件：{log_file}")
            logger.warning(f"日志文件不存在: {log_file}")
            return

        self.monitor_process = QProcess(self)
        self.monitor_process.setProcessChannelMode(QProcess.MergedChannels)
        self.monitor_process.start("tail", ["-f", log_file])
        self.monitor_process.readyRead.connect(self.update_log_monitor)
        logger.info(f"启动日志监控: {log_file}")

    def update_log_monitor(self) -> None:
        if self.monitor_process:
            output = self.monitor_process.readAllStandardOutput().data().decode()
            self.log_monitor.append(output)

    def stop_log_monitor(self) -> None:
        if self.monitor_process:
            self.monitor_process.terminate()
            self.monitor_process = None
            logger.info("停止日志监控")


if __name__ == "__main__":
    app = QApplication([])

    # 创建主窗口
    main_window = QMainWindow()
    main_window.setWindowTitle("Nginx 配置工具")
    main_window.setFixedSize(1200, 800)

    # 创建 NginxConfigurator 并设置为中心部件
    configurator = NginxConfigurator()
    main_window.setCentralWidget(configurator)

    main_window.show()
    app.exec()
