import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QLocale, QTranslator
from qfluentwidgets import FluentTranslator
from app.main_interface import Main
from app.model.config import cfg

# 配置 DPI 缩放
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

# 启动应用程序
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

locale = cfg.get(cfg.language).value
translator = FluentTranslator(locale)
localTranslator = QTranslator()
localTranslator.load(f"src\\translate\\{locale.name()}.qm")

app.installTranslator(translator)
app.installTranslator(localTranslator)


def restart_app():
    QApplication.exit(1000)  # 使用特定的退出代码以便重新启动


def shutdown_app():
    QApplication.quit()


window = Main()
window.reload_signal.connect(restart_app)
window.shutdown_signal.connect(shutdown_app)
window.show()

# 检查退出代码
exit_code = app.exec()
if exit_code == 1000:
    os.execv(sys.executable, ['python'] + sys.argv)  # 重新启动应用程序

sys.exit(exit_code)
