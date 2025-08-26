"""
UI国际化辅助工具
提供UI组件国际化支持和语言切换响应
"""

from typing import Any, Callable, Dict, List, Optional, Union

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTextEdit, QWidget
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    TextEdit,
    TitleLabel,
)

from .i18n import Language, tr, translation_manager
from .logging_config import get_logger

logger = get_logger(__name__)


class I18nWidget(QObject):
    """国际化Widget基类，为UI组件提供国际化支持"""

    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.widget = widget
        self.i18n_elements: Dict[str, Dict[str, Any]] = {}
        self.logger = logger.bind(widget=widget.__class__.__name__)

        # 连接语言变化信号
        translation_manager.language_changed.connect(self.on_language_changed)

    def register_element(
        self, element: QWidget, key: str, property_name: str = "text", **kwargs: Any
    ) -> None:
        """注册需要国际化的UI元素"""
        element_id = str(id(element))
        self.i18n_elements[element_id] = {
            "element": element,
            "key": key,
            "property": property_name,
            "kwargs": kwargs,
        }

        # 立即应用翻译
        self._apply_translation(element_id)

    def register_text(
        self, element: Union[QLabel, QPushButton, PushButton], key: str, **kwargs: Any
    ) -> None:
        """注册文本元素（标签、按钮等）"""
        self.register_element(element, key, "setText", **kwargs)

    def register_placeholder(
        self, element: Union[QLineEdit, LineEdit, TextEdit], key: str, **kwargs: Any
    ) -> None:
        """注册占位符文本"""
        self.register_element(element, key, "setPlaceholderText", **kwargs)

    def register_window_title(self, key: str, **kwargs) -> None:
        """注册窗口标题"""
        if hasattr(self.widget, "setWindowTitle"):
            self.register_element(self.widget, key, "setWindowTitle", **kwargs)

    def on_language_changed(self, language: Language) -> None:
        """语言变化时的响应"""
        self.logger.debug(f"语言切换到: {language.value}")
        for element_id in self.i18n_elements:
            self._apply_translation(element_id)

    def _apply_translation(self, element_id: str) -> None:
        """应用翻译到指定元素"""
        try:
            info = self.i18n_elements[element_id]
            element = info["element"]
            key = info["key"]
            property_name = info["property"]
            kwargs = info["kwargs"]

            # 获取翻译文本
            translated_text = tr(key, **kwargs)

            # 应用到元素
            if hasattr(element, property_name):
                getattr(element, property_name)(translated_text)
            else:
                self.logger.warning(f"元素 {element} 没有属性 {property_name}")

        except Exception as e:
            self.logger.error(f"应用翻译失败: {e}")


class I18nHelper:
    """国际化辅助工具类"""

    @staticmethod
    def setup_widget(widget: QWidget) -> I18nWidget:
        """为Widget设置国际化支持"""
        return I18nWidget(widget)

    @staticmethod
    def create_translated_button(key: str, icon: Any = None, **kwargs: Any) -> PushButton:
        """创建已翻译的按钮"""
        text = tr(key, **kwargs)
        if icon:
            return PushButton(icon, text)
        return PushButton(text)

    @staticmethod
    def create_translated_primary_button(
        key: str, icon: Any = None, **kwargs: Any
    ) -> PrimaryPushButton:
        """创建已翻译的主要按钮"""
        text = tr(key, **kwargs)
        if icon:
            return PrimaryPushButton(icon, text)
        return PrimaryPushButton(text)

    @staticmethod
    def create_translated_label(key: str, label_type: str = "body", **kwargs: Any) -> QLabel:
        """创建已翻译的标签"""
        text = tr(key, **kwargs)

        label_classes = {
            "title": TitleLabel,
            "subtitle": SubtitleLabel,
            "body": BodyLabel,
            "strong": StrongBodyLabel,
        }

        label_class = label_classes.get(label_type, BodyLabel)
        return label_class(text)

    @staticmethod
    def create_translated_line_edit(placeholder_key: str, **kwargs: Any) -> LineEdit:
        """创建已翻译占位符的输入框"""
        line_edit = LineEdit()
        placeholder_text = tr(placeholder_key, **kwargs)
        line_edit.setPlaceholderText(placeholder_text)
        return line_edit


def setup_component_i18n(widget: QWidget) -> I18nWidget:
    """为组件设置国际化支持的便捷函数"""
    return I18nHelper.setup_widget(widget)


def tr_button(
    key: str, icon: Any = None, primary: bool = False, **kwargs: Any
) -> Union[PushButton, PrimaryPushButton]:
    """创建翻译按钮的便捷函数"""
    if primary:
        return I18nHelper.create_translated_primary_button(key, icon, **kwargs)
    return I18nHelper.create_translated_button(key, icon, **kwargs)


def tr_label(key: str, label_type: str = "body", **kwargs: Any) -> QLabel:
    """创建翻译标签的便捷函数"""
    return I18nHelper.create_translated_label(key, label_type, **kwargs)


def tr_line_edit(placeholder_key: str, **kwargs: Any) -> LineEdit:
    """创建翻译输入框的便捷函数"""
    return I18nHelper.create_translated_line_edit(placeholder_key, **kwargs)


# 常用翻译键的便捷函数
def tr_ok() -> str:
    return tr("ok")


def tr_cancel() -> str:
    return tr("cancel")


def tr_save() -> str:
    return tr("save")


def tr_load() -> str:
    return tr("load")


def tr_refresh() -> str:
    return tr("refresh")


def tr_start() -> str:
    return tr("start")


def tr_stop() -> str:
    return tr("stop")


def tr_success() -> str:
    return tr("success")


def tr_error() -> str:
    return tr("error")


def tr_warning() -> str:
    return tr("warning")


# 为了兼容性，添加I18nUI别名
I18nUI = I18nWidget
