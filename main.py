import os
import sys
from inspect import getsourcefile
from pathlib import Path
from typing import Any

from src.heal.common.application import SingletonApplication
from src.heal.common.logging_config import setup_logging, get_logger
from src.heal.common.i18n import setup_i18n, set_language, t
from src.heal.common.exception_handler import ExceptionHandler
from src.heal.common.resource_manager import resource_manager, cleanup_on_exit
from src.heal.common.startup_performance_monitor import (
    start_startup_monitoring, record_startup_phase, finish_startup_monitoring,
    get_startup_performance_summary
)
from src.heal.common.lazy_resource_loader import (
    start_background_loading
)
from src.heal.common.resource_preloader import (
    preload_critical_resources
)
from src.heal.common.startup_error_handler import (
    detect_startup_error, run_startup_system_checks, get_startup_error_report
)
from src.heal.common.startup_health_checker import (
    run_startup_health_checks, get_startup_health_report
)

# 开始启动性能监控
start_startup_monitoring()

# 设置工作目录
source_file = getsourcefile(lambda: 0)
if source_file:
    os.chdir(Path(source_file).resolve().parent)

# 初始化系统
record_startup_phase("logging_setup", start=True)
setup_logging()
logger = get_logger('main')
exception_handler = ExceptionHandler()
record_startup_phase("logging_setup", start=False)

# 运行启动前系统检查
record_startup_phase("system_checks", start=True)
try:
    system_errors = run_startup_system_checks()
    if system_errors:
        critical_errors = [e for e in system_errors if e.severity.value >= 3]  # HIGH or CRITICAL
        if critical_errors:
            logger.critical(f"发现 {len(critical_errors)} 个严重系统问题，可能影响启动")
            for error in critical_errors:
                logger.critical(f"- {error.message}")
        else:
            logger.warning(f"发现 {len(system_errors)} 个系统问题，但不影响启动")
    else:
        logger.info("系统检查通过")
    record_startup_phase("system_checks", start=False)
except Exception as e:
    logger.error(f"系统检查失败: {e}")
    record_startup_phase("system_checks", start=False, success=False, error=str(e))

# 运行健康检查
record_startup_phase("health_checks", start=True)
try:
    health_results = run_startup_health_checks(critical_only=True)
    critical_health_issues = [
        result for result in health_results.values()
        if result.status.value == "critical"
    ]

    if critical_health_issues:
        logger.critical(f"发现 {len(critical_health_issues)} 个关键健康问题")
        for issue in critical_health_issues:
            logger.critical(f"- {issue.name}: {issue.message}")
            if issue.recommendations:
                logger.info(f"  建议: {'; '.join(issue.recommendations)}")
    else:
        logger.info("关键健康检查通过")

    record_startup_phase("health_checks", start=False)
except Exception as e:
    logger.error(f"健康检查失败: {e}")
    record_startup_phase("health_checks", start=False, success=False, error=str(e))

# 验证配置文件
record_startup_phase("config_validation", start=True)
from src.heal.common.config_validator import validate_all_configs
logger.info(t('app.validating_configs'))
validation_results = validate_all_configs(auto_fix=True)

# 检查验证结果
config_errors: list[Any] = []
for filename, result in validation_results.items():
    if result.has_errors:
        config_errors.extend([f"{filename}: {error}" for error in result.errors])
    if result.warnings:
        for warning in result.warnings:
            logger.warning(f"配置警告 {filename}: {warning}")

if config_errors:
    logger.error("配置文件验证失败:")
    for error in config_errors:
        logger.error(f"  {error}")
    record_startup_phase("config_validation", start=False, success=False,
                        error=f"配置验证失败: {len(config_errors)} 个错误")
    # 可以选择继续运行或退出
    # sys.exit(1)
else:
    logger.info(t('app.configs_validated'))
    record_startup_phase("config_validation", start=False)

# 安装全局异常处理器 - 统一在这里设置，避免冲突
sys.excepthook = exception_handler.handle_exception

# 连接应用级别的异常信号处理
from src.heal.common.signal_bus import signalBus
from src.heal.common.application import application_exception_hook

# 连接异常信号到应用级别的处理函数
exception_handler.exception_occurred.connect(
    lambda exc_info: signalBus.appErrorSig.emit(str(exc_info.exception))
)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTranslator
from qfluentwidgets import FluentTranslator
from src.heal.interfaces.main_interface import Main
from src.heal.models.config import cfg

logger.info(t('app.starting'))

if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

app = SingletonApplication(sys.argv, "HEAL-Application")
app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

# 设置语言
record_startup_phase("i18n_setup", start=True)
locale = cfg.get(cfg.language).value
setup_i18n(locale.name().lower())

translator = FluentTranslator(locale)
localTranslator = QTranslator()
localTranslator.load(f"src\\heal\\resources\\translations\\{locale.name()}.qm")

app.installTranslator(translator)
app.installTranslator(localTranslator)

logger.info(t('app.translators_installed', locale=locale.name()))
record_startup_phase("i18n_setup", start=False)

# 预加载关键资源
record_startup_phase("resource_preload", start=True)
try:
    preload_results = preload_critical_resources()
    logger.info(f"预加载了 {sum(1 for r in preload_results.values() if r)} 个关键资源")
    record_startup_phase("resource_preload", start=False)
except Exception as e:
    logger.warning(f"关键资源预加载失败: {e}")
    record_startup_phase("resource_preload", start=False, success=False, error=str(e))


def restart_app() -> None:
    """重启应用程序"""
    logger.info(t('app.restarting'))
    QApplication.exit(1000)


def shutdown_app() -> None:
    """关闭应用程序"""
    logger.info(t('app.shutting_down'))

    # 清理所有资源
    try:
        cleanup_on_exit()
        logger.info(t('app.resources_cleaned'))
    except Exception as e:
        logger.error(t('app.cleanup_error', error=str(e)))

    QApplication.quit()


# 创建主窗口并设置信号连接
try:
    window = Main()
    window.reload_signal.connect(restart_app)
    window.shutdown_signal.connect(shutdown_app)
    window.show()

    logger.info(t('app.main_window_created'))

    # 完成启动监控
    startup_metrics = finish_startup_monitoring()
    performance_summary = get_startup_performance_summary()

    logger.info(f"启动完成 - 总耗时: {startup_metrics.total_startup_time:.2f}s, "
               f"内存使用: {startup_metrics.memory_usage_end:.1f}MB")

    if startup_metrics.bottleneck_phases:
        logger.warning(f"发现性能瓶颈: {', '.join(startup_metrics.bottleneck_phases)}")

    # 启动后台资源加载
    try:
        start_background_loading()
        logger.info("已启动后台资源加载")
    except Exception as e:
        logger.warning(f"启动后台资源加载失败: {e}")

    exit_code = app.exec()
    if exit_code == 1000:
        logger.info(t('app.restart_requested'))
        os.execv(sys.executable, ['python'] + sys.argv)

    logger.info(t('app.exiting', code=exit_code))
    sys.exit(exit_code)

except Exception as e:
    logger.critical(t('app.startup_error', error=str(e)))

    # Record startup failure and detect error
    try:
        record_startup_phase("startup_error", start=False, success=False, error=str(e))

        # Detect and analyze the startup error
        startup_error = detect_startup_error(e, "main_startup")
        if startup_error:
            logger.error(f"Startup error analysis: {startup_error.category.value} - {startup_error.severity.name}")
            if startup_error.recovery_suggestions:
                logger.info("Recovery suggestions:")
                for suggestion in startup_error.recovery_suggestions:
                    logger.info(f"  - {suggestion}")

        # Generate error report
        error_report = get_startup_error_report()
        logger.error(f"Total startup errors detected: {error_report['total_errors']}")

        finish_startup_monitoring()
    except:
        pass  # Don't let monitoring errors prevent error handling

    exception_handler.handle_known_exception(
        exception=e,
        exc_type='startup_error',
        severity='critical',
        user_message='启动失败'
    )
    sys.exit(1)
