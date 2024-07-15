import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt, QPropertyAnimation, QMimeData, QRect, QPoint
from PySide6.QtGui import QDrag, QPixmap


class DraggableButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "border: 1px solid gray; border-radius: 5px; background-color: lightgray;")
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)

            # Create a pixmap for the drag operation
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            # Adjust the hotspot position using global position
            drag.setHotSpot(event.position().toPoint() - self.rect().topLeft())
            drag.exec(Qt.MoveAction)


class FlowLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(10)
        self.setContentsMargins(10, 10, 10, 10)
        self.addStretch()
        self.buttons = []

    def addButton(self, button):
        current_row = None
        if self.count() == 1:  # If only the stretch is present
            current_row = QHBoxLayout()
            current_row.setSpacing(10)
            self.insertLayout(self.count() - 1, current_row)
        else:
            current_row = self.itemAt(self.count() - 2).layout()

        current_row.addWidget(button)
        self.buttons.append(button)
        self.updateLayout()

    def removeButton(self, button):
        for i in range(self.count()):
            row_layout = self.itemAt(i).layout()
            if row_layout and row_layout.indexOf(button) != -1:
                row_layout.removeWidget(button)
                self.buttons.remove(button)
                button.setParent(None)
                self.updateLayout()
                return

    def insertButton(self, index, button):
        if index >= len(self.buttons):
            self.addButton(button)
            return

        current_row = None
        count = 0
        for i in range(self.count() - 1):  # Exclude the stretch item
            row_layout = self.itemAt(i).layout()
            if row_layout:
                for j in range(row_layout.count()):
                    if count == index:
                        current_row = row_layout
                        break
                    count += 1
                if current_row:
                    break

        if current_row:
            current_row.insertWidget(index - count, button)
        else:
            new_row = QHBoxLayout()
            new_row.setSpacing(10)
            new_row.addWidget(button)
            self.insertLayout(self.count() - 1, new_row)

        self.buttons.insert(index, button)
        self.updateLayout()

    def updateLayout(self):
        self.update()
        self.parentWidget().update()

    def findInsertionPosition(self, position):
        for i in range(self.count() - 1):  # Exclude the stretch item
            row_layout = self.itemAt(i).layout()
            if row_layout:
                row_rect = QRect(self.parentWidget().mapToGlobal(row_layout.geometry().topLeft()),
                                 row_layout.geometry().size())
                if row_rect.contains(position):
                    for j in range(row_layout.count()):
                        widget = row_layout.itemAt(j).widget()
                        if widget:
                            widget_rect = QRect(widget.mapToGlobal(
                                QPoint(0, 0)), widget.size())
                            if widget_rect.contains(position):
                                return i * row_layout.count() + j
                    return i * row_layout.count() + row_layout.count()
        return len(self.buttons)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        container = DropArea(self)
        scroll_area.setWidget(container)

        self.flow_layout = FlowLayout()
        container.setLayout(self.flow_layout)

        for i in range(1, 5):
            button = DraggableButton(f"Button {i}")
            self.flow_layout.addButton(button)

        self.setWindowTitle("Draggable Flow Layout Example")
        self.resize(400, 600)


class DropArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_button = event.source()
        target_position = event.position().toPoint()
        parent_layout = self.layout()

        if not parent_layout:
            return

        insertion_index = parent_layout.findInsertionPosition(
            self.mapToGlobal(target_position))
        parent_layout.removeButton(source_button)
        parent_layout.insertButton(insertion_index, source_button)
        self.animateButton(source_button, source_button.geometry())

    def animateButton(self, button, target_geometry):
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(300)
        animation.setStartValue(button.geometry())
        animation.setEndValue(target_geometry)
        animation.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
