"""
国际化更新工具
确保语言切换时所有组件都能正确更新
"""

from typing import Dict, List, Set, WeakSet
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QObject, Signal

from app.common.i18n import translation_manager, Language
from app.common.logging_config import get_logger

logger = get_logger(__name__)


class I18nUpdater(QObject):
    """国际化更新器，管理所有需要更新的组件"""
    
    language_changed = Signal(Language)
    
    def __init__(self):
        super().__init__()
        self.registered_widgets: WeakSet[QWidget] = WeakSet()
        self.update_callbacks: List[callable] = []
        
        # 连接语言变化信号
        translation_manager.language_changed.connect(self.on_language_changed)
        
        self.logger = logger.bind(component="I18nUpdater")
        
    def register_widget(self, widget: QWidget):
        """注册需要更新的Widget"""
        self.registered_widgets.add(widget)
        self.logger.debug(f"注册Widget: {widget.__class__.__name__}")
        
    def register_callback(self, callback: callable):
        """注册更新回调函数"""
        self.update_callbacks.append(callback)
        self.logger.debug(f"注册回调函数: {callback.__name__}")
        
    def unregister_widget(self, widget: QWidget):
        """取消注册Widget"""
        self.registered_widgets.discard(widget)
        self.logger.debug(f"取消注册Widget: {widget.__class__.__name__}")
        
    def on_language_changed(self, language: Language):
        """语言变化时的处理"""
        self.logger.info(f"开始更新UI语言到: {language.value}")
        
        # 发出语言变化信号
        self.language_changed.emit(language)
        
        # 执行所有回调函数
        for callback in self.update_callbacks:
            try:
                callback(language)
                self.logger.debug(f"执行回调函数: {callback.__name__}")
            except Exception as e:
                self.logger.error(f"执行回调函数失败 {callback.__name__}: {e}")
        
        # 强制刷新所有注册的Widget
        self.refresh_all_widgets()
        
        self.logger.info("UI语言更新完成")
        
    def refresh_all_widgets(self):
        """刷新所有注册的Widget"""
        for widget in list(self.registered_widgets):
            try:
                if widget and not widget.isHidden():
                    widget.update()
                    widget.repaint()
                    self.logger.debug(f"刷新Widget: {widget.__class__.__name__}")
            except Exception as e:
                self.logger.error(f"刷新Widget失败 {widget.__class__.__name__}: {e}")
                
    def force_update_all(self):
        """强制更新所有组件"""
        current_language = translation_manager.get_current_language()
        self.on_language_changed(current_language)


# 全局更新器实例
i18n_updater = I18nUpdater()


def register_for_i18n_updates(widget: QWidget):
    """注册Widget以接收国际化更新"""
    i18n_updater.register_widget(widget)


def register_i18n_callback(callback: callable):
    """注册国际化更新回调"""
    i18n_updater.register_callback(callback)


def unregister_from_i18n_updates(widget: QWidget):
    """取消注册Widget"""
    i18n_updater.unregister_widget(widget)


def force_i18n_update():
    """强制执行国际化更新"""
    i18n_updater.force_update_all()


class I18nMixin:
    """国际化混入类，为组件提供自动国际化支持"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self, QWidget):
            register_for_i18n_updates(self)
            
    def setup_i18n(self):
        """设置国际化支持，子类应重写此方法"""
        pass
        
    def update_i18n(self, language: Language):
        """更新国际化，子类应重写此方法"""
        pass


def create_i18n_aware_widget(widget_class):
    """创建支持国际化的Widget类装饰器"""
    
    class I18nAwareWidget(widget_class, I18nMixin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setup_i18n()
            
            # 连接语言变化信号
            i18n_updater.language_changed.connect(self.update_i18n)
            
    return I18nAwareWidget


# 便捷装饰器
def i18n_aware(cls):
    """类装饰器，使类支持国际化"""
    return create_i18n_aware_widget(cls)


def auto_i18n_update(func):
    """方法装饰器，自动触发国际化更新"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        force_i18n_update()
        return result
    return wrapper
