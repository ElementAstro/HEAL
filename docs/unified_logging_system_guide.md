# 统一日志系统使用指南

## 概述

本项目已成功迁移到基于loguru的统一日志系统，并提供了完整的日志面板UI组件。新的日志系统提供了以下功能：

- 🚀 **基于loguru的高性能日志系统**
- 📊 **实时日志查看和监控**
- 🔍 **强大的日志过滤和搜索功能**
- 📤 **多格式日志导出（TXT、CSV、JSON）**
- 🔗 **关联ID追踪和性能监控**
- 🎯 **统一的日志面板界面**
- 🔧 **与现有组件的无缝集成**

## 快速开始

### 1. 基础日志记录

```python
from app.common.logging_config import get_logger

# 获取logger实例
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 2. 结构化日志

```python
from app.common.logging_config import log_download, log_network, log_exception

# 下载日志
log_download(
    "文件下载完成",
    file_name="example.zip",
    file_size=1024*1024,
    download_time=5.2,
    source_url="https://example.com/file.zip"
)

# 网络日志
log_network(
    "API请求",
    method="GET",
    url="/api/users",
    status_code=200,
    response_time=150
)

# 异常日志
try:
    risky_operation()
except Exception as e:
    log_exception(e, "操作失败", operation="risky_operation")
```

### 3. 性能监控

```python
from app.common.logging_config import log_performance

@log_performance("data_processing")
async def process_data(data):
    # 处理逻辑
    return result

# 或者用于同步函数
@log_performance("sync_operation")
def sync_operation():
    # 同步操作
    return result
```

### 4. 关联ID追踪

```python
from app.common.logging_config import with_correlation_id, get_logger

logger = get_logger(__name__)

def handle_user_request(user_id):
    with with_correlation_id() as cid:
        logger.info("开始处理用户请求", extra={"user_id": user_id})
        
        # 子操作1
        validate_user(user_id)
        
        # 子操作2
        load_user_data(user_id)
        
        logger.info("用户请求处理完成")
```

## 统一日志面板

### 创建日志界面

```python
from app.components.logging import create_log_interface

# 创建日志界面
log_interface = create_log_interface(parent_widget)

# 或者直接使用组件
from app.components.logging import LogPanel

log_panel = LogPanel(parent_widget)
```

### 集成到现有组件

现有的日志显示功能已自动集成到统一面板：

```python
from app.components.logging import (
    show_server_log, show_process_log, show_performance_log,
    show_download_log, show_network_log
)

# 显示服务器日志
show_server_log("my_server")

# 显示进程日志
show_process_log("my_process")

# 显示性能日志
show_performance_log("my_operation")

# 显示下载日志
show_download_log("download_123")

# 显示网络日志
show_network_log("GET")
```

## 日志文件结构

```
logs/
├── application.log     # 主应用日志
├── errors.log         # 错误专用日志
├── exceptions.log     # 异常专用日志（带完整堆栈）
├── performance.log    # 性能监控日志（JSON格式）
├── downloads.log      # 下载操作日志
├── network.log        # 网络请求日志
├── process_manager.log # 进程管理日志
└── archive/           # 归档目录
    └── 20250824_*.log # 按日期归档的旧日志
```

## 日志面板功能

### 1. 实时日志查看
- 多标签页显示不同类型的日志
- 语法高亮显示
- 自动滚动到最新日志
- 支持大文件加载优化

### 2. 日志过滤
- 按日志级别过滤（DEBUG、INFO、WARNING、ERROR、CRITICAL）
- 按时间范围过滤
- 按模块名过滤
- 关键词搜索
- 正则表达式搜索

### 3. 日志导出
- 导出为文本文件（.txt）
- 导出为CSV格式（.csv）
- 导出为JSON格式（.json）
- 支持压缩导出
- 应用过滤条件导出

### 4. 统计和监控
- 实时日志统计
- 系统健康状态监控
- 磁盘使用情况
- 性能指标展示

## 配置选项

日志系统的配置文件位于 `config/logging_config.json`：

```json
{
  "logging": {
    "features": {
      "correlation_tracking": {
        "enabled": true
      },
      "performance_monitoring": {
        "enabled": true,
        "threshold_slow_operation": 1.0
      },
      "structured_logging": {
        "enabled": true,
        "json_serialization": true
      }
    },
    "log_levels": {
      "console": "INFO",
      "file": "DEBUG",
      "error_file": "ERROR"
    }
  }
}
```

## 迁移指南

### 从标准库logging迁移

**旧代码：**
```python
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

logger.info("信息日志")
```

**新代码：**
```python
from app.common.logging_config import get_logger

logger = get_logger(__name__)
logger.info("信息日志")
```

### 现有组件集成

现有的日志显示组件已自动集成：

- `dialog_manager.show_log_dialog()` → 使用统一日志面板
- `process_monitor.show_process_log()` → 使用统一日志面板
- 其他日志显示功能 → 自动重定向到统一面板

## 最佳实践

### 1. 日志级别使用
- **DEBUG**: 详细的调试信息，仅在开发时使用
- **INFO**: 一般信息，记录程序正常运行状态
- **WARNING**: 警告信息，程序可以继续运行但需要注意
- **ERROR**: 错误信息，程序遇到错误但可以继续运行
- **CRITICAL**: 严重错误，程序可能无法继续运行

### 2. 结构化日志
使用专门的日志函数记录特定类型的事件：
```python
# 好的做法
log_download("下载完成", file_name="test.zip", file_size=1024)

# 避免这样做
logger.info("下载完成 test.zip 1024 bytes")
```

### 3. 异常处理
```python
try:
    risky_operation()
except Exception as e:
    log_exception(e, "操作失败", context="additional_info")
    # 继续处理或重新抛出异常
```

### 4. 性能监控
对重要的操作使用性能监控装饰器：
```python
@log_performance("critical_operation")
def critical_operation():
    # 重要操作
    pass
```

## 故障排除

### 常见问题

1. **日志文件过大**
   - 系统会自动轮转日志文件
   - 可以手动清理旧日志：`cleanup_logs()`

2. **日志面板无法显示**
   - 检查日志文件是否存在
   - 确认日志目录权限
   - 查看控制台错误信息

3. **性能问题**
   - 日志系统使用异步写入，性能影响最小
   - 可以调整日志级别减少输出量

### 健康检查

```python
from app.common.logging_config import health_check

health = health_check()
print(f"日志系统状态: {health['status']}")
```

### 日志统计

```python
from app.common.logging_config import get_log_stats

stats = get_log_stats()
print(f"日志统计: {stats}")
```

## 更新日志

### v2.0 (2025-08-24)
- ✅ 完全迁移到loguru
- ✅ 新增统一日志面板UI
- ✅ 集成现有日志组件
- ✅ 支持日志过滤和导出
- ✅ 添加性能监控和关联ID追踪
- ✅ 完善的测试覆盖

### v1.0 (之前)
- 基于标准库logging
- 分散的日志显示组件
- 基础的日志记录功能

---

如有问题或建议，请查看项目文档或联系开发团队。
