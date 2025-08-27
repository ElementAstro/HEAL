from typing import Any, Dict, List, Sequence

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FlowLayout,
    FluentIcon,
    HorizontalFlipView,
    PrimaryPushButton,
    setCustomStyleSheet,
)

from src.heal.common.i18n_ui import tr
from src.heal.models.config import cfg
from src.heal.resources import resource_manager
from .compact_banner_widget import CompactBannerWidget
from .custom_flip_delegate import CustomFlipItemDelegate
from .quick_action_bar import QuickActionBar
from .server_status_card import ServerStatusCard
from .status_overview_widget import StatusOverviewWidget

# 定义常量避免重复
BUTTON_BORDER_RADIUS_STYLE = "PushButton{border-radius: 12px}"


class HomeLayoutManager:
    """Manages the layout and UI components for the home interface."""

    def __init__(self, parent_widget: QWidget) -> None:
        self.parent = parent_widget
        self.use_optimized_layout = True  # Flag to enable new layout

        # Store references to new components
        self.compact_banner: Any = None
        self.status_overview: Any = None
        self.quick_action_bar: Any = None
        self.server_status_cards: list[Any] = []

    def create_flip_view(self) -> HorizontalFlipView:
        """创建并配置翻页视图"""
        flip_view = HorizontalFlipView()
        flip_view.addImages(
            [
                str(resource_manager.get_resource_path(
                    "images", "bg_home_1.png")),
                str(resource_manager.get_resource_path(
                    "images", "bg_home_2.png")),
                str(resource_manager.get_resource_path(
                    "images", "bg_home_3.png")),
            ]
        )
        flip_view.setItemSize(QSize(1160, 350))
        flip_view.setFixedSize(QSize(1160, 350))
        flip_view.setCurrentIndex(0)
        flip_view.setItemDelegate(CustomFlipItemDelegate(flip_view))
        return flip_view

    def create_toggle_button(self) -> PrimaryPushButton:
        """创建切换按钮"""
        button_toggle = PrimaryPushButton(
            FluentIcon.PLAY_SOLID, tr("home.one_click_start")
        )
        button_toggle.setFixedSize(200, 65)
        button_toggle.setIconSize(QSize(20, 20))
        button_toggle.setFont(QFont(f"{cfg.APP_FONT}", 18))
        setCustomStyleSheet(
            button_toggle, BUTTON_BORDER_RADIUS_STYLE, BUTTON_BORDER_RADIUS_STYLE
        )
        return button_toggle

    def create_toolbar(self) -> QToolBar:
        """创建工具栏"""
        toolbar = QToolBar(self.parent)
        toolbar.setVisible(False)
        return toolbar

    def create_compact_banner(self) -> CompactBannerWidget:
        """创建紧凑横幅组件"""
        self.compact_banner = CompactBannerWidget(self.parent)
        return self.compact_banner  # type: ignore[no-any-return]

    def create_status_overview(self) -> StatusOverviewWidget:
        """创建状态概览组件"""
        self.status_overview = StatusOverviewWidget(self.parent)
        return self.status_overview  # type: ignore[no-any-return]

    def create_quick_action_bar(self) -> QuickActionBar:
        """创建快速操作栏"""
        self.quick_action_bar = QuickActionBar(self.parent)
        return self.quick_action_bar  # type: ignore[no-any-return]

    def create_server_status_cards(
        self, server_configs: Dict[str, Any]
    ) -> List[ServerStatusCard]:
        """创建服务器状态卡片"""
        self.server_status_cards = []  # Clear existing cards
        for server_name, server_config in server_configs.items():
            card = ServerStatusCard(server_name, server_config, self.parent)
            self.server_status_cards.append(card)
        return self.server_status_cards

    def setup_main_layout(
        self,
        flip_view: HorizontalFlipView,
        server_buttons: Sequence[QWidget],
        toggle_button: PrimaryPushButton,
        toolbar: QToolBar,
    ) -> QVBoxLayout:
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

    def setup_optimized_layout(
        self,
        compact_banner: CompactBannerWidget,
        status_overview: StatusOverviewWidget,
        server_status_cards: List[ServerStatusCard],
        quick_action_bar: QuickActionBar,
        toolbar: QToolBar,
    ) -> QVBoxLayout:
        """设置优化后的主布局"""
        # 主布局
        main_layout = QVBoxLayout(self.parent)
        main_layout.setContentsMargins(15, 20, 15, 15)
        main_layout.setSpacing(15)

        # 1. 紧凑横幅 (顶部)
        main_layout.addWidget(compact_banner)

        # 2. 状态概览 (横幅下方)
        main_layout.addWidget(status_overview)

        # 3. 服务器状态卡片网格 (主要内容区域)
        if server_status_cards:
            cards_scroll_area = self._create_server_cards_area(
                server_status_cards)
            main_layout.addWidget(cards_scroll_area, 1)  # 给予最大空间
        else:
            # 如果没有服务器，显示占位符
            placeholder = self._create_no_servers_placeholder()
            main_layout.addWidget(placeholder, 1)

        # 4. 快速操作栏 (底部)
        main_layout.addWidget(quick_action_bar)

        # 5. 工具栏 (隐藏)
        main_layout.addWidget(toolbar)

        return main_layout

    def _create_server_cards_area(
        self, server_cards: List[ServerStatusCard]
    ) -> QScrollArea:
        """创建服务器卡片滚动区域"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)

        # 卡片容器
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setContentsMargins(5, 5, 5, 5)
        cards_layout.setSpacing(15)

        # 按网格排列卡片 (每行最多2个卡片)
        columns = 2
        for i, card in enumerate(server_cards):
            row = i // columns
            col = i % columns
            cards_layout.addWidget(card, row, col)

        # 添加拉伸以保持卡片在顶部对齐
        cards_layout.setRowStretch(len(server_cards) // columns + 1, 1)

        scroll_area.setWidget(cards_widget)
        return scroll_area

    def _create_no_servers_placeholder(self) -> QWidget:
        """创建无服务器时的占位符"""
        placeholder = QFrame()
        placeholder.setFrameStyle(QFrame.Shape.Box)
        placeholder.setStyleSheet(
            """
            QFrame {
                border: 2px dashed rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                background-color: rgba(240, 240, 240, 0.5);
            }
        """
        )

        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(tr("home.no_servers_title"))
        title.setFont(QFont(cfg.APP_FONT, 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("QLabel { color: #7F8C8D; }")

        subtitle = QLabel(tr("home.no_servers_subtitle"))
        subtitle.setFont(QFont(cfg.APP_FONT, 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("QLabel { color: #95A5A6; }")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return placeholder
