import sys
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QTreeWidgetItem,
    QInputDialog, QToolBar, QSplitter, QStatusBar, QHBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from qfluentwidgets import TextEdit, MessageBox, Action, FluentIcon, InfoBar, InfoBarPosition, TreeWidget, PrimaryPushButton


class JsonTextEdit(TextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabStopDistance(20)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            cursor = self.textCursor()
            cursor.insertText('\n' + ' ' * (len(cursor.block().text()) - len(cursor.block().text().lstrip())))
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key_BraceLeft:
            cursor = self.textCursor()
            cursor.insertText('{}')
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key_BracketLeft:
            cursor = self.textCursor()
            cursor.insertText('[]')
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key_QuoteDbl:
            cursor = self.textCursor()
            cursor.insertText('""')
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)


class JsonEditor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JSON Editor")
        self.setGeometry(100, 100, 1500, 1000)

        # Status Bar
        self.status_bar = QStatusBar()

        # Text editor for raw JSON input
        self.text_edit = JsonTextEdit(self)
        self.text_edit.setPlaceholderText("Enter or load JSON data...")
        self.text_edit.textChanged.connect(self.auto_parse_render)

        # Tree widget for parsed JSON display
        self.tree_widget = TreeWidget(self)
        self.tree_widget.setHeaderLabels(["Key", "Value"])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setColumnWidth(1, 700)
        self.tree_widget.itemDoubleClicked.connect(self.edit_item)

        # ToolBar
        toolbar = QToolBar("Main Toolbar")

        open_action = Action(FluentIcon.FOLDER_ADD, "Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        save_action = Action(FluentIcon.SAVE, "Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

        clear_action = Action(FluentIcon.DELETE, "Clear", self)
        clear_action.triggered.connect(self.clear_text)
        toolbar.addAction(clear_action)

        batch_process_action = Action(FluentIcon.CODE, "Batch Process", self)
        batch_process_action.triggered.connect(self.batch_process)
        toolbar.addAction(batch_process_action)

        add_action = Action(FluentIcon.ADD, "Add Node", self)
        add_action.triggered.connect(self.add_node)
        toolbar.addAction(add_action)

        delete_action = Action(FluentIcon.REMOVE, "Delete Node", self)
        delete_action.triggered.connect(self.delete_node)
        toolbar.addAction(delete_action)

        search_action = Action(FluentIcon.SEARCH, "Search", self)
        search_action.triggered.connect(self.search_node)
        toolbar.addAction(search_action)

        cut_action = Action(FluentIcon.CUT, "Cut", self)
        cut_action.triggered.connect(self.cut_node)
        toolbar.addAction(cut_action)

        copy_action = Action(FluentIcon.COPY, "Copy", self)
        copy_action.triggered.connect(self.copy_node)
        toolbar.addAction(copy_action)

        paste_action = Action(FluentIcon.PASTE, "Paste", self)
        paste_action.triggered.connect(self.paste_node)
        toolbar.addAction(paste_action)

        undo_action = Action(FluentIcon.ROTATE, "Undo", self)
        undo_action.triggered.connect(self.text_edit.undo)
        toolbar.addAction(undo_action)

        redo_action = Action(FluentIcon.SYNC, "Redo", self)
        redo_action.triggered.connect(self.text_edit.redo)
        toolbar.addAction(redo_action)

        import_action = Action(FluentIcon.FOLDER, "Import", self)
        import_action.triggered.connect(self.import_json)
        toolbar.addAction(import_action)

        export_action = Action(FluentIcon.DOWNLOAD, "Export", self)
        export_action.triggered.connect(self.export_json)
        toolbar.addAction(export_action)

        # Splitter for layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.tree_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)
        self.clipboard = None

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    data = json.load(file)
                    self.text_edit.setPlainText(json.dumps(data, indent=4))
                    self.auto_parse_render()
                    self.status_bar.showMessage("File opened successfully", 5000)
            except Exception as e:
                MessageBox.critical(self, "Error", f"Could not open file: {e}")

    def save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            try:
                data = self.tree_to_dict(self.tree_widget.invisibleRootItem())
                with open(file_name, 'w') as file:
                    json.dump(data, file, indent=4)
                    self.status_bar.showMessage("File saved successfully", 5000)
            except Exception as e:
                MessageBox.critical(self, "Error", f"Could not save file: {e}")

    def clear_text(self):
        self.text_edit.clear()
        self.tree_widget.clear()

    def auto_parse_render(self):
        try:
            text = self.text_edit.toPlainText()
            if text.strip():
                parsed_data = json.loads(text)
                self.tree_widget.clear()
                self.populate_tree(parsed_data, parent=self.tree_widget)
            else:
                self.tree_widget.clear()
        except json.JSONDecodeError:
            pass  # JSON is invalid, do nothing

    def batch_process(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Open JSON Files", "", "JSON Files (*.json);;All Files (*)")
        if file_names:
            for file_name in file_names:
                try:
                    with open(file_name, 'r') as file:
                        data = json.load(file)
                        self.text_edit.setPlainText(json.dumps(data, indent=4))
                        self.auto_parse_render()
                except Exception as e:
                    MessageBox.critical(self, "Error", f"Could not process file '{file_name}': {e}")

    def populate_tree(self, data, parent=None):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent, [str(key)])
                self.populate_tree(value, parent=item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem(parent, [str(index)])
                self.populate_tree(value, parent=item)
        else:
            parent.setText(1, str(data))

    def add_node(self):
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            key, ok = QInputDialog.getText(self, "Add Node", "Enter key:")
            if ok:
                value, ok = QInputDialog.getText(self, "Add Node", "Enter value:")
                if ok:
                    new_item = QTreeWidgetItem([key, value])
                    selected_item.addChild(new_item)
                    selected_item.setExpanded(True)
                    InfoBar.success(
                        title='Node Added',
                        content=f'Added node with key: {key}',
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000,
                        parent=self
                    )

    def delete_node(self):
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            parent = selected_item.parent()
            if parent:
                parent.removeChild(selected_item)
            else:
                self.tree_widget.takeTopLevelItem(self.tree_widget.indexOfTopLevelItem(selected_item))

    def search_node(self):
        search_key, ok = QInputDialog.getText(self, "Search", "Enter key or value to search:")
        if ok:
            self.search_tree(self.tree_widget.invisibleRootItem(), search_key)

    def search_tree(self, parent, search_key):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if search_key in child.text(0) or search_key in child.text(1):
                self.tree_widget.setCurrentItem(child)
                child.setSelected(True)
                self.tree_widget.scrollToItem(child)
                return
            self.search_tree(child, search_key)

    def edit_item(self, item, column):
        if column == 0:
            new_key, ok = QInputDialog.getText(self, "Edit Key", "Enter new key:", text=item.text(0))
            if ok:
                item.setText(0, new_key)
        elif column == 1:
            new_value, ok = QInputDialog.getText(self, "Edit Value", "Enter new value:", text=item.text(1))
            if ok:
                item.setText(1, new_value)

    def tree_to_dict(self, parent):
        data = {}
        for i in range(parent.childCount()):
            child = parent.child(i)
            key = child.text(0)
            if child.childCount() > 0:
                value = self.tree_to_dict(child)
            else:
                value = child.text(1)
            data[key] = value
        return data

    def cut_node(self):
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            self.copy_node()
            self.delete_node()

    def copy_node(self):
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            self.clipboard = selected_item.clone()

    def paste_node(self):
        selected_item = self.tree_widget.currentItem()
        if selected_item and self.clipboard:
            new_item = self.clipboard.clone()
            selected_item.addChild(new_item)
            selected_item.setExpanded(True)

    def import_json(self):
        json_string, ok = QInputDialog.getMultiLineText(self, "Import JSON", "Paste your JSON string here:")
        if ok:
            try:
                data = json.loads(json_string)
                self.text_edit.setPlainText(json.dumps(data, indent=4))
                self.auto_parse_render()
            except json.JSONDecodeError:
                MessageBox.critical(self, "Error", "Invalid JSON string")

    def export_json(self):
        try:
            data = self.tree_to_dict(self.tree_widget.invisibleRootItem())
            json_string = json.dumps(data, indent=4)
            export_dialog = QInputDialog(self)
            export_dialog.setWindowTitle("Export JSON")
            export_dialog.setLabelText("Here is your JSON string:")
            export_dialog.setOption(QInputDialog.UsePlainTextEditForTextInput)
            export_dialog.setTextValue(json_string)
            export_dialog.exec()
        except Exception as e:
            MessageBox.critical(self, "Error", f"Could not export JSON: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


# Main execution
if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = JsonEditor()
    editor.show()
    sys.exit(app.exec())

