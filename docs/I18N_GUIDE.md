# HEAL 国际化指南

本指南介绍如何在 HEAL 项目中使用和维护国际化功能。

## 概述

HEAL 项目支持多语言国际化，目前支持：
- 英文 (en_US)
- 简体中文 (zh_CN)
- 繁体中文 (zh_TW)

## 核心组件

### 1. 翻译管理器 (`app/common/i18n.py`)
- 管理所有翻译文件
- 提供翻译函数 `tr()` 和 `t()`
- 支持语言切换和动态更新

### 2. UI国际化工具 (`app/common/i18n_ui.py`)
- 为UI组件提供国际化支持
- 自动响应语言切换
- 提供便捷的创建函数

### 3. 国际化更新器 (`app/common/i18n_updater.py`)
- 管理语言切换时的UI更新
- 提供混入类和装饰器
- 确保所有组件同步更新

## 使用方法

### 基本翻译

```python
from app.common.i18n import tr, t

# 基本翻译
text = tr("hello")  # 或 t("hello")

# 带参数的翻译
text = tr("welcome_user", username="John")

# 带默认值的翻译
text = tr("unknown_key", default="Default Text")
```

### UI组件国际化

```python
from app.common.i18n_ui import setup_component_i18n, tr_button, tr_label

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 设置国际化支持
        self.i18n = setup_component_i18n(self)
        
        # 注册窗口标题
        self.i18n.register_window_title("my_widget.title")
        
        # 创建已翻译的按钮
        self.ok_btn = tr_button("ok", primary=True)
        self.cancel_btn = tr_button("cancel")
        
        # 创建已翻译的标签
        self.title_label = tr_label("my_widget.title", "title")
        
        # 注册需要更新的元素
        self.i18n.register_text(self.title_label, "my_widget.title")
```

### 便捷函数

```python
from app.common.i18n_ui import (
    tr_ok, tr_cancel, tr_save, tr_load,
    tr_start, tr_stop, tr_success, tr_error
)

# 使用预定义的常用翻译
ok_text = tr_ok()
cancel_text = tr_cancel()
```

### 自动国际化支持

```python
from app.common.i18n_updater import i18n_aware, register_for_i18n_updates

@i18n_aware
class MyWidget(QWidget):
    def setup_i18n(self):
        """设置国际化支持"""
        self.setWindowTitle(tr("my_widget.title"))
        
    def update_i18n(self, language):
        """语言切换时的更新"""
        self.setWindowTitle(tr("my_widget.title"))
```

## 翻译文件结构

翻译文件位于 `src/data/translations/` 目录：

```
src/data/translations/
├── en_US.json    # 英文翻译
├── zh_CN.json    # 简体中文翻译
└── zh_TW.json    # 繁体中文翻译
```

### 翻译文件格式

```json
{
  "app_name": "HEAL - Hello ElementAstro Launcher",
  "welcome": "Welcome to HEAL",
  "ok": "OK",
  "cancel": "Cancel",
  
  "scaffold": {
    "title": "Module Scaffold Generator",
    "welcome": "Welcome to the Module Scaffold Generator",
    "next": "Next",
    "previous": "Previous"
  },
  
  "process_monitor": {
    "title": "Process Monitor",
    "refresh_status": "Refresh Status",
    "start_all": "Start All",
    "stop_all": "Stop All"
  }
}
```

## 添加新翻译

### 1. 在代码中使用翻译键

```python
# 使用新的翻译键
button = PushButton(tr("my_module.new_button"))
```

### 2. 在翻译文件中添加翻译

在所有语言的翻译文件中添加对应的翻译：

**en_US.json:**
```json
{
  "my_module": {
    "new_button": "New Button"
  }
}
```

**zh_CN.json:**
```json
{
  "my_module": {
    "new_button": "新按钮"
  }
}
```

**zh_TW.json:**
```json
{
  "my_module": {
    "new_button": "新按鈕"
  }
}
```

## 工具和检查

### 国际化检查工具

运行检查工具来发现缺失的翻译：

```bash
python tools/i18n_checker.py
```

这个工具会：
- 扫描所有Python文件中的翻译键
- 检查缺失的翻译
- 检查未使用的翻译
- 生成缺失翻译的模板文件

### 国际化测试

运行测试脚本来验证国际化功能：

```bash
python test_i18n.py
```

## 最佳实践

### 1. 翻译键命名规范

- 使用模块名作为前缀：`module_name.key`
- 使用描述性的键名：`process_monitor.start_all`
- 避免使用数字开头的键名

### 2. 组织翻译

- 按功能模块组织翻译键
- 使用嵌套结构避免键名冲突
- 保持翻译文件的一致性

### 3. 参数化翻译

```python
# 好的做法
tr("welcome_user", username=user.name)

# 翻译文件中
"welcome_user": "Welcome, {username}!"
```

### 4. 默认值

```python
# 为新功能提供默认值
tr("new_feature.title", default="New Feature")
```

## 语言切换

### 程序化切换

```python
from app.common.i18n import set_language, Language

# 切换到中文
set_language(Language.CHINESE_SIMPLIFIED)

# 切换到英文
set_language(Language.ENGLISH)
```

### 响应语言切换

```python
from app.common.i18n import translation_manager

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 连接语言变化信号
        translation_manager.language_changed.connect(self.on_language_changed)
        
    def on_language_changed(self, language):
        """语言变化时的处理"""
        self.update_ui_texts()
```

## 故障排除

### 常见问题

1. **翻译不显示**
   - 检查翻译键是否正确
   - 确认翻译文件中存在对应的翻译
   - 检查文件编码是否为UTF-8

2. **语言切换不生效**
   - 确认组件已注册到国际化系统
   - 检查是否连接了语言变化信号
   - 验证翻译文件是否正确加载

3. **缺失翻译**
   - 运行 `python tools/i18n_checker.py` 检查
   - 查看生成的模板文件
   - 添加缺失的翻译项

### 调试技巧

```python
# 启用调试日志
import logging
logging.getLogger('i18n').setLevel(logging.DEBUG)

# 检查当前语言
from app.common.i18n import get_current_language
print(f"Current language: {get_current_language()}")

# 强制重新加载翻译
from app.common.i18n import translation_manager
translation_manager.reload_translations()
```

## 贡献指南

当添加新功能时：

1. 使用翻译函数而不是硬编码文本
2. 为所有支持的语言添加翻译
3. 运行国际化检查工具
4. 测试语言切换功能
5. 更新相关文档

## 参考资料

- [PySide6 国际化文档](https://doc.qt.io/qtforpython/tutorials/basictutorial/translations.html)
- [Qt 翻译系统](https://doc.qt.io/qt-6/internationalization.html)
- [Python gettext 模块](https://docs.python.org/3/library/gettext.html)
