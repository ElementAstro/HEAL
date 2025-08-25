# coding:utf-8
import sys
import traceback
from typing import List

from PySide6.QtCore import QIODevice, QSharedMemory, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from app.common.logging_config import get_logger, log_exception
from .signal_bus import signalBus

# 使用统一日志配置
logger = get_logger('application')


class SingletonApplication(QApplication):
    """ Singleton application """

    messageSig = Signal(object)

    def __init__(self, argv: List[str], key: str):
        super().__init__(argv)
        self.key = key
        self.timeout = 1000
        self.server = QLocalServer(self)

        # cleanup (only needed for unix)
        QSharedMemory(key).attach()
        self.memory = QSharedMemory(self)
        self.memory.setKey(key)

        if self.memory.attach():
            self.isRunning = True

            self.sendMessage(" ".join(argv[1:]) if len(argv) > 1 else 'show')
            sys.exit()

        self.isRunning = False
        if not self.memory.create(1):
            logger.bind(name="application").error(self.memory.errorString())
            raise RuntimeError(self.memory.errorString())

        self.server.newConnection.connect(self.__onNewConnection)
        QLocalServer.removeServer(key)
        self.server.listen(key)

    def __onNewConnection(self):
        socket = self.server.nextPendingConnection()
        if socket.waitForReadyRead(self.timeout):
            signalBus.appMessageSig.emit(
                bytes(socket.readAll().data()).decode('utf-8'))
            socket.disconnectFromServer()

    def sendMessage(self, message: str):
        """ send message to another application """
        if not self.isRunning:
            return

        # connect to another application
        socket = QLocalSocket(self)
        socket.connectToServer(self.key, QIODevice.OpenModeFlag.WriteOnly)
        if not socket.waitForConnected(self.timeout):
            logger.bind(name="application").error(socket.errorString())
            return

        # send message
        socket.write(message.encode("utf-8"))
        if not socket.waitForBytesWritten(self.timeout):
            logger.bind(name="application").error(socket.errorString())
            return

        socket.disconnectFromServer()


# 注意：全局异常处理器现在在main.py中统一设置
# 这里只保留应用级别的异常处理函数，但不设置为全局处理器

def application_exception_hook(exception_type, value, tb):
    """ Application-level exception callback function """
    logger.bind(name="application").error(
        "Application exception: {}: {}", exception_type.__name__, value)
    message = '\n'.join([''.join(traceback.format_tb(tb)),
                        '{0}: {1}'.format(exception_type.__name__, value)])
    signalBus.appErrorSig.emit(message)

# 不再在这里设置全局异常处理器，避免与main.py中的设置冲突
# sys.excepthook = exception_hook
