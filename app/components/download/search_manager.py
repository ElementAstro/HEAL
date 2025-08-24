"""
Download Search Manager
Handles search functionality for download interface
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import QObject, Signal
from qfluentwidgets import LineEdit, PushButton, ComboBox

from app.common.logging_config import get_logger
from app.common.i18n import t


class DownloadSearchManager(QObject):
    """下载搜索管理器"""
    
    # 信号
    search_performed = Signal(str)  # search_text
    section_found = Signal(str)     # section_title
    search_toggled = Signal(bool)   # visibility
    
    def __init__(self, parent_widget: QWidget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.logger = get_logger('download_search_manager', module='DownloadSearchManager')
        
        # 初始化组件
        self.search_box: Optional[LineEdit] = None
        self.search_button: Optional[PushButton] = None
        self.toggle_search_button: Optional[PushButton] = None
        self.combo_box: Optional[ComboBox] = None
        
        # 数据
        self.interface_data: Dict[str, Any] = {}
    
    def init_search_components(self) -> tuple:
        """初始化搜索组件"""
        # 搜索控件
        self.search_box = LineEdit(self.parent_widget)
        self.search_box.setPlaceholderText(t('download.search_placeholder'))
        self.search_box.textChanged.connect(self.search_items)
        
        # 按钮控件
        self.search_button = PushButton(t('common.search'), self.parent_widget)
        self.search_button.clicked.connect(self.search_items)
        
        self.toggle_search_button = PushButton(t('download.toggle_search'), self.parent_widget)
        self.toggle_search_button.clicked.connect(self.toggle_search_box)
        
        # 组合框
        self.combo_box = ComboBox(self.parent_widget)
        self.combo_box.currentIndexChanged.connect(self.navigate_to_section)
        
        # 默认隐藏搜索框
        self.search_box.setVisible(False)
        
        return self.search_box, self.search_button, self.toggle_search_button, self.combo_box
    
    def set_interface_data(self, interface_data: dict):
        """设置接口数据"""
        self.interface_data = interface_data
        self.populate_combo_box()
    
    def populate_combo_box(self):
        """填充组合框"""
        if not self.combo_box:
            return
            
        self.combo_box.clear()
        self.combo_box.addItem(t('download.select_section'))
        for section in self.interface_data.get('sections', []):
            section_title = section.get('title', t('download.untitled'))
            self.combo_box.addItem(section_title)
    
    def toggle_search_box(self):
        """切换搜索框显示状态"""
        if not self.search_box:
            return
            
        current_visibility = self.search_box.isVisible()
        new_visibility = not current_visibility
        self.search_box.setVisible(new_visibility)
        
        self.search_toggled.emit(new_visibility)
        self.logger.debug(t('download.search_box_toggled', visible=new_visibility))
    
    def search_items(self):
        """搜索项目"""
        if not self.search_box or not self.combo_box:
            return
            
        search_text = self.search_box.text().lower()
        if not search_text:
            return
            
        self.search_performed.emit(search_text)
        
        matched_index = -1
        for index in range(1, self.combo_box.count()):
            item_text = self.combo_box.itemText(index).lower()
            if search_text in item_text:
                matched_index = index
                break
        
        if matched_index >= 0:
            self.combo_box.setCurrentIndex(matched_index)
            section_title = self.interface_data['sections'][matched_index - 1].get('title', '')
            self.section_found.emit(section_title)
            self.logger.info(t('download.match_found', title=section_title))
        else:
            QMessageBox.warning(
                self.parent_widget, 
                t('download.not_found'), 
                t('download.no_match')
            )
            self.logger.info(t('download.no_match_log'))
    
    def navigate_to_section(self):
        """导航到指定部分"""
        if not self.combo_box:
            return
            
        section_index = self.combo_box.currentIndex() - 1
        if section_index < 0:
            return
        
        section = self.interface_data['sections'][section_index]
        section_title = section.get('title', '')
        
        # 发出导航信号（由父组件处理）
        self.section_found.emit(section_title)
        self.logger.debug(t('download.navigate_to_section', title=section_title))
    
    def get_current_section_index(self) -> int:
        """获取当前选中的部分索引"""
        if not self.combo_box:
            return -1
        return self.combo_box.currentIndex() - 1
