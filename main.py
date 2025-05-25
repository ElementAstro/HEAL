import os
import sys
from inspect import getsourcefile
from pathlib import Path

from app.common.application import SingletonApplication

source_file = getsourcefile(lambda: 0)
if source_file:
    os.chdir(Path(source_file).resolve().parent)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTranslator
from qfluentwidgets import FluentTranslator
from app.main_interface import Main
from app.model.config import cfg

if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

app = SingletonApplication(sys.argv, "HEAL-Application")
app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

locale = cfg.get(cfg.language).value
translator = FluentTranslator(locale)
localTranslator = QTranslator()
localTranslator.load(f"src\\translate\\{locale.name()}.qm")

app.installTranslator(translator)
app.installTranslator(localTranslator)


def restart_app():
    QApplication.exit(1000)


def shutdown_app():
    QApplication.quit()


window = Main()
window.reload_signal.connect(restart_app)
window.shutdown_signal.connect(shutdown_app)
window.show()

exit_code = app.exec()
if exit_code == 1000:
    os.execv(sys.executable, ['python'] + sys.argv)

sys.exit(exit_code)
