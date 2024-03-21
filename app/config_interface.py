import json
import os
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QLayout
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat
from PySide6.QtCore import Qt, QEvent
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import Pivot, qrouter, ScrollArea, PrimaryPushSettingCard, InfoBar, InfoBarPosition, TextEdit, LineEdit,PrimaryPushButton
from app.component.style_sheet import StyleSheet
from app.component.setting_group import SettingCardGroup

class JSONSyntaxHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        index = 0
        while index >= 0:
            index = text.find('"', index)
            if index >= 0:
                self.setFormat(index, 1, self.quotationFormat)
                index += 1

    def __init__(self, parent=None):
        super(JSONSyntaxHighlighter, self).__init__(parent) # type: ignore

        self.quotationFormat = QTextCharFormat()
        self.quotationFormat.setForeground(Qt.darkGreen)


class JsonEditor(QWidget):
    def __init__(self, json_data, parent=None):
        super().__init__(parent)
        self.json_data = json_data

        self.layout = QVBoxLayout(self)

        self.search_layout = QHBoxLayout()
        self.search_input = LineEdit()
        self.search_button = PrimaryPushButton('查找')
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.search_button)
        self.layout.addLayout(self.search_layout)

        self.text_edit = TextEdit()
        self.syntax_highlighter = JSONSyntaxHighlighter(self.text_edit.document())

        self.text_edit.setPlainText(json.dumps(json_data, indent=4))  # 将 JSON 数据格式化后显示在 QPlainTextEdit 中
        self.layout.addWidget(self.text_edit)

        self.format_button = PrimaryPushButton('格式化')
        self.save_button = PrimaryPushButton('保存')
        self.format_button.clicked.connect(self.format_json)
        self.save_button.clicked.connect(self.save_json)
        self.layout.addWidget(self.format_button)
        self.layout.addWidget(self.save_button)

        # 添加拖放支持
        self.text_edit.setAcceptDrops(True)
        self.text_edit.setAcceptDrops(True)
        self.text_edit.installEventFilter(self)

    def format_json(self):
        try:
            formatted_json = json.dumps(json.loads(self.text_edit.toPlainText()), indent=4)
            self.text_edit.setPlainText(formatted_json)
        except Exception as e:
            print(f"Error formatting JSON: {e}")

    def save_json(self):
        modified_json = json.loads(self.text_edit.toPlainText())  # 从 QPlainTextEdit 中获取修改后的 JSON 数据
        # 在这里可以添加保存 JSON 数据的逻辑，比如将修改后的数据保存回文件中

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            # 在这里处理拖放的文件路径，比如读取文件内容并显示在 QPlainTextEdit 中

    def eventFilter(self, obj, event):
        if obj is self.text_edit and event.type() == QEvent.DragEnter:
            mime_data = event.mimeData()
            if mime_data.hasUrls():
                event.accept()
                return True
        return super(JsonEditor, self).eventFilter(obj, event)

class Config(ScrollArea):
    Nav = Pivot
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.parent = parent
        self.setObjectName(text.replace(' ', '-'))
        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)

        # 栏定义
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)

        # 添加项
        self.LauncherInterface = SettingCardGroup(self.scrollWidget)
        self.settingConfigCard = PrimaryPushSettingCard(
            '打开文件',
            FIF.LABEL,
            '启动器设置',
            '自定义启动器配置'
        )
        self.personalConfigCard = PrimaryPushSettingCard(
            '打开文件',
            FIF.LABEL,
            '个性化',
            '自定义个性化配置'
        )
        self.LunarCoreInterface = SettingCardGroup(self.scrollWidget)
        self.bannersConfigCard = PrimaryPushSettingCard(
            '打开文件',
            FIF.LABEL,
            'Banners(外部)',
            'LunarCore的跃迁配置'
        )

        self.openEditorButton = PrimaryPushButton('打开编辑器')
        
        self.__initWidget()

    def __initWidget(self):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)     # 水平滚动条关闭
        self.setViewportMargins(20, 0, 20, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)    # 必须设置！！！
        
        # 使用qss设置样式
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        # 项绑定到栏目
        self.LauncherInterface.addSettingCard(self.settingConfigCard)
        self.LauncherInterface.addSettingCard(self.personalConfigCard)
        self.LunarCoreInterface.addSettingCard(self.bannersConfigCard)

        # 栏绑定界面
        self.addSubInterface(self.LauncherInterface, 'LauncherInterface','启动器', icon=FIF.TAG)
        self.addSubInterface(self.LunarCoreInterface, 'LunarCoreInterface','LunarCore', icon=FIF.TAG)

        # 初始化配置界面
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setSpacing(15)
        self.vBoxLayout.setContentsMargins(0, 10, 10, 0)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.LauncherInterface)
        self.pivot.setCurrentItem(self.LauncherInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.LauncherInterface.objectName())

        self.vBoxLayout.addWidget(self.openEditorButton)
        self.openEditorButton.clicked.connect(self.open_json_editor)
        
    def __connectSignalToSlot(self):
        self.settingConfigCard.clicked.connect(lambda: self.open_file('config/config.json'))
        self.personalConfigCard.clicked.connect(lambda: self.open_file('config/auto.json'))
        self.bannersConfigCard.clicked.connect(lambda: self.open_file('server/lunarcore/data/banners.json'))

    def addSubInterface(self, widget: QLabel, objectName, text, icon=None):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            icon=icon,
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())

    def open_file(self, file_path):
        if os.path.exists(file_path):
            subprocess.run(['start', file_path], shell=True)
        else:
            InfoBar.error(
                title="找不到文件，请重新下载！",
                content="",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def open_json_editor(self):
        file_path = './config/server.json'  # 替换成您要打开的 JSON 文件路径
        self.show_json_editor(file_path)
    def show_json_editor(self, file_path):
        with open(file_path) as f:
            json_data = json.load(f)
        self.editor = JsonEditor(json_data, parent=self)
        self.editor.show()

        self.openEditorButton.setText('关闭编辑器')
        self.openEditorButton.clicked.disconnect(self.open_json_editor)
        self.openEditorButton.clicked.connect(self.close_json_editor)

    def close_json_editor(self):
        # 在这里添加关闭编辑器的逻辑
        self.openEditorButton.setText('打开编辑器')
        self.openEditorButton.clicked.disconnect(self.close_json_editor)
        self.openEditorButton.clicked.connect(self.open_json_editor)
        self.editor.close()