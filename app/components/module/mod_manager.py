import sys
import os
import json
from functools import partial
from typing import Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QFrame, QVBoxLayout, QListWidgetItem,
    QStackedWidget, QHBoxLayout, QLabel,
    QInputDialog, QGridLayout, QTreeWidget, QTreeWidgetItem, QWidget
)
from qfluentwidgets import (LineEdit, PushButton, MessageBox, FluentIcon, SubtitleLabel, TitleLabel, ImageLabel,
                            Action, CommandBarView, ListWidget, TransparentPushButton)


class JsonTreeWidget(QTreeWidget):
    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.setHeaderLabels(["Key", "Value"])
        self.setColumnWidth(0, 200)
        self.populate_tree(data)

    def populate_tree(self, data: Any, parent: QTreeWidgetItem | None = None):
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem(parent or self, [str(key)])
                self.populate_tree(value, item)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem(parent or self, [str(i)])
                self.populate_tree(value, item)
        else:
            QTreeWidgetItem(parent or self, ["", str(data)])


class ModDetailPage(QFrame):
    def __init__(self, mod_name: str, mod_info: Dict[str, Any], parent: 'ModManager'):
        super().__init__()
        self.mod_name = mod_name
        self.mod_info = mod_info
        self.parent = parent
        self.current_page = 0
        self.pages_per_view = 20
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title_label = QLabel(f"Details of {self.mod_name}")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # JSON Tree View
        self.tree_widget = JsonTreeWidget(self.mod_info)
        main_layout.addWidget(self.tree_widget)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = PushButton("Previous")
        self.next_button = PushButton("Next")
        self.page_label = QLabel()

        for button in (self.prev_button, self.next_button):
            button.setFont(QFont("Arial", 12))
            button.setStyleSheet("""
                PushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 10px;
                    border: none;
                    border-radius: 3px;
                }
                PushButton:hover {
                    background-color: #45a049;
                }
                PushButton:disabled {
                    background-color: #cccccc;
                }
            """)

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_button)
        main_layout.addLayout(nav_layout)

        # Back button
        back_button = PushButton("Back to Mod List")
        back_button.setFont(QFont("Arial", 14))
        back_button.setStyleSheet("""
            PushButton {
                background-color: #008CBA;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            PushButton:hover {
                background-color: #007B9A;
            }
        """)
        back_button.clicked.connect(self.go_back)
        main_layout.addWidget(back_button)

        self.setLayout(main_layout)

        # Set background color
        self.setStyleSheet("background-color: #f0f0f0;")

        self.update_page()

    def update_page(self):
        start = self.current_page * self.pages_per_view
        end = start + self.pages_per_view

        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            item.setHidden(i < start or i >= end)

        total_pages = (self.tree_widget.topLevelItemCount() -
                       1) // self.pages_per_view + 1
        self.page_label.setText(
            f"Page {self.current_page + 1} of {total_pages}")

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

    def go_back(self):
        self.parent.stacked_widget.setCurrentIndex(0)


class ModManager(QFrame):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Mod Manager')
        # Removed setGeometry since it's not necessary for embedding

        main_layout = QVBoxLayout()

        # Toolbar
        toolbar = CommandBarView()
        # toolbar.setIconSize(QSize(24, 24))

        add_action = Action(FluentIcon.ADD_TO, "Add Mod", self)
        add_action.triggered.connect(self.add_mod)
        toolbar.addAction(add_action)

        delete_action = Action(FluentIcon.DELETE, "Delete Mod", self)
        delete_action.triggered.connect(self.confirm_delete_mod)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        enable_action = Action(FluentIcon.ACCEPT, "Enable Mod", self)
        enable_action.triggered.connect(self.enable_mod)
        toolbar.addAction(enable_action)

        disable_action = Action(FluentIcon.CLOSE, "Disable Mod", self)
        disable_action.triggered.connect(self.disable_mod)
        toolbar.addAction(disable_action)

        toolbar.addSeparator()

        refresh_action = Action(FluentIcon.SYNC, "Refresh", self)
        refresh_action.triggered.connect(self.load_mods)
        toolbar.addAction(refresh_action)

        self.search_box = LineEdit()
        self.search_box.setPlaceholderText("Search mods...")
        self.search_box.textChanged.connect(self.filter_mods)
        toolbar.addWidget(self.search_box)

        main_layout.addWidget(toolbar)

        self.stacked_widget = QStackedWidget()

        self.mod_list_page = QFrame()
        mod_list_layout = QVBoxLayout()
        """self.search_box = LineEdit()
        self.search_box.setPlaceholderText("Search mods...")
        self.search_box.textChanged.connect(self.filter_mods)
        mod_list_layout.addWidget(self.search_box)"""

        self.list_widget = ListWidget()
        self.list_widget.itemDoubleClicked.connect(self.show_mod_details)
        mod_list_layout.addWidget(self.list_widget)

        self.mod_list_page.setLayout(mod_list_layout)

        self.stacked_widget.addWidget(self.mod_list_page)

        main_layout.addWidget(self.stacked_widget)

        self.setLayout(main_layout)

        self.mods = {}
        self.load_mods()

    def load_mods(self):
        self.mods.clear()
        modules_path = os.path.join(os.getcwd(), 'modules')
        for mod_dir in os.listdir(modules_path):
            mod_path = os.path.join(modules_path, mod_dir)
            if os.path.isdir(mod_path):
                package_file = os.path.join(mod_path, 'package.json')
                if os.path.isfile(package_file):
                    with open(package_file, 'r', encoding='utf-8') as f:
                        mod_info = json.load(f)
                        mod_info['Enabled'] = not os.path.isfile(
                            os.path.join(mod_path, '.disabled'))
                        mod_info['Path'] = mod_path
                        mod_info['Thumbnail'] = os.path.join(mod_path, 'thumbnail.png') if os.path.isfile(
                            os.path.join(mod_path, 'thumbnail.png')) else None
                        mod_info['Usable'] = self.check_mod_usability(mod_path)
                        self.mods[mod_info.get('name', mod_dir)] = mod_info

        self.update_mod_list()

    def check_mod_usability(self, mod_path: str) -> bool:
        # 这里可以添加更多的检查逻辑
        return os.path.isfile(os.path.join(mod_path, 'main.py'))

    def update_mod_list(self):
        self.list_widget.clear()
        for mod, info in self.mods.items():
            item_widget = QWidget()
            item_layout = QGridLayout()
            if info["Thumbnail"]:
                thumbnail = ImageLabel()
                thumbnail.setPixmap(QIcon(info["Thumbnail"]).pixmap(32, 32))
                item_layout.addWidget(thumbnail, 0, 0, 2, 1)

            name_label = TitleLabel(mod)
            name_label.setFont(QFont("Arial", 14, QFont.Bold))
            item_layout.addWidget(name_label, 0, 1)

            version_author_label = SubtitleLabel(
                f"Version: {info['version']} | Author: {info['author']}")
            item_layout.addWidget(version_author_label, 1, 1)

            status_frame = QFrame()
            status_layout = QHBoxLayout(status_frame)

            #enabled_badge = SubtitleLabel(
            #    "Enabled" if info['Enabled'] else "Disabled")
            #enabled_badge.setStyleSheet(
            #    f"background-color: {'green' if info['Enabled'] else 'red'}; padding: 2px; border-radius: 3px;")
            #status_layout.addWidget(enabled_badge)

            # usable_badge = QLabel("Usable" if info['Usable'] else "Unusable")
            # usable_badge.setStyleSheet(f"background-color: {'green' if info['Usable'] else 'orange'}; color: white; padding: 2px; border-radius: 3px;")
            # status_layout.addWidget(usable_badge)

            item_layout.addWidget(status_frame, 0, 2, 2, 1, Qt.AlignRight)

            open_folder_button = TransparentPushButton(
                FluentIcon.FOLDER, "")
            open_folder_button.clicked.connect(
                partial(self.open_folder, info['Path']))
            item_layout.addWidget(open_folder_button, 0, 3, 2, 1, Qt.AlignRight)

            item_widget.setLayout(item_layout)
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(item, item_widget)

    def filter_mods(self):
        search_text = self.search_box.text().lower()
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            name_label = widget.findChild(QLabel)
            item.setHidden(search_text not in name_label.text().lower())

    def show_mod_details(self, item: QListWidgetItem):
        widget = self.list_widget.itemWidget(item)
        name_label = widget.findChild(QLabel)
        mod_name = name_label.text()
        if mod_name in self.mods:
            mod_info = self.mods[mod_name]
            detail_page = ModDetailPage(mod_name, mod_info, self)
            self.stacked_widget.addWidget(detail_page)
            self.stacked_widget.setCurrentWidget(detail_page)

    def add_mod(self):
        mod_name, ok = QInputDialog.getText(self, 'Add Mod', 'Enter mod name:')
        if ok and mod_name:
            if mod_name in self.mods:
                MessageBox.warning(self, 'Warning', 'Mod already exists.')
            else:
                mod_info = {"name": mod_name, "author": "Unknown",
                            "version": "N/A", "Enabled": False}
                mod_path = os.path.join(os.getcwd(), 'modules', mod_name)
                os.makedirs(mod_path, exist_ok=True)
                with open(os.path.join(mod_path, 'package.json'), 'w', encoding='utf-8') as f:
                    json.dump(mod_info, f, ensure_ascii=False, indent=4)
                self.load_mods()

    def confirm_delete_mod(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            mod_names = [self.list_widget.itemWidget(item).findChild(
                QLabel).text() for item in selected_items]
            reply = MessageBox.question(self, 'Delete Mod',
                                        f"Are you sure you want to delete the selected mod(s)?\n{
                                            ', '.join(mod_names)}",
                                        MessageBox.Yes | MessageBox.No, MessageBox.No)
            if reply == MessageBox.Yes:
                for mod_name in mod_names:
                    self.delete_mod(mod_name)
        else:
            MessageBox.warning(self, 'Warning', 'No mod selected.')

    def delete_mod(self, mod_name: str):
        if mod_name in self.mods:
            mod_path = self.mods[mod_name]['Path']
            if os.path.isdir(mod_path):
                for root, dirs, files in os.walk(mod_path, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(mod_path)
            self.load_mods()

    def enable_mod(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            widget = self.list_widget.itemWidget(item)
            name_label = widget.findChild(QLabel)
            mod_name = name_label.text()
            if mod_name in self.mods:
                mod_path = self.mods[mod_name]['Path']
                disabled_file = os.path.join(mod_path, '.disabled')
                if os.path.isfile(disabled_file):
                    os.remove(disabled_file)
                self.mods[mod_name]["Enabled"] = True
        self.update_mod_list()

    def disable_mod(self):
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            widget = self.list_widget.itemWidget(item)
            name_label = widget.findChild(QLabel)
            mod_name = name_label.text()
            if mod_name in self.mods:
                mod_path = self.mods[mod_name]['Path']
                disabled_file = os.path.join(mod_path, '.disabled')
                with open(disabled_file, 'w') as f:
                    pass
                self.mods[mod_name]["Enabled"] = False
        self.update_mod_list()

    def open_folder(self, path: str):
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mod_manager = ModManager()
    mod_manager.show()
    sys.exit(app.exec())
