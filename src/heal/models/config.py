import json
import os
from enum import Enum
from typing import Any

from PySide6.QtCore import QLocale, Qt
from qfluentwidgets import (
    BoolValidator,
    ConfigItem,
    ConfigSerializer,
    InfoBar,
    InfoBarPosition,
    OptionsConfigItem,
    OptionsValidator,
    QConfig,
    Theme,
    qconfig,
)

from src.heal.common.logging_config import get_logger

# 使用统一日志配置
logger = get_logger("config")


def Info(self: Any, types: str, time: int, title: str, content: str = "") -> None:
    if types == "S":
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=time,
            parent=self,
        )
    elif types == "E":
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=time,
            parent=self,
        )
    elif types == "W":
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=time,
            parent=self,
        )


def open_file(self: Any, file_path: str) -> None:
    if os.path.exists(file_path):
        os.startfile(file_path)
        Info(self, "S", 1000, self.tr("文件已打开!"))
    else:
        Info(self, "E", 3000, self.tr("找不到文件!"))


from src.heal.common.config_manager import ConfigType, config_manager

# 使用新的JSON工具替换原有实现
from src.heal.common.json_utils import get_json

logger.debug("配置模块已加载")


def save_json(data: Any, types: Any) -> None:
    """Legacy function - use config_manager instead."""
    try:
        main_config = config_manager.get_config(ConfigType.MAIN)
        main_config[types] = data
        config_manager.set_config(ConfigType.MAIN, main_config)
    except Exception as e:
        logger.error(f"Failed to save config data: {e}")
        # Fallback to old method
        with open("config/config.json", "r", encoding="utf-8") as file:
            info = json.load(file)
            info[types] = data
        with open("config/config.json", "w", encoding="utf-8") as file:
            json.dump(info, file, indent=2, ensure_ascii=False)


def get_version_type(version: Any) -> str:
    if not os.path.exists("firefly-launcher.py"):
        return f"{version} REL"
    else:
        return f"{version} DEV"


class Language(Enum):
    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Language.Chinese, QLocale.Country.Taiwan)
    ENGLISH = QLocale(QLocale.Language.English)


class LanguageSerializer(ConfigSerializer):
    def serialize(self, value: Any) -> str:
        return str(value.value.name())

    def deserialize(self, value: str) -> Language:
        return Language(QLocale(value))


class Config(QConfig):
    ############### APP CONFIG ###############
    dpiScale = OptionsConfigItem(
        "Style",
        "DpiScale",
        "Auto",
        OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]),
        restart=True,
    )
    language = OptionsConfigItem(
        "Style",
        "Language",
        Language.ENGLISH,
        OptionsValidator(Language),
        LanguageSerializer(),
        restart=True,
    )
    autoCopy = ConfigItem("Function", "AutoCopy", True, BoolValidator())
    useLogin = ConfigItem("Function", "UseLogin", False, BoolValidator())
    useAudio = ConfigItem("Function", "UseAudio", True, BoolValidator())
    proxyStatus = ConfigItem("Proxy", "ProxyStatus", True, BoolValidator())
    chinaStatus = ConfigItem("Proxy", "ChinaStatus", False, BoolValidator())
    useRemote = ConfigItem("Command", "useRemote", False, BoolValidator())

    APP_NAME = "Hello ElementAstro Launcher"
    APP_VERSION = get_version_type(get_json("./config/version.json", "APP_VERSION"))
    APP_FONT = "SDK_SC_Web"

    ############### LINK CONFIG ###############
    URL_LATEST = "https://github.com/letheriver2007/Firefly-Launcher/releases/latest"

    URL_WRITER = "https://github.com/letheriver2007"
    URL_REPO = "https://github.com/letheriver2007/Firefly-Launcher"
    URL_RELEASES = "https://github.com/letheriver2007/Firefly-Launcher/releases"
    URL_ISSUES = "https://github.com/letheriver2007/Firefly-Launcher/issues"

    DOWNLOAD_COMMANDS_AUDIO = (
        "https://github.com/letheriver2007/Firefly-Launcher-Res.git src/audio"
    )
    DOWNLOAD_COMMANDS_GIT = "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe"
    DOWNLOAD_COMMANDS_JAVA = (
        "https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.msi"
    )
    DOWNLOAD_COMMANDS_MONGODB_INSTALLER = (
        "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.6-signed.msi"
    )
    DOWNLOAD_COMMANDS_MONGODB_PORTABLE = (
        "https://github.com/Letheriver2007/Firefly-Launcher-Res.git tool/mongodb"
    )
    DOWNLOAD_COMMANDS_LUNARCORE = (
        "https://github.com/Melledy/LunarCore.git server/LunarCore"
    )
    DOWNLOAD_COMMANDS_LUNARCORE_RES_1 = (
        "https://github.com/Dimbreath/StarRailData.git server/LunarCore/resources"
    )
    DOWNLOAD_COMMANDS_LUNARCORE_RES_2 = (
        "https://gitlab.com/Melledy/LunarCore-Configs.git server/LunarCore/resources/Config/Config && "
        'move "server/LunarCore/resources/Config/Config/Config/ConfigSummonUnit" "server/LunarCore/resources/Config/ConfigSummonUnit" && '
        'xcopy /s /e /y "server/LunarCore/resources/Config/Config/Config/LevelOutput" "server/LunarCore/resources/Config/LevelOutput" && '
        'rmdir /s /q "server/LunarCore/resources/Config/Config"'
    )
    DOWNLOAD_COMMANDS_FIDDLER = (
        "https://github.com/Letheriver2007/Firefly-Launcher-Res.git tool/fiddler"
    )

    DOWNLOAD_COMMANDS_AUDIO_MIRROR = (
        "https://gitee.com/letheriver2007/Firefly-Launcher-Res.git src/audio"
    )
    DOWNLOAD_COMMANDS_GIT_MIRROR = "https://cdn.npmmirror.com/binaries/git-for-windows/v2.44.0.windows.1/Git-2.44.0-64-bit.exe"
    DOWNLOAD_COMMANDS_JAVA_MIRROR = (
        "https://d6.injdk.cn/oraclejdk/17/jdk-17_windows-x64_bin.msi"
    )
    DOWNLOAD_COMMANDS_MONGODB_INSTALLER_MIRROR = (
        "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.6-signed.msi"
    )
    DOWNLOAD_COMMANDS_MONGODB_PORTABLE_MIRROR = (
        "https://gitee.com/letheriver2007/Firefly-Launcher-Res.git tool/mongodb"
    )
    DOWNLOAD_COMMANDS_LUNARCORE_MIRROR = (
        "https://gitee.com/kenny-pk/LunarCore.git server/LunarCore"
    )
    DOWNLOAD_COMMANDS_LUNARCORE_RES_MIRROR = "https://gitee.com/Letheriver2007/Firefly-Launcher-Res.git server/LunarCore/resources"
    DOWNLOAD_COMMANDS_FIDDLER_MIRROR = (
        "https://gitee.com/Letheriver2007/Firefly-Launcher-Res.git tool/fiddler"
    )

    ############### SERVER CONFIG ###############
    SERVER = get_json("./config/config.json", "SERVER")


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load("./config/auto.json", cfg)
