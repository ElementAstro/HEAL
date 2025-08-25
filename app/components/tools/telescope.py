import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QDialog,
    QDialogButtonBox, QMessageBox, QLabel
)
from qfluentwidgets import (
    PushButton, LineEdit, ComboBox, ListWidget, FluentIcon,
    isDarkTheme, setTheme, Theme, MessageBox
)
from PySide6.QtCore import Qt
from app.common.logging_config import get_logger, log_performance, with_correlation_id

# 使用统一日志配置
logger = get_logger(__name__)


@dataclass
class Telescope:
    make: str
    model: str
    aperture: float
    focal_length: float


class AddEditTelescopeDialog(QDialog):
    def __init__(self, parent=None, telescope: Telescope = None):
        super().__init__(parent)
        self.setWindowTitle("添加望远镜" if telescope is None else "编辑望远镜")
        self.telescope = telescope

        layout = QVBoxLayout(self)

        self.make_input = LineEdit()
        self.make_input.setPlaceholderText("制造商")
        layout.addWidget(QLabel("制造商:"))
        layout.addWidget(self.make_input)

        self.model_input = LineEdit()
        self.model_input.setPlaceholderText("型号")
        layout.addWidget(QLabel("型号:"))
        layout.addWidget(self.model_input)

        self.aperture_input = LineEdit()
        self.aperture_input.setPlaceholderText("孔径 (mm)")
        layout.addWidget(QLabel("孔径 (mm):"))
        layout.addWidget(self.aperture_input)

        self.focal_length_input = LineEdit()
        self.focal_length_input.setPlaceholderText("焦距 (mm)")
        layout.addWidget(QLabel("焦距 (mm):"))
        layout.addWidget(self.focal_length_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        if telescope:
            self.make_input.setText(telescope.make)
            self.model_input.setText(telescope.model)
            self.aperture_input.setText(str(telescope.aperture))
            self.focal_length_input.setText(str(telescope.focal_length))

    def get_telescope_data(self) -> Any:
        try:
            make = self.make_input.text().strip()
            model = self.model_input.text().strip()
            aperture = float(self.aperture_input.text().strip())
            focal_length = float(self.focal_length_input.text().strip())
            if not make or not model:
                raise ValueError("制造商和型号不能为空。")
            return Telescope(make, model, aperture, focal_length)
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", str(e))
            return None


class TelescopeCatalog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("望远镜目录")

        logger.info("初始化望远镜目录")

        self.telescopes: List[Telescope] = [
            Telescope(make="Zhumell", model="Z12", aperture=304.8, focal_length=1500.0),
            # 添加更多望远镜数据
        ]
        self.filtered_telescopes = self.telescopes.copy()

        self.layout = QVBoxLayout(self)

        logger.debug(f"加载了 {len(self.telescopes)} 个望远镜")

        # 搜索输入
        search_layout = QHBoxLayout()
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("搜索...")
        self.search_input.textChanged.connect(self.filter_telescopes)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)

        # 排序组合框
        sort_layout = QHBoxLayout()
        self.sort_combobox = ComboBox()
        self.sort_combobox.addItems(["制造商", "型号", "孔径", "焦距"])
        self.sort_combobox.currentIndexChanged.connect(self.sort_telescopes)
        sort_layout.addWidget(QLabel("排序方式:"))
        sort_layout.addWidget(self.sort_combobox)
        self.layout.addLayout(sort_layout)

        # 望远镜列表
        self.telescopes_list = ListWidget()
        self.telescopes_list.setAlternatingRowColors(True)
        self.telescopes_list.itemDoubleClicked.connect(self.edit_telescope)
        self.populate_telescopes()
        self.layout.addWidget(self.telescopes_list)

        # 操作按钮
        buttons_layout = QHBoxLayout()
        self.add_button = PushButton(FluentIcon.ADD, "添加望远镜")
        self.add_button.clicked.connect(self.add_telescope)
        self.edit_button = PushButton(FluentIcon.EDIT, "编辑选中")
        self.edit_button.clicked.connect(self.edit_selected_telescope)
        self.delete_button = PushButton(FluentIcon.DELETE, "删除选中")
        self.delete_button.clicked.connect(self.delete_selected_telescope)
        self.copy_button = PushButton(FluentIcon.COPY, "复制选中详情")
        self.copy_button.clicked.connect(self.copy_selected_telescope)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.copy_button)
        self.layout.addLayout(buttons_layout)

        # 设置主题
        setTheme(Theme.DARK if isDarkTheme() else Theme.LIGHT)

    def populate_telescopes(self):
        self.telescopes_list.clear()
        for telescope in self.filtered_telescopes:
            item_text = f"{telescope.make} - {telescope.model} | 孔径: {telescope.aperture}mm | 焦距: {telescope.focal_length}mm"
            self.telescopes_list.addItem(item_text)

    def filter_telescopes(self):
        search_term = self.search_input.text().lower()
        self.filtered_telescopes = [
            t for t in self.telescopes
            if search_term in t.make.lower() or search_term in t.model.lower()
        ]
        self.populate_telescopes()

    def sort_telescopes(self):
        key = self.sort_combobox.currentText()
        if key == "制造商":
            self.filtered_telescopes.sort(key=lambda x: x.make)
        elif key == "型号":
            self.filtered_telescopes.sort(key=lambda x: x.model)
        elif key == "孔径":
            self.filtered_telescopes.sort(key=lambda x: x.aperture)
        elif key == "焦距":
            self.filtered_telescopes.sort(key=lambda x: x.focal_length)
        self.populate_telescopes()

    def add_telescope(self):
        dialog = AddEditTelescopeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            telescope = dialog.get_telescope_data()
            if telescope:
                self.telescopes.append(telescope)
                self.filter_telescopes()

    def edit_telescope(self, item):
        index = self.telescopes_list.currentRow()
        telescope = self.filtered_telescopes[index]
        dialog = AddEditTelescopeDialog(self, telescope)
        if dialog.exec() == QDialog.Accepted:
            updated_telescope = dialog.get_telescope_data()
            if updated_telescope:
                self.telescopes[self.telescopes.index(telescope)] = updated_telescope
                self.filter_telescopes()

    def edit_selected_telescope(self):
        index = self.telescopes_list.currentRow()
        if index >= 0:
            self.edit_telescope(self.telescopes_list.currentItem())
        else:
            QMessageBox.warning(self, "警告", "请选中一个望远镜进行编辑。")

    def delete_selected_telescope(self):
        index = self.telescopes_list.currentRow()
        if index >= 0:
            telescope = self.filtered_telescopes[index]
            confirm = QMessageBox.warning(
                self, "确认删除",
                f"确定要删除望远镜: {telescope.make} - {telescope.model} 吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.telescopes.remove(telescope)
                self.filter_telescopes()
        else:
            QMessageBox.warning(self, "警告", "请选中一个望远镜进行删除。")

    def copy_selected_telescope(self):
        index = self.telescopes_list.currentRow()
        if index >= 0:
            telescope = self.filtered_telescopes[index]
            details = (
                f"制造商: {telescope.make}\n"
                f"型号: {telescope.model}\n"
                f"孔径: {telescope.aperture}mm\n"
                f"焦距: {telescope.focal_length}mm"
            )
            QApplication.clipboard().setText(details)
            QMessageBox.information(self, "已复制", "选中望远镜详情已复制到剪贴板。")
        else:
            QMessageBox.warning(self, "警告", "请选中一个望远镜进行复制。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelescopeCatalog()
    window.show()
    sys.exit(app.exec())