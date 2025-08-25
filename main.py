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

# 设置工作目录
source_file = getsourcefile(lambda: 0)
if source_file:
    os.chdir(Path(source_file).resolve().parent)

# 初始化系统
setup_logging()
logger = get_logger('main')
exception_handler = ExceptionHandler()

# 验证配置文件
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
    # 可以选择继续运行或退出
    # sys.exit(1)
else:
    logger.info(t('app.configs_validated'))

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
locale = cfg.get(cfg.language).value
setup_i18n(locale.name().lower())

translator = FluentTranslator(locale)
localTranslator = QTranslator()
localTranslator.load(f"src\\heal\\resources\\translations\\{locale.name()}.qm")

app.installTranslator(translator)
app.installTranslator(localTranslator)

logger.info(t('app.translators_installed', locale=locale.name()))


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
    
    exit_code = app.exec()
    if exit_code == 1000:
        logger.info(t('app.restart_requested'))
        os.execv(sys.executable, ['python'] + sys.argv)
    
    logger.info(t('app.exiting', code=exit_code))
    sys.exit(exit_code)
    
except Exception as e:
    logger.critical(t('app.startup_error', error=str(e)))
    exception_handler.handle_known_exception(
        exception=e,
        exc_type='startup_error',
        severity='critical',
        user_message='启动失败'
    )
    sys.exit(1)
