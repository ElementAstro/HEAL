"""
Download Interface Navigation Manager
Handles navigation and UI layout for download interface
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QObject, Signal
from qfluentwidgets import Pivot, qrouter

from app.common.logging_config import get_logger
from app.model.setting_card import SettingCardGroup


class DownloadNavigationManager(QObject):
    """下载界面导航管理器"""
    
    # 信号
    navigation_changed = Signal(str, int)  # section_title, index
    
    def __init__(self, parent_widget: QWidget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger('download_navigation_manager', module='DownloadNavigationManager')
        
        # UI组件
        self.pivot: Pivot = None
        self.stacked_widget: QStackedWidget = None
        self.section_widgets: List[SettingCardGroup] = []
    
    def init_navigation_components(self, pivot_class) -> tuple:
        """初始化导航组件"""
        self.pivot = pivot_class(self.parent_widget)
        self.stacked_widget = QStackedWidget(self.parent_widget)
        
        return self.pivot, self.stacked_widget
    
    def setup_sections(self, section_widgets: List[SettingCardGroup], sections_data: List[Dict[str, Any]]):
        """设置所有部分"""
        self.section_widgets = section_widgets
        
        # 清空现有的导航项
        if self.stacked_widget:
            while self.stacked_widget.count() > 0:
                widget = self.stacked_widget.widget(0)
                self.stacked_widget.removeWidget(widget)
        
        # 添加新的部分
        for i, (widget, section_data) in enumerate(zip(section_widgets, sections_data)):
            self.add_sub_interface(
                widget,
                section_data.get('id', f'section_{i}'),
                section_data.get('title', f'Section {i+1}'),
                section_data.get('icon')
            )
    
    def add_sub_interface(self, widget: QWidget, object_name: str, text: str, icon=None):
        """添加子界面"""
        widget.setObjectName(object_name)
        if self.stacked_widget:
            self.stacked_widget.addWidget(widget)
        
        if self.pivot:
            self.pivot.addItem(
                icon=icon,
                routeKey=object_name,
                text=text,
                onClick=lambda: self.navigate_to_widget(widget, text)
            )
        
        self.logger.debug(f"添加子界面: {text} ({object_name})")
    
    def navigate_to_widget(self, widget: QWidget, title: str):
        """导航到指定的组件"""
        if self.stacked_widget:
            index = self.stacked_widget.indexOf(widget)
            if index >= 0:
                self.stacked_widget.setCurrentWidget(widget)
                self.navigation_changed.emit(title, index)
        
        if self.pivot:
            self.pivot.setCurrentItem(widget.objectName())
            qrouter.push(self.stacked_widget, widget.objectName())
    
    def navigate_to_section_by_title(self, section_title: str):
        """根据标题导航到部分"""
        pivot_item_name = section_title.replace(' ', '-')
        
        if self.pivot:
            self.pivot.setCurrentItem(pivot_item_name)
        
        # 查找对应的组件并设置为当前组件
        for i, widget in enumerate(self.section_widgets):
            if widget.objectName() == pivot_item_name:
                if self.stacked_widget:
                    self.stacked_widget.setCurrentIndex(i)
                self.navigation_changed.emit(section_title, i)
                break
        
        self.logger.debug(f"导航到部分: {section_title}")
    
    def navigate_to_index(self, index: int):
        """导航到指定索引"""
        if self.stacked_widget and 0 <= index < self.stacked_widget.count():
            widget = self.stacked_widget.widget(index)
            self.stacked_widget.setCurrentIndex(index)
            
            if self.pivot:
                self.pivot.setCurrentItem(widget.objectName())
            
            self.navigation_changed.emit(f"Section {index + 1}", index)
    
    def get_current_index(self) -> int:
        """获取当前索引"""
        if self.stacked_widget:
            return self.stacked_widget.currentIndex()
        return -1
    
    def get_current_widget(self) -> QWidget:
        """获取当前组件"""
        if self.stacked_widget:
            return self.stacked_widget.currentWidget()
        return None
    
    def setup_layout(self, vbox_layout: QVBoxLayout, refresh_button, search_components: tuple):
        """设置布局"""
        search_box, search_button, toggle_search_button, combo_box = search_components
        
        # 搜索区域布局
        search_layout = QHBoxLayout()
        search_layout.addWidget(search_box)
        search_layout.addWidget(search_button)
        search_layout.addWidget(toggle_search_button)
        search_layout.addWidget(combo_box)
        search_layout.addWidget(refresh_button)
        
        # 主布局
        vbox_layout.addLayout(search_layout)
        if self.pivot:
            vbox_layout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        if self.stacked_widget:
            vbox_layout.addWidget(self.stacked_widget)
        
        vbox_layout.setSpacing(15)
        vbox_layout.setContentsMargins(0, 10, 10, 0)

    def navigate_to_category(self, category: str):
        """导航到指定分类"""
        self.logger.info(f"导航到分类: {category}")
        # 这里可以实现分类导航逻辑
        # 例如：切换到对应的分类页面或过滤显示

    def navigate_to_section_by_id(self, section_id: str):
        """根据ID导航到指定部分"""
        for i, widget in enumerate(self.section_widgets):
            # 假设widget有一个section_id属性或者可以通过其他方式识别
            if hasattr(widget, 'section_id') and widget.section_id == section_id:
                if self.stacked_widget:
                    self.stacked_widget.setCurrentIndex(i)
                if self.pivot:
                    self.pivot.setCurrentItem(widget.objectName())
                self.logger.info(f"导航到部分ID: {section_id}")
                return

        self.logger.warning(f"未找到部分ID: {section_id}")
