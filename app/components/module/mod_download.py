import os
import sys
import json
from dataclasses import dataclass
from typing import List, Optional

import requests
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QListWidgetItem, QStackedWidget, QWidget,
    QSplitter, QFileDialog, QFrame, QDialog
)
from qfluentwidgets import (
    FluentIcon, PushButton, ListWidget, MessageBox, ProgressBar, ToolButton,
    ComboBox, LineEdit, CheckBox, SpinBox
)
from loguru import logger

# 配置loguru
logger.add("mod_manager.log", rotation="500 MB")

@dataclass
class Mod:
    name: str
    description: str
    size: str
    icon: str
    type: str
    installed: bool
    download_url: str

class ModDownloadThread(QThread):
    """多线程下载模组"""
    progress_updated = Signal(int)
    download_finished = Signal(bool, str)

    def __init__(self, url: str, save_path: str, proxy: Optional[str] = None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.proxy = proxy

    def run(self):
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            with requests.get(self.url, stream=True, proxies=proxies) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                with open(self.save_path, 'wb') as f:
                    if total_length is None:
                        f.write(r.content)
                        self.progress_updated.emit(100)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for chunk in r.iter_content(chunk_size=4096):
                            if chunk:
                                f.write(chunk)
                                dl += len(chunk)
                                done = int(100 * dl / total_length)
                                self.progress_updated.emit(done)
            self.download_finished.emit(True, self.save_path)
            logger.info(f"下载完成: {self.save_path}")
        except Exception as e:
            logger.error(f"下载失败: {e}")
            self.download_finished.emit(False, str(e))

class SettingsWindow(QDialog):
    """设置窗口"""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(500, 300)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 下载目录
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("下载目录:")
        self.dir_display = LineEdit()
        self.dir_display.setReadOnly(True)
        self.dir_display.setText(self.settings.get('download_dir', os.path.expanduser('~/Downloads')))
        self.browse_button = PushButton("浏览")
        self.browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_display)
        dir_layout.addWidget(self.browse_button)
        layout.addLayout(dir_layout)

        # 并发下载数
        concurrency_layout = QHBoxLayout()
        self.concurrency_label = QLabel("并发下载数:")
        self.concurrency_spin = SpinBox()
        self.concurrency_spin.setRange(1, 10)
        self.concurrency_spin.setValue(self.settings.get('concurrent_downloads', 3))
        concurrency_layout.addWidget(self.concurrency_label)
        concurrency_layout.addWidget(self.concurrency_spin)
        layout.addLayout(concurrency_layout)

        # 代理设置
        proxy_layout = QHBoxLayout()
        self.proxy_label = QLabel("代理 (可选):")
        self.proxy_input = LineEdit()
        self.proxy_input.setText(self.settings.get('proxy', ''))
        proxy_layout.addWidget(self.proxy_label)
        proxy_layout.addWidget(self.proxy_input)
        layout.addLayout(proxy_layout)

        # 文件验证
        self.verify_checkbox = CheckBox("启用文件验证 (MD5)")
        self.verify_checkbox.setChecked(self.settings.get('enable_verification', False))
        layout.addWidget(self.verify_checkbox)

        # 启用自动更新
        self.auto_update_checkbox = CheckBox("启用自动更新")
        self.auto_update_checkbox.setChecked(self.settings.get('auto_update', True))
        layout.addWidget(self.auto_update_checkbox)

        # 保存按钮
        self.save_button = PushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button, alignment=Qt.AlignRight)

        self.setLayout(layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.dir_display.text())
        if directory:
            self.dir_display.setText(directory)

    def save_settings(self):
        self.settings['download_dir'] = self.dir_display.text()
        self.settings['concurrent_downloads'] = self.concurrency_spin.value()
        self.settings['proxy'] = self.proxy_input.text()
        self.settings['enable_verification'] = self.verify_checkbox.isChecked()
        self.settings['auto_update'] = self.auto_update_checkbox.isChecked()
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
            MessageBox.information(self, "保存成功", "设置已保存。")
            logger.info(f"设置已保存: {self.settings}")
            self.accept()
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            MessageBox.warning(self, "保存失败", "设置保存失败。")

class ModDownload(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 加载设置
        self.settings = self.load_settings()

        # 主容器
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 搜索栏、分类选择和设置按钮
        search_settings_layout = QHBoxLayout()
        self.search_bar = LineEdit()
        self.search_bar.setPlaceholderText("搜索模组...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self.filter_mod_list)

        self.category_selector = ComboBox()
        self.category_selector.addItems(["全部", "生存", "科技", "魔法"])
        self.category_selector.currentTextChanged.connect(self.filter_mod_list)

        self.settings_button = PushButton()
        self.settings_button.setText("设置")
        self.settings_button.setIcon(FluentIcon.SETTING)
        self.settings_button.clicked.connect(self.open_settings)

        search_settings_layout.addWidget(self.search_bar)
        search_settings_layout.addWidget(self.category_selector)
        search_settings_layout.addWidget(self.settings_button)

        self.main_layout.addLayout(search_settings_layout)

        # 左侧模组列表
        self.mod_list = ListWidget()
        self.mod_list.setFixedWidth(300)
        self.mod_list.itemClicked.connect(self.display_mod_details)

        # 下载历史记录
        self.history_label = QLabel("下载历史")
        self.history_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.history_list = ListWidget()
        self.history_list.setFixedHeight(150)

        # 右侧模组详情和下载
        self.details_widget = QStackedWidget()
        self.default_details = QLabel("请选择一个模组查看详情")
        self.default_details.setAlignment(Qt.AlignCenter)
        self.default_details.setStyleSheet("color: gray; font-size: 16px;")
        self.details_widget.addWidget(self.default_details)

        # 主布局
        mod_list_layout = QVBoxLayout()
        mod_list_label = QLabel("模组列表")
        mod_list_label.setFont(QFont("Arial", 12, QFont.Bold))
        mod_list_layout.addWidget(mod_list_label)
        mod_list_layout.addWidget(self.mod_list)
        mod_list_layout.addWidget(self.history_label)
        mod_list_layout.addWidget(self.history_list)

        splitter = QSplitter(Qt.Horizontal)
        left_panel = QWidget()
        left_panel.setLayout(mod_list_layout)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.details_widget)
        splitter.setStretchFactor(1, 3)

        self.main_layout.addWidget(splitter)

        # 模拟模组数据
        self.mods: List[Mod] = self.load_mods()
        self.load_mod_list()

    def load_settings(self) -> dict:
        """加载设置"""
        if os.path.exists('settings.json'):
            try:
                with open('settings.json', 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("settings.json 格式错误，使用默认设置。")
        return {
            'download_dir': os.path.expanduser('~/Downloads'),
            'concurrent_downloads': 3,
            'proxy': '',
            'enable_verification': False,
            'auto_update': True
        }

    def open_settings(self):
        """打开设置窗口"""
        self.settings_window = SettingsWindow(self.settings, self)
        if self.settings_window.exec():
            self.settings = self.load_settings()
            logger.info("设置窗口已关闭，更新设置。")

    def load_mods(self) -> List[Mod]:
        """加载模组数据，并更新安装状态"""
        mods = [
            Mod(
                name="生存拓展",
                description="增加了更多生物与物品，丰富生存体验。",
                size="10MB",
                icon="mod1.png",
                type="生存",
                installed=False,
                download_url="https://example.com/mod1.zip"
            ),
            Mod(
                name="科技进步",
                description="引入高科技设备和机器，适合科技玩家。",
                size="15MB",
                icon="mod2.png",
                type="科技",
                installed=True,
                download_url="https://example.com/mod2.zip"
            ),
            Mod(
                name="魔法世界",
                description="添加魔法技能与魔法生物，探索神秘世界。",
                size="20MB",
                icon="mod3.png",
                type="魔法",
                installed=False,
                download_url="https://example.com/mod3.zip"
            )
        ]
        # 加载已安装状态
        if os.path.exists('installed_mods.json'):
            try:
                with open('installed_mods.json', 'r') as f:
                    installed = json.load(f)
                for mod in mods:
                    mod.installed = mod.name in installed
            except json.JSONDecodeError:
                logger.error("installed_mods.json 格式错误，忽略已安装状态。")
        return mods

    def save_installed_mods(self):
        """保存已安装的模组"""
        installed = [mod.name for mod in self.mods if mod.installed]
        try:
            with open('installed_mods.json', 'w') as f:
                json.dump(installed, f, indent=4)
            logger.info("已安装模组列表已保存。")
        except Exception as e:
            logger.error(f"保存已安装模组失败: {e}")

    def load_mod_list(self):
        """加载模组列表"""
        self.mod_list.clear()
        for mod in self.mods:
            item_text = f"{mod.name} (已安装)" if mod.installed else mod.name
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, mod)
            self.mod_list.addItem(item)
        logger.info("模组列表已加载。")

    def display_mod_details(self, item: QListWidgetItem):
        """显示模组详情"""
        selected_mod: Optional[Mod] = item.data(Qt.UserRole)
        if not selected_mod:
            return

        mod_widget = QWidget()
        layout = QVBoxLayout()

        # 模组图标
        icon_label = QLabel()
        icon_path = selected_mod.icon
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(
                150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(150, 150)
            pixmap.fill(Qt.gray)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        # 模组名称
        name_label = QLabel(selected_mod.name)
        name_label.setFont(QFont("Arial", 16, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)

        # 模组描述
        desc_label = QLabel(selected_mod.description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)

        # 文件大小
        size_label = QLabel(f"大小: {selected_mod.size}")
        size_label.setAlignment(Qt.AlignCenter)

        # 下载/卸载按钮
        download_button = PushButton(
            text="卸载" if selected_mod.installed else "下载",
            icon=FluentIcon.DELETE if selected_mod.installed else FluentIcon.DOWNLOAD
        )
        download_button.clicked.connect(lambda: self.manage_mod(selected_mod, download_button))

        # 复制模组名称按钮
        copy_name_button = ToolButton(FluentIcon.COPY)
        copy_name_button.setToolTip("复制模组名称")
        copy_name_button.clicked.connect(lambda: self.copy_to_clipboard(selected_mod.name))

        # 复制模组描述按钮
        copy_desc_button = ToolButton(FluentIcon.COPY)
        copy_desc_button.setToolTip("复制模组描述")
        copy_desc_button.clicked.connect(lambda: self.copy_to_clipboard(selected_mod.description))

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(download_button)
        button_layout.addWidget(copy_name_button)
        button_layout.addWidget(copy_desc_button)
        button_layout.addStretch()

        # 下载进度条
        progress_bar = ProgressBar()
        progress_bar.setValue(0)
        progress_bar.setVisible(False)

        layout.addWidget(icon_label)
        layout.addWidget(name_label)
        layout.addWidget(desc_label)
        layout.addWidget(size_label)
        layout.addLayout(button_layout)
        layout.addWidget(progress_bar)

        mod_widget.setLayout(layout)

        self.details_widget.addWidget(mod_widget)
        self.details_widget.setCurrentWidget(mod_widget)

        self.current_progress_bar: ProgressBar = progress_bar
        self.current_download_button: PushButton = download_button

    def manage_mod(self, mod: Mod, button: PushButton):
        """下载或卸载模组"""
        if mod.installed:
            self.uninstall_mod(mod, button)
        else:
            self.download_mod(mod, button)

    def download_mod(self, mod: Mod, button: PushButton):
        """下载模组"""
        save_path = os.path.join(
            self.settings.get('download_dir', os.path.expanduser('~/Downloads')),
            f"{mod.name}.zip"
        )
        self.current_progress_bar.setVisible(True)
        self.current_progress_bar.setValue(0)
        self.current_download_button.setEnabled(False)

        self.download_thread = ModDownloadThread(
            mod.download_url,
            save_path,
            proxy=self.settings.get('proxy') if self.settings.get('proxy') else None
        )
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.download_finished.connect(lambda success, info: self.finish_download(mod, button, success, info))
        self.download_thread.start()
        logger.info(f"开始下载: {mod.name} 从 {mod.download_url} 到 {save_path}")

    def uninstall_mod(self, mod: Mod, button: PushButton):
        """卸载模组"""
        reply = MessageBox.question(
            self, "确认卸载", f"确定要卸载模组 {mod.name} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            mod.installed = False
            button.setText("下载")
            button.setIcon(FluentIcon.DOWNLOAD)
            self.save_installed_mods()
            self.update_mod_list()
            MessageBox.information(self, "卸载成功", f"模组 {mod.name} 已卸载。")
            logger.info(f"卸载模组: {mod.name}")

    @Slot(int)
    def update_progress(self, value: int):
        """更新下载进度"""
        self.current_progress_bar.setValue(value)

    @Slot(bool, str)
    def finish_download(self, mod: Mod, button: PushButton, success: bool, info: str):
        """下载完成"""
        if success:
            mod.installed = True
            button.setText("卸载")
            button.setIcon(FluentIcon.DELETE)
            self.history_list.addItem(f"{mod.name} 下载完成")
            self.save_installed_mods()
            MessageBox.information(self, "下载完成", f"模组 {mod.name} 已下载并安装。")
            logger.info(f"模组下载完成: {mod.name}")
        else:
            MessageBox.warning(self, "下载失败", f"模组 {mod.name} 下载失败: {info}")
            logger.error(f"模组下载失败: {mod.name} 错误: {info}")
        self.update_mod_list()
        self.current_progress_bar.setVisible(False)
        button.setEnabled(True)

    def update_mod_list(self):
        """更新模组列表显示"""
        self.load_mod_list()

    def filter_mod_list(self):
        """根据搜索和分类过滤模组列表"""
        keyword = self.search_bar.text().lower()
        category = self.category_selector.currentText()
        self.mod_list.clear()
        for mod in self.mods:
            if keyword not in mod.name.lower() and keyword not in mod.description.lower():
                continue
            if category != "全部" and mod.type != category:
                continue
            item_text = f"{mod.name} (已安装)" if mod.installed else mod.name
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, mod)
            self.mod_list.addItem(item)
        logger.info("模组列表已根据搜索和分类筛选。")

    def copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        MessageBox.information(self, "复制成功", "内容已复制到剪贴板。")
        logger.info(f"复制到剪贴板: {text}")

def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Mod Manager")
    window.resize(900, 600)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    mod_download_frame = ModDownload()
    layout.addWidget(mod_download_frame)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()