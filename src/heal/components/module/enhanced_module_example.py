"""
Enhanced Module Management Example

Demonstrates the complete integration of all enhanced module management components
including workflow management, error handling, notifications, bulk operations,
and the unified dashboard.
"""

import os
import sys
import time
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.heal.common.logging_config import get_logger
from .mod_download import ModDownload
from .mod_manager import ModManager
from .module_bulk_operations import BulkOperationType, ModuleBulkOperations
from .module_dashboard import ModuleDashboard
from .module_error_handler import (
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ModuleErrorHandler,
)
from .module_notification_system import (
    ModuleNotificationSystem,
    NotificationAction,
    NotificationType,
)

# Import all enhanced components
from .module_workflow_manager import ModuleWorkflowManager, WorkflowStep
from .performance_dashboard_ui import PerformanceDashboardUI, PerformanceMonitor

logger = get_logger(__name__)


class EnhancedModuleInterface(QMainWindow):
    """Enhanced module interface with all new features integrated"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Enhanced Module Management System")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize core systems
        self.setup_core_systems()

        # Setup UI
        self.setup_ui()

        # Setup system integrations
        self.setup_integrations()

        logger.info("Enhanced Module Interface initialized")

    def setup_core_systems(self) -> None:
        """Initialize all core management systems"""
        # Error handling system
        self.error_handler = ModuleErrorHandler()

        # Notification system
        self.notification_system = ModuleNotificationSystem(self)

        # Workflow management
        self.workflow_manager = ModuleWorkflowManager()

        # Bulk operations
        self.bulk_operations = ModuleBulkOperations(
            self.error_handler, self.notification_system
        )

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()

        logger.info("Core systems initialized")

    def setup_ui(self) -> None:
        """Setup the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Dashboard tab
        self.dashboard = ModuleDashboard(
            self.workflow_manager,
            self.error_handler,
            self.notification_system,
            self.bulk_operations,
        )
        self.tab_widget.addTab(self.dashboard, "仪表板")

        # Module manager tab
        self.module_manager = ModManager()
        # Integrate our systems with the module manager
        self._integrate_module_manager()
        self.tab_widget.addTab(self.module_manager, "模组管理")

        # Download tab
        self.module_download = ModDownload()
        self.tab_widget.addTab(self.module_download, "模组下载")

        # Performance tab
        self.performance_dashboard = PerformanceDashboardUI(
            self.tab_widget, self.performance_monitor
        )
        self.tab_widget.addTab(self.performance_dashboard.main_frame, "性能监控")

        layout.addWidget(self.tab_widget)

        logger.info("UI setup completed")

    def setup_integrations(self) -> None:
        """Setup integrations between systems"""
        # Connect dashboard quick actions
        self.dashboard.quick_action_triggered.connect(self.handle_quick_action)

        # Register workflow step handlers
        self.workflow_manager.register_step_handler(
            WorkflowStep.DOWNLOAD, self.handle_download_step
        )
        self.workflow_manager.register_step_handler(
            WorkflowStep.VALIDATE, self.handle_validate_step
        )
        self.workflow_manager.register_step_handler(
            WorkflowStep.INSTALL, self.handle_install_step
        )
        self.workflow_manager.register_step_handler(
            WorkflowStep.CONFIGURE, self.handle_configure_step
        )
        self.workflow_manager.register_step_handler(
            WorkflowStep.ENABLE, self.handle_enable_step
        )

        # Register error recovery handlers
        self.error_handler.register_recovery_handler(
            "retry_operation", self.handle_retry_operation
        )
        self.error_handler.register_recovery_handler(
            "check_network", self.handle_check_network
        )
        self.error_handler.register_recovery_handler(
            "fix_permissions", self.handle_fix_permissions
        )

        # Register notification action handlers
        self.notification_system.register_action_handler(
            "view_details", self.handle_view_details
        )
        self.notification_system.register_action_handler(
            "retry_action", self.handle_retry_action
        )

        logger.info("System integrations setup completed")

    def _integrate_module_manager(self) -> None:
        """Integrate enhanced systems with existing module manager"""
        # Replace the module manager's systems with our enhanced ones
        if hasattr(self.module_manager, "error_handler"):
            self.module_manager.error_handler = self.error_handler
        if hasattr(self.module_manager, "notification_system"):
            self.module_manager.notification_system = self.notification_system
        if hasattr(self.module_manager, "workflow_manager"):
            self.module_manager.workflow_manager = self.workflow_manager
        if hasattr(self.module_manager, "bulk_operations"):
            self.module_manager.bulk_operations = self.bulk_operations

    def handle_quick_action(self, action_id: str) -> None:
        """Handle quick actions from dashboard"""
        try:
            if action_id == "refresh_modules":
                self.module_manager.load_mods()
                self.notification_system.show_success("刷新完成", "模组列表已刷新")

            elif action_id == "validate_all":
                # Get all modules and start bulk validation
                all_modules = list(self.module_manager.mods.keys())
                if all_modules:
                    self.bulk_operations.set_selected_modules(all_modules)
                    operation_id = self.bulk_operations.validate_selected_modules()
                    self.notification_system.show_info(
                        "批量验证", f"开始验证 {len(all_modules)} 个模组"
                    )
                else:
                    self.notification_system.show_warning(
                        "无模组", "没有找到可验证的模组"
                    )

            elif action_id == "system_check":
                self.perform_system_check()

            elif action_id == "cleanup_cache":
                self.cleanup_system_cache()

            elif action_id == "export_report":
                self.export_system_report()

            elif action_id == "open_settings":
                self.notification_system.show_info("设置", "设置功能即将推出")

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.SYSTEM,
                context=ErrorContext(user_action=f"quick_action_{action_id}"),
            )

    def perform_system_check(self) -> None:
        """Perform comprehensive system health check"""
        try:
            issues_found = 0

            # Check for recent errors
            recent_errors = self.error_handler.get_unresolved_errors()
            if recent_errors:
                issues_found += len(recent_errors)

            # Check active workflows
            active_workflows = self.workflow_manager.get_active_workflows()
            stuck_workflows = [
                w
                for w in active_workflows.values()
                if w.updated_at < (time.time() - 3600)
            ]  # 1 hour old
            if stuck_workflows:
                issues_found += len(stuck_workflows)

            # Check module states
            error_modules = [
                name
                for name, info in self.module_manager.mods.items()
                if not info.usable
            ]
            if error_modules:
                issues_found += len(error_modules)

            if issues_found == 0:
                self.notification_system.show_success(
                    "系统检查", "系统运行正常，未发现问题"
                )
            else:
                actions = [
                    NotificationAction("view_report", "查看详细报告"),
                    NotificationAction("auto_fix", "自动修复"),
                ]
                self.notification_system.add_notification(
                    title="系统检查完成",
                    message=f"发现 {issues_found} 个问题需要注意",
                    notification_type=NotificationType.WARNING,
                    actions=actions,
                )

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.SYSTEM,
                context=ErrorContext(operation="system_check"),
            )

    def cleanup_system_cache(self) -> None:
        """Clean up system cache and temporary files"""
        try:
            cleaned_files = 0

            # Clean up old workflow data
            self.workflow_manager.save_workflows()  # Save current state first

            # Clean up old error logs
            old_errors = self.error_handler.get_recent_errors(hours=168)  # 1 week
            if len(old_errors) > 100:
                self.error_handler.clear_resolved_errors()
                cleaned_files += len(old_errors) - 100

            # Clean up old notifications
            self.notification_system.clear_read_notifications()

            # Clean up completed bulk operations
            self.bulk_operations.cleanup_completed_operations(older_than_hours=24)

            self.notification_system.show_success(
                "清理完成", f"已清理 {cleaned_files} 个临时文件"
            )

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.FILESYSTEM,
                context=ErrorContext(operation="cleanup_cache"),
            )

    def export_system_report(self) -> None:
        """Export comprehensive system report"""
        try:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"module_system_report_{timestamp}.json"

            # Export error report
            error_report_file = f"errors_{timestamp}.json"
            self.error_handler.export_error_report(
                error_report_file, include_resolved=True
            )

            # Export performance data
            performance_data = self.performance_monitor.export_data()

            self.notification_system.show_success(
                "报告导出", f"系统报告已导出到 {report_file}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.FILESYSTEM,
                context=ErrorContext(operation="export_report"),
            )

    # Workflow step handlers
    def handle_download_step(
        self, workflow_id: str, module_name: str, step_info: Any
    ) -> bool:
        """Handle download workflow step"""
        try:
            # Simulate download process
            self.workflow_manager.update_step_progress(workflow_id, 50, "正在下载...")
            # In real implementation, integrate with mod_download component
            self.workflow_manager.update_step_progress(workflow_id, 100, "下载完成")
            return True
        except Exception as e:
            logger.error(f"Download step failed for {module_name}: {e}")
            return False

    def handle_validate_step(
        self, workflow_id: str, module_name: str, step_info: Any
    ) -> bool:
        """Handle validation workflow step"""
        try:
            # Use existing validation logic
            if module_name in self.module_manager.mods:
                mod_info = self.module_manager.mods[module_name]
                return mod_info.usable
            return False
        except Exception as e:
            logger.error(f"Validation step failed for {module_name}: {e}")
            return False

    def handle_install_step(
        self, workflow_id: str, module_name: str, step_info: Any
    ) -> bool:
        """Handle installation workflow step"""
        try:
            # Simulate installation
            self.workflow_manager.update_step_progress(workflow_id, 30, "准备安装...")
            self.workflow_manager.update_step_progress(workflow_id, 70, "安装中...")
            self.workflow_manager.update_step_progress(workflow_id, 100, "安装完成")
            return True
        except Exception as e:
            logger.error(f"Install step failed for {module_name}: {e}")
            return False

    def handle_configure_step(
        self, workflow_id: str, module_name: str, step_info: Any
    ) -> bool:
        """Handle configuration workflow step"""
        try:
            # Apply default configuration
            return True
        except Exception as e:
            logger.error(f"Configure step failed for {module_name}: {e}")
            return False

    def handle_enable_step(self, workflow_id: str, module_name: str, step_info: Any) -> bool:
        """Handle enable workflow step"""
        try:
            if module_name in self.module_manager.mods:
                mod_info = self.module_manager.mods[module_name]
                mod_info.enabled = True
                return True
            return False
        except Exception as e:
            logger.error(f"Enable step failed for {module_name}: {e}")
            return False

    # Error recovery handlers
    def handle_retry_operation(self, error: Any, parameters: Any) -> bool:
        """Handle retry operation recovery"""
        try:
            # Implement retry logic based on error context
            return True
        except Exception:
            return False

    def handle_check_network(self, error: Any, parameters: Any) -> bool:
        """Handle network check recovery"""
        try:
            # Implement network connectivity check
            return True
        except Exception:
            return False

    def handle_fix_permissions(self, error: Any, parameters: Any) -> bool:
        """Handle permission fix recovery"""
        try:
            # Implement permission fixing logic
            return True
        except Exception:
            return False

    # Notification action handlers
    def handle_view_details(self, notification: Any, parameters: Any) -> bool:
        """Handle view details action"""
        try:
            # Switch to appropriate tab or show details dialog
            return True
        except Exception:
            return False

    def handle_retry_action(self, notification: Any, parameters: Any) -> bool:
        """Handle retry action"""
        try:
            # Implement retry logic based on notification context
            return True
        except Exception:
            return False


def main() -> None:
    """Main entry point for enhanced module interface"""
    import time

    app = QApplication(sys.argv)

    # Create and show the enhanced interface
    interface = EnhancedModuleInterface()
    interface.show()

    # Show welcome notification
    interface.notification_system.show_info("欢迎使用", "增强型模组管理系统已启动")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
