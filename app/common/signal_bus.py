# coding: utf-8
from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """ Signal bus """

    appMessageSig = Signal(str)
    appErrorSig = Signal(str)

    checkUpdateSig = Signal()
    micaEnableChanged = Signal(bool)

    downloadTerminated = Signal(int, bool)  # pid, isClearCache

    switchToTaskInterfaceSig = Signal()


signalBus = SignalBus()
