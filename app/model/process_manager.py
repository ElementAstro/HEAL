import os
import sys
import json
import time
import psutil
import signal
import threading
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtWidgets import QMessageBox

from app.common.logging_config import get_logger, log_performance, log_exception

# 使用统一日志配置
logger = get_logger('process_manager')


class ProcessStatus(Enum):
    """进程状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    CRASHED = "crashed"


@dataclass
class ProcessInfo:
    """进程信息"""
    name: str
    pid: Optional[int] = None
    status: ProcessStatus = ProcessStatus.STOPPED
    command: str = ""
    working_dir: str = ""
    start_time: Optional[float] = None
    restart_count: int = 0
    max_restarts: int = 3
    auto_restart: bool = True
    environment: Dict[str, str] = field(default_factory=dict)
    log_file: Optional[str] = None
    error_callback: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'pid': self.pid,
            'status': self.status.value,
            'command': self.command,
            'working_dir': self.working_dir,
            'start_time': self.start_time,
            'restart_count': self.restart_count,
            'max_restarts': self.max_restarts,
            'auto_restart': self.auto_restart,
            'log_file': self.log_file
        }


class ProcessMonitor(QThread):
    """进程监控线程"""
    
    process_status_changed = Signal(str, ProcessStatus)
    process_output = Signal(str, str)  # name, output
    process_error = Signal(str, str)   # name, error
    
    def __init__(self, process_manager):
        super().__init__()
        self.process_manager = process_manager
        self.running = False
        
    def run(self):
        """监控线程主循环"""
        self.running = True
        while self.running:
            try:
                self.process_manager._check_processes()
                self.msleep(1000)  # 每秒检查一次
            except Exception as e:
                logger.error(f"Process monitor error: {e}")
                self.msleep(5000)  # 错误时等待5秒
                
    def stop(self):
        """停止监控"""
        self.running = False
        self.wait()


class ProcessManager(QObject):
    """进程管理器"""
    
    # 信号
    process_started = Signal(str)
    process_stopped = Signal(str)
    process_crashed = Signal(str)
    process_output = Signal(str, str)
    process_restarted = Signal(str)  # Signal emitted when a process is restarted
    
    def __init__(self):
        super().__init__()
        self.processes: Dict[str, ProcessInfo] = {}
        self.running_processes: Dict[str, psutil.Process] = {}
        
        # 创建日志目录
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 启动监控线程
        self.monitor = ProcessMonitor(self)
        self.monitor.process_status_changed.connect(self._on_status_changed)
        self.monitor.start()
        
        # 配置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志 - 使用统一日志配置"""
        # 日志配置现在在统一的 logging_config 中处理
        logger.info("Process manager logging initialized")
        
    def register_process(self, name: str, command: str, working_dir: Optional[str] = None,
                        auto_restart: bool = True, max_restarts: int = 3,
                        environment: Optional[Dict[str, str]] = None,
                        error_callback: Optional[Callable[..., Any]] = None) -> bool:
        """注册进程"""
        try:
            if name in self.processes:
                logger.warning(f"Process {name} already registered")
                return False
                
            working_dir = working_dir or os.getcwd()
            environment = environment or {}
            
            process_info = ProcessInfo(
                name=name,
                command=command,
                working_dir=working_dir,
                auto_restart=auto_restart,
                max_restarts=max_restarts,
                environment=environment,
                log_file=str(self.log_dir / f"{name}.log"),
                error_callback=error_callback
            )
            
            self.processes[name] = process_info
            logger.info(f"Registered process: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register process {name}: {e}")
            return False
            
    def start_process(self, name: str, **kwargs) -> bool:
        """启动进程"""
        try:
            if name not in self.processes:
                logger.error(f"Process {name} not registered")
                return False
                
            process_info = self.processes[name]
            
            if process_info.status == ProcessStatus.RUNNING:
                logger.warning(f"Process {name} is already running")
                return True
                
            if process_info.status == ProcessStatus.STARTING:
                logger.warning(f"Process {name} is starting")
                return True
                
            # 更新状态为启动中
            process_info.status = ProcessStatus.STARTING
            
            # 准备环境变量
            env = os.environ.copy()
            env.update(process_info.environment)
            env.update(kwargs.get('environment', {}))
            
            # 准备命令
            command = kwargs.get('command', process_info.command)
            working_dir = kwargs.get('working_dir', process_info.working_dir)
            
            logger.info(f"Starting process {name}: {command}")
            
            # 启动进程
            if sys.platform == 'win32':
                # Windows平台
                import subprocess
                proc = subprocess.Popen(
                    command,
                    cwd=working_dir,
                    env=env,
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Unix平台
                import subprocess
                proc = subprocess.Popen(
                    command,
                    cwd=working_dir,
                    env=env,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid
                )
                
            # 获取psutil进程对象
            psutil_proc = psutil.Process(proc.pid)
            self.running_processes[name] = psutil_proc
            
            # 更新进程信息
            process_info.pid = proc.pid
            process_info.status = ProcessStatus.RUNNING
            process_info.start_time = time.time()
            
            # 启动输出监控线程
            self._start_output_monitor(name, proc)
            
            logger.info(f"Process {name} started with PID {proc.pid}")
            self.process_started.emit(name)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start process {name}: {e}")
            if name in self.processes:
                self.processes[name].status = ProcessStatus.ERROR
            return False
            
    def stop_process(self, name: str, force: bool = False, timeout: int = 10) -> bool:
        """停止进程"""
        try:
            if name not in self.processes:
                logger.error(f"Process {name} not registered")
                return False
                
            process_info = self.processes[name]
            
            if process_info.status != ProcessStatus.RUNNING:
                logger.warning(f"Process {name} is not running")
                return True
                
            # 更新状态为停止中
            process_info.status = ProcessStatus.STOPPING
            
            if name in self.running_processes:
                psutil_proc = self.running_processes[name]
                
                try:
                    if force:
                        # 强制终止
                        psutil_proc.kill()
                        logger.info(f"Force killed process {name}")
                    else:
                        # 优雅停止
                        psutil_proc.terminate()
                        
                        # 等待进程结束
                        try:
                            psutil_proc.wait(timeout=timeout)
                            logger.info(f"Process {name} terminated gracefully")
                        except psutil.TimeoutExpired:
                            logger.warning(f"Process {name} did not terminate, killing...")
                            psutil_proc.kill()
                            
                except psutil.NoSuchProcess:
                    logger.info(f"Process {name} already terminated")
                    
                # 清理
                del self.running_processes[name]
                
            # 更新进程信息
            process_info.pid = None
            process_info.status = ProcessStatus.STOPPED
            
            logger.info(f"Process {name} stopped")
            self.process_stopped.emit(name)
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop process {name}: {e}")
            return False
            
    def restart_process(self, name: str) -> bool:
        """重启进程"""
        try:
            if name not in self.processes:
                logger.error(f"Process {name} not registered")
                return False
                
            logger.info(f"Restarting process {name}")
            
            # 停止进程
            if not self.stop_process(name):
                logger.error(f"Failed to stop process {name} for restart")
                return False
                
            # 等待一下
            time.sleep(1)
            
            # 启动进程
            success = self.start_process(name)
            
            if success:
                self.processes[name].restart_count += 1
                logger.info(f"Process {name} restarted (count: {self.processes[name].restart_count})")
                self.process_restarted.emit(name)  # Emit restart signal on successful restart
            else:
                logger.error(f"Failed to restart process {name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to restart process {name}: {e}")
            return False
            
    def get_process_status(self, name: str) -> Optional[ProcessStatus]:
        """获取进程状态"""
        if name in self.processes:
            return self.processes[name].status
        return None
        
    def get_process_info(self, name: str) -> Optional[ProcessInfo]:
        """获取进程信息"""
        return self.processes.get(name)
        
    def list_processes(self) -> Dict[str, ProcessInfo]:
        """列出所有进程"""
        return self.processes.copy()
        
    def is_process_running(self, name: str) -> bool:
        """检查进程是否运行"""
        if name not in self.processes:
            return False
        return self.processes[name].status == ProcessStatus.RUNNING
        
    def _check_processes(self):
        """检查进程状态"""
        for name, process_info in self.processes.items():
            if process_info.status == ProcessStatus.RUNNING:
                if name in self.running_processes:
                    psutil_proc = self.running_processes[name]
                    try:
                        if not psutil_proc.is_running():
                            # 进程已经停止
                            self._handle_process_crash(name)
                    except psutil.NoSuchProcess:
                        # 进程不存在
                        self._handle_process_crash(name)
                else:
                    # 进程对象丢失
                    self._handle_process_crash(name)
                    
    def _handle_process_crash(self, name: str):
        """处理进程崩溃"""
        try:
            process_info = self.processes[name]
            process_info.status = ProcessStatus.CRASHED
            
            logger.error(f"Process {name} crashed")
            self.process_crashed.emit(name)
            
            # 清理
            if name in self.running_processes:
                del self.running_processes[name]
                
            process_info.pid = None
            
            # 调用错误回调
            if process_info.error_callback:
                try:
                    process_info.error_callback(name, "Process crashed")
                except Exception as e:
                    logger.error(f"Error callback failed for {name}: {e}")
                    
            # 自动重启
            if (process_info.auto_restart and 
                process_info.restart_count < process_info.max_restarts):
                logger.info(f"Auto-restarting process {name}")
                self.restart_process(name)
            else:
                logger.warning(f"Process {name} will not be auto-restarted")
                
        except Exception as e:
            logger.error(f"Failed to handle crash for process {name}: {e}")
            
    def _start_output_monitor(self, name: str, proc):
        """启动输出监控线程"""
        def monitor_output():
            try:
                while proc.poll() is None:
                    # 读取标准输出
                    if proc.stdout:
                        line = proc.stdout.readline()
                        if line:
                            self.process_output.emit(name, line.strip())
                            self._write_to_log(name, line.strip())
                            
                    # 读取错误输出
                    if proc.stderr:
                        line = proc.stderr.readline()
                        if line:
                            self.process_output.emit(name, f"ERROR: {line.strip()}")
                            self._write_to_log(name, f"ERROR: {line.strip()}")
                            
            except Exception as e:
                logger.error(f"Output monitor error for {name}: {e}")
                
        thread = threading.Thread(target=monitor_output, daemon=True)
        thread.start()
        
    def _write_to_log(self, name: str, message: str):
        """写入日志文件"""
        try:
            if name in self.processes and self.processes[name].log_file is not None:
                log_file_path = Path(str(self.processes[name].log_file))
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"Failed to write log for {name}: {e}")
            
    def _on_status_changed(self, name: str, status: ProcessStatus):
        """状态变化处理"""
        if name in self.processes:
            self.processes[name].status = status
            
    def save_state(self, file_path: Optional[str] = None):
        """保存状态到文件"""
        try:
            if not file_path:
                file_path = "logs/process_manager_state.json"
                
            state = {
                'processes': {name: info.to_dict() for name, info in self.processes.items()}
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            logger.info(f"State saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            
    def load_state(self, file_path: Optional[str] = None):
        """从文件加载状态"""
        try:
            if not file_path:
                file_path = "logs/process_manager_state.json"
                
            if not os.path.exists(file_path):
                logger.info("No state file found")
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # 加载进程信息（但不启动进程）
            for name, info in state.get('processes', {}).items():
                if name not in self.processes:
                    process_info = ProcessInfo(
                        name=info['name'],
                        command=info['command'],
                        working_dir=info['working_dir'],
                        auto_restart=info.get('auto_restart', True),
                        max_restarts=info.get('max_restarts', 3),
                        log_file=info.get('log_file')
                    )
                    process_info.status = ProcessStatus.STOPPED  # 重置状态
                    self.processes[name] = process_info
                    
            logger.info(f"State loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            
    def shutdown(self):
        """关闭进程管理器"""
        try:
            logger.info("Shutting down process manager")
            
            # 停止监控线程
            if self.monitor:
                self.monitor.stop()
                
            # 停止所有进程
            for name in list(self.processes.keys()):
                if self.is_process_running(name):
                    logger.info(f"Stopping process {name}")
                    self.stop_process(name, force=True, timeout=5)
                    
            # 保存状态
            self.save_state()
            
            logger.info("Process manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# 全局进程管理器实例
process_manager = ProcessManager()
