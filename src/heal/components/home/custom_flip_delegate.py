from PySide6.QtCore import QModelIndex, QRect, Qt
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import QStyleOptionViewItem
from qfluentwidgets import FlipImageDelegate

from ...models.config import cfg


class CustomFlipItemDelegate(FlipImageDelegate):
    """Custom delegate for flip view items with application name and version overlay."""

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        # Draw using parent's implementation first
        super().paint(painter, option, index)
        self.setBorderRadius(35)

        painter.save()

        # Create rect without accessing device properties
        viewport = painter.viewport()
        item_rect = QRect(0, 0, viewport.width(), viewport.height())

        painter.setPen(Qt.GlobalColor.white)

        # 绘制应用程序名称
        painter.setFont(QFont(cfg.APP_FONT, 35))
        # QRect.adjusted() 方法返回一个新的 QRect，因此 item_rect 本身不会被修改。
        painter.drawText(
            item_rect.adjusted(
                0, -20, 0, 0), Qt.AlignmentFlag.AlignCenter, cfg.APP_NAME
        )

        # 绘制应用程序版本
        painter.setFont(QFont(cfg.APP_FONT, 20))
        painter.drawText(
            item_rect.adjusted(0, 90, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            cfg.APP_VERSION,
        )

        painter.restore()
