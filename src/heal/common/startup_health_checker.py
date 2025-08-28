"""
Startup Health Checker
Comprehensive health check system to validate startup state and diagnose issues
"""

import time
import psutil
import sys
import platform
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set
import json

from .logging_config import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class CheckCategory(Enum):
    """检查类别"""
    SYSTEM = "system"
    RESOURCES = "resources"
    DEPENDENCIES = "dependencies"
    CONFIGURATION = "configuration"
    PERMISSIONS = "permissions"
    NETWORK = "network"
    PERFORMANCE = "performance"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    check_id: str
    name: str
    category: CheckCategory
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    # Metrics
    value: Optional[float] = None
    threshold: Optional[float] = None
    unit: str = ""


@dataclass
class HealthCheckDefinition:
    """健康检查定义"""
    check_id: str
    name: str
    category: CheckCategory
    check_func: Callable[[], HealthCheckResult]
    enabled: bool = True
    timeout: float = 10.0
    critical: bool = False
    description: str = ""


class StartupHealthChecker:
    """启动健康检查器"""
    
    def __init__(self):
        self.logger = logger.bind(component="StartupHealthChecker")
        self.health_checks: Dict[str, HealthCheckDefinition] = {}
        self.last_check_results: Dict[str, HealthCheckResult] = {}
        self.check_history: List[Dict[str, Any]] = []
        
        # Health statistics
        self.health_stats = {
            "total_checks": 0,
            "healthy_checks": 0,
            "warning_checks": 0,
            "critical_checks": 0,
            "failed_checks": 0,
            "last_check_time": None,
            "average_check_time": 0.0
        }
        
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        """注册默认健康检查"""
        # System checks
        self.register_health_check(
            "system_memory",
            "系统内存检查",
            CheckCategory.SYSTEM,
            self._check_system_memory,
            critical=True,
            description="检查系统内存使用情况"
        )
        
        self.register_health_check(
            "system_disk",
            "系统磁盘检查",
            CheckCategory.SYSTEM,
            self._check_system_disk,
            critical=True,
            description="检查系统磁盘空间"
        )
        
        self.register_health_check(
            "system_cpu",
            "系统CPU检查",
            CheckCategory.SYSTEM,
            self._check_system_cpu,
            description="检查系统CPU使用情况"
        )
        
        # Dependencies checks
        self.register_health_check(
            "python_version",
            "Python版本检查",
            CheckCategory.DEPENDENCIES,
            self._check_python_version,
            critical=True,
            description="检查Python版本兼容性"
        )
        
        self.register_health_check(
            "critical_modules",
            "关键模块检查",
            CheckCategory.DEPENDENCIES,
            self._check_critical_modules,
            critical=True,
            description="检查关键Python模块"
        )
        
        # Configuration checks
        self.register_health_check(
            "config_files",
            "配置文件检查",
            CheckCategory.CONFIGURATION,
            self._check_config_files,
            critical=True,
            description="检查配置文件完整性"
        )
        
        self.register_health_check(
            "config_syntax",
            "配置语法检查",
            CheckCategory.CONFIGURATION,
            self._check_config_syntax,
            description="检查配置文件语法"
        )
        
        # Permissions checks
        self.register_health_check(
            "file_permissions",
            "文件权限检查",
            CheckCategory.PERMISSIONS,
            self._check_file_permissions,
            critical=True,
            description="检查文件和目录权限"
        )
        
        # Performance checks
        self.register_health_check(
            "startup_performance",
            "启动性能检查",
            CheckCategory.PERFORMANCE,
            self._check_startup_performance,
            description="检查启动性能指标"
        )
    
    def register_health_check(self, check_id: str, name: str, category: CheckCategory,
                            check_func: Callable[[], HealthCheckResult],
                            enabled: bool = True, timeout: float = 10.0,
                            critical: bool = False, description: str = "") -> None:
        """注册健康检查"""
        check_def = HealthCheckDefinition(
            check_id=check_id,
            name=name,
            category=category,
            check_func=check_func,
            enabled=enabled,
            timeout=timeout,
            critical=critical,
            description=description
        )
        
        self.health_checks[check_id] = check_def
        self.logger.debug(f"Registered health check: {check_id}")
    
    def run_health_checks(self, categories: Optional[List[CheckCategory]] = None,
                         critical_only: bool = False) -> Dict[str, HealthCheckResult]:
        """运行健康检查"""
        start_time = time.time()
        results = {}
        
        # Filter checks
        checks_to_run = []
        for check_def in self.health_checks.values():
            if not check_def.enabled:
                continue
            if categories and check_def.category not in categories:
                continue
            if critical_only and not check_def.critical:
                continue
            checks_to_run.append(check_def)
        
        self.logger.info(f"Running {len(checks_to_run)} health checks")
        
        # Execute checks
        for check_def in checks_to_run:
            try:
                check_start = time.time()
                result = check_def.check_func()
                result.execution_time = time.time() - check_start
                
                results[check_def.check_id] = result
                self.last_check_results[check_def.check_id] = result
                
                self.logger.debug(f"Health check {check_def.check_id}: {result.status.value}")
                
            except Exception as e:
                # Create error result
                error_result = HealthCheckResult(
                    check_id=check_def.check_id,
                    name=check_def.name,
                    category=check_def.category,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    execution_time=time.time() - check_start
                )
                
                results[check_def.check_id] = error_result
                self.last_check_results[check_def.check_id] = error_result
                
                self.logger.error(f"Health check {check_def.check_id} failed: {e}")
        
        # Update statistics
        self._update_health_stats(results)
        
        # Store in history
        total_time = time.time() - start_time
        self.check_history.append({
            "timestamp": time.time(),
            "total_time": total_time,
            "checks_run": len(results),
            "results_summary": self._summarize_results(results)
        })
        
        # Keep only last 50 check histories
        if len(self.check_history) > 50:
            self.check_history.pop(0)
        
        self.logger.info(f"Health checks completed in {total_time:.2f}s")
        return results
    
    def _update_health_stats(self, results: Dict[str, HealthCheckResult]) -> None:
        """更新健康统计"""
        self.health_stats["total_checks"] = len(results)
        self.health_stats["healthy_checks"] = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
        self.health_stats["warning_checks"] = sum(1 for r in results.values() if r.status == HealthStatus.WARNING)
        self.health_stats["critical_checks"] = sum(1 for r in results.values() if r.status == HealthStatus.CRITICAL)
        self.health_stats["failed_checks"] = sum(1 for r in results.values() if r.status == HealthStatus.UNKNOWN)
        self.health_stats["last_check_time"] = time.time()
        
        if results:
            avg_time = sum(r.execution_time for r in results.values()) / len(results)
            self.health_stats["average_check_time"] = avg_time
    
    def _summarize_results(self, results: Dict[str, HealthCheckResult]) -> Dict[str, int]:
        """汇总结果"""
        summary = {status.value: 0 for status in HealthStatus}
        for result in results.values():
            summary[result.status.value] += 1
        return summary
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        overall_status = self._determine_overall_status()
        
        return {
            "overall_status": overall_status.value,
            "timestamp": time.time(),
            "statistics": self.health_stats,
            "check_results": {
                check_id: {
                    "name": result.name,
                    "category": result.category.value,
                    "status": result.status.value,
                    "message": result.message,
                    "execution_time": result.execution_time,
                    "value": result.value,
                    "threshold": result.threshold,
                    "unit": result.unit
                }
                for check_id, result in self.last_check_results.items()
            },
            "recommendations": self._get_all_recommendations(),
            "critical_issues": self._get_critical_issues()
        }
    
    def _determine_overall_status(self) -> HealthStatus:
        """确定整体健康状态"""
        if not self.last_check_results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self.last_check_results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.HEALTHY in statuses:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _get_all_recommendations(self) -> List[str]:
        """获取所有建议"""
        recommendations = []
        for result in self.last_check_results.values():
            recommendations.extend(result.recommendations)
        return list(set(recommendations))  # Remove duplicates
    
    def _get_critical_issues(self) -> List[Dict[str, str]]:
        """获取关键问题"""
        critical_issues = []
        for result in self.last_check_results.values():
            if result.status == HealthStatus.CRITICAL:
                critical_issues.append({
                    "check_id": result.check_id,
                    "name": result.name,
                    "message": result.message
                })
        return critical_issues
    
    # Default health check implementations
    def _check_system_memory(self) -> HealthCheckResult:
        """检查系统内存"""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"内存使用率过高: {usage_percent:.1f}%"
                recommendations = ["关闭不必要的应用程序", "重启计算机释放内存", "考虑增加内存"]
            elif usage_percent > 80:
                status = HealthStatus.WARNING
                message = f"内存使用率较高: {usage_percent:.1f}%"
                recommendations = ["监控内存使用情况", "关闭部分应用程序"]
            else:
                status = HealthStatus.HEALTHY
                message = f"内存使用正常: {usage_percent:.1f}%"
                recommendations = []
            
            return HealthCheckResult(
                check_id="system_memory",
                name="系统内存检查",
                category=CheckCategory.SYSTEM,
                status=status,
                message=message,
                details={
                    "total_memory": memory.total,
                    "available_memory": memory.available,
                    "used_memory": memory.used
                },
                recommendations=recommendations,
                value=usage_percent,
                threshold=80.0,
                unit="%"
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_id="system_memory",
                name="系统内存检查",
                category=CheckCategory.SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"内存检查失败: {str(e)}"
            )
    
    def _check_system_disk(self) -> HealthCheckResult:
        """检查系统磁盘"""
        try:
            disk_path = 'C:' if sys.platform == 'win32' else '/'
            disk = psutil.disk_usage(disk_path)
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
                message = f"磁盘空间严重不足: {usage_percent:.1f}%"
                recommendations = ["立即清理磁盘空间", "删除临时文件", "移动文件到外部存储"]
            elif usage_percent > 85:
                status = HealthStatus.WARNING
                message = f"磁盘空间不足: {usage_percent:.1f}%"
                recommendations = ["清理磁盘空间", "删除不需要的文件"]
            else:
                status = HealthStatus.HEALTHY
                message = f"磁盘空间充足: {usage_percent:.1f}%"
                recommendations = []
            
            return HealthCheckResult(
                check_id="system_disk",
                name="系统磁盘检查",
                category=CheckCategory.SYSTEM,
                status=status,
                message=message,
                details={
                    "total_space": disk.total,
                    "free_space": disk.free,
                    "used_space": disk.used,
                    "disk_path": disk_path
                },
                recommendations=recommendations,
                value=usage_percent,
                threshold=85.0,
                unit="%"
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_id="system_disk",
                name="系统磁盘检查",
                category=CheckCategory.SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"磁盘检查失败: {str(e)}"
            )
    
    def _check_system_cpu(self) -> HealthCheckResult:
        """检查系统CPU"""
        try:
            # Get CPU usage over 1 second
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > 90:
                status = HealthStatus.WARNING
                message = f"CPU使用率较高: {cpu_percent:.1f}%"
                recommendations = ["检查高CPU使用的进程", "关闭不必要的应用程序"]
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU使用正常: {cpu_percent:.1f}%"
                recommendations = []
            
            return HealthCheckResult(
                check_id="system_cpu",
                name="系统CPU检查",
                category=CheckCategory.SYSTEM,
                status=status,
                message=message,
                details={
                    "cpu_count": psutil.cpu_count(),
                    "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                recommendations=recommendations,
                value=cpu_percent,
                threshold=90.0,
                unit="%"
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_id="system_cpu",
                name="系统CPU检查",
                category=CheckCategory.SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"CPU检查失败: {str(e)}"
            )
    
    def _check_python_version(self) -> HealthCheckResult:
        """检查Python版本"""
        try:
            version = sys.version_info
            version_str = f"{version.major}.{version.minor}.{version.micro}"
            
            # Check minimum Python version (3.8+)
            if version.major < 3 or (version.major == 3 and version.minor < 8):
                status = HealthStatus.CRITICAL
                message = f"Python版本过低: {version_str} (需要3.8+)"
                recommendations = ["升级Python到3.8或更高版本"]
            elif version.major == 3 and version.minor < 10:
                status = HealthStatus.WARNING
                message = f"Python版本较旧: {version_str} (建议3.10+)"
                recommendations = ["考虑升级到Python 3.10或更高版本"]
            else:
                status = HealthStatus.HEALTHY
                message = f"Python版本正常: {version_str}"
                recommendations = []
            
            return HealthCheckResult(
                check_id="python_version",
                name="Python版本检查",
                category=CheckCategory.DEPENDENCIES,
                status=status,
                message=message,
                details={
                    "version": version_str,
                    "implementation": platform.python_implementation(),
                    "compiler": platform.python_compiler()
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_id="python_version",
                name="Python版本检查",
                category=CheckCategory.DEPENDENCIES,
                status=HealthStatus.UNKNOWN,
                message=f"Python版本检查失败: {str(e)}"
            )
    
    def _check_critical_modules(self) -> HealthCheckResult:
        """检查关键模块"""
        critical_modules = [
            'PySide6',
            'qfluentwidgets', 
            'psutil',
            'json',
            'pathlib'
        ]
        
        missing_modules = []
        available_modules = []
        
        for module in critical_modules:
            try:
                __import__(module)
                available_modules.append(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            status = HealthStatus.CRITICAL
            message = f"缺少关键模块: {', '.join(missing_modules)}"
            recommendations = [f"安装缺少的模块: pip install {' '.join(missing_modules)}"]
        else:
            status = HealthStatus.HEALTHY
            message = "所有关键模块都可用"
            recommendations = []
        
        return HealthCheckResult(
            check_id="critical_modules",
            name="关键模块检查",
            category=CheckCategory.DEPENDENCIES,
            status=status,
            message=message,
            details={
                "available_modules": available_modules,
                "missing_modules": missing_modules,
                "total_checked": len(critical_modules)
            },
            recommendations=recommendations
        )
    
    def _check_config_files(self) -> HealthCheckResult:
        """检查配置文件"""
        config_dir = Path("config")
        required_configs = ["app.json", "ui.json"]
        
        missing_files = []
        existing_files = []
        
        if not config_dir.exists():
            status = HealthStatus.CRITICAL
            message = "配置目录不存在"
            recommendations = ["创建配置目录", "恢复配置文件"]
        else:
            for config_file in required_configs:
                config_path = config_dir / config_file
                if config_path.exists():
                    existing_files.append(config_file)
                else:
                    missing_files.append(config_file)
            
            if missing_files:
                status = HealthStatus.WARNING
                message = f"缺少配置文件: {', '.join(missing_files)}"
                recommendations = ["创建缺少的配置文件", "从备份恢复配置"]
            else:
                status = HealthStatus.HEALTHY
                message = "所有配置文件都存在"
                recommendations = []
        
        return HealthCheckResult(
            check_id="config_files",
            name="配置文件检查",
            category=CheckCategory.CONFIGURATION,
            status=status,
            message=message,
            details={
                "config_dir_exists": config_dir.exists(),
                "existing_files": existing_files,
                "missing_files": missing_files
            },
            recommendations=recommendations
        )
    
    def _check_config_syntax(self) -> HealthCheckResult:
        """检查配置语法"""
        config_dir = Path("config")
        config_files = []
        syntax_errors = []
        
        if config_dir.exists():
            for config_file in config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                    config_files.append(config_file.name)
                except json.JSONDecodeError as e:
                    syntax_errors.append(f"{config_file.name}: {str(e)}")
                except Exception as e:
                    syntax_errors.append(f"{config_file.name}: {str(e)}")
        
        if syntax_errors:
            status = HealthStatus.CRITICAL
            message = f"配置文件语法错误: {len(syntax_errors)} 个文件"
            recommendations = ["修复配置文件语法错误", "恢复正确的配置文件"]
        elif config_files:
            status = HealthStatus.HEALTHY
            message = f"配置文件语法正确: {len(config_files)} 个文件"
            recommendations = []
        else:
            status = HealthStatus.WARNING
            message = "没有找到配置文件"
            recommendations = ["创建必要的配置文件"]
        
        return HealthCheckResult(
            check_id="config_syntax",
            name="配置语法检查",
            category=CheckCategory.CONFIGURATION,
            status=status,
            message=message,
            details={
                "valid_files": config_files,
                "syntax_errors": syntax_errors
            },
            recommendations=recommendations
        )
    
    def _check_file_permissions(self) -> HealthCheckResult:
        """检查文件权限"""
        test_paths = [
            Path.cwd(),
            Path("config"),
            Path("logs")
        ]
        
        permission_issues = []
        accessible_paths = []
        
        for path in test_paths:
            try:
                if path.exists():
                    # Test read permission
                    if path.is_dir():
                        list(path.iterdir())
                    else:
                        path.read_text()
                    
                    # Test write permission
                    test_file = path / "test_write.tmp" if path.is_dir() else path.with_suffix('.tmp')
                    test_file.write_text("test")
                    test_file.unlink()
                    
                    accessible_paths.append(str(path))
                else:
                    # Try to create directory
                    if not path.exists() and path.name in ['config', 'logs']:
                        path.mkdir(parents=True, exist_ok=True)
                        accessible_paths.append(str(path))
                    
            except PermissionError:
                permission_issues.append(f"权限不足: {path}")
            except Exception as e:
                permission_issues.append(f"访问错误 {path}: {str(e)}")
        
        if permission_issues:
            status = HealthStatus.CRITICAL
            message = f"文件权限问题: {len(permission_issues)} 个路径"
            recommendations = ["以管理员身份运行", "检查文件和目录权限", "更改文件所有权"]
        else:
            status = HealthStatus.HEALTHY
            message = "文件权限正常"
            recommendations = []
        
        return HealthCheckResult(
            check_id="file_permissions",
            name="文件权限检查",
            category=CheckCategory.PERMISSIONS,
            status=status,
            message=message,
            details={
                "accessible_paths": accessible_paths,
                "permission_issues": permission_issues
            },
            recommendations=recommendations
        )
    
    def _check_startup_performance(self) -> HealthCheckResult:
        """检查启动性能"""
        try:
            from .startup_performance_monitor import get_startup_performance_summary
            
            perf_summary = get_startup_performance_summary()
            
            if "error" in perf_summary:
                status = HealthStatus.WARNING
                message = "无法获取启动性能数据"
                recommendations = ["检查性能监控系统"]
            else:
                avg_time = perf_summary.get("average_startup_time", 0)
                
                if avg_time > 10:
                    status = HealthStatus.WARNING
                    message = f"启动时间较长: {avg_time:.2f}s"
                    recommendations = ["优化启动流程", "检查系统性能", "清理启动项"]
                elif avg_time > 5:
                    status = HealthStatus.WARNING
                    message = f"启动时间一般: {avg_time:.2f}s"
                    recommendations = ["考虑优化启动流程"]
                else:
                    status = HealthStatus.HEALTHY
                    message = f"启动性能良好: {avg_time:.2f}s"
                    recommendations = []
            
            return HealthCheckResult(
                check_id="startup_performance",
                name="启动性能检查",
                category=CheckCategory.PERFORMANCE,
                status=status,
                message=message,
                details=perf_summary,
                recommendations=recommendations,
                value=perf_summary.get("average_startup_time"),
                threshold=5.0,
                unit="s"
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_id="startup_performance",
                name="启动性能检查",
                category=CheckCategory.PERFORMANCE,
                status=HealthStatus.UNKNOWN,
                message=f"性能检查失败: {str(e)}"
            )


# Global startup health checker
startup_health_checker = StartupHealthChecker()


# Convenience functions
def run_startup_health_checks(critical_only: bool = False) -> Dict[str, HealthCheckResult]:
    """运行启动健康检查"""
    return startup_health_checker.run_health_checks(critical_only=critical_only)


def get_startup_health_report() -> Dict[str, Any]:
    """获取启动健康报告"""
    return startup_health_checker.get_health_report()


def register_custom_health_check(check_id: str, name: str, category: CheckCategory,
                                check_func: Callable[[], HealthCheckResult],
                                critical: bool = False) -> None:
    """注册自定义健康检查"""
    startup_health_checker.register_health_check(
        check_id, name, category, check_func, critical=critical
    )
