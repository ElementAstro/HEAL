"""
Optimization Validator - 优化验证工具
验证性能优化的效果和正确性
"""

import gc
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import psutil

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceBenchmark:
    """性能基准测试结果"""
    name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """验证结果"""
    test_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    benchmark: Optional[PerformanceBenchmark] = None


class OptimizationValidator:
    """优化验证器"""
    
    def __init__(self) -> None:
        self.logger = logger.bind(component="OptimizationValidator")
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        self.validation_results: List[ValidationResult] = []
        
        # 性能基准阈值
        self.performance_thresholds = {
            "max_execution_time": 5.0,  # 5秒
            "max_memory_usage_mb": 100,  # 100MB
            "max_cpu_usage_percent": 80,  # 80%
            "min_cache_hit_ratio": 0.7,  # 70%
            "max_ui_response_time": 0.1,  # 100ms
        }
    
    def benchmark_function(
        self,
        name: str,
        func: Callable,
        *args: Any,
        iterations: int = 1,
        **kwargs: Any
    ) -> PerformanceBenchmark:
        """对函数进行性能基准测试"""
        self.logger.info(f"开始基准测试: {name}")
        
        # 准备测试环境
        gc.collect()  # 清理垃圾
        tracemalloc.start()
        
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()
        
        success = True
        error = None
        total_time = 0.0
        
        try:
            start_time = time.time()
            
            # 执行多次迭代
            for _ in range(iterations):
                result = func(*args, **kwargs)
            
            total_time = time.time() - start_time
            
        except Exception as e:
            success = False
            error = str(e)
            total_time = time.time() - start_time
            self.logger.error(f"基准测试失败 {name}: {e}")
        
        # 收集性能数据
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        benchmark = PerformanceBenchmark(
            name=name,
            execution_time=total_time / iterations,  # 平均执行时间
            memory_usage_mb=end_memory - start_memory,
            cpu_usage_percent=max(end_cpu - start_cpu, 0),
            success=success,
            error=error,
            metadata={
                "iterations": iterations,
                "peak_memory_mb": peak / 1024 / 1024,
                "total_execution_time": total_time,
            }
        )
        
        self.benchmarks[name] = benchmark
        self.logger.info(f"基准测试完成 {name}: {benchmark}")
        
        return benchmark
    
    def validate_performance_improvement(
        self, 
        test_name: str,
        before_benchmark: PerformanceBenchmark,
        after_benchmark: PerformanceBenchmark,
        min_improvement_percent: float = 10.0
    ) -> ValidationResult:
        """验证性能改进"""
        
        if not before_benchmark.success or not after_benchmark.success:
            return ValidationResult(
                test_name=test_name,
                passed=False,
                message="基准测试失败，无法验证性能改进",
                details={
                    "before_error": before_benchmark.error,
                    "after_error": after_benchmark.error
                }
            )
        
        # 计算改进百分比
        time_improvement = (
            (before_benchmark.execution_time - after_benchmark.execution_time) 
            / before_benchmark.execution_time * 100
        )
        
        memory_improvement = (
            (before_benchmark.memory_usage_mb - after_benchmark.memory_usage_mb) 
            / max(before_benchmark.memory_usage_mb, 0.1) * 100
        )
        
        passed = time_improvement >= min_improvement_percent
        
        result = ValidationResult(
            test_name=test_name,
            passed=passed,
            message=f"性能改进验证{'通过' if passed else '失败'}",
            details={
                "time_improvement_percent": time_improvement,
                "memory_improvement_percent": memory_improvement,
                "before_time": before_benchmark.execution_time,
                "after_time": after_benchmark.execution_time,
                "before_memory": before_benchmark.memory_usage_mb,
                "after_memory": after_benchmark.memory_usage_mb,
                "min_required_improvement": min_improvement_percent
            },
            benchmark=after_benchmark
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_memory_usage(self, test_name: str, benchmark: PerformanceBenchmark) -> ValidationResult:
        """验证内存使用"""
        max_memory = self.performance_thresholds["max_memory_usage_mb"]
        passed = benchmark.memory_usage_mb <= max_memory
        
        result = ValidationResult(
            test_name=test_name,
            passed=passed,
            message=f"内存使用验证{'通过' if passed else '失败'}",
            details={
                "actual_memory_mb": benchmark.memory_usage_mb,
                "max_allowed_mb": max_memory,
                "peak_memory_mb": benchmark.metadata.get("peak_memory_mb", 0)
            },
            benchmark=benchmark
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_execution_time(self, test_name: str, benchmark: PerformanceBenchmark) -> ValidationResult:
        """验证执行时间"""
        max_time = self.performance_thresholds["max_execution_time"]
        passed = benchmark.execution_time <= max_time
        
        result = ValidationResult(
            test_name=test_name,
            passed=passed,
            message=f"执行时间验证{'通过' if passed else '失败'}",
            details={
                "actual_time_s": benchmark.execution_time,
                "max_allowed_s": max_time,
                "total_time_s": benchmark.metadata.get("total_execution_time", 0)
            },
            benchmark=benchmark
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_cache_performance(self) -> ValidationResult:
        """验证缓存性能"""
        try:
            from .cache_manager import global_cache_manager
            
            total_hits = 0
            total_requests = 0
            
            for cache in global_cache_manager.caches.values():
                stats = cache.get_stats()
                total_hits += stats.get("hits", 0)
                total_requests += stats.get("hits", 0) + stats.get("misses", 0)
            
            hit_ratio = total_hits / max(total_requests, 1)
            min_ratio = self.performance_thresholds["min_cache_hit_ratio"]
            passed = hit_ratio >= min_ratio
            
            result = ValidationResult(
                test_name="cache_performance",
                passed=passed,
                message=f"缓存性能验证{'通过' if passed else '失败'}",
                details={
                    "hit_ratio": hit_ratio,
                    "min_required_ratio": min_ratio,
                    "total_hits": total_hits,
                    "total_requests": total_requests
                }
            )
            
        except ImportError:
            result = ValidationResult(
                test_name="cache_performance",
                passed=False,
                message="缓存管理器不可用",
                details={"error": "ImportError"}
            )
        
        self.validation_results.append(result)
        return result
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """运行综合验证"""
        self.logger.info("开始综合验证")
        
        validation_summary: Dict[str, Any] = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "performance_improvements": [],
            "issues_found": [],
            "recommendations": []
        }
        
        # 验证缓存性能
        cache_result = self.validate_cache_performance()
        validation_summary["total_tests"] += 1
        if cache_result.passed:
            validation_summary["passed_tests"] += 1
        else:
            validation_summary["failed_tests"] += 1
            validation_summary["issues_found"].append(cache_result.message)
        
        # 验证所有基准测试
        for name, benchmark in self.benchmarks.items():
            # 验证内存使用
            memory_result = self.validate_memory_usage(f"{name}_memory", benchmark)
            validation_summary["total_tests"] += 1
            if memory_result.passed:
                validation_summary["passed_tests"] += 1
            else:
                validation_summary["failed_tests"] += 1
                validation_summary["issues_found"].append(memory_result.message)
            
            # 验证执行时间
            time_result = self.validate_execution_time(f"{name}_time", benchmark)
            validation_summary["total_tests"] += 1
            if time_result.passed:
                validation_summary["passed_tests"] += 1
            else:
                validation_summary["failed_tests"] += 1
                validation_summary["issues_found"].append(time_result.message)
        
        # 生成建议
        if validation_summary["failed_tests"] > 0:
            validation_summary["recommendations"].extend([
                "考虑进一步优化内存使用",
                "检查是否有性能瓶颈",
                "优化缓存策略",
                "考虑使用异步操作"
            ])
        
        validation_summary["success_rate"] = (
            validation_summary["passed_tests"] / max(validation_summary["total_tests"], 1)
        )
        
        self.logger.info(f"综合验证完成: {validation_summary}")
        return validation_summary
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        return {
            "benchmarks": {name: benchmark.__dict__ for name, benchmark in self.benchmarks.items()},
            "validation_results": [result.__dict__ for result in self.validation_results],
            "summary": self.run_comprehensive_validation()
        }


# 全局验证器实例
global_optimization_validator = OptimizationValidator()


def benchmark_function(name: str, func: Callable, *args: Any, **kwargs: Any) -> PerformanceBenchmark:
    """基准测试函数的便捷函数"""
    return global_optimization_validator.benchmark_function(name, func, *args, **kwargs)


def validate_optimization() -> Dict[str, Any]:
    """验证优化效果的便捷函数"""
    return global_optimization_validator.run_comprehensive_validation()
