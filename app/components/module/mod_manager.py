import sys
import os
import json
from functools import partial
from typing import Dict, Any, Optional
from dataclasses import dataclass
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QFrame, QVBoxLayout, QListWidgetItem,
    QStackedWidget, QHBoxLayout, QLabel, QDialog,
    QGridLayout, QTreeWidget, QTreeWidgetItem, QWidget, QMessageBox
)
from qfluentwidgets import (
    LineEdit, PushButton, FluentIcon, SubtitleLabel, TitleLabel, ImageLabel,
    Action, CommandBarView, ListWidget, setTheme, Theme, isDarkTheme
)


@dataclass
class ModInfo:
    name: str
    author: str
    version: str
    enabled: bool
    path: str
    thumbnail: Optional[str] = None
    usable: bool = False


class JsonTreeWidget(QTreeWidget):
    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.setHeaderLabels(["Key", "Value"])
        self.setColumnWidth(0, 200)
        self.populate_tree(data)

    def populate_tree(self, data: Any, parent: Optional[QTreeWidgetItem] = None):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent or self, [str(key)])
                self.populate_tree(value, item)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem(parent or self, [f"[{i}]"])
                self.populate_tree(value, item)
        else:
            QTreeWidgetItem(parent or self, ["", str(data)])


class ModDetailPage(QFrame):
    def __init__(self, mod_info: ModInfo, parent_manager: 'ModManager'):
        super().__init__()
        self.mod_info = mod_info
        self.parent_manager = parent_manager  # 重命名避免与QWidget.parent()冲突
        self.current_page = 0
        self.pages_per_view = 20
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title_label = TitleLabel(f"详情 - {self.mod_info.name}")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # JSON Tree View
        self.tree_widget = JsonTreeWidget(
            self.parent_manager.load_mod_details(self.mod_info.path))
        main_layout.addWidget(self.tree_widget)

        # 分页导航按钮
        nav_layout = QHBoxLayout()
        self.prev_button = PushButton("上一页")
        self.next_button = PushButton("下一页")
        self.page_label = QLabel()

        for button in (self.prev_button, self.next_button):
            button.setFont(QFont("Arial", 12))

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_button)
        main_layout.addLayout(nav_layout)

        # 操作按钮
        operations_layout = QHBoxLayout()
        self.copy_button = PushButton(FluentIcon.COPY, "复制详情")
        self.copy_button.clicked.connect(self.copy_details)
        operations_layout.addWidget(self.copy_button)
        main_layout.addLayout(operations_layout)

        # 返回按钮
        back_button = PushButton("返回模组列表")
        back_button.setFont(QFont("Arial", 14))
        back_button.clicked.connect(self.go_back)
        main_layout.addWidget(back_button)

        self.setLayout(main_layout)
        self.update_page()

    def update_page(self):
        start = self.current_page * self.pages_per_view
        end = start + self.pages_per_view

        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item:  # 检查item不为None
                item.setHidden(i < start or i >= end)

        total_pages = (self.tree_widget.topLevelItemCount() -
                       1) // self.pages_per_view + 1
        self.page_label.setText(
            f"第 {self.current_page + 1} 页 / 共 {total_pages} 页")

        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_page(self):
        total_pages = (self.tree_widget.topLevelItemCount() -
                       1) // self.pages_per_view + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_page()

    def copy_details(self):
        details = self.parent_manager.load_mod_details(self.mod_info.path)
        details_str = json.dumps(details, indent=4, ensure_ascii=False)
        QApplication.clipboard().setText(details_str)
        QMessageBox.information(self, "已复制", "模组详情已复制到剪贴板。")

    def go_back(self):
        self.parent_manager.stacked_widget.setCurrentIndex(0)


class AddModDialog(QDialog):
    def __init__(self, parent_manager: 'ModManager'):
        super().__init__(parent_manager)
        self.setWindowTitle('添加模组')
        self.parent_manager = parent_manager  # 重命名避免冲突

        self.mod_name_label = SubtitleLabel('模组名称:')
        self.mod_name_edit = LineEdit()
        self.mod_name_edit.setPlaceholderText('请输入模组名称')

        self.author_label = SubtitleLabel('作者:')
        self.author_edit = LineEdit()
        self.author_edit.setPlaceholderText('请输入作者名称')

        self.version_label = SubtitleLabel('版本:')
        self.version_edit = LineEdit()
        self.version_edit.setPlaceholderText('例如 1.0.0')

        self.add_button = PushButton('添加')
        self.add_button.clicked.connect(self.add_mod)

        layout = QVBoxLayout()
        layout.addWidget(self.mod_name_label)
        layout.addWidget(self.mod_name_edit)
        layout.addWidget(self.author_label)
        layout.addWidget(self.author_edit)
        layout.addWidget(self.version_label)
        layout.addWidget(self.version_edit)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_mod(self):
        mod_name = self.mod_name_edit.text().strip()
        author = self.author_edit.text().strip()
        version = self.version_edit.text().strip()

        if not mod_name:
            QMessageBox.warning(self, '输入错误', '模组名称不能为空。')
            return
        if not author:
            QMessageBox.warning(self, '输入错误', '作者名称不能为空。')
            return
        if not version:
            QMessageBox.warning(self, '输入错误', '版本不能为空。')
            return

        if mod_name in self.parent_manager.mods:
            QMessageBox.warning(self, '警告', '模组已存在。')
            return

        mod_info = ModInfo(
            name=mod_name,
            author=author,
            version=version,
            enabled=True,
            path=os.path.join(os.getcwd(), 'modules', mod_name),
            thumbnail=None,
            usable=self.parent_manager.check_mod_usability(
                os.path.join(os.getcwd(), 'modules', mod_name))
        )

        try:
            os.makedirs(mod_info.path, exist_ok=True)
            package_file = os.path.join(mod_info.path, 'package.json')
            with open(package_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "name": mod_info.name,
                    "author": mod_info.author,
                    "version": mod_info.version,
                    "Enabled": mod_info.enabled
                }, f, ensure_ascii=False, indent=4)
            self.parent_manager.load_mods()
            QMessageBox.information(self, '成功', f"模组 '{mod_name}' 已成功添加。")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f"添加模组时发生错误: {e}")


class ModManager(QFrame):
    def __init__(self):
        super().__init__()
        self.mods: Dict[str, ModInfo] = {}
        self.filtered_mods: Dict[str, ModInfo] = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle('模组管理器')
        self.setGeometry(100, 100, 1000, 700)

        main_layout = QVBoxLayout()

        # 工具栏
        toolbar = CommandBarView()

        add_action = Action(FluentIcon.ADD_TO, "添加模组", self)
        add_action.triggered.connect(self.add_mod)
        toolbar.addAction(add_action)

        delete_action = Action(FluentIcon.DELETE, "删除模组", self)
        delete_action.triggered.connect(self.confirm_delete_mod)
        toolbar.addAction(delete_action)

        enable_action = Action(FluentIcon.ACCEPT, "启用模组", self)
        enable_action.triggered.connect(self.enable_mod)
        toolbar.addAction(enable_action)

        disable_action = Action(FluentIcon.CLOSE, "禁用模组", self)
        disable_action.triggered.connect(self.disable_mod)
        toolbar.addAction(disable_action)

        refresh_action = Action(FluentIcon.SYNC, "刷新", self)
        refresh_action.triggered.connect(self.load_mods)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        self.search_box = LineEdit()
        self.search_box.setPlaceholderText("搜索模组...")
        self.search_box.textChanged.connect(self.filter_mods)
        toolbar.addWidget(self.search_box)

        main_layout.addWidget(toolbar)

        # 主要内容区
        self.stacked_widget = QStackedWidget()

        # 模组列表页面
        self.mod_list_page = QFrame()
        mod_list_layout = QVBoxLayout()

        self.list_widget = ListWidget()
        self.list_widget.itemDoubleClicked.connect(self.show_mod_details)
        mod_list_layout.addWidget(self.list_widget)

        self.mod_list_page.setLayout(mod_list_layout)
        self.stacked_widget.addWidget(self.mod_list_page)

        main_layout.addWidget(self.stacked_widget)

        self.setLayout(main_layout)

        # 加载模组
        self.load_mods()

        # 设置主题
        setTheme(Theme.DARK if isDarkTheme() else Theme.LIGHT)

    def load_mods(self):
        self.mods.clear()
        modules_path = os.path.join(os.getcwd(), 'modules')
        if not os.path.exists(modules_path):
            os.makedirs(modules_path, exist_ok=True)

        for mod_dir in os.listdir(modules_path):
            mod_path = os.path.join(modules_path, mod_dir)
            if os.path.isdir(mod_path):
                package_file = os.path.join(mod_path, 'package.json')
                if os.path.isfile(package_file):
                    try:
                        with open(package_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            mod_name = data.get('name', mod_dir)
                            author = data.get('author', 'Unknown')
                            version = data.get('version', 'N/A')
                            enabled = data.get('Enabled', False)
                            thumbnail = os.path.join(mod_path, 'thumbnail.png') if os.path.isfile(
                                os.path.join(mod_path, 'thumbnail.png')) else None
                            usable = self.check_mod_usability(mod_path)

                            mod_info = ModInfo(
                                name=mod_name,
                                author=author,
                                version=version,
                                enabled=enabled,
                                path=mod_path,
                                thumbnail=thumbnail,
                                usable=usable
                            )
                            self.mods[mod_name] = mod_info
                    except Exception as e:
                        QMessageBox.critical(self, '错误', f"加载模组 '{mod_dir}' 时发生错误: {e}")

        self.filtered_mods = self.mods.copy()
        self.update_mod_list()

    def check_mod_usability(self, mod_path: str) -> bool:
        # 这里可以添加更多的检查逻辑
        return os.path.isfile(os.path.join(mod_path, 'main.py'))

    def update_mod_list(self):
        self.list_widget.clear()
        for info in self.filtered_mods.values():
            item_widget = QWidget()
            item_layout = QGridLayout()
            item_layout.setContentsMargins(5, 5, 5, 5)
            item_layout.setSpacing(10)

            if info.thumbnail:
                thumbnail_label = ImageLabel()
                thumbnail_label.setPixmap(QIcon(info.thumbnail).pixmap(64, 64))
                item_layout.addWidget(thumbnail_label, 0, 0, 2, 1)
            else:
                placeholder = QLabel("No Image")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setFixedSize(64, 64)
                placeholder.setStyleSheet(
                    "background-color: #ccc; border: 1px solid #999;")
                item_layout.addWidget(placeholder, 0, 0, 2, 1)

            name_label = TitleLabel(info.name)
            name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            item_layout.addWidget(name_label, 0, 1)

            version_author_label = SubtitleLabel(
                f"Version: {info.version} | Author: {info.author}")
            item_layout.addWidget(version_author_label, 1, 1)

            # 状态标签
            status_layout = QHBoxLayout()
            status_label = SubtitleLabel("启用" if info.enabled else "禁用")
            status_label.setStyleSheet(
                f"color: {'green' if info.enabled else 'red'};")
            status_layout.addWidget(status_label)

            usable_label = SubtitleLabel("可用" if info.usable else "不可用")
            usable_label.setStyleSheet(
                f"color: {'green' if info.usable else 'orange'};")
            status_layout.addWidget(usable_label)

            item_layout.addLayout(status_layout, 0, 2, 2, 1)

            # 操作按钮
            operations_layout = QHBoxLayout()
            open_folder_button = PushButton(FluentIcon.FOLDER, "")
            open_folder_button.setToolTip("打开文件夹")
            open_folder_button.clicked.connect(
                partial(self.open_folder, info.path))
            operations_layout.addWidget(open_folder_button)

            copy_button = PushButton(FluentIcon.COPY, "")
            copy_button.setToolTip("复制详情")
            copy_button.clicked.connect(partial(self.copy_mod_details, info))
            operations_layout.addWidget(copy_button)

            item_layout.addLayout(operations_layout, 0, 3, 2, 1)

            item_widget.setLayout(item_layout)
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(item, item_widget)

    def filter_mods(self):
        search_text = self.search_box.text().lower()
        if search_text:
            self.filtered_mods = {name: info for name, info in self.mods.items()
                                  if search_text in name.lower() or search_text in info.author.lower()}
        else:
            self.filtered_mods = self.mods.copy()
        self.update_mod_list()

    def show_mod_details(self, item: QListWidgetItem):
        widget = self.list_widget.itemWidget(item)
        if widget:
            name_label = widget.findChild(TitleLabel)
            if name_label:
                mod_name = name_label.text()
                if mod_name in self.mods:
                    mod_info = self.mods[mod_name]
                    detail_page = ModDetailPage(mod_info, self)
                    self.stacked_widget.addWidget(detail_page)
                    self.stacked_widget.setCurrentWidget(detail_page)

    def add_mod(self):
        dialog = AddModDialog(self)
        dialog.exec()

    def confirm_delete_mod(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            mod_names = [self.get_mod_name_from_item(
                item) for item in selected_items]
            # Filter out None values before joining
            valid_mod_names = [name for name in mod_names if name is not None]
            reply = QMessageBox.warning(
                self, '确认删除',
                f"确定要删除以下模组吗？\n{', '.join(valid_mod_names)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                for mod_name in mod_names:
                    if mod_name:  # 确保mod_name不为None
                        self.delete_mod(mod_name)
        else:
            QMessageBox.warning(self, '警告', '未选中任何模组。')

    def get_mod_name_from_item(self, item: QListWidgetItem) -> Optional[str]:
        widget = self.list_widget.itemWidget(item)
        if widget:
            name_label = widget.findChild(TitleLabel)
            if name_label:
                return name_label.text()
        return None

    def delete_mod(self, mod_name: str):
        if mod_name in self.mods:
            mod_path = self.mods[mod_name].path
            try:
                for root, dirs, files in os.walk(mod_path, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(mod_path)
                QMessageBox.information(self, '成功', f"模组 '{mod_name}' 已删除。")
            except Exception as e:
                QMessageBox.critical(self, '错误', f"删除模组 '{mod_name}' 时发生错误: {e}")
            self.load_mods()

    def enable_mod(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '未选中任何模组。')
            return
        for item in selected_items:
            mod_name = self.get_mod_name_from_item(item)
            if mod_name and mod_name in self.mods and not self.mods[mod_name].enabled:
                mod_info = self.mods[mod_name]
                disabled_file = os.path.join(mod_info.path, '.disabled')
                if os.path.isfile(disabled_file):
                    os.remove(disabled_file)
                mod_info.enabled = True
        self.load_mods()
        QMessageBox.information(self, '成功', '选中的模组已启用。')

    def disable_mod(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '未选中任何模组。')
            return
        for item in selected_items:
            mod_name = self.get_mod_name_from_item(item)
            if mod_name and mod_name in self.mods and self.mods[mod_name].enabled:
                mod_info = self.mods[mod_name]
                disabled_file = os.path.join(mod_info.path, '.disabled')
                with open(disabled_file, 'w') as f:
                    f.write('disabled')
                mod_info.enabled = False
        self.load_mods()
        QMessageBox.information(self, '成功', '选中的模组已禁用。')

    def open_folder(self, path: str):
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            QMessageBox.critical(self, '错误', f"打开文件夹时发生错误: {e}")

    def copy_mod_details(self, mod_info: ModInfo):
        details = {
            "Name": mod_info.name,
            "Author": mod_info.author,
            "Version": mod_info.version,
            "Enabled": mod_info.enabled,
            "Path": mod_info.path,
            "Usable": mod_info.usable
        }
        details_str = json.dumps(details, indent=4, ensure_ascii=False)
        QApplication.clipboard().setText(details_str)
        QMessageBox.information(
            self, '已复制', f"模组 '{mod_info.name}' 的详情已复制到剪贴板。")

    def load_mod_details(self, mod_path: str) -> Dict[str, Any]:
        package_file = os.path.join(mod_path, 'package.json')
        if os.path.isfile(package_file):
            try:
                with open(package_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                QMessageBox.critical(self, '错误', f"加载模组详情时发生错误: {e}")
        return {}


if __name__ == '__main__':
    import subprocess
    app = QApplication(sys.argv)
    mod_manager = ModManager()
    mod_manager.show()
    sys.exit(app.exec())
