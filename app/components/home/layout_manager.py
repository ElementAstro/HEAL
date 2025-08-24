from typing import List, Sequence
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar
from PySide6.QtGui import QFont
from qfluentwidgets import (PrimaryPushButton, FlowLayout, HorizontalFlipView, 
                            FluentIcon, setCustomStyleSheet)
from app.model.config import cfg
from app.components.home.custom_flip_delegate import CustomFlipItemDelegate

# 定义常量避免重复
BUTTON_BORDER_RADIUS_STYLE = 'PushButton{border-radius: 12px}'
ONE_CLICK_START_TEXT = ' 一键启动'


class HomeLayoutManager:
    """Manages the layout and UI components for the home interface."""
    
    def __init__(self, parent_widget: QWidget):
        self.parent = parent_widget
        
    def create_flip_view(self) -> HorizontalFlipView:
        """创建并配置翻页视图"""
        flip_view = HorizontalFlipView()
        flip_view.addImages([
            "./src/image/bg_home_1.png", 
            "./src/image/bg_home_2.png", 
            "./src/image/bg_home_3.png"
        ])
        flip_view.setItemSize(QSize(1160, 350))
        flip_view.setFixedSize(QSize(1160, 350))
        flip_view.setCurrentIndex(0)
        flip_view.setItemDelegate(CustomFlipItemDelegate(flip_view))
        return flip_view
        
    def create_toggle_button(self) -> PrimaryPushButton:
        """创建切换按钮"""
        button_toggle = PrimaryPushButton(FluentIcon.PLAY_SOLID, ONE_CLICK_START_TEXT)
        button_toggle.setFixedSize(200, 65)
        button_toggle.setIconSize(QSize(20, 20))
        button_toggle.setFont(QFont(f'{cfg.APP_FONT}', 18))
        setCustomStyleSheet(
            button_toggle, BUTTON_BORDER_RADIUS_STYLE, BUTTON_BORDER_RADIUS_STYLE)
        return button_toggle
        
    def create_toolbar(self) -> QToolBar:
        """创建工具栏"""
        toolbar = QToolBar(self.parent)
        toolbar.setVisible(False)
        return toolbar
        
    def setup_main_layout(self, flip_view: HorizontalFlipView, 
                         server_buttons: Sequence[QWidget], 
                         toggle_button: PrimaryPushButton,
                         toolbar: QToolBar) -> QVBoxLayout:
        """设置主布局"""
        # 图像布局
        image_layout = QVBoxLayout()
        image_layout.addWidget(flip_view)
        image_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # 按钮布局
        button_layout = FlowLayout(needAni=True)
        button_layout.setVerticalSpacing(30)
        button_layout.setHorizontalSpacing(30)
        for button in server_buttons:
            button_layout.addWidget(button)

        play_layout = QHBoxLayout()
        play_layout.addSpacing(15)
        play_layout.addLayout(button_layout)
        play_layout.addSpacing(300)

        # 切换按钮布局
        button_toggle_layout = QHBoxLayout()
        button_toggle_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        button_toggle_layout.addWidget(toggle_button)
        button_toggle_layout.setContentsMargins(0, 0, 25, 0)

        # 主布局
        main_layout = QVBoxLayout(self.parent)
        main_layout.setContentsMargins(10, 30, 10, 10)
        main_layout.addLayout(image_layout)
        main_layout.addSpacing(25)
        main_layout.addLayout(play_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(button_toggle_layout)
        main_layout.addSpacing(25)
        main_layout.addWidget(toolbar)
        
        return main_layout
