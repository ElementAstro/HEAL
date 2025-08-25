import sys
import os
import json
from functools import partial
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QFrame, QVBoxLayout, QListWidgetItem,
    QStackedWidget, QHBoxLayout, QLabel, QDialog,
    QGridLayout, QTreeWidget, QTreeWidgetItem, QWidget, QMessageBox,
    QProgressBar, QCheckBox, QSplitter, QTextEdit
)
from qfluentwidgets import (
    LineEdit, PushButton, FluentIcon, SubtitleLabel, TitleLabel, ImageLabel,
    Action, CommandBarView, ListWidget, setTheme, Theme, isDarkTheme,
    InfoBar, InfoBarPosition, ProgressBar as FluentProgressBar, ScrollArea
)

# Import our new systems
from .module_workflow_manager import ModuleWorkflowManager, WorkflowStep
from .module_error_handler import ModuleErrorHandler, ErrorCategory, ErrorSeverity
from .module_notification_system import ModuleNotificationSystem, NotificationType
from .module_bulk_operations import ModuleBulkOperations, BulkOperationType


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


class ModManager(ScrollArea):
    def __init__(self):
        super().__init__()
        self.mods: Dict[str, ModInfo] = {}
        self.filtered_mods: Dict[str, ModInfo] = {}
        self.selected_modules: Set[str] = set()
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []

        # Initialize new systems
        self.error_handler = ModuleErrorHandler()
        self.notification_system = ModuleNotificationSystem(self)
        self.workflow_manager = ModuleWorkflowManager()
        self.bulk_operations = ModuleBulkOperations(self.error_handler, self.notification_system)

        # Setup connections
        self._setup_system_connections()

        self.initUI()

    def _setup_system_connections(self):
        """Setup connections between systems"""
        # Connect workflow manager signals
        self.workflow_manager.workflow_completed.connect(self._on_workflow_completed)
        self.workflow_manager.workflow_step_failed.connect(self._on_workflow_step_failed)

        # Connect bulk operations signals
        self.bulk_operations.operation_completed.connect(self._on_bulk_operation_completed)
        self.bulk_operations.operation_progress.connect(self._on_bulk_operation_progress)

        # Register bulk operation handlers
        self.bulk_operations.register_operation_handler(BulkOperationType.ENABLE, self._handle_bulk_enable)
        self.bulk_operations.register_operation_handler(BulkOperationType.DISABLE, self._handle_bulk_disable)
        self.bulk_operations.register_operation_handler(BulkOperationType.DELETE, self._handle_bulk_delete)
        self.bulk_operations.register_operation_handler(BulkOperationType.VALIDATE, self._handle_bulk_validate)

    def initUI(self):
        self.setWindowTitle('模组管理器')
        self.setGeometry(100, 100, 1200, 800)

        # 设置ScrollArea属性
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.enableTransparentBackground()

        # 创建主容器widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        self.setWidgetResizable(True)

        main_layout = QVBoxLayout(main_widget)

        # Enhanced toolbar with bulk operations
        toolbar = CommandBarView()

        # Individual operations
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

        # Bulk operations
        bulk_enable_action = Action(FluentIcon.ACCEPT, "批量启用", self)
        bulk_enable_action.triggered.connect(self.bulk_enable_selected)
        toolbar.addAction(bulk_enable_action)

        bulk_disable_action = Action(FluentIcon.CLOSE, "批量禁用", self)
        bulk_disable_action.triggered.connect(self.bulk_disable_selected)
        toolbar.addAction(bulk_disable_action)

        bulk_validate_action = Action(FluentIcon.CERTIFICATE, "批量验证", self)
        bulk_validate_action.triggered.connect(self.bulk_validate_selected)
        toolbar.addAction(bulk_validate_action)

        bulk_delete_action = Action(FluentIcon.DELETE, "批量删除", self)
        bulk_delete_action.triggered.connect(self.bulk_delete_selected)
        toolbar.addAction(bulk_delete_action)

        toolbar.addSeparator()

        # Selection controls
        select_all_action = Action(FluentIcon.CHECKBOX, "全选", self)
        select_all_action.triggered.connect(self.select_all_modules)
        toolbar.addAction(select_all_action)

        clear_selection_action = Action(FluentIcon.CANCEL, "清除选择", self)
        clear_selection_action.triggered.connect(self.clear_selection)
        toolbar.addAction(clear_selection_action)

        toolbar.addSeparator()

        # Undo/Redo
        self.undo_action = Action(FluentIcon.RETURN, "撤销", self)
        self.undo_action.triggered.connect(self.undo_last_action)
        self.undo_action.setEnabled(False)
        toolbar.addAction(self.undo_action)

        self.redo_action = Action(FluentIcon.SHARE, "重做", self)
        self.redo_action.triggered.connect(self.redo_last_action)
        self.redo_action.setEnabled(False)
        toolbar.addAction(self.redo_action)

        toolbar.addSeparator()

        self.search_box = LineEdit()
        self.search_box.setPlaceholderText("搜索模组...")
        self.search_box.textChanged.connect(self.filter_mods)
        toolbar.addWidget(self.search_box)

        main_layout.addWidget(toolbar)

        # Selection info bar
        self.selection_info = QLabel("未选择模组")
        self.selection_info.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        main_layout.addWidget(self.selection_info)

        # Main content area with splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - module list
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)

        self.list_widget = ListWidget()
        self.list_widget.itemDoubleClicked.connect(self.show_mod_details)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        left_layout.addWidget(self.list_widget)

        content_splitter.addWidget(left_panel)

        # Right panel - details and operations
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        # Module details
        self.stacked_widget = QStackedWidget()

        # Default page
        self.mod_list_page = QFrame()
        mod_list_layout = QVBoxLayout()

        default_label = QLabel("选择模组查看详情")
        default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_label.setStyleSheet("color: #999; font-size: 16px;")
        mod_list_layout.addWidget(default_label)

        self.mod_list_page.setLayout(mod_list_layout)
        self.stacked_widget.addWidget(self.mod_list_page)

        right_layout.addWidget(self.stacked_widget)

        # Progress area for bulk operations
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_frame)

        self.progress_label = QLabel("操作进行中...")
        self.progress_bar = FluentProgressBar()
        self.progress_details = QTextEdit()
        self.progress_details.setMaximumHeight(100)
        self.progress_details.setReadOnly(True)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_details)

        right_layout.addWidget(self.progress_frame)

        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)

        main_layout.addWidget(content_splitter)

        # 设置布局边距和间距
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

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

            # Selection checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(info.name in self.selected_modules)
            checkbox.toggled.connect(partial(self._on_module_selection_changed, info.name))
            item_layout.addWidget(checkbox, 0, 0, 2, 1)

            if info.thumbnail:
                thumbnail_label = ImageLabel()
                thumbnail_label.setPixmap(QIcon(info.thumbnail).pixmap(64, 64))
                item_layout.addWidget(thumbnail_label, 0, 1, 2, 1)
            else:
                placeholder = QLabel("No Image")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setFixedSize(64, 64)
                placeholder.setStyleSheet(
                    "background-color: #ccc; border: 1px solid #999;")
                item_layout.addWidget(placeholder, 0, 1, 2, 1)

            name_label = TitleLabel(info.name)
            name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            item_layout.addWidget(name_label, 0, 2)

            version_author_label = SubtitleLabel(
                f"Version: {info.version} | Author: {info.author}")
            item_layout.addWidget(version_author_label, 1, 2)

            # Enhanced status labels with loading states
            status_layout = QHBoxLayout()
            status_label = SubtitleLabel("启用" if info.enabled else "禁用")
            status_label.setStyleSheet(
                f"color: {'green' if info.enabled else 'red'};")
            status_layout.addWidget(status_label)

            usable_label = SubtitleLabel("可用" if info.usable else "不可用")
            usable_label.setStyleSheet(
                f"color: {'green' if info.usable else 'orange'};")
            status_layout.addWidget(usable_label)

            # Add workflow status if applicable
            workflow_status = self._get_module_workflow_status(info.name)
            if workflow_status:
                workflow_label = SubtitleLabel(workflow_status)
                workflow_label.setStyleSheet("color: #0078d4; font-style: italic;")
                status_layout.addWidget(workflow_label)

            item_layout.addLayout(status_layout, 0, 3, 2, 1)

            # Enhanced operation buttons
            operations_layout = QHBoxLayout()

            # Workflow button
            workflow_button = PushButton(FluentIcon.PLAY, "")
            workflow_button.setToolTip("启动工作流")
            workflow_button.clicked.connect(partial(self.start_module_workflow, info.name))
            operations_layout.addWidget(workflow_button)

            open_folder_button = PushButton(FluentIcon.FOLDER, "")
            open_folder_button.setToolTip("打开文件夹")
            open_folder_button.clicked.connect(
                partial(self.open_folder, info.path))
            operations_layout.addWidget(open_folder_button)

            copy_button = PushButton(FluentIcon.COPY, "")
            copy_button.setToolTip("复制详情")
            copy_button.clicked.connect(partial(self.copy_mod_details, info))
            operations_layout.addWidget(copy_button)

            item_layout.addLayout(operations_layout, 0, 4, 2, 1)

            item_widget.setLayout(item_layout)
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, info.name)  # Store module name
            self.list_widget.setItemWidget(item, item_widget)

        # Update selection info
        self._update_selection_info()

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
                self.error_handler.handle_error(
                    exception=e,
                    category=ErrorCategory.FILESYSTEM,
                    context={"module_path": mod_path, "operation": "load_details"}
                )
                self.notification_system.show_error(
                    "加载失败", f"加载模组详情时发生错误: {e}"
                )
        return {}

    # New methods for enhanced functionality
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click for selection"""
        module_name = item.data(Qt.ItemDataRole.UserRole)
        if module_name:
            # Toggle selection with Ctrl+Click
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                self._toggle_module_selection(module_name)
            else:
                # Single selection
                self.selected_modules.clear()
                self.selected_modules.add(module_name)
                self._update_selection_info()
                self._update_checkboxes()

    def _on_module_selection_changed(self, module_name: str, checked: bool):
        """Handle checkbox selection change"""
        if checked:
            self.selected_modules.add(module_name)
        else:
            self.selected_modules.discard(module_name)

        self._update_selection_info()
        self.bulk_operations.set_selected_modules(list(self.selected_modules))

    def _toggle_module_selection(self, module_name: str):
        """Toggle module selection"""
        if module_name in self.selected_modules:
            self.selected_modules.discard(module_name)
        else:
            self.selected_modules.add(module_name)

        self._update_selection_info()
        self._update_checkboxes()
        self.bulk_operations.set_selected_modules(list(self.selected_modules))

    def _update_selection_info(self):
        """Update selection info display"""
        count = len(self.selected_modules)
        if count == 0:
            self.selection_info.setText("未选择模组")
        elif count == 1:
            module_name = next(iter(self.selected_modules))
            self.selection_info.setText(f"已选择: {module_name}")
        else:
            self.selection_info.setText(f"已选择 {count} 个模组")

    def _update_checkboxes(self):
        """Update checkbox states to match selection"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                module_name = item.data(Qt.ItemDataRole.UserRole)
                if checkbox and module_name:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(module_name in self.selected_modules)
                    checkbox.blockSignals(False)

    def _get_module_workflow_status(self, module_name: str) -> Optional[str]:
        """Get workflow status for module"""
        workflows = self.workflow_manager.get_workflows_for_module(module_name)
        if workflows:
            # Get most recent workflow
            latest_workflow = max(workflows, key=lambda w: w.updated_at)
            if latest_workflow.current_step != WorkflowStep.COMPLETE:
                return f"工作流: {latest_workflow.current_step.value}"
        return None

    def select_all_modules(self):
        """Select all visible modules"""
        self.selected_modules.clear()
        for module_name in self.filtered_mods.keys():
            self.selected_modules.add(module_name)

        self._update_selection_info()
        self._update_checkboxes()
        self.bulk_operations.set_selected_modules(list(self.selected_modules))

        self.notification_system.show_info(
            "全选", f"已选择 {len(self.selected_modules)} 个模组"
        )

    def clear_selection(self):
        """Clear all selections"""
        self.selected_modules.clear()
        self._update_selection_info()
        self._update_checkboxes()
        self.bulk_operations.clear_selection()

        self.notification_system.show_info("清除选择", "已清除所有选择")

    def start_module_workflow(self, module_name: str):
        """Start workflow for a module"""
        try:
            workflow_id = self.workflow_manager.start_workflow(
                module_name=module_name,
                metadata={"initiated_from": "module_manager"}
            )

            self.notification_system.show_info(
                "工作流启动", f"已为模组 '{module_name}' 启动工作流"
            )

            # Execute first step
            self.workflow_manager.execute_next_step(workflow_id)

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.SYSTEM,
                context={"module_name": module_name, "operation": "start_workflow"}
            )


    # Bulk operation methods
    def bulk_enable_selected(self):
        """Enable selected modules in bulk"""
        if not self.selected_modules:
            self.notification_system.show_warning("无选择", "请先选择要启用的模组")
            return

        # Show confirmation dialog
        reply = QMessageBox.question(
            self, "确认批量启用",
            f"确定要启用 {len(self.selected_modules)} 个模组吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._save_state_for_undo("bulk_enable", list(self.selected_modules))
            operation_id = self.bulk_operations.enable_selected_modules()
            self._show_bulk_operation_progress(operation_id)

    def bulk_disable_selected(self):
        """Disable selected modules in bulk"""
        if not self.selected_modules:
            self.notification_system.show_warning("无选择", "请先选择要禁用的模组")
            return

        reply = QMessageBox.question(
            self, "确认批量禁用",
            f"确定要禁用 {len(self.selected_modules)} 个模组吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._save_state_for_undo("bulk_disable", list(self.selected_modules))
            operation_id = self.bulk_operations.disable_selected_modules()
            self._show_bulk_operation_progress(operation_id)

    def bulk_validate_selected(self):
        """Validate selected modules in bulk"""
        if not self.selected_modules:
            self.notification_system.show_warning("无选择", "请先选择要验证的模组")
            return

        operation_id = self.bulk_operations.validate_selected_modules()
        self._show_bulk_operation_progress(operation_id)

    def bulk_delete_selected(self):
        """Delete selected modules in bulk"""
        if not self.selected_modules:
            self.notification_system.show_warning("无选择", "请先选择要删除的模组")
            return

        reply = QMessageBox.warning(
            self, "确认批量删除",
            f"确定要删除 {len(self.selected_modules)} 个模组吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Create backup for potential recovery
            backup_data = {}
            for module_name in self.selected_modules:
                if module_name in self.mods:
                    backup_data[module_name] = {
                        'info': self.mods[module_name],
                        'path': self.mods[module_name].path
                    }

            self._save_state_for_undo("bulk_delete", list(self.selected_modules), backup_data)
            operation_id = self.bulk_operations.delete_selected_modules()
            self._show_bulk_operation_progress(operation_id)

    def _show_bulk_operation_progress(self, operation_id: str):
        """Show progress for bulk operation"""
        operation = self.bulk_operations.get_operation(operation_id)
        if not operation:
            return

        self.progress_frame.setVisible(True)
        self.progress_label.setText(f"执行批量{operation.operation_type.value}...")
        self.progress_bar.setValue(0)
        self.progress_details.clear()

        # Store operation ID for tracking
        self.current_bulk_operation = operation_id

    # Undo/Redo functionality
    def _save_state_for_undo(self, action_type: str, affected_modules: List[str],
                           additional_data: Optional[Dict[str, Any]] = None):
        """Save current state for undo functionality"""
        state = {
            'action_type': action_type,
            'affected_modules': affected_modules,
            'timestamp': time.time(),
            'module_states': {}
        }

        # Save current state of affected modules
        for module_name in affected_modules:
            if module_name in self.mods:
                mod_info = self.mods[module_name]
                state['module_states'][module_name] = {
                    'enabled': mod_info.enabled,
                    'exists': True
                }
            else:
                state['module_states'][module_name] = {'exists': False}

        if additional_data:
            state['additional_data'] = additional_data

        # Add to undo stack
        self.undo_stack.append(state)

        # Clear redo stack
        self.redo_stack.clear()

        # Limit undo stack size
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

        # Update UI
        self.undo_action.setEnabled(True)
        self.redo_action.setEnabled(False)

    def undo_last_action(self):
        """Undo the last action"""
        if not self.undo_stack:
            return

        state = self.undo_stack.pop()

        try:
            # Restore previous state
            for module_name, module_state in state['module_states'].items():
                if module_name in self.mods:
                    mod_info = self.mods[module_name]
                    if 'enabled' in module_state:
                        mod_info.enabled = module_state['enabled']

            # Add to redo stack
            self.redo_stack.append(state)

            # Refresh UI
            self.load_mods()

            self.notification_system.show_success(
                "撤销成功", f"已撤销{state['action_type']}操作"
            )

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.SYSTEM,
                context={"operation": "undo", "action_type": state['action_type']}
            )

        # Update UI
        self.undo_action.setEnabled(len(self.undo_stack) > 0)
        self.redo_action.setEnabled(True)

    def redo_last_action(self):
        """Redo the last undone action"""
        if not self.redo_stack:
            return

        state = self.redo_stack.pop()

        try:
            # Re-execute the action
            if state['action_type'] == 'bulk_enable':
                for module_name in state['affected_modules']:
                    if module_name in self.mods:
                        self.mods[module_name].enabled = True
            elif state['action_type'] == 'bulk_disable':
                for module_name in state['affected_modules']:
                    if module_name in self.mods:
                        self.mods[module_name].enabled = False

            # Add back to undo stack
            self.undo_stack.append(state)

            # Refresh UI
            self.load_mods()

            self.notification_system.show_success(
                "重做成功", f"已重做{state['action_type']}操作"
            )

        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.SYSTEM,
                context={"operation": "redo", "action_type": state['action_type']}
            )

        # Update UI
        self.undo_action.setEnabled(True)
        self.redo_action.setEnabled(len(self.redo_stack) > 0)

    # Bulk operation handlers
    def _handle_bulk_enable(self, module_name: str, operation_type: BulkOperationType,
                          parameters: Dict[str, Any]) -> bool:
        """Handle bulk enable operation for a single module"""
        try:
            if module_name in self.mods:
                mod_info = self.mods[module_name]
                if not mod_info.enabled:
                    disabled_file = os.path.join(mod_info.path, '.disabled')
                    if os.path.isfile(disabled_file):
                        os.remove(disabled_file)
                    mod_info.enabled = True
                return True
        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.FILESYSTEM,
                context={"module_name": module_name, "operation": "bulk_enable"}
            )
        return False

    def _handle_bulk_disable(self, module_name: str, operation_type: BulkOperationType,
                           parameters: Dict[str, Any]) -> bool:
        """Handle bulk disable operation for a single module"""
        try:
            if module_name in self.mods:
                mod_info = self.mods[module_name]
                if mod_info.enabled:
                    disabled_file = os.path.join(mod_info.path, '.disabled')
                    with open(disabled_file, 'w') as f:
                        f.write('disabled')
                    mod_info.enabled = False
                return True
        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.FILESYSTEM,
                context={"module_name": module_name, "operation": "bulk_disable"}
            )
        return False

    def _handle_bulk_delete(self, module_name: str, operation_type: BulkOperationType,
                          parameters: Dict[str, Any]) -> bool:
        """Handle bulk delete operation for a single module"""
        try:
            if module_name in self.mods:
                return self.delete_mod(module_name)
        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.FILESYSTEM,
                context={"module_name": module_name, "operation": "bulk_delete"}
            )
        return False

    def _handle_bulk_validate(self, module_name: str, operation_type: BulkOperationType,
                            parameters: Dict[str, Any]) -> bool:
        """Handle bulk validate operation for a single module"""
        try:
            if module_name in self.mods:
                mod_info = self.mods[module_name]
                # Simulate validation - in real implementation, use actual validator
                return os.path.exists(mod_info.path) and mod_info.usable
        except Exception as e:
            self.error_handler.handle_error(
                exception=e,
                category=ErrorCategory.VALIDATION,
                context={"module_name": module_name, "operation": "bulk_validate"}
            )
        return False

    # Event handlers for system connections
    def _on_workflow_completed(self, workflow_id: str):
        """Handle workflow completion"""
        workflow = self.workflow_manager.get_workflow(workflow_id)
        if workflow:
            self.notification_system.show_success(
                "工作流完成", f"模组 '{workflow.module_name}' 的工作流已完成"
            )
            self.load_mods()  # Refresh to show updated status

    def _on_workflow_step_failed(self, workflow_id: str, step: str, error: str):
        """Handle workflow step failure"""
        workflow = self.workflow_manager.get_workflow(workflow_id)
        if workflow:
            self.notification_system.show_error(
                "工作流失败", f"模组 '{workflow.module_name}' 的{step}步骤失败: {error}"
            )

    def _on_bulk_operation_completed(self, operation_id: str, success: bool):
        """Handle bulk operation completion"""
        self.progress_frame.setVisible(False)
        self.load_mods()  # Refresh module list

        if hasattr(self, 'current_bulk_operation'):
            delattr(self, 'current_bulk_operation')

    def _on_bulk_operation_progress(self, operation_id: str, progress_data: Dict[str, Any]):
        """Handle bulk operation progress updates"""
        if hasattr(self, 'current_bulk_operation') and operation_id == self.current_bulk_operation:
            self.progress_bar.setValue(int(progress_data['progress']))

            current_module = progress_data.get('current_module', '')
            completed = progress_data.get('completed', 0)
            total = progress_data.get('total', 0)

            self.progress_label.setText(
                f"处理中: {current_module} ({completed}/{total})"
            )

            # Add to details
            if current_module:
                self.progress_details.append(f"正在处理: {current_module}")


if __name__ == '__main__':
    import subprocess
    import time
    app = QApplication(sys.argv)
    mod_manager = ModManager()
    mod_manager.show()
    sys.exit(app.exec())
