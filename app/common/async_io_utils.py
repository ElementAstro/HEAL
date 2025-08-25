"""
Async IO Utilities - 异步IO工具
优化文件读写和网络请求等IO操作，提升应用性能
"""

import asyncio
import aiofiles
import aiohttp
import concurrent.futures
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import json
import time
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from app.common.logging_config import get_logger
from app.common.performance_analyzer import profile_performance, profile_io

logger = get_logger(__name__)


@dataclass
class AsyncIOResult:
    """异步IO操作结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    operation_type: str = ""


class AsyncFileManager:
    """异步文件管理器"""
    
    def __init__(self, max_concurrent_operations: int = 10):
        self.max_concurrent_operations = max_concurrent_operations
        self.semaphore = asyncio.Semaphore(max_concurrent_operations)
        self.logger = logger.bind(component="AsyncFileManager")
    
    async def read_file_async(self, file_path: Union[str, Path], 
                             encoding: str = 'utf-8') -> AsyncIOResult:
        """异步读取文件"""
        start_time = time.perf_counter()
        
        async with self.semaphore:
            try:
                async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                    content = await f.read()
                
                execution_time = time.perf_counter() - start_time
                self.logger.debug(f"异步读取文件完成: {file_path} ({execution_time:.3f}s)")
                
                return AsyncIOResult(
                    success=True,
                    data=content,
                    execution_time=execution_time,
                    operation_type="file_read"
                )
                
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                error_msg = f"异步读取文件失败: {e}"
                self.logger.error(error_msg)
                
                return AsyncIOResult(
                    success=False,
                    error=error_msg,
                    execution_time=execution_time,
                    operation_type="file_read"
                )
    
    async def write_file_async(self, file_path: Union[str, Path], 
                              content: str, encoding: str = 'utf-8',
                              create_dirs: bool = True) -> AsyncIOResult:
        """异步写入文件"""
        start_time = time.perf_counter()
        
        async with self.semaphore:
            try:
                file_path = Path(file_path)
                
                # 创建目录
                if create_dirs:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                
                async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                    await f.write(content)
                
                execution_time = time.perf_counter() - start_time
                self.logger.debug(f"异步写入文件完成: {file_path} ({execution_time:.3f}s)")
                
                return AsyncIOResult(
                    success=True,
                    execution_time=execution_time,
                    operation_type="file_write"
                )
                
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                error_msg = f"异步写入文件失败: {e}"
                self.logger.error(error_msg)
                
                return AsyncIOResult(
                    success=False,
                    error=error_msg,
                    execution_time=execution_time,
                    operation_type="file_write"
                )
    
    async def read_json_async(self, file_path: Union[str, Path]) -> AsyncIOResult:
        """异步读取JSON文件"""
        result = await self.read_file_async(file_path)
        
        if not result.success:
            return result
        
        try:
            json_data = json.loads(result.data)
            result.data = json_data
            result.operation_type = "json_read"
            return result
            
        except json.JSONDecodeError as e:
            return AsyncIOResult(
                success=False,
                error=f"JSON解析失败: {e}",
                execution_time=result.execution_time,
                operation_type="json_read"
            )
    
    async def write_json_async(self, file_path: Union[str, Path], 
                              data: Dict[str, Any], indent: int = 2) -> AsyncIOResult:
        """异步写入JSON文件"""
        try:
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)
            result = await self.write_file_async(file_path, json_content)
            result.operation_type = "json_write"
            return result
            
        except Exception as e:
            return AsyncIOResult(
                success=False,
                error=f"JSON序列化失败: {e}",
                operation_type="json_write"
            )
    
    async def batch_read_files(self, file_paths: List[Union[str, Path]]) -> List[AsyncIOResult]:
        """批量异步读取文件"""
        tasks = [self.read_file_async(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AsyncIOResult(
                    success=False,
                    error=str(result),
                    operation_type="batch_file_read"
                ))
            else:
                processed_results.append(result)
        
        return processed_results


class AsyncNetworkManager:
    """异步网络管理器"""
    
    def __init__(self, max_concurrent_requests: int = 10, timeout: int = 30):
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.logger = logger.bind(component="AsyncNetworkManager")
    
    async def get_async(self, url: str, headers: Optional[Dict[str, str]] = None,
                       params: Optional[Dict[str, Any]] = None) -> AsyncIOResult:
        """异步GET请求"""
        start_time = time.perf_counter()
        
        async with self.semaphore:
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        content = await response.text()
                        
                        execution_time = time.perf_counter() - start_time
                        self.logger.debug(f"异步GET请求完成: {url} ({execution_time:.3f}s)")
                        
                        return AsyncIOResult(
                            success=response.status == 200,
                            data={
                                'content': content,
                                'status': response.status,
                                'headers': dict(response.headers)
                            },
                            execution_time=execution_time,
                            operation_type="http_get"
                        )
                        
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                error_msg = f"异步GET请求失败: {e}"
                self.logger.error(error_msg)
                
                return AsyncIOResult(
                    success=False,
                    error=error_msg,
                    execution_time=execution_time,
                    operation_type="http_get"
                )
    
    async def post_async(self, url: str, data: Optional[Dict[str, Any]] = None,
                        json_data: Optional[Dict[str, Any]] = None,
                        headers: Optional[Dict[str, str]] = None) -> AsyncIOResult:
        """异步POST请求"""
        start_time = time.perf_counter()
        
        async with self.semaphore:
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(url, data=data, json=json_data, headers=headers) as response:
                        content = await response.text()
                        
                        execution_time = time.perf_counter() - start_time
                        self.logger.debug(f"异步POST请求完成: {url} ({execution_time:.3f}s)")
                        
                        return AsyncIOResult(
                            success=response.status in [200, 201],
                            data={
                                'content': content,
                                'status': response.status,
                                'headers': dict(response.headers)
                            },
                            execution_time=execution_time,
                            operation_type="http_post"
                        )
                        
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                error_msg = f"异步POST请求失败: {e}"
                self.logger.error(error_msg)
                
                return AsyncIOResult(
                    success=False,
                    error=error_msg,
                    execution_time=execution_time,
                    operation_type="http_post"
                )
    
    async def batch_requests(self, requests: List[Dict[str, Any]]) -> List[AsyncIOResult]:
        """批量异步请求"""
        tasks = []
        
        for req in requests:
            method = req.get('method', 'GET').upper()
            url = req['url']
            
            if method == 'GET':
                task = self.get_async(
                    url, 
                    headers=req.get('headers'),
                    params=req.get('params')
                )
            elif method == 'POST':
                task = self.post_async(
                    url,
                    data=req.get('data'),
                    json_data=req.get('json'),
                    headers=req.get('headers')
                )
            else:
                # 不支持的方法，创建错误结果
                tasks.append(asyncio.create_task(asyncio.coroutine(lambda: AsyncIOResult(
                    success=False,
                    error=f"不支持的HTTP方法: {method}",
                    operation_type="http_request"
                ))()))
                continue
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(AsyncIOResult(
                    success=False,
                    error=str(result),
                    operation_type="batch_http_request"
                ))
            else:
                processed_results.append(result)
        
        return processed_results


class AsyncIOWorker(QThread):
    """异步IO工作线程"""
    
    # 信号
    operation_completed = Signal(str, object)  # operation_id, result
    batch_completed = Signal(str, list)        # batch_id, results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_manager = AsyncFileManager()
        self.network_manager = AsyncNetworkManager()
        self.logger = logger.bind(component="AsyncIOWorker")
        
        # 操作队列
        self.operation_queue = asyncio.Queue()
        self.running = False
    
    def run(self):
        """运行异步IO工作线程"""
        self.running = True
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._process_operations())
        finally:
            loop.close()
    
    async def _process_operations(self):
        """处理操作队列"""
        while self.running:
            try:
                # 等待操作
                operation = await asyncio.wait_for(
                    self.operation_queue.get(), 
                    timeout=1.0
                )
                
                # 执行操作
                result = await self._execute_operation(operation)
                
                # 发送结果信号
                self.operation_completed.emit(operation['id'], result)
                
            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except Exception as e:
                self.logger.error(f"处理异步操作时发生错误: {e}")
    
    async def _execute_operation(self, operation: Dict[str, Any]) -> AsyncIOResult:
        """执行单个操作"""
        op_type = operation['type']
        
        if op_type == 'read_file':
            return await self.file_manager.read_file_async(
                operation['file_path'],
                operation.get('encoding', 'utf-8')
            )
        elif op_type == 'write_file':
            return await self.file_manager.write_file_async(
                operation['file_path'],
                operation['content'],
                operation.get('encoding', 'utf-8')
            )
        elif op_type == 'read_json':
            return await self.file_manager.read_json_async(operation['file_path'])
        elif op_type == 'write_json':
            return await self.file_manager.write_json_async(
                operation['file_path'],
                operation['data']
            )
        elif op_type == 'http_get':
            return await self.network_manager.get_async(
                operation['url'],
                operation.get('headers'),
                operation.get('params')
            )
        elif op_type == 'http_post':
            return await self.network_manager.post_async(
                operation['url'],
                operation.get('data'),
                operation.get('json'),
                operation.get('headers')
            )
        else:
            return AsyncIOResult(
                success=False,
                error=f"不支持的操作类型: {op_type}",
                operation_type=op_type
            )
    
    def stop(self):
        """停止工作线程"""
        self.running = False


# 全局异步IO管理器
global_async_file_manager = AsyncFileManager()
global_async_network_manager = AsyncNetworkManager()


# 便捷函数
async def read_file_async(file_path: Union[str, Path], encoding: str = 'utf-8') -> AsyncIOResult:
    """异步读取文件的便捷函数"""
    return await global_async_file_manager.read_file_async(file_path, encoding)


async def write_file_async(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> AsyncIOResult:
    """异步写入文件的便捷函数"""
    return await global_async_file_manager.write_file_async(file_path, content, encoding)


async def read_json_async(file_path: Union[str, Path]) -> AsyncIOResult:
    """异步读取JSON文件的便捷函数"""
    return await global_async_file_manager.read_json_async(file_path)


async def write_json_async(file_path: Union[str, Path], data: Dict[str, Any]) -> AsyncIOResult:
    """异步写入JSON文件的便捷函数"""
    return await global_async_file_manager.write_json_async(file_path, data)
