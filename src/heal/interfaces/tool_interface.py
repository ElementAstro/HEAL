from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon, Pivot, ScrollArea, qrouter

from ..common.logging_config import get_logger, log_performance, with_correlation_id
from ..components.tools.nginx import NginxConfigurator
from ..components.tools.system_command import CommandCenter
from ..components.tools.telescope import TelescopeCatalog
from ..models.style_sheet import StyleSheet

# 使用统一日志配置
logger = get_logger("tool_interface")


class Tools(ScrollArea):
    Nav = Pivot

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.parent = parent
        self.setObjectName(text)
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        logger.info(f"初始化工具界面: {text}")

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # 添加项
        logger.debug("初始化工具组件")
        self.NginxConfiguratorInterface = NginxConfigurator()
        self.NginxConfiguratorInterface.setContentsMargins(10, 10, 10, 10)

        self.TelescopeCatalogInterface = TelescopeCatalog()
        self.TelescopeCatalogInterface.setContentsMargins(10, 10, 10, 10)

        self.CommandCenterInterface = CommandCenter()
        self.CommandCenterInterface.setContentsMargins(10, 10, 10, 10)

        self.__initWidget()
        logger.debug("工具界面初始化完成")

    def __initWidget(self) -> None:
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)  # 必须设置！！！

        # 使用qss设置样式
        self.scrollWidget.setObjectName("scrollWidget")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self) -> None:
        # 栏绑定界面
        self.addSubInterface(
            self.NginxConfiguratorInterface,
            "NginxConfiguratorInterface",
            self.tr("Nginx配置"),
            icon=FluentIcon.CLOUD,
        )

        self.addSubInterface(
            self.TelescopeCatalogInterface,
            "TelescopeCatalogInterface",
            self.tr("望远镜分类"),
            icon=FluentIcon.IOT,
        )

        self.addSubInterface(
            self.CommandCenterInterface,
            "CommandCenterInterface",
            self.tr("命令行"),
            icon=FluentIcon.LABEL,
        )

        # 初始化配置界面 - 添加到主布局
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)

        # 连接信号
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)

        # 设置默认界面
        self.stackedWidget.setCurrentWidget(self.NginxConfiguratorInterface)
        self.pivot.setCurrentItem(self.NginxConfiguratorInterface.objectName())
        qrouter.setDefaultRouteKey(
            self.stackedWidget, self.NginxConfiguratorInterface.objectName()
        )

    def __connectSignalToSlot(self) -> None:
        """"""

    def addSubInterface(self, widget: QWidget, objectName: str, text: str, icon: Optional[Any] = None) -> None:
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index: int) -> None:
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
