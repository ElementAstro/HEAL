"""
Fallback Initializer
Enhanced fallback initialization mechanisms with better recovery strategies
"""

import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from pathlib import Path

from .logging_config import get_logger
from .startup_error_handler import StartupError, ErrorSeverity, detect_startup_error

logger = get_logger(__name__)


class FallbackStrategy(Enum):
    """回退策略"""
    SKIP_COMPONENT = "skip_component"           # 跳过组件
    USE_DEFAULT = "use_default"                 # 使用默认值
    RETRY_WITH_DELAY = "retry_with_delay"       # 延迟重试
    LOAD_MINIMAL = "load_minimal"               # 加载最小配置
    SAFE_MODE = "safe_mode"                     # 安全模式
    EMERGENCY_MODE = "emergency_mode"           # 紧急模式


class RecoveryResult(Enum):
    """恢复结果"""
    SUCCESS = "success"                         # 成功恢复
    PARTIAL_SUCCESS = "partial_success"         # 部分成功
    FAILED = "failed"                          # 恢复失败
    SKIPPED = "skipped"                        # 跳过处理


@dataclass
class FallbackAction:
    """回退动作"""
    action_id: str
    strategy: FallbackStrategy
    handler: Callable[[], Any]
    description: str = ""
    priority: int = 1  # 1 = highest priority
    max_attempts: int = 3
    delay_between_attempts: float = 1.0
    
    # Runtime state
    attempts: int = 0
    last_attempt_time: float = 0.0
    last_result: Optional[RecoveryResult] = None
    last_error: Optional[Exception] = None


@dataclass
class ComponentFallback:
    """组件回退配置"""
    component_id: str
    component_name: str
    is_critical: bool = True
    fallback_actions: List[FallbackAction] = field(default_factory=list)
    emergency_handler: Optional[Callable[[], Any]] = None
    
    # State tracking
    current_action_index: int = 0
    recovery_attempts: int = 0
    is_recovered: bool = False
    final_result: Optional[RecoveryResult] = None


class FallbackInitializer:
    """回退初始化器"""
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="FallbackInitializer")
        self.component_fallbacks: Dict[str, ComponentFallback] = {}
        self.global_fallback_actions: List[FallbackAction] = []
        
        # Recovery statistics
        self.recovery_stats = {
            "total_recoveries_attempted": 0,
            "successful_recoveries": 0,
            "partial_recoveries": 0,
            "failed_recoveries": 0,
            "components_skipped": 0,
            "emergency_mode_activations": 0
        }
        
        self._register_default_fallbacks()
    
    def _register_default_fallbacks(self) -> None:
        """注册默认回退策略"""
        # Configuration fallback
        self.register_component_fallback(
            "configuration",
            "配置系统",
            is_critical=True,
            fallback_actions=[
                FallbackAction(
                    "config_retry",
                    FallbackStrategy.RETRY_WITH_DELAY,
                    self._retry_config_load,
                    "重试配置加载",
                    priority=1,
                    delay_between_attempts=2.0
                ),
                FallbackAction(
                    "config_default",
                    FallbackStrategy.USE_DEFAULT,
                    self._load_default_config,
                    "使用默认配置",
                    priority=2
                ),
                FallbackAction(
                    "config_minimal",
                    FallbackStrategy.LOAD_MINIMAL,
                    self._load_minimal_config,
                    "加载最小配置",
                    priority=3
                )
            ],
            emergency_handler=self._emergency_config_handler
        )
        
        # UI Theme fallback
        self.register_component_fallback(
            "theme",
            "主题系统",
            is_critical=False,
            fallback_actions=[
                FallbackAction(
                    "theme_default",
                    FallbackStrategy.USE_DEFAULT,
                    self._load_default_theme,
                    "使用默认主题",
                    priority=1
                ),
                FallbackAction(
                    "theme_skip",
                    FallbackStrategy.SKIP_COMPONENT,
                    self._skip_theme,
                    "跳过主题加载",
                    priority=2
                )
            ]
        )
        
        # Font system fallback
        self.register_component_fallback(
            "fonts",
            "字体系统",
            is_critical=False,
            fallback_actions=[
                FallbackAction(
                    "font_system",
                    FallbackStrategy.USE_DEFAULT,
                    self._use_system_fonts,
                    "使用系统字体",
                    priority=1
                ),
                FallbackAction(
                    "font_skip",
                    FallbackStrategy.SKIP_COMPONENT,
                    self._skip_font_check,
                    "跳过字体检查",
                    priority=2
                )
            ]
        )
        
        # Network components fallback
        self.register_component_fallback(
            "network",
            "网络组件",
            is_critical=False,
            fallback_actions=[
                FallbackAction(
                    "network_offline",
                    FallbackStrategy.SAFE_MODE,
                    self._enable_offline_mode,
                    "启用离线模式",
                    priority=1
                ),
                FallbackAction(
                    "network_skip",
                    FallbackStrategy.SKIP_COMPONENT,
                    self._skip_network_features,
                    "跳过网络功能",
                    priority=2
                )
            ]
        )
    
    def register_component_fallback(self, component_id: str, component_name: str,
                                  is_critical: bool = True,
                                  fallback_actions: Optional[List[FallbackAction]] = None,
                                  emergency_handler: Optional[Callable[[], Any]] = None) -> None:
        """注册组件回退配置"""
        fallback = ComponentFallback(
            component_id=component_id,
            component_name=component_name,
            is_critical=is_critical,
            fallback_actions=fallback_actions or [],
            emergency_handler=emergency_handler
        )
        
        self.component_fallbacks[component_id] = fallback
        self.logger.debug(f"Registered fallback for component: {component_id}")
    
    def attempt_recovery(self, component_id: str, original_error: Exception) -> RecoveryResult:
        """尝试恢复组件"""
        if component_id not in self.component_fallbacks:
            self.logger.warning(f"No fallback registered for component: {component_id}")
            return RecoveryResult.FAILED
        
        fallback = self.component_fallbacks[component_id]
        fallback.recovery_attempts += 1
        self.recovery_stats["total_recoveries_attempted"] += 1
        
        self.logger.info(f"Attempting recovery for component: {component_id}")
        
        # Analyze the original error
        startup_error = detect_startup_error(original_error, component_id)
        if startup_error:
            self.logger.debug(f"Error analysis: {startup_error.category.value} - {startup_error.severity.name}")
        
        # Try each fallback action in order
        for i, action in enumerate(fallback.fallback_actions):
            if i < fallback.current_action_index:
                continue  # Skip already tried actions
            
            fallback.current_action_index = i
            result = self._execute_fallback_action(action, component_id, original_error)
            
            if result == RecoveryResult.SUCCESS:
                fallback.is_recovered = True
                fallback.final_result = result
                self.recovery_stats["successful_recoveries"] += 1
                self.logger.info(f"Successfully recovered component {component_id} using {action.strategy.value}")
                return result
            elif result == RecoveryResult.PARTIAL_SUCCESS:
                fallback.is_recovered = True
                fallback.final_result = result
                self.recovery_stats["partial_recoveries"] += 1
                self.logger.info(f"Partially recovered component {component_id} using {action.strategy.value}")
                return result
            elif result == RecoveryResult.SKIPPED:
                fallback.final_result = result
                self.recovery_stats["components_skipped"] += 1
                self.logger.info(f"Skipped component {component_id}")
                return result
        
        # All fallback actions failed, try emergency handler
        if fallback.emergency_handler:
            try:
                self.logger.warning(f"Attempting emergency recovery for {component_id}")
                fallback.emergency_handler()
                fallback.final_result = RecoveryResult.PARTIAL_SUCCESS
                self.recovery_stats["emergency_mode_activations"] += 1
                return RecoveryResult.PARTIAL_SUCCESS
            except Exception as e:
                self.logger.error(f"Emergency handler failed for {component_id}: {e}")
        
        # Complete failure
        fallback.final_result = RecoveryResult.FAILED
        self.recovery_stats["failed_recoveries"] += 1
        
        if fallback.is_critical:
            self.logger.critical(f"Critical component {component_id} recovery failed")
        else:
            self.logger.warning(f"Non-critical component {component_id} recovery failed")
        
        return RecoveryResult.FAILED
    
    def _execute_fallback_action(self, action: FallbackAction, component_id: str, 
                                original_error: Exception) -> RecoveryResult:
        """执行回退动作"""
        action.attempts += 1
        action.last_attempt_time = time.time()
        
        try:
            self.logger.debug(f"Executing fallback action: {action.action_id} for {component_id}")
            
            # Add delay if this is a retry
            if action.strategy == FallbackStrategy.RETRY_WITH_DELAY and action.attempts > 1:
                time.sleep(action.delay_between_attempts)
            
            # Execute the action
            result = action.handler()
            
            # Determine success based on strategy
            if action.strategy == FallbackStrategy.SKIP_COMPONENT:
                action.last_result = RecoveryResult.SKIPPED
                return RecoveryResult.SKIPPED
            elif result is not None:
                action.last_result = RecoveryResult.SUCCESS
                return RecoveryResult.SUCCESS
            else:
                action.last_result = RecoveryResult.PARTIAL_SUCCESS
                return RecoveryResult.PARTIAL_SUCCESS
                
        except Exception as e:
            action.last_error = e
            action.last_result = RecoveryResult.FAILED
            
            self.logger.error(f"Fallback action {action.action_id} failed: {e}")
            
            # Retry if attempts remaining
            if action.attempts < action.max_attempts:
                self.logger.info(f"Retrying fallback action {action.action_id} "
                               f"(attempt {action.attempts + 1}/{action.max_attempts})")
                return self._execute_fallback_action(action, component_id, original_error)
            
            return RecoveryResult.FAILED
    
    def get_recovery_status(self, component_id: str) -> Optional[Dict[str, Any]]:
        """获取组件恢复状态"""
        if component_id not in self.component_fallbacks:
            return None
        
        fallback = self.component_fallbacks[component_id]
        
        return {
            "component_id": component_id,
            "component_name": fallback.component_name,
            "is_critical": fallback.is_critical,
            "recovery_attempts": fallback.recovery_attempts,
            "is_recovered": fallback.is_recovered,
            "final_result": fallback.final_result.value if fallback.final_result else None,
            "current_action_index": fallback.current_action_index,
            "total_actions": len(fallback.fallback_actions),
            "action_details": [
                {
                    "action_id": action.action_id,
                    "strategy": action.strategy.value,
                    "attempts": action.attempts,
                    "last_result": action.last_result.value if action.last_result else None,
                    "has_error": action.last_error is not None
                }
                for action in fallback.fallback_actions
            ]
        }
    
    def get_recovery_report(self) -> Dict[str, Any]:
        """获取恢复报告"""
        component_statuses = {}
        for component_id in self.component_fallbacks:
            component_statuses[component_id] = self.get_recovery_status(component_id)
        
        return {
            "recovery_stats": self.recovery_stats,
            "component_statuses": component_statuses,
            "total_components": len(self.component_fallbacks),
            "recovered_components": sum(1 for f in self.component_fallbacks.values() if f.is_recovered),
            "failed_components": sum(1 for f in self.component_fallbacks.values() 
                                   if f.final_result == RecoveryResult.FAILED),
            "critical_failures": sum(1 for f in self.component_fallbacks.values() 
                                   if f.is_critical and f.final_result == RecoveryResult.FAILED)
        }
    
    # Default fallback handlers
    def _retry_config_load(self) -> Any:
        """重试配置加载"""
        from .config_manager import config_manager
        try:
            # Clear cache and retry
            config_manager.clear_cache()
            # Try to get a basic config
            from .config_manager import ConfigType
            return config_manager.get_config(ConfigType.APP)
        except Exception as e:
            self.logger.error(f"Config retry failed: {e}")
            raise
    
    def _load_default_config(self) -> Any:
        """加载默认配置"""
        self.logger.info("Loading default configuration")
        return {
            "app": {"name": "HEAL", "version": "1.0.0"},
            "ui": {"theme": "light", "language": "zh_CN"},
            "startup": {"check_updates": False, "show_splash": True}
        }
    
    def _load_minimal_config(self) -> Any:
        """加载最小配置"""
        self.logger.info("Loading minimal configuration")
        return {
            "app": {"name": "HEAL"},
            "ui": {"theme": "light"}
        }
    
    def _emergency_config_handler(self) -> Any:
        """紧急配置处理器"""
        self.logger.warning("Activating emergency configuration mode")
        return {"app": {"name": "HEAL", "emergency_mode": True}}
    
    def _load_default_theme(self) -> Any:
        """加载默认主题"""
        self.logger.info("Loading default theme")
        return {"theme": "light", "fallback": True}
    
    def _skip_theme(self) -> Any:
        """跳过主题加载"""
        self.logger.info("Skipping theme loading")
        return None
    
    def _use_system_fonts(self) -> Any:
        """使用系统字体"""
        self.logger.info("Using system fonts")
        return {"fonts": "system", "fallback": True}
    
    def _skip_font_check(self) -> Any:
        """跳过字体检查"""
        self.logger.info("Skipping font check")
        return None
    
    def _enable_offline_mode(self) -> Any:
        """启用离线模式"""
        self.logger.info("Enabling offline mode")
        return {"network": "offline", "mode": "safe"}
    
    def _skip_network_features(self) -> Any:
        """跳过网络功能"""
        self.logger.info("Skipping network features")
        return None
    
    def reset_component(self, component_id: str) -> None:
        """重置组件状态"""
        if component_id in self.component_fallbacks:
            fallback = self.component_fallbacks[component_id]
            fallback.current_action_index = 0
            fallback.recovery_attempts = 0
            fallback.is_recovered = False
            fallback.final_result = None
            
            # Reset actions
            for action in fallback.fallback_actions:
                action.attempts = 0
                action.last_attempt_time = 0.0
                action.last_result = None
                action.last_error = None
            
            self.logger.debug(f"Reset fallback state for component: {component_id}")
    
    def reset_all(self) -> None:
        """重置所有组件状态"""
        for component_id in self.component_fallbacks:
            self.reset_component(component_id)
        
        self.recovery_stats = {
            "total_recoveries_attempted": 0,
            "successful_recoveries": 0,
            "partial_recoveries": 0,
            "failed_recoveries": 0,
            "components_skipped": 0,
            "emergency_mode_activations": 0
        }
        
        self.logger.info("Reset all fallback states")


# Global fallback initializer
fallback_initializer = FallbackInitializer()


class AutoRecoveryManager:
    """自动恢复管理器 - 处理常见启动失败场景"""

    def __init__(self) -> None:
        self.logger = logger.bind(component="AutoRecoveryManager")
        self.recovery_strategies: Dict[str, Callable[[Exception], bool]] = {}
        self.recovery_history: List[Dict[str, Any]] = []

        self._register_common_recovery_strategies()

    def _register_common_recovery_strategies(self) -> None:
        """注册常见恢复策略"""
        self.recovery_strategies.update({
            "FileNotFoundError": self._recover_missing_file,
            "PermissionError": self._recover_permission_issue,
            "ImportError": self._recover_import_error,
            "ModuleNotFoundError": self._recover_missing_module,
            "ConnectionError": self._recover_connection_error,
            "MemoryError": self._recover_memory_error,
            "OSError": self._recover_os_error,
            "ValueError": self._recover_value_error,
            "ConfigurationError": self._recover_config_error,
            "DatabaseError": self._recover_database_error
        })

    def attempt_auto_recovery(self, error: Exception, context: str = "") -> bool:
        """尝试自动恢复"""
        error_type = type(error).__name__

        if error_type in self.recovery_strategies:
            try:
                self.logger.info(f"Attempting auto-recovery for {error_type} in {context}")

                recovery_start = time.time()
                success = self.recovery_strategies[error_type](error)
                recovery_time = time.time() - recovery_start

                # Record recovery attempt
                self.recovery_history.append({
                    "error_type": error_type,
                    "context": context,
                    "success": success,
                    "recovery_time": recovery_time,
                    "timestamp": time.time(),
                    "error_message": str(error)
                })

                if success:
                    self.logger.info(f"Auto-recovery successful for {error_type} in {recovery_time:.2f}s")
                else:
                    self.logger.warning(f"Auto-recovery failed for {error_type}")

                return success

            except Exception as recovery_error:
                self.logger.error(f"Auto-recovery strategy failed: {recovery_error}")
                return False

        self.logger.debug(f"No auto-recovery strategy for {error_type}")
        return False

    def _recover_missing_file(self, error: Exception) -> bool:
        """恢复缺失文件"""
        error_str = str(error)

        # Extract filename from error message
        if "'" in error_str:
            filename = error_str.split("'")[1]
        else:
            return False

        file_path = Path(filename)

        # Try to create missing directories
        if not file_path.parent.exists():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created missing directory: {file_path.parent}")
            except Exception as e:
                self.logger.error(f"Failed to create directory: {e}")
                return False

        # Try to restore from backup
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        if backup_path.exists():
            try:
                import shutil
                shutil.copy2(backup_path, file_path)
                self.logger.info(f"Restored file from backup: {filename}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to restore from backup: {e}")

        # Try to create default file for known config files
        if 'config' in filename.lower() and filename.endswith('.json'):
            try:
                default_config = {"app": {"name": "HEAL", "version": "1.0.0"}}
                with open(file_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(default_config, f, indent=2)
                self.logger.info(f"Created default config file: {filename}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create default config: {e}")

        return False

    def _recover_permission_issue(self, error: Exception) -> bool:
        """恢复权限问题"""
        error_str = str(error)

        # Try to identify the problematic path
        import re
        path_match = re.search(r"'([^']+)'", error_str)
        if not path_match:
            return False

        problem_path = Path(path_match.group(1))

        # Try to fix permissions
        try:
            import stat
            if problem_path.exists():
                # Add read/write permissions for owner
                current_mode = problem_path.stat().st_mode
                new_mode = current_mode | stat.S_IRUSR | stat.S_IWUSR
                problem_path.chmod(new_mode)
                self.logger.info(f"Fixed permissions for: {problem_path}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to fix permissions: {e}")

        # Try alternative location in user directory
        try:
            import os
            user_dir = Path.home() / "HEAL"
            user_dir.mkdir(exist_ok=True)

            # Update path in environment or config
            os.environ['HEAL_USER_DIR'] = str(user_dir)
            self.logger.info(f"Set alternative user directory: {user_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set alternative directory: {e}")

        return False

    def _recover_import_error(self, error: Exception) -> bool:
        """恢复导入错误"""
        error_str = str(error)

        # Try to identify missing module
        if "'" in error_str:
            module_name = error_str.split("'")[1]
        else:
            return False

        # Try to install missing module
        try:
            import subprocess
            import sys

            self.logger.info(f"Attempting to install missing module: {module_name}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", module_name],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully installed module: {module_name}")
                return True
            else:
                self.logger.error(f"Failed to install module: {result.stderr}")
        except Exception as e:
            self.logger.error(f"Module installation failed: {e}")

        return False

    def _recover_missing_module(self, error: Exception) -> bool:
        """恢复缺失模块"""
        return self._recover_import_error(error)

    def _recover_connection_error(self, error: Exception) -> bool:
        """恢复连接错误"""
        # Enable offline mode
        try:
            import os
            os.environ['HEAL_OFFLINE_MODE'] = 'true'
            self.logger.info("Enabled offline mode due to connection error")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable offline mode: {e}")

        return False

    def _recover_memory_error(self, error: MemoryError) -> bool:
        """恢复内存错误"""
        try:
            import gc
            import os

            # Force garbage collection
            gc.collect()

            # Enable memory-saving mode
            os.environ['HEAL_MEMORY_SAVE_MODE'] = 'true'

            # Reduce cache sizes
            os.environ['HEAL_CACHE_SIZE'] = '10'  # Reduce cache size

            self.logger.info("Enabled memory-saving mode")
            return True
        except Exception as e:
            self.logger.error(f"Memory recovery failed: {e}")

        return False

    def _recover_os_error(self, error: OSError) -> bool:
        """恢复操作系统错误"""
        error_code = getattr(error, 'errno', None)

        if error_code == 28:  # No space left on device
            try:
                import tempfile
                import os

                # Use temporary directory
                temp_dir = tempfile.mkdtemp(prefix="heal_")
                os.environ['HEAL_TEMP_DIR'] = temp_dir
                self.logger.info(f"Using temporary directory: {temp_dir}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to set temporary directory: {e}")

        return False

    def _recover_value_error(self, error: ValueError) -> bool:
        """恢复值错误"""
        # Usually indicates configuration issues
        try:
            import os
            os.environ['HEAL_USE_DEFAULT_CONFIG'] = 'true'
            self.logger.info("Enabled default configuration mode")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable default config mode: {e}")

        return False

    def _recover_config_error(self, error: Exception) -> bool:
        """恢复配置错误"""
        try:
            # Reset to default configuration
            from .config_manager import config_manager
            config_manager.clear_cache()

            import os
            os.environ['HEAL_RESET_CONFIG'] = 'true'

            self.logger.info("Reset configuration to defaults")
            return True
        except Exception as e:
            self.logger.error(f"Config recovery failed: {e}")

        return False

    def _recover_database_error(self, error: Exception) -> bool:
        """恢复数据库错误"""
        try:
            import os
            os.environ['HEAL_DATABASE_RECOVERY'] = 'true'
            self.logger.info("Enabled database recovery mode")
            return True
        except Exception as e:
            self.logger.error(f"Database recovery failed: {e}")

        return False

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """获取恢复统计"""
        if not self.recovery_history:
            return {"total_attempts": 0}

        total_attempts = len(self.recovery_history)
        successful_attempts = sum(1 for r in self.recovery_history if r["success"])

        error_types = {}
        for record in self.recovery_history:
            error_type = record["error_type"]
            if error_type not in error_types:
                error_types[error_type] = {"total": 0, "successful": 0}
            error_types[error_type]["total"] += 1
            if record["success"]:
                error_types[error_type]["successful"] += 1

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "error_types": error_types,
            "recent_attempts": self.recovery_history[-10:]  # Last 10 attempts
        }


# Global auto recovery manager
auto_recovery_manager = AutoRecoveryManager()


# Convenience functions
def attempt_component_recovery(component_id: str, error: Exception) -> RecoveryResult:
    """尝试组件恢复"""
    # First try auto-recovery
    if auto_recovery_manager.attempt_auto_recovery(error, component_id):
        return RecoveryResult.SUCCESS

    # Fall back to manual recovery strategies
    return fallback_initializer.attempt_recovery(component_id, error)


def attempt_auto_recovery(error: Exception, context: str = "") -> bool:
    """尝试自动恢复"""
    return auto_recovery_manager.attempt_auto_recovery(error, context)


def get_auto_recovery_stats() -> Dict[str, Any]:
    """获取自动恢复统计"""
    return auto_recovery_manager.get_recovery_statistics()


def get_component_recovery_status(component_id: str) -> Optional[Dict[str, Any]]:
    """获取组件恢复状态"""
    return fallback_initializer.get_recovery_status(component_id)


def get_fallback_recovery_report() -> Dict[str, Any]:
    """获取回退恢复报告"""
    return fallback_initializer.get_recovery_report()


def register_component_fallback(component_id: str, component_name: str,
                              is_critical: bool = True,
                              fallback_actions: Optional[List[FallbackAction]] = None,
                              emergency_handler: Optional[Callable[[], Any]] = None) -> None:
    """注册组件回退配置"""
    fallback_initializer.register_component_fallback(
        component_id, component_name, is_critical, fallback_actions, emergency_handler
    )
