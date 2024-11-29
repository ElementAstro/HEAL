import sys
from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QRect
from PySide6.QtGui import QDrag, QMimeData, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSizePolicy, QScrollArea, QMessageBox
)


@dataclass
class DraggableButtonConfig:
    text: str
    color: str = "lightgray"


class DraggableButton(QPushButton):
    def __init__(self, config: DraggableButtonConfig, parent: Optional[QWidget] = None):
        super().__init__(config.text, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            f"border: 1px solid gray; border-radius: 5px; background-color: {
                config.color};"
        )
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)

            # 创建拖拽的图像
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            # 设置热点位置
            drag.setHotSpot(event.position().toPoint() - self.rect().topLeft())
            drag.exec(Qt.MoveAction)


class FlowLayout(QVBoxLayout):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setSpacing(10)
        self.setContentsMargins(10, 10, 10, 10)
        self.addStretch()
        self.buttons: List[DraggableButton] = []

    def add_button(self, button: DraggableButton):
        row_layout = self._get_current_row()
        row_layout.addWidget(button)
        self.buttons.append(button)
        self.update_layout()

    def remove_button(self, button: DraggableButton):
        for row_index in range(self.count()):
            row_layout = self.itemAt(row_index).layout()
            if row_layout and row_layout.indexOf(button) != -1:
                row_layout.removeWidget(button)
                self.buttons.remove(button)
                button.setParent(None)
                self.update_layout()
                return

    def insert_button(self, index: int, button: DraggableButton):
        if index >= len(self.buttons):
            self.add_button(button)
            return

        row_index, widget_index = divmod(index, 4)  # 假设每行最多4个按钮
        row_layout = self._get_or_create_row(row_index)
        row_layout.insertWidget(widget_index, button)
        self.buttons.insert(index, button)
        self.update_layout()

    def update_layout(self):
        self.update()
        self.parentWidget().update()

    def find_insertion_position(self, position: QPoint) -> int:
        for i, button in enumerate(self.buttons):
            if button.geometry().contains(position):
                return i
        return len(self.buttons)

    def _get_current_row(self) -> QHBoxLayout:
        if self.count() <= 1:
            new_row = QHBoxLayout()
            new_row.setSpacing(10)
            self.insertLayout(self.count() - 1, new_row)
            return new_row
        return self.itemAt(self.count() - 2).layout()

    def _get_or_create_row(self, row_index: int) -> QHBoxLayout:
        while self.count() - 1 <= row_index:
            new_row = QHBoxLayout()
            new_row.setSpacing(10)
            self.insertLayout(self.count() - 1, new_row)
        return self.itemAt(row_index).layout()


class DropArea(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_button = event.source()
        target_position = event.position().toPoint()
        parent_layout: FlowLayout = self.layout()

        if not parent_layout:
            return

        insertion_index = parent_layout.find_insertion_position(
            self.mapToGlobal(target_position)
        )
        parent_layout.remove_button(source_button)
        parent_layout.insert_button(insertion_index, source_button)
        self.animate_button(source_button, source_button.geometry())

    def animate_button(self, button: DraggableButton, target_geometry: QRect):
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(300)
        animation.setStartValue(button.geometry())
        animation.setEndValue(target_geometry)
        animation.start()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Draggable Flow Layout 示例")
        self.resize(600, 800)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        container = DropArea(self)
        scroll_area.setWidget(container)

        flow_layout = FlowLayout()
        container.setLayout(flow_layout)
        self.flow_layout = flow_layout

        # 初始化按钮
        initial_buttons = [
            DraggableButton(DraggableButtonConfig(
                text=f"按钮 {i}", color="lightblue"))
            for i in range(1, 9)
        ]
        for button in initial_buttons:
            self.flow_layout.add_button(button)

        # 添加控制按钮
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        add_button = QPushButton("添加按钮")
        add_button.clicked.connect(self.add_new_button)
        remove_button = QPushButton("移除按钮")
        remove_button.clicked.connect(self.remove_last_button)
        control_layout.addWidget(add_button)
        control_layout.addWidget(remove_button)
        self.flow_layout.add_widget(control_widget)

    def add_new_button(self):
        new_index = len(self.flow_layout.buttons) + 1
        new_button = DraggableButton(
            DraggableButtonConfig(text=f"按钮 {new_index}", color="lightgreen")
        )
        self.flow_layout.add_button(new_button)
        QMessageBox.information(self, "添加按钮", f"已添加按钮 {new_index}")

    def remove_last_button(self):
        if not self.flow_layout.buttons:
            QMessageBox.warning(self, "移除按钮", "没有按钮可移除")
            return
        button = self.flow_layout.buttons[-1]
        self.flow_layout.remove_button(button)
        QMessageBox.information(self, "移除按钮", f"已移除 {button.text()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
