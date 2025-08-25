import os
import subprocess
from typing import Union, Optional, List, Tuple
from PySide6.QtGui import QIcon
from PySide6.QtCore import QThread, Signal, QSize, Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (MessageBoxBase, TitleLabel, SubtitleLabel, BodyLabel,
                            PlainTextEdit, FluentIconBase, HyperlinkButton, IndeterminateProgressBar)
from app.model.config import cfg
from app.model.setting_card import SettingCard
from app.common.logging_config import get_logger, log_performance, log_download

# 使用统一日志配置
logger = get_logger('message_download')


class HyperlinkCard(SettingCard):
    def __init__(self, urls: List[Tuple[str, str]], icon: Union[str, QIcon, FluentIconBase], title: str, content: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(icon, title, content, parent)
        for url, text in urls:
            link_button = HyperlinkButton(url, text, self)
            self.hBoxLayout.addWidget(
                link_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class MessageDialog(MessageBoxBase):
    def __init__(self, title: str, content: str, items: List[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.titleLabel = TitleLabel(title)
        self.label1 = SubtitleLabel(content)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.label1)
        for item in items:
            self.viewLayout.addWidget(BodyLabel(item))
        self.yesButton.setText('下载')
        self.cancelButton.setText('取消')


class MessageLauncher(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('选择启动器版本:', '当前内容包含以下项目:', [
            f'Firefly-Launcher:{cfg.APP_VERSION}'], parent)


class MessagePython(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['Python: Python环境'], parent)


class MessageCompiler(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['Compiler: 编译环境'], parent)


class MessageNINA(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['NINA: NINA项目本体'], parent)


class MessagePHD2(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['PHD2: PHD2项目本体'], parent)


class MessageSharpCap(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['SharpCap: SharpCap项目本体'], parent)


class MessageGit(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:', ['Git: Git环境'], parent)


class MessageJava(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:', ['Java: Java环境'], parent)


class MessageMongoDB(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['MongoDB: MongoDB数据库'], parent)


class MessageLunarCore(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['LunarCore: LunarCore项目本体'], parent)


class MessageLunarCoreRes(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:', [
            'LunarCoreRes: StarRailData和Configs'], parent)


class MessageFiddler(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:', [
            'Fiddler: 用于Hutao-GS和LunarCore'], parent)


class MessageMitmdump(MessageDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__('确认当前下载项目:', '当前内容包含以下项目:',
                         ['Mitmdump: 用于Grasscutter'], parent)


class MessageDownload(MessageBoxBase):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.titleLabel = TitleLabel('下载进程：')
        self.yesButton.setHidden(True)
        self.cancelButton.setHidden(True)
        self.progressBar = IndeterminateProgressBar(self)
        self.progressBar.setFixedHeight(6)
        self.commandOutput = PlainTextEdit()
        self.commandOutput.setReadOnly(True)
        self.commandOutput.setFixedSize(QSize(600, 450))
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.commandOutput)
        self.buttonLayout.addWidget(self.progressBar)

    def start_download(self, types, command, file_path, build_jar):
        self.runner = CommandRunner(types, command, file_path, build_jar)
        self.runner.output_updated.connect(self.update_output)
        self.runner.download_finished.connect(self.download_finished)
        self.runner.start()

    def update_output(self, output):
        self.commandOutput.appendPlainText(output)

    def download_finished(self, success, file_path):
        self.progressBar.setHidden(True)
        if success:
            self.yesButton.setHidden(False)
            self.yesButton.setText('完成')
            self.yesButton.clicked.connect(
                lambda: subprocess.Popen(f'start {file_path}', shell=True))
        else:
            self.cancelButton.setHidden(False)
            self.cancelButton.setText('退出')


class CommandRunner(QThread):
    output_updated = Signal(str)
    download_finished = Signal(bool, str)

    def __init__(self, types, command, check, build_jar):
        super().__init__()
        self.types = types
        self.command = command
        self.check = check
        self.build_jar = build_jar

    def run(self):
        if self.types == 'url' and not os.path.exists('temp'):
            subprocess.run('mkdir temp', shell=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process = subprocess.Popen(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)

        # 确保process.stdout不为None再进行迭代
        if process.stdout:
            for line in process.stdout:
                self.output_updated.emit(line.rstrip('\n'))

        process.communicate()
        if self.build_jar == 'lunarcore':
            self.output_updated.emit('正在编译LunarCore...')
            if cfg.chinaStatus:
                subprocess.run('copy /y "src\\patch\\gradle\\gradle-wrapper.properties" "server\\LunarCore\\gradle\\wrapper\\gradle-wrapper.properties" && '
                               'copy /y "src\\patch\\gradle\\build.gradle" "server\\LunarCore\\build.gradle"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run('cd server/LunarCore && gradlew jar', shell=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if process.returncode == 0:
                self.output_updated.emit('LunarCore编译完成！')
            else:
                self.output_updated.emit('LunarCore编译失败！')
        self.download_finished.emit(process.returncode == 0, self.check)
