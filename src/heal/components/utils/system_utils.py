"""
System Utilities
Consolidated system-level utility functions including installation checks,
platform operations, and system information gathering.
"""

import os
import sys
import platform
import subprocess
import shutil
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ...common.logging_config import get_logger

# Re-export from existing modules for backward compatibility
from .check_installed import is_software_installed, get_software_path, get_software_version

logger = get_logger(__name__)


class SystemUtilities:
    """
    Consolidated system utilities that provide comprehensive
    system-level operations and information gathering.
    """
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_executable': sys.executable,
            'python_path': sys.path,
            'environment_variables': dict(os.environ),
            'current_directory': os.getcwd(),
            'user_home': str(Path.home()),
            'temp_directory': str(Path.temp() if hasattr(Path, 'temp') else Path('/tmp'))
        }
    
    @staticmethod
    def check_system_requirements() -> Dict[str, bool]:
        """Check if system meets minimum requirements"""
        requirements = {
            'python_version_ok': sys.version_info >= (3, 8),
            'platform_supported': platform.system() in ['Windows', 'Linux', 'Darwin'],
            'sufficient_memory': True,  # Placeholder for actual memory check
            'disk_space_ok': True,      # Placeholder for actual disk check
        }
        
        try:
            import psutil
            # Check memory (require at least 2GB)
            memory = psutil.virtual_memory()
            requirements['sufficient_memory'] = memory.total >= 2 * 1024 * 1024 * 1024
            
            # Check disk space (require at least 1GB free)
            disk = psutil.disk_usage('/')
            requirements['disk_space_ok'] = disk.free >= 1 * 1024 * 1024 * 1024
            
        except ImportError:
            logger.warning("psutil not available for system checks")
        
        return requirements
    
    @staticmethod
    def find_executable(name: str, paths: Optional[List[str]] = None) -> Optional[str]:
        """Find executable in system PATH or specified paths"""
        # First try system PATH
        executable = shutil.which(name)
        if executable:
            return executable
        
        # Try additional paths if provided
        if paths:
            for path in paths:
                potential_path = Path(path) / name
                if potential_path.exists() and potential_path.is_file():
                    return str(potential_path)
                
                # Try with common extensions on Windows
                if platform.system() == 'Windows':
                    for ext in ['.exe', '.bat', '.cmd']:
                        potential_path_ext = Path(path) / f"{name}{ext}"
                        if potential_path_ext.exists():
                            return str(potential_path_ext)
        
        return None
    
    @staticmethod
    def run_command(
        command: List[str], 
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> Tuple[int, str, str]:
        """Run a system command and return result"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=False
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    @staticmethod
    def check_network_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
        """Check network connectivity"""
        try:
            import socket
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_environment_variable(name: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default"""
        return os.environ.get(name, default)
    
    @staticmethod
    def set_environment_variable(name: str, value: str) -> None:
        """Set environment variable for current process"""
        os.environ[name] = value
    
    @staticmethod
    def get_available_disk_space(path: str = ".") -> int:
        """Get available disk space in bytes"""
        try:
            import psutil
            return psutil.disk_usage(path).free
        except ImportError:
            # Fallback method
            try:
                import shutil
                return shutil.disk_usage(path).free
            except Exception:
                return 0
    
    @staticmethod
    def get_memory_usage() -> Dict[str, int]:
        """Get current memory usage information"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percentage': memory.percent
            }
        except ImportError:
            return {
                'total': 0,
                'available': 0,
                'used': 0,
                'percentage': 0
            }
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information"""
        try:
            import psutil
            return {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'current_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'usage_percent': psutil.cpu_percent(interval=1)
            }
        except ImportError:
            return {
                'physical_cores': 0,
                'logical_cores': 0,
                'current_frequency': 0,
                'usage_percent': 0
            }
    
    @staticmethod
    def create_directory(path: str, parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory with error handling"""
        try:
            Path(path).mkdir(parents=parents, exist_ok=exist_ok)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    
    @staticmethod
    def copy_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """Copy file with error handling"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            if dest_path.exists() and not overwrite:
                logger.warning(f"Destination exists and overwrite=False: {destination}")
                return False
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source, destination)
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy file {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
        """Get file hash using specified algorithm"""
        try:
            import hashlib
            
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def is_admin() -> bool:
        """Check if running with administrator privileges"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    @staticmethod
    def get_process_list() -> List[Dict[str, Any]]:
        """Get list of running processes"""
        try:
            import psutil
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return processes
            
        except ImportError:
            logger.warning("psutil not available for process listing")
            return []
    
    @staticmethod
    def cleanup_temp_files(pattern: str = "heal_*", max_age_hours: int = 24) -> int:
        """Clean up temporary files matching pattern"""
        try:
            import tempfile
            import time
            import glob
            
            temp_dir = tempfile.gettempdir()
            pattern_path = os.path.join(temp_dir, pattern)
            
            files_removed = 0
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in glob.glob(pattern_path):
                try:
                    file_stat = os.stat(file_path)
                    if current_time - file_stat.st_mtime > max_age_seconds:
                        os.remove(file_path)
                        files_removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {file_path}: {e}")
            
            logger.info(f"Cleaned up {files_removed} temporary files")
            return files_removed
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0


# Convenience functions for backward compatibility
def check_installed(software_name: str) -> bool:
    """Check if software is installed (backward compatibility)"""
    return is_software_installed(software_name)

def get_system_platform() -> str:
    """Get system platform (backward compatibility)"""
    return platform.system()

def get_python_version() -> str:
    """Get Python version (backward compatibility)"""
    return platform.python_version()
