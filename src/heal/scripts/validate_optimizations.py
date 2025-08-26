#!/usr/bin/env python3
"""
Optimization Validation Script - 优化验证脚本
运行性能测试并生成优化报告
"""

import json
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.heal.common.optimization_validator import global_optimization_validator, benchmark_function
from src.heal.common.memory_optimizer import global_memory_optimizer, optimize_memory
from src.heal.common.workflow_optimizer import create_workflow
from src.heal.common.logging_config import get_logger

logger = get_logger(__name__)


def run_performance_benchmarks():
    """运行性能基准测试"""
    logger.info("开始性能基准测试")
    
    benchmarks = {}
    
    # 1. 内存优化基准测试
    logger.info("测试内存优化性能")
    memory_benchmark = benchmark_function("memory_optimization", optimize_memory)
    benchmarks["memory_optimization"] = memory_benchmark
    
    # 2. JSON处理基准测试
    logger.info("测试JSON处理性能")
    
    def json_processing_test():
        from src.heal.common.json_utils import JsonUtils
        import tempfile
        
        # 创建测试数据
        test_data = {
            "config": {"setting1": "value1", "setting2": "value2"},
            "data": list(range(1000)),
            "metadata": {"version": "1.0", "timestamp": time.time()}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)
        
        try:
            # 测试加载
            result = JsonUtils.load_json_file(temp_path)
            
            # 测试保存
            JsonUtils.save_json_file(temp_path, test_data)
            
            return result.success
        finally:
            temp_path.unlink(missing_ok=True)
    
    json_benchmark = benchmark_function("json_processing", json_processing_test, iterations=10)
    benchmarks["json_processing"] = json_benchmark
    
    # 3. 缓存系统基准测试
    logger.info("测试缓存系统性能")
    
    def cache_performance_test():
        from src.heal.common.cache_manager import global_cache_manager
        
        cache = global_cache_manager.get_cache("benchmark_test")
        if not cache:
            from src.heal.common.cache_manager import LRUCache
            cache = LRUCache(max_size=1000)
            global_cache_manager.register_cache("benchmark_test", cache)
        
        # 写入测试
        for i in range(500):
            cache.put(f"key_{i}", f"value_{i}")
        
        # 读取测试
        results = []
        for i in range(500):
            result = cache.get(f"key_{i}")
            results.append(result)
        
        # 清理测试
        cache.clear()
        
        return len([r for r in results if r is not None])
    
    cache_benchmark = benchmark_function("cache_performance", cache_performance_test, iterations=5)
    benchmarks["cache_performance"] = cache_benchmark
    
    # 4. 工作流系统基准测试
    logger.info("测试工作流系统性能")
    
    def workflow_performance_test():
        workflow = create_workflow("benchmark_workflow")
        
        def step1():
            time.sleep(0.001)  # 1ms模拟工作
            return "step1_done"
        
        def step2():
            time.sleep(0.001)  # 1ms模拟工作
            return "step2_done"
        
        def step3():
            time.sleep(0.001)  # 1ms模拟工作
            return "step3_done"
        
        workflow.add_step("step1", step1)
        workflow.add_step("step2", step2, dependencies=["step1"])
        workflow.add_step("step3", step3, dependencies=["step2"])
        
        result = workflow.execute()
        return result["success"]
    
    workflow_benchmark = benchmark_function("workflow_performance", workflow_performance_test, iterations=10)
    benchmarks["workflow_performance"] = workflow_benchmark
    
    logger.info("性能基准测试完成")
    return benchmarks


def validate_optimizations():
    """验证优化效果"""
    logger.info("开始优化验证")
    
    # 运行基准测试
    benchmarks = run_performance_benchmarks()
    
    # 运行综合验证
    validation_summary = global_optimization_validator.run_comprehensive_validation()
    
    # 生成详细报告
    report = global_optimization_validator.get_validation_report()
    
    return {
        "benchmarks": benchmarks,
        "validation_summary": validation_summary,
        "detailed_report": report,
        "timestamp": time.time()
    }


def generate_optimization_report(results, output_file=None):
    """生成优化报告"""
    logger.info("生成优化报告")
    
    report_content = {
        "optimization_validation_report": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(results["timestamp"])),
            "summary": results["validation_summary"],
            "performance_benchmarks": {},
            "recommendations": [],
            "issues": []
        }
    }
    
    # 处理基准测试结果
    for name, benchmark in results["benchmarks"].items():
        report_content["optimization_validation_report"]["performance_benchmarks"][name] = {
            "execution_time_ms": benchmark.execution_time * 1000,
            "memory_usage_mb": benchmark.memory_usage_mb,
            "cpu_usage_percent": benchmark.cpu_usage_percent,
            "success": benchmark.success,
            "error": benchmark.error
        }
        
        # 生成建议
        if benchmark.execution_time > 1.0:  # 超过1秒
            report_content["optimization_validation_report"]["issues"].append(
                f"{name}: 执行时间过长 ({benchmark.execution_time:.2f}s)"
            )
            report_content["optimization_validation_report"]["recommendations"].append(
                f"优化 {name} 的执行效率"
            )
        
        if benchmark.memory_usage_mb > 50:  # 超过50MB
            report_content["optimization_validation_report"]["issues"].append(
                f"{name}: 内存使用过高 ({benchmark.memory_usage_mb:.1f}MB)"
            )
            report_content["optimization_validation_report"]["recommendations"].append(
                f"优化 {name} 的内存使用"
            )
    
    # 添加通用建议
    success_rate = results["validation_summary"]["success_rate"]
    if success_rate < 0.8:
        report_content["optimization_validation_report"]["recommendations"].extend([
            "考虑进一步优化性能关键路径",
            "检查内存泄漏和资源管理",
            "优化缓存策略和命中率",
            "考虑使用更多异步操作"
        ])
    elif success_rate >= 0.9:
        report_content["optimization_validation_report"]["recommendations"].append(
            "优化效果良好，继续监控性能指标"
        )
    
    # 保存报告
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"优化报告已保存到: {output_path}")
    
    return report_content


def print_summary(results):
    """打印优化摘要"""
    summary = results["validation_summary"]
    
    print("\n" + "="*60)
    print("HEAL 项目优化验证报告")
    print("="*60)
    
    print(f"\n📊 验证统计:")
    print(f"  总测试数: {summary['total_tests']}")
    print(f"  通过测试: {summary['passed_tests']}")
    print(f"  失败测试: {summary['failed_tests']}")
    print(f"  成功率: {summary['success_rate']:.1%}")
    
    print(f"\n⚡ 性能基准:")
    for name, benchmark in results["benchmarks"].items():
        status = "✅" if benchmark.success else "❌"
        print(f"  {status} {name}:")
        print(f"    执行时间: {benchmark.execution_time*1000:.1f}ms")
        print(f"    内存使用: {benchmark.memory_usage_mb:.1f}MB")
        if benchmark.error:
            print(f"    错误: {benchmark.error}")
    
    if summary.get("issues_found"):
        print(f"\n⚠️  发现的问题:")
        for issue in summary["issues_found"]:
            print(f"  • {issue}")
    
    if summary.get("recommendations"):
        print(f"\n💡 优化建议:")
        for rec in summary["recommendations"]:
            print(f"  • {rec}")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    logger.info("开始HEAL项目优化验证")
    
    try:
        # 运行验证
        results = validate_optimizations()
        
        # 生成报告
        report_file = project_root / "optimization_report.json"
        generate_optimization_report(results, report_file)
        
        # 打印摘要
        print_summary(results)
        
        # 返回成功率作为退出码
        success_rate = results["validation_summary"]["success_rate"]
        if success_rate >= 0.8:
            logger.info("优化验证成功完成")
            return 0
        else:
            logger.warning(f"优化验证完成，但成功率较低: {success_rate:.1%}")
            return 1
            
    except Exception as e:
        logger.error(f"优化验证失败: {e}")
        print(f"\n❌ 验证过程中发生错误: {e}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
