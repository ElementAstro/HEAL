"""
Module data models and enums
Contains core data structures for module management
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ModuleState(Enum):
    """模块状态枚举"""

    IDLE = "idle"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class ModuleMetrics:
    """模块性能指标"""

    load_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    operations_count: int = 0
    success_rate: float = 100.0


@dataclass
class ModuleConfig:
    """模块配置"""

    name: str
    enabled: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    max_retries: int = 3
    timeout: int = 10  # seconds
    validation_enabled: bool = True
    performance_monitoring: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)
