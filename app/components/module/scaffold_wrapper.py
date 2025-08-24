"""
ScaffoldApp Wrapper
Wrapper component for ScaffoldApp to make it compatible with QFrame
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout
from app.components.tools.scaffold import ScaffoldApp


class ScaffoldAppWrapper(QFrame):
    """ScaffoldApp包装器，使其兼容QFrame"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scaffold_app = ScaffoldApp()
        layout.addWidget(self.scaffold_app)

    def get_scaffold_app(self):
        """获取内部的ScaffoldApp实例"""
        return self.scaffold_app
