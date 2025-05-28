import os
import sys
from inspect import getsourcefile
from pathlib import Path

from app.common.application import SingletonApplication
from app.common.logging_config import setup_logging, get_logger
from app.common.i18n import setup_i18n, set_language, t
from app.common.enhanced_exception_handler import EnhancedExceptionHandler

# 设置工作目录
source_file = getsourcefile(lambda: 0)
if source_file:
    os.chdir(Path(source_file).resolve().parent)

# 初始化系统
setup_logging()
logger = get_logger('main')
exception_handler = EnhancedExceptionHandler()

# 安装全局异常处理器
sys.excepthook = exception_handler.handle_uncaught_exception

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTranslator
from qfluentwidgets import FluentTranslator
from app.main_interface import Main
from app.model.config import cfg

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
localTranslator.load(f"src\\translate\\{locale.name()}.qm")

app.installTranslator(translator)
app.installTranslator(localTranslator)

logger.info(t('app.translators_installed', locale=locale.name()))


def restart_app():
    """重启应用程序"""
    logger.info(t('app.restarting'))
    QApplication.exit(1000)


def shutdown_app():
    """关闭应用程序"""
    logger.info(t('app.shutting_down'))
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
    exception_handler.handle_exception(e, 'startup_error')
    sys.exit(1)
