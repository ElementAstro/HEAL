import json
import sys
from typing import Any, Dict, Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QKeyEvent, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QSplitter,
    QStatusBar,
    QToolBar,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    Action,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBox,
    TextEdit,
    TreeWidget,
)

from src.heal.common.logging_config import (
    get_logger,
    log_exception,
    log_performance,
    with_correlation_id,
)

# 使用统一日志配置
logger = get_logger(__name__)


class JsonTextEdit(TextEdit):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTabStopDistance(20)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
        ):
            cursor = self.textCursor()
            indent = len(cursor.block().text()) - len(cursor.block().text().lstrip())
            cursor.insertText("\n" + " " * indent)
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key.Key_BraceLeft:
            cursor = self.textCursor()
            cursor.insertText("{}")
            cursor.movePosition(
                QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1
            )
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key.Key_BracketLeft:
            cursor = self.textCursor()
            cursor.insertText("[]")
            cursor.movePosition(
                QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1
            )
            self.setTextCursor(cursor)
        elif event.key() == Qt.Key.Key_QuoteDbl:
            cursor = self.textCursor()
            cursor.insertText('""')
            cursor.movePosition(
                QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1
            )
            self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)


class JsonEditor(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("JSON Editor")
        self.setGeometry(100, 100, 1600, 900)

        # 状态栏
        self.status_bar = QStatusBar()

        # 原始JSON输入的文本编辑器
        self.text_edit = JsonTextEdit(self)
        self.text_edit.setPlaceholderText("输入或加载JSON数据...")
        self.text_edit.textChanged.connect(self.auto_parse_render)

        # 解析后的JSON显示的树形控件
        self.tree_widget = TreeWidget(self)
        self.tree_widget.setHeaderLabels(["键", "值"])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setColumnWidth(1, 700)
        self.tree_widget.itemDoubleClicked.connect(self.edit_item)

        # 工具栏
        toolbar = QToolBar("主工具栏")

        open_action = Action(FluentIcon.FOLDER_ADD, "打开", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        save_action = Action(FluentIcon.SAVE, "保存", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

        copy_action = Action(FluentIcon.COPY, "复制到剪贴板", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        toolbar.addAction(copy_action)

        clear_action = Action(FluentIcon.DELETE, "清空", self)
        clear_action.triggered.connect(self.clear_text)
        toolbar.addAction(clear_action)

        batch_process_action = Action(FluentIcon.CODE, "批量处理", self)
        batch_process_action.triggered.connect(self.batch_process)
        toolbar.addAction(batch_process_action)

        add_action = Action(FluentIcon.ADD, "添加节点", self)
        add_action.triggered.connect(self.add_node)
        toolbar.addAction(add_action)

        delete_action = Action(FluentIcon.REMOVE, "删除节点", self)
        delete_action.triggered.connect(self.delete_node)
        toolbar.addAction(delete_action)

        search_action = Action(FluentIcon.SEARCH, "搜索", self)
        search_action.triggered.connect(self.search_node)
        toolbar.addAction(search_action)

        cut_action = Action(FluentIcon.CUT, "剪切", self)
        cut_action.triggered.connect(self.cut_node)
        toolbar.addAction(cut_action)

        copy_node_action = Action(FluentIcon.COPY, "复制", self)
        copy_node_action.triggered.connect(self.copy_node)
        toolbar.addAction(copy_node_action)

        paste_action = Action(FluentIcon.PASTE, "粘贴", self)
        paste_action.triggered.connect(self.paste_node)
        toolbar.addAction(paste_action)

        undo_action = Action(FluentIcon.ROTATE, "撤销", self)
        undo_action.triggered.connect(self.text_edit.undo)
        toolbar.addAction(undo_action)

        redo_action = Action(FluentIcon.SYNC, "重做", self)
        redo_action.triggered.connect(self.text_edit.redo)
        toolbar.addAction(redo_action)

        import_action = Action(FluentIcon.FOLDER, "导入", self)
        import_action.triggered.connect(self.import_json)
        toolbar.addAction(import_action)

        export_action = Action(FluentIcon.DOWNLOAD, "导出", self)
        export_action.triggered.connect(self.export_json)
        toolbar.addAction(export_action)

        format_action = Action(FluentIcon.FONT, "格式化JSON", self)
        format_action.triggered.connect(self.format_json)
        toolbar.addAction(format_action)

        # 搜索栏
        search_bar = LineEdit()
        search_bar.setPlaceholderText("搜索键或值...")
        search_bar.returnPressed.connect(self.search_node)
        toolbar.addWidget(search_bar)

        # 分割器布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.tree_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)
        self.clipboard: Optional[QTreeWidgetItem] = None

    @log_performance("open_json_file")
    def open_file(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self, "打开JSON文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_name:
            logger.info(f"打开JSON文件: {file_name}")
            try:
                with open(file_name, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.text_edit.setPlainText(
                        json.dumps(data, indent=4, ensure_ascii=False)
                    )
                    self.auto_parse_render()
                    self.status_bar.showMessage("文件打开成功", 5000)
                    logger.info(f"JSON文件打开成功: {file_name}")
            except Exception as e:
                logger.error(f"打开JSON文件失败: {file_name}, 错误: {e}")
                log_exception(e, f"打开JSON文件失败: {file_name}")
                MessageBox.critical(self, "错误", f"无法打开文件: {e}")

    def save_file(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存JSON文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_name:
            try:
                data = self.tree_to_dict(self.tree_widget.invisibleRootItem())
                with open(file_name, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
                    self.status_bar.showMessage("文件保存成功", 5000)
            except Exception as e:
                MessageBox.critical(self, "错误", f"无法保存文件: {e}")

    def clear_text(self) -> None:
        self.text_edit.clear()
        self.tree_widget.clear()
        self.status_bar.showMessage("内容已清空", 3000)

    def auto_parse_render(self) -> None:
        try:
            text = self.text_edit.toPlainText()
            if text.strip():
                parsed_data = json.loads(text)
                self.tree_widget.clear()
                self.populate_tree(
                    parsed_data, parent=self.tree_widget.invisibleRootItem()
                )
                self.status_bar.showMessage("JSON已解析", 2000)
            else:
                self.tree_widget.clear()
        except json.JSONDecodeError:
            self.status_bar.showMessage("JSON格式无效", 2000)

    def batch_process(self) -> None:
        file_names, _ = QFileDialog.getOpenFileNames(
            self, "打开JSON文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_names:
            for file_name in file_names:
                try:
                    with open(file_name, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        formatted = json.dumps(data, indent=4, ensure_ascii=False)
                        self.text_edit.append(formatted)
                        self.auto_parse_render()
                        self.status_bar.showMessage(f"处理文件: {file_name}", 3000)
                except Exception as e:
                    MessageBox.critical(
                        self, "错误", f"无法处理文件 '{file_name}': {e}"
                    )

    def populate_tree(
        self, data: Any, parent: Optional[QTreeWidgetItem] = None
    ) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent, [str(key)])
                self.populate_tree(value, parent=item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem(parent, [str(index)])
                self.populate_tree(value, parent=item)
        else:
            if parent:
                parent.setText(1, str(data))

    def add_node(self) -> None:
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            key, ok = QInputDialog.getText(self, "添加节点", "输入键:")
            if ok and key:
                value, ok = QInputDialog.getText(self, "添加节点", "输入值:")
                if ok:
                    new_item = QTreeWidgetItem([key, value])
                    selected_item.addChild(new_item)
                    selected_item.setExpanded(True)
                    InfoBar.success(
                        title="节点已添加",
                        content=f"已添加键: {key}",
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000,
                        parent=self,
                    )

    def delete_node(self) -> None:
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            parent = selected_item.parent()
            if parent:
                parent.removeChild(selected_item)
            else:
                self.tree_widget.takeTopLevelItem(
                    self.tree_widget.indexOfTopLevelItem(selected_item)
                )
            self.status_bar.showMessage("节点已删除", 2000)

    def search_node(self) -> None:
        search_key, ok = QInputDialog.getText(self, "搜索", "输入键或值进行搜索:")
        if ok and search_key:
            self.search_tree(self.tree_widget.invisibleRootItem(), search_key)

    def search_tree(self, parent: QTreeWidgetItem, search_key: str) -> bool:
        found = False
        for i in range(parent.childCount()):
            child = parent.child(i)
            if (
                search_key.lower() in child.text(0).lower()
                or search_key.lower() in child.text(1).lower()
            ):
                self.tree_widget.setCurrentItem(child)
                child.setSelected(True)
                self.tree_widget.scrollToItem(child)
                found = True
                break
            if self.search_tree(child, search_key):
                found = True
                break
        return found

    def edit_item(self, item: QTreeWidgetItem, column: int) -> None:
        if column == 0:
            new_key, ok = QInputDialog.getText(
                self, "编辑键", "输入新的键:", text=item.text(0)
            )
            if ok and new_key:
                item.setText(0, new_key)
        elif column == 1:
            new_value, ok = QInputDialog.getText(
                self, "编辑值", "输入新的值:", text=item.text(1)
            )
            if ok:
                item.setText(1, new_value)
        self.status_bar.showMessage("节点已更新", 2000)

    def tree_to_dict(self, parent: QTreeWidgetItem) -> Dict[str, Any]:
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

    def cut_node(self) -> None:
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            self.copy_node()
            self.delete_node()

    def copy_node(self) -> None:
        selected_item = self.tree_widget.currentItem()
        if selected_item:
            self.clipboard = self.clone_item(selected_item)
            self.status_bar.showMessage("节点已复制", 2000)

    def paste_node(self) -> None:
        selected_item = self.tree_widget.currentItem()
        if selected_item and self.clipboard:
            new_item = self.clone_item(self.clipboard)
            selected_item.addChild(new_item)
            selected_item.setExpanded(True)
            self.status_bar.showMessage("节点已粘贴", 2000)

    def clone_item(self, item: QTreeWidgetItem) -> QTreeWidgetItem:
        cloned_item = QTreeWidgetItem([item.text(0), item.text(1)])
        for i in range(item.childCount()):
            cloned_child = self.clone_item(item.child(i))
            cloned_item.addChild(cloned_child)
        return cloned_item

    def import_json(self) -> None:
        json_string, ok = QInputDialog.getMultiLineText(
            self, "导入JSON", "在此处粘贴您的JSON字符串:"
        )
        if ok and json_string:
            try:
                data = json.loads(json_string)
                self.text_edit.setPlainText(
                    json.dumps(data, indent=4, ensure_ascii=False)
                )
                self.auto_parse_render()
                self.status_bar.showMessage("JSON已导入", 2000)
            except json.JSONDecodeError:
                MessageBox.critical(self, "错误", "无效的JSON字符串")

    def export_json(self) -> None:
        try:
            data = self.tree_to_dict(self.tree_widget.invisibleRootItem())
            json_string = json.dumps(data, indent=4, ensure_ascii=False)
            export_dialog = QInputDialog(self)
            export_dialog.setWindowTitle("导出JSON")
            export_dialog.setLabelText("这是您的JSON字符串:")
            export_dialog.setOption(
                QInputDialog.InputDialogOption.UsePlainTextEditForTextInput
            )
            export_dialog.setTextValue(json_string)
            export_dialog.exec()
            self.status_bar.showMessage("JSON已导出", 2000)
        except Exception as e:
            MessageBox.critical(self, "错误", f"无法导出JSON: {e}")

    def format_json(self) -> None:
        try:
            data = json.loads(self.text_edit.toPlainText())
            formatted = json.dumps(data, indent=4, ensure_ascii=False)
            self.text_edit.setPlainText(formatted)
            self.auto_parse_render()
            self.status_bar.showMessage("JSON已格式化", 2000)
        except json.JSONDecodeError:
            MessageBox.critical(self, "错误", "无法格式化，无效的JSON")

    def copy_to_clipboard(self) -> None:
        clipboard: QClipboard = QApplication.clipboard()
        json_string = self.text_edit.toPlainText()
        clipboard.setText(json_string)
        self.status_bar.showMessage("JSON已复制到剪贴板", 2000)


# 主执行
if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = JsonEditor()
    editor.show()
    sys.exit(app.exec())
