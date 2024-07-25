from PySide6.QtWidgets import QSystemTrayIcon
from PySide6.QtGui import QIcon
from PySide6.QtCore import QCoreApplication, QTimer
from qfluentwidgets import Action, FluentIcon, RoundMenu

class SystemTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置初始图标
        self.setIcon(QIcon("src/image/atom.png"))
        
        # 创建托盘图标的右键菜单
        self.tray_menu = RoundMenu(parent)
        self.tray_icon = SystemTray(self)
        
        # 添加显示/隐藏主窗口的菜单项
        self.toggle_action = Action(FluentIcon.HOME, "Show Window", self)
        self.toggle_action.triggered.connect(parent.toggle_window)
        self.tray_menu.addAction(self.toggle_action)
        
        # 添加退出的菜单项
        quit_action = Action(FluentIcon.CLOSE, "Quit", self)
        quit_action.triggered.connect(QCoreApplication.instance().quit)
        self.tray_menu.addAction(quit_action)
        
        # 将菜单应用到托盘图标
        self.setContextMenu(self.tray_menu)
        
        # 显示托盘图标
        self.show()
        
        # 连接托盘图标的点击事件
        self.activated.connect(parent.on_tray_icon_activated)
        
        # 显示图标提示
        self.setToolTip("My Application is running")
        
        # 动态更新图标
        self.icon_timer = QTimer(self)
        self.icon_timer.timeout.connect(self.update_icon)
        self.icon_timer.start(5000)  # 每5秒更新图标
        
    def update_icon(self):
        # 动态更新图标
        new_icon_path = "./atom.png"
        self.setIcon(QIcon(new_icon_path))