import json
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PySide6.QtCore import QCoreApplication, QObject, QTranslator, Signal

from src.heal.resources import resource_manager

from .logging_config import get_logger

# 使用统一日志配置
logger = get_logger("i18n")


class Language(Enum):
    """支持的语言"""

    ENGLISH = "en_US"
    CHINESE_SIMPLIFIED = "zh_CN"
    CHINESE_TRADITIONAL = "zh_TW"


class TranslationManager(QObject):
    """翻译管理器"""

    language_changed = Signal(Language)

    def __init__(self) -> None:
        super().__init__()
        self.current_language = Language.ENGLISH  # 默认英文
        self.translations: Dict[Language, Dict[str, Any]] = {}
        self.translation_dir = Path(
            str(resource_manager.get_resource_path("data", "translations"))
        )
        self.translation_dir.mkdir(parents=True, exist_ok=True)
        self.translators: List[QTranslator] = []

        # 加载所有翻译文件
        self._load_translations()

        # 创建默认翻译文件
        self._create_default_translations()

    def _load_translations(self) -> None:
        """加载所有翻译文件"""
        try:
            for lang in Language:
                translation_file = self.translation_dir / f"{lang.value}.json"
                if translation_file.exists():
                    with translation_file.open("r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                        logger.info(f"已加载语言文件: {lang.value}")
                else:
                    logger.warning(f"语言文件不存在: {translation_file}")
                    self.translations[lang] = {}
        except Exception as e:
            logger.error(f"加载翻译文件失败: {e}")

    def _create_default_translations(self) -> None:
        """创建默认翻译文件"""
        # 英文翻译（默认）
        english_translations = {
            # 通用界面文本
            "app_name": "HEAL - Hello ElementAstro Launcher",
            "welcome": "Welcome to HEAL",
            "settings": "Settings",
            "download": "Download",
            "environment": "Environment",
            "tools": "Tools",
            "home": "Home",
            "launcher": "Launcher",
            "modules": "Modules",
            "proxy": "Proxy",
            # 按钮和操作
            "ok": "OK",
            "cancel": "Cancel",
            "apply": "Apply",
            "save": "Save",
            "load": "Load",
            "refresh": "Refresh",
            "restart": "Restart",
            "start": "Start",
            "stop": "Stop",
            "pause": "Pause",
            "resume": "Resume",
            "retry": "Retry",
            "browse": "Browse",
            "search": "Search",
            "clear": "Clear",
            "reset": "Reset",
            "export": "Export",
            "import": "Import",
            "copy": "Copy",
            "paste": "Paste",
            "delete": "Delete",
            "edit": "Edit",
            "add": "Add",
            "remove": "Remove",
            # 状态和消息
            "success": "Success",
            "error": "Error",
            "warning": "Warning",
            "info": "Information",
            "loading": "Loading...",
            "connecting": "Connecting...",
            "connected": "Connected",
            "disconnected": "Disconnected",
            "downloading": "Downloading...",
            "download_complete": "Download Complete",
            "download_failed": "Download Failed",
            "installation_complete": "Installation Complete",
            "installation_failed": "Installation Failed",
            "configuration_saved": "Configuration Saved",
            "configuration_loaded": "Configuration Loaded",
            "operation_cancelled": "Operation Cancelled",
            # 错误消息
            "file_not_found": "File not found",
            "network_error": "Network error",
            "permission_denied": "Permission denied",
            "invalid_input": "Invalid input",
            "operation_failed": "Operation failed",
            "timeout_error": "Timeout error",
            "unknown_error": "Unknown error",
            # 设置相关
            "theme": "Theme",
            "language": "Language",
            "auto_copy": "Auto Copy Commands",
            "use_login": "Enable Login",
            "use_audio": "Enable Audio",
            "proxy_settings": "Proxy Settings",
            "china_mirror": "China Mirror",
            "proxy_port": "Proxy Port",
            "current_port": "Current Port",
            # 下载相关
            "download_url": "Download URL",
            "mirror_url": "Mirror URL",
            "git_clone": "Git Clone",
            "file_download": "File Download",
            "download_directory": "Download Directory",
            "download_progress": "Download Progress",
            # 环境相关
            "environment_setup": "Environment Setup",
            "database_setup": "Database Setup",
            "server_setup": "Server Setup",
            "mongodb_start": "Start MongoDB",
            "mongodb_stop": "Stop MongoDB",
            "server_status": "Server Status",
            # 工具相关
            "nginx_config": "Nginx Configuration",
            "command_center": "Command Center",
            "telescope_catalog": "Telescope Catalog",
            "log_monitor": "Log Monitor",
            # 登录相关
            "login": "Login",
            "logout": "Logout",
            "password": "Password",
            "login_success": "Login Successful",
            "login_failed": "Login Failed",
            "password_incorrect": "Password Incorrect",
            "attempt_count": "Attempt Count",
            # 日志相关
            "log_file": "Log File",
            "view_logs": "View Logs",
            "clear_logs": "Clear Logs",
            "log_level": "Log Level",
            "debug_mode": "Debug Mode",
            # 更新相关
            "check_update": "Check for Updates",
            "update_available": "Update Available",
            "no_updates": "No Updates Available",
            "downloading_update": "Downloading Update...",
            "update_complete": "Update Complete",
            "update_failed": "Update Failed",
            # 模块相关
            "module_manager": "Module Manager",
            "install_module": "Install Module",
            "uninstall_module": "Uninstall Module",
            "module_info": "Module Information",
            "module_settings": "Module Settings",
            # 系统相关
            "system_info": "System Information",
            "performance_monitor": "Performance Monitor",
            "resource_usage": "Resource Usage",
            "memory_usage": "Memory Usage",
            "cpu_usage": "CPU Usage",
            "disk_usage": "Disk Usage",
            # 网络相关
            "network_status": "Network Status",
            "connection_test": "Connection Test",
            "ping_test": "Ping Test",
            "speed_test": "Speed Test",
        }

        # 中文简体翻译
        chinese_simplified_translations = {
            # 通用界面文本
            "app_name": "HEAL - 元素天体启动器",
            "welcome": "欢迎使用 HEAL",
            "settings": "设置",
            "download": "下载",
            "environment": "环境",
            "tools": "工具",
            "home": "主页",
            "launcher": "启动器",
            "modules": "模块",
            "proxy": "代理",
            # 按钮和操作
            "ok": "确定",
            "cancel": "取消",
            "apply": "应用",
            "save": "保存",
            "load": "加载",
            "refresh": "刷新",
            "restart": "重启",
            "start": "开始",
            "stop": "停止",
            "pause": "暂停",
            "resume": "继续",
            "retry": "重试",
            "browse": "浏览",
            "search": "搜索",
            "clear": "清除",
            "reset": "重置",
            "export": "导出",
            "import": "导入",
            "copy": "复制",
            "paste": "粘贴",
            "delete": "删除",
            "edit": "编辑",
            "add": "添加",
            "remove": "移除",
            # 状态和消息
            "success": "成功",
            "error": "错误",
            "warning": "警告",
            "info": "信息",
            "loading": "加载中...",
            "connecting": "连接中...",
            "connected": "已连接",
            "disconnected": "已断开",
            "downloading": "下载中...",
            "download_complete": "下载完成",
            "download_failed": "下载失败",
            "installation_complete": "安装完成",
            "installation_failed": "安装失败",
            "configuration_saved": "配置已保存",
            "configuration_loaded": "配置已加载",
            "operation_cancelled": "操作已取消",
            # 错误消息
            "file_not_found": "文件未找到",
            "network_error": "网络错误",
            "permission_denied": "权限被拒绝",
            "invalid_input": "无效输入",
            "operation_failed": "操作失败",
            "timeout_error": "超时错误",
            "unknown_error": "未知错误",
            # 设置相关
            "theme": "主题",
            "language": "语言",
            "auto_copy": "自动复制命令",
            "use_login": "启用登录",
            "use_audio": "启用音频",
            "proxy_settings": "代理设置",
            "china_mirror": "国内镜像",
            "proxy_port": "代理端口",
            "current_port": "当前端口",
            # 下载相关
            "download_url": "下载链接",
            "mirror_url": "镜像链接",
            "git_clone": "Git克隆",
            "file_download": "文件下载",
            "download_directory": "下载目录",
            "download_progress": "下载进度",
            # 环境相关
            "environment_setup": "环境设置",
            "database_setup": "数据库设置",
            "server_setup": "服务器设置",
            "mongodb_start": "启动 MongoDB",
            "mongodb_stop": "停止 MongoDB",
            "server_status": "服务器状态",
            # 工具相关
            "nginx_config": "Nginx 配置",
            "command_center": "命令中心",
            "telescope_catalog": "望远镜分类",
            "log_monitor": "日志监控",
            # 登录相关
            "login": "登录",
            "logout": "登出",
            "password": "密码",
            "login_success": "登录成功",
            "login_failed": "登录失败",
            "password_incorrect": "密码错误",
            "attempt_count": "尝试次数",
            # 日志相关
            "log_file": "日志文件",
            "view_logs": "查看日志",
            "clear_logs": "清除日志",
            "log_level": "日志级别",
            "debug_mode": "调试模式",
            # 更新相关
            "check_update": "检查更新",
            "update_available": "有可用更新",
            "no_updates": "无可用更新",
            "downloading_update": "下载更新中...",
            "update_complete": "更新完成",
            "update_failed": "更新失败",
            # 模块相关
            "module_manager": "模块管理器",
            "install_module": "安装模块",
            "uninstall_module": "卸载模块",
            "module_info": "模块信息",
            "module_settings": "模块设置",
            # 系统相关
            "system_info": "系统信息",
            "performance_monitor": "性能监控",
            "resource_usage": "资源使用",
            "memory_usage": "内存使用",
            "cpu_usage": "CPU使用",
            "disk_usage": "磁盘使用",
            # 网络相关
            "network_status": "网络状态",
            "connection_test": "连接测试",
            "ping_test": "Ping测试",
            "speed_test": "速度测试",
        }

        # 中文繁体翻译
        chinese_traditional_translations = {
            # 通用界面文本
            "app_name": "HEAL - 元素天體啟動器",
            "welcome": "歡迎使用 HEAL",
            "settings": "設置",
            "download": "下載",
            "environment": "環境",
            "tools": "工具",
            "home": "主頁",
            "launcher": "啟動器",
            "modules": "模組",
            "proxy": "代理",
            # 按钮和操作
            "ok": "確定",
            "cancel": "取消",
            "apply": "應用",
            "save": "保存",
            "load": "加載",
            "refresh": "刷新",
            "restart": "重啟",
            "start": "開始",
            "stop": "停止",
            "pause": "暫停",
            "resume": "繼續",
            "retry": "重試",
            "browse": "瀏覽",
            "search": "搜索",
            "clear": "清除",
            "reset": "重置",
            "export": "導出",
            "import": "導入",
            "copy": "複製",
            "paste": "粘貼",
            "delete": "刪除",
            "edit": "編輯",
            "add": "添加",
            "remove": "移除",
            # ... 其他翻译项目
        }

        # 保存默认翻译文件
        self._save_translation_file(Language.ENGLISH, english_translations)
        self._save_translation_file(
            Language.CHINESE_SIMPLIFIED, chinese_simplified_translations
        )
        self._save_translation_file(
            Language.CHINESE_TRADITIONAL, chinese_traditional_translations
        )

    def _save_translation_file(self, language: Language, translations: Dict[str, str]) -> None:
        """保存翻译文件"""
        try:
            translation_file = self.translation_dir / f"{language.value}.json"
            # 如果文件已存在，合并翻译
            if translation_file.exists():
                with translation_file.open("r", encoding="utf-8") as f:
                    existing_translations = json.load(f)
                # 合并新翻译，保留现有翻译
                for key, value in translations.items():
                    if key not in existing_translations:
                        existing_translations[key] = value
                translations = existing_translations

            with translation_file.open("w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)

            self.translations[language] = translations
            logger.info(f"已保存语言文件: {language.value}")
        except Exception as e:
            logger.error(f"保存翻译文件失败 {language.value}: {e}")

    def set_language(self, language: Language) -> None:
        """设置当前语言"""
        if language != self.current_language:
            self.current_language = language
            self.language_changed.emit(language)
            logger.info(f"语言已切换到: {language.value}")

    @lru_cache(maxsize=1024)
    def translate(self, key: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """翻译文本"""
        try:
            # 获取当前语言的翻译
            translations = self.translations.get(self.current_language, {})

            # 如果当前语言没有翻译，尝试使用英文
            if key not in translations and self.current_language != Language.ENGLISH:
                translations = self.translations.get(Language.ENGLISH, {})

            # 获取翻译文本
            text = translations.get(key, default or key)

            # 确保返回字符串类型
            if not isinstance(text, str):
                text = str(text)

            # 格式化文本（支持参数替换）
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"翻译文本格式化失败 '{key}': {e}")

            return text
        except Exception as e:
            logger.error(f"翻译失败 '{key}': {e}")
            return default or key

    def tr(self, key: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """翻译文本的简短方法"""
        return self.translate(key, default, **kwargs)

    def add_translation(self, language: Language, key: str, value: str) -> None:
        """添加单个翻译"""
        if language not in self.translations:
            self.translations[language] = {}

        self.translations[language][key] = value

        # 保存到文件
        translation_file = self.translation_dir / f"{language.value}.json"
        try:
            with translation_file.open("w", encoding="utf-8") as f:
                json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
            logger.debug(f"已添加翻译 {language.value}: {key} = {value}")
        except Exception as e:
            logger.error(f"保存翻译失败: {e}")

    def get_available_languages(self) -> List[Language]:
        """获取可用语言列表"""
        return list(self.translations.keys())

    def get_current_language(self) -> Language:
        """获取当前语言"""
        return self.current_language

    def reload_translations(self) -> None:
        """重新加载翻译文件"""
        self._load_translations()
        self.language_changed.emit(self.current_language)
        logger.info("翻译文件已重新加载")

    def load_qt_translations(self, app: QCoreApplication) -> None:
        """加载Qt翻译文件"""
        try:
            # 清理现有翻译器
            for translator in self.translators:
                app.removeTranslator(translator)
            self.translators.clear()

            # 加载Qt标准翻译
            qt_translator = QTranslator()
            qt_ts_file = f"qt_{self.current_language.value}"
            if qt_translator.load(qt_ts_file, ":/translations"):
                app.installTranslator(qt_translator)
                self.translators.append(qt_translator)
                logger.info(f"已加载Qt翻译: {qt_ts_file}")

            # 加载应用程序翻译
            app_translator = QTranslator()
            app_ts_file = f"heal_{self.current_language.value}"
            if app_translator.load(app_ts_file, ":/translations"):
                app.installTranslator(app_translator)
                self.translators.append(app_translator)
                logger.info(f"已加载应用翻译: {app_ts_file}")

        except Exception as e:
            logger.error(f"加载Qt翻译失败: {e}")


# 全局翻译管理器实例
translation_manager = TranslationManager()


def tr(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """全局翻译函数"""
    return translation_manager.translate(key, default, **kwargs)


# 简化的别名函数
def t(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """简化的翻译函数别名"""
    return tr(key, default, **kwargs)


def setup_i18n(language: Union[Language, str] = Language.ENGLISH) -> None:
    """初始化国际化系统"""
    set_language(language)
    logger.info(f"国际化系统已初始化，当前语言: {get_current_language().value}")


def set_language(language: Union[Language, str]) -> None:
    """设置全局语言"""
    if isinstance(language, str):
        try:
            language = Language(language)
        except ValueError:
            logger.warning(f"不支持的语言: {language}，使用默认语言")
            language = Language.ENGLISH

    translation_manager.set_language(language)


def get_current_language() -> Language:
    """获取当前语言"""
    return translation_manager.get_current_language()


def add_translation(language: Union[Language, str], key: str, value: str) -> None:
    """添加翻译"""
    if isinstance(language, str):
        try:
            language = Language(language)
        except ValueError:
            logger.warning(f"不支持的语言: {language}")
            return

    translation_manager.add_translation(language, key, value)
