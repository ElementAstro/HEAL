"""
Download Search Manager
Handles search functionality for download interface
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QStringListModel, Qt, QTimer, Signal
from PySide6.QtWidgets import QCompleter, QHBoxLayout, QMessageBox, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PushButton,
    SearchLineEdit,
    ToolButton,
)

from src.heal.common.i18n import t
from src.heal.common.logging_config import get_logger


class DownloadSearchManager(QObject):
    """下载搜索管理器 - 增强版"""

    # 信号
    search_performed = Signal(str)  # search_text
    section_found = Signal(str)  # section_title
    search_toggled = Signal(bool)  # visibility
    item_found = Signal(str, str)  # section_title, item_title
    search_cleared = Signal()  # search cleared

    def __init__(self, parent_widget: QWidget) -> None:
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger(
            "download_search_manager", module="DownloadSearchManager"
        )

        # 初始化组件
        self.search_box: Optional[SearchLineEdit] = None
        self.search_button: Optional[ToolButton] = None
        self.clear_button: Optional[ToolButton] = None
        self.combo_box: Optional[ComboBox] = None
        self.search_container: Optional[CardWidget] = None

        # 搜索相关
        self.search_timer: QTimer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        self.search_history: List[str] = []
        self.search_completer: Optional[QCompleter] = None

        # 数据
        self.interface_data: Dict[str, Any] = {}
        self.search_index: Dict[str, List[Dict[str, Any]]] = {}

    def init_search_components(self) -> tuple:
        """初始化增强的搜索组件"""
        # 创建搜索容器
        self.search_container = CardWidget(self.parent_widget)
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(12, 8, 12, 8)

        # 搜索控件 - 使用SearchLineEdit
        self.search_box = SearchLineEdit(self.parent_widget)
        self.search_box.setPlaceholderText("搜索软件、工具或分类...")
        self.search_box.textChanged.connect(self._on_search_text_changed)
        self.search_box.searchSignal.connect(self._perform_search)
        self.search_box.clearSignal.connect(self._clear_search)

        # 搜索按钮
        self.search_button = ToolButton(FluentIcon.SEARCH, self.parent_widget)
        self.search_button.setToolTip("搜索")
        self.search_button.clicked.connect(self._perform_search)

        # 清除按钮
        self.clear_button = ToolButton(FluentIcon.CLOSE, self.parent_widget)
        self.clear_button.setToolTip("清除搜索")
        self.clear_button.clicked.connect(self._clear_search)

        # 组合框 - 快速导航
        self.combo_box = ComboBox(self.parent_widget)
        self.combo_box.currentIndexChanged.connect(self.navigate_to_section)

        # 布局
        search_layout.addWidget(BodyLabel("搜索:"))
        search_layout.addWidget(self.search_box, 1)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)
        search_layout.addWidget(BodyLabel("快速导航:"))
        search_layout.addWidget(self.combo_box)

        # 设置搜索自动完成
        self._setup_search_completer()

        return self.search_container, self.search_box, self.combo_box

    def set_interface_data(self, interface_data: dict) -> None:
        """设置接口数据并构建搜索索引"""
        self.interface_data = interface_data
        self.populate_combo_box()
        self._build_search_index()
        self._update_search_completer()

    def populate_combo_box(self) -> None:
        """填充组合框"""
        if not self.combo_box:
            return

        self.combo_box.clear()
        self.combo_box.addItem("选择分类...")
        for section in self.interface_data.get("sections", []):
            section_title = section.get("title", "未命名")
            self.combo_box.addItem(section_title)

    def _build_search_index(self) -> None:
        """构建搜索索引"""
        self.search_index.clear()

        for section in self.interface_data.get("sections", []):
            section_title = section.get("title", "")
            items = section.get("items", [])

            # 为每个分类建立索引
            self.search_index[section_title.lower()] = []

            for item in items:
                item_data = {
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "section": section_title,
                    "type": item.get("type", ""),
                    "url": item.get("url", ""),
                    "text": item.get("text", ""),
                }
                self.search_index[section_title.lower()].append(item_data)

    def _setup_search_completer(self) -> None:
        """设置搜索自动完成"""
        if not self.search_box:
            return

        # 创建自动完成器
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_box.setCompleter(self.search_completer)

    def _update_search_completer(self) -> None:
        """更新搜索自动完成数据"""
        if not self.search_completer:
            return

        suggestions = []

        # 添加分类名称
        for section in self.interface_data.get("sections", []):
            suggestions.append(section.get("title", ""))

        # 添加软件名称
        for section_items in self.search_index.values():
            for item in section_items:
                if item["title"]:
                    suggestions.append(item["title"])

        # 添加搜索历史
        suggestions.extend(self.search_history[-10:])  # 最近10个搜索

        # 去重并设置
        unique_suggestions = list(set(suggestions))
        model = QStringListModel(unique_suggestions)
        self.search_completer.setModel(model)

    def _on_search_text_changed(self, text: str) -> None:
        """搜索文本变化时的处理"""
        # 延迟搜索，避免频繁搜索
        self.search_timer.stop()
        if text.strip():
            self.search_timer.start(300)  # 300ms延迟

    def _perform_search(self) -> None:
        """执行搜索"""
        if not self.search_box:
            return

        search_text = self.search_box.text().strip()
        if not search_text:
            return

        self.logger.info(f"执行搜索: {search_text}")

        # 添加到搜索历史
        if search_text not in self.search_history:
            self.search_history.append(search_text)
            if len(self.search_history) > 20:  # 保持最近20个搜索
                self.search_history.pop(0)
            self._update_search_completer()

        # 执行搜索
        results = self._search_in_data(search_text.lower())

        if results:
            # 如果找到结果，导航到第一个匹配的分类
            first_result = results[0]
            section_title = first_result["section"]

            # 更新组合框选择
            if self.combo_box:
                for index in range(1, self.combo_box.count()):
                    if self.combo_box.itemText(index) == section_title:
                        self.combo_box.setCurrentIndex(index)
                        break

            self.section_found.emit(section_title)
            self.item_found.emit(section_title, first_result["title"])

            # 显示搜索结果信息
            InfoBar.success(
                title="搜索成功",
                content=f"找到 {len(results)} 个相关结果",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent_widget,
            )

            self.logger.info(f"搜索成功，找到 {len(results)} 个结果")
        else:
            # 没有找到结果
            InfoBar.warning(
                title="未找到结果",
                content=f"没有找到与 '{search_text}' 相关的内容",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.parent_widget,
            )
            self.logger.info(f"搜索无结果: {search_text}")

        self.search_performed.emit(search_text)

    def _search_in_data(self, search_text: str) -> List[Dict[str, Any]]:
        """在数据中搜索"""
        results = []

        for section_title, items in self.search_index.items():
            # 搜索分类标题
            if search_text in section_title:
                for item in items:
                    results.append(item)
                continue

            # 搜索项目
            for item in items:
                if (
                    search_text in item["title"].lower()
                    or search_text in item["content"].lower()
                    or search_text in item["type"].lower()
                ):
                    results.append(item)

        return results

    def _clear_search(self) -> None:
        """清除搜索"""
        if self.search_box:
            self.search_box.clear()

        if self.combo_box:
            self.combo_box.setCurrentIndex(0)

        self.search_cleared.emit()
        self.logger.debug("搜索已清除")

    def navigate_to_section(self) -> None:
        """导航到指定部分"""
        if not self.combo_box:
            return

        section_index = self.combo_box.currentIndex() - 1
        if section_index < 0:
            return

        section = self.interface_data["sections"][section_index]
        section_title = section.get("title", "")

        # 发出导航信号（由父组件处理）
        self.section_found.emit(section_title)
        self.logger.debug(t("download.navigate_to_section", title=section_title))

    def get_current_section_index(self) -> int:
        """获取当前选中的部分索引"""
        if not self.combo_box:
            return -1
        return int(self.combo_box.currentIndex()) - 1

    def perform_search(self, search_text: str, category: str = "all") -> None:
        """执行搜索（新增方法用于新界面）"""
        if not search_text.strip():
            self.search_cleared.emit()
            return

        # 如果指定了分类，则在该分类内搜索
        if category != "all":
            results = self._search_in_category(search_text, category)
        else:
            results = self.search_items_by_text(search_text)

        self.search_performed.emit(search_text)
        self.logger.info(
            f"执行搜索: '{search_text}' in '{category}', 找到 {len(results)} 个结果"
        )

    def _search_in_category(
        self, search_text: str, category_id: str
    ) -> List[Dict[str, Any]]:
        """在指定分类中搜索"""
        results = []
        sections = self.interface_data.get("sections", [])

        for section in sections:
            if section.get("id") == category_id:
                items = section.get("items", [])
                for item in items:
                    if self._item_matches_search(item, search_text):
                        results.append(
                            {
                                "section": section,
                                "item": item,
                                "match_type": "category_search",
                            }
                        )
                break

        return results
