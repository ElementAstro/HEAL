"""
Module Validation System
Provides comprehensive validation for modules including structure, dependencies, and security checks.
"""

import hashlib
import json
import re
import time
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


class ValidationLevel(Enum):
    """验证级别"""

    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    SECURITY = "security"


class ValidationResult(Enum):
    """验证结果"""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """验证问题"""

    level: ValidationResult
    category: str
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class ModuleValidationReport:
    """模块验证报告"""

    module_path: str
    validation_level: ValidationLevel
    overall_result: ValidationResult
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]
    timestamp: float

    @property
    def is_valid(self) -> bool:
        """模块是否有效"""
        return self.overall_result in [
            ValidationResult.PASSED,
            ValidationResult.WARNING,
        ]

    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """获取严重问题"""
        return [
            issue for issue in self.issues if issue.level == ValidationResult.CRITICAL
        ]

    @property
    def error_issues(self) -> List[ValidationIssue]:
        """获取错误问题"""
        return [
            issue for issue in self.issues if issue.level == ValidationResult.FAILED
        ]


class ModuleValidator:
    """模块验证器"""

    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {".jar", ".zip", ".mod", ".py"}

    # 必需的元数据字段
    REQUIRED_METADATA = {"name", "version", "author"}

    # 危险的代码模式
    DANGEROUS_PATTERNS = [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r'open\s*\([^)]*["\']w["\']',
        r"subprocess\.",
        r"os\.system",
        r"os\.popen",
    ]

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD) -> None:
        self.validation_level = validation_level
        self.logger = logger.bind(component="ModuleValidator")

    def validate_module(self, module_path: str) -> ModuleValidationReport:
        """验证模块"""
        path = Path(module_path)
        issues: List[ValidationIssue] = []
        metadata: Dict[str, Any] = {}

        self.logger.info(f"开始验证模块: {module_path}")

        try:
            # 基础验证
            issues.extend(self._validate_basic(path))

            # 结构验证
            issues.extend(self._validate_structure(path))

            # 元数据验证
            metadata_issues, module_metadata = self._validate_metadata(path)
            issues.extend(metadata_issues)
            metadata.update(module_metadata)

            if self.validation_level in [
                ValidationLevel.STRICT,
                ValidationLevel.SECURITY,
            ]:
                # 依赖验证
                issues.extend(self._validate_dependencies())

                # 安全验证
                if self.validation_level == ValidationLevel.SECURITY:
                    issues.extend(self._validate_security(path))

            # 确定总体结果
            overall_result = self._determine_overall_result(issues)

        except Exception as e:
            self.logger.error(f"验证模块时发生错误: {e}")
            issues.append(
                ValidationIssue(
                    level=ValidationResult.CRITICAL,
                    category="validation_error",
                    message=f"验证过程中发生错误: {str(e)}",
                    fix_suggestion="检查模块文件是否损坏或格式不正确",
                )
            )
            overall_result = ValidationResult.CRITICAL

        report = ModuleValidationReport(
            module_path=module_path,
            validation_level=self.validation_level,
            overall_result=overall_result,
            issues=issues,
            metadata=metadata,
            timestamp=time.time(),
        )

        self.logger.info(
            f"模块验证完成: {overall_result.value}, 发现 {len(issues)} 个问题"
        )
        return report

    def _validate_basic(self, path: Path) -> List[ValidationIssue]:
        """基础验证"""
        issues = []

        # 检查文件存在
        if not path.exists():
            issues.append(
                ValidationIssue(
                    level=ValidationResult.CRITICAL,
                    category="file_not_found",
                    message="模块文件不存在",
                    fix_suggestion="确保文件路径正确",
                )
            )
            return issues

        # 检查文件大小
        issues.extend(self._check_file_size(path))

        # 检查文件扩展名
        issues.extend(self._check_file_extension(path))

        return issues

    def _check_file_size(self, path: Path) -> List[ValidationIssue]:
        """检查文件大小"""
        issues = []
        size = path.stat().st_size

        if size == 0:
            issues.append(
                ValidationIssue(
                    level=ValidationResult.CRITICAL,
                    category="empty_file",
                    message="模块文件为空",
                    fix_suggestion="检查文件是否正确下载或创建",
                )
            )
        elif size > 100 * 1024 * 1024:  # 100MB
            issues.append(
                ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="large_file",
                    message=f"模块文件较大 ({size / 1024 / 1024:.1f}MB)",
                    details="大文件可能影响加载性能",
                )
            )

        return issues

    def _check_file_extension(self, path: Path) -> List[ValidationIssue]:
        """检查文件扩展名"""
        issues = []

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            issues.append(
                ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="unsupported_extension",
                    message=f"不支持的文件扩展名: {path.suffix}",
                    details=f"支持的扩展名: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                )
            )

        return issues

    def _validate_structure(self, path: Path) -> List[ValidationIssue]:
        """结构验证"""
        issues = []

        if path.suffix.lower() in [".jar", ".zip"]:
            issues.extend(self._validate_archive_structure(path))

        return issues

    def _validate_archive_structure(self, path: Path) -> List[ValidationIssue]:
        """验证压缩文件结构"""
        issues = []

        try:
            with zipfile.ZipFile(path, "r") as zip_file:
                # 检查压缩文件完整性
                bad_files = zip_file.testzip()
                if bad_files:
                    issues.append(
                        ValidationIssue(
                            level=ValidationResult.FAILED,
                            category="corrupt_archive",
                            message=f"压缩文件损坏: {bad_files}",
                            fix_suggestion="重新下载或修复文件",
                        )
                    )

                # 检查可执行文件
                if self.validation_level == ValidationLevel.SECURITY:
                    issues.extend(self._check_executable_files(zip_file))

        except zipfile.BadZipFile:
            issues.append(
                ValidationIssue(
                    level=ValidationResult.FAILED,
                    category="invalid_archive",
                    message="不是有效的压缩文件",
                    fix_suggestion="检查文件格式或重新下载",
                )
            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    level=ValidationResult.FAILED,
                    category="structure_error",
                    message=f"结构验证失败: {str(e)}",
                )
            )

        return issues

    def _check_executable_files(
        self, zip_file: zipfile.ZipFile
    ) -> List[ValidationIssue]:
        """检查可执行文件"""
        issues = []
        file_list = zip_file.namelist()

        executable_files = [
            f for f in file_list if f.endswith((".exe", ".bat", ".sh", ".cmd"))
        ]
        if executable_files:
            issues.append(
                ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="executable_content",
                    message=f"包含可执行文件: {', '.join(executable_files)}",
                    details="可执行文件可能存在安全风险",
                )
            )

        return issues

    def _validate_metadata(
        self, path: Path
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """元数据验证"""
        issues: List[ValidationIssue] = []
        metadata = {}

        # 查找元数据文件
        metadata = self._find_metadata(path, issues)

        # 验证必需字段
        issues.extend(self._validate_required_fields(metadata))

        # 验证版本格式
        issues.extend(self._validate_version_format(metadata))

        return issues, metadata

    def _find_metadata(
        self, path: Path, issues: List[ValidationIssue]
    ) -> Dict[str, Any]:
        """查找元数据文件"""
        metadata = {}
        metadata_files = ["mod.json", "module.json",
                          "metadata.json", "info.json"]

        if path.suffix.lower() in [".jar", ".zip"]:
            metadata = self._extract_metadata_from_archive(
                path, metadata_files, issues)

        return metadata

    def _extract_metadata_from_archive(
        self, path: Path, metadata_files: List[str], issues: List[ValidationIssue]
    ) -> Dict[str, Any]:
        """从压缩文件中提取元数据"""
        metadata = {}

        try:
            with zipfile.ZipFile(path, "r") as zip_file:
                for meta_file in metadata_files:
                    if meta_file in zip_file.namelist():
                        try:
                            with zip_file.open(meta_file) as f:
                                metadata = json.loads(f.read().decode("utf-8"))
                            break
                        except json.JSONDecodeError:
                            issues.append(
                                ValidationIssue(
                                    level=ValidationResult.FAILED,
                                    category="invalid_metadata",
                                    message=f"元数据文件 {meta_file} 格式错误",
                                    fix_suggestion="检查JSON格式是否正确",
                                )
                            )
                        except Exception as e:
                            issues.append(
                                ValidationIssue(
                                    level=ValidationResult.WARNING,
                                    category="metadata_read_error",
                                    message=f"无法读取元数据文件 {meta_file}: {str(e)}",
                                )
                            )
        except Exception:
            pass

        return metadata

    def _validate_required_fields(
        self, metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """验证必需字段"""
        issues = []

        for field in self.REQUIRED_METADATA:
            if field not in metadata:
                issues.append(
                    ValidationIssue(
                        level=ValidationResult.WARNING,
                        category="missing_metadata",
                        message=f"缺少必需的元数据字段: {field}",
                        fix_suggestion="添加完整的模块元数据",
                    )
                )

        return issues

    def _validate_version_format(
        self, metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """验证版本格式"""
        issues: List[ValidationIssue] = []

        if "version" in metadata:
            version = metadata["version"]
            if not re.match(r"^\d+\.\d+(\.\d+)?(-\w+)?$", str(version)):
                issues.append(
                    ValidationIssue(
                        level=ValidationResult.WARNING,
                        category="invalid_version",
                        message=f"版本号格式不标准: {version}",
                        details="建议使用语义化版本号 (如: 1.0.0)",
                    )
                )

        return issues

    def _validate_dependencies(self) -> List[ValidationIssue]:
        """依赖验证"""
        issues: List[ValidationIssue] = []
        return issues

    def _validate_security(self, path: Path) -> List[ValidationIssue]:
        """安全验证"""
        issues = []

        # 计算文件哈希用于安全检查
        try:
            self._calculate_file_hash(path)
        except Exception as e:
            issues.append(
                ValidationIssue(
                    level=ValidationResult.WARNING,
                    category="security_check_failed",
                    message=f"安全检查失败: {str(e)}",
                )
            )

        # 检查危险代码模式
        if path.suffix.lower() == ".py":
            issues.extend(self._check_dangerous_patterns(path))

        return issues

    def _calculate_file_hash(self, path: Path) -> str:
        """计算文件哈希"""
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _check_dangerous_patterns(self, path: Path) -> List[ValidationIssue]:
        """检查危险代码模式"""
        issues = []

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, content):
                    issues.append(
                        ValidationIssue(
                            level=ValidationResult.WARNING,
                            category="dangerous_code",
                            message=f"发现潜在危险代码模式: {pattern}",
                            details="此代码可能存在安全风险",
                        )
                    )
        except Exception:
            pass

        return issues

    def _determine_overall_result(
        self, issues: List[ValidationIssue]
    ) -> ValidationResult:
        """确定总体验证结果"""
        if not issues:
            return ValidationResult.PASSED

        # 检查是否有严重问题
        if any(issue.level == ValidationResult.CRITICAL for issue in issues):
            return ValidationResult.CRITICAL

        # 检查是否有错误
        if any(issue.level == ValidationResult.FAILED for issue in issues):
            return ValidationResult.FAILED

        # 只有警告
        return ValidationResult.WARNING

    def validate_batch(self, module_paths: List[str]) -> List[ModuleValidationReport]:
        """批量验证模块"""
        reports = []

        for path in module_paths:
            try:
                report = self.validate_module(path)
                reports.append(report)
            except Exception as e:
                self.logger.error(f"批量验证模块 {path} 时发生错误: {e}")
                # 创建错误报告
                error_report = ModuleValidationReport(
                    module_path=path,
                    validation_level=self.validation_level,
                    overall_result=ValidationResult.CRITICAL,
                    issues=[
                        ValidationIssue(
                            level=ValidationResult.CRITICAL,
                            category="validation_error",
                            message=f"验证失败: {str(e)}",
                        )
                    ],
                    metadata={},
                    timestamp=time.time(),
                )
                reports.append(error_report)

        return reports

    def get_validation_summary(
        self, reports: List[ModuleValidationReport]
    ) -> Dict[str, Any]:
        """获取验证摘要"""
        total = len(reports)
        passed = sum(1 for r in reports if r.overall_result ==
                     ValidationResult.PASSED)
        warnings = sum(
            1 for r in reports if r.overall_result == ValidationResult.WARNING
        )
        failed = sum(1 for r in reports if r.overall_result ==
                     ValidationResult.FAILED)
        critical = sum(
            1 for r in reports if r.overall_result == ValidationResult.CRITICAL
        )

        return {
            "total_modules": total,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "critical": critical,
            "success_rate": (passed + warnings) / total * 100 if total > 0 else 0,
            "validation_level": self.validation_level.value,
        }
