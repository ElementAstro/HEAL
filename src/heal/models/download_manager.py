"""
增强的下载管理器模块
支持断点续传、并发下载、重试机制和进度监控
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.heal.common.logging_config import (
    get_logger,
    log_download,
    log_exception,
    log_performance,
)
from src.heal.common.performance_analyzer import profile_io, profile_performance

# 使用统一日志配置
logger = get_logger("download_manager")


class DownloadStatus(Enum):
    """下载状态枚举"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadItem:
    """下载项"""

    id: str
    url: str
    file_path: str
    file_size: int = 0
    downloaded_size: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    speed: float = 0.0
    eta: int = 0
    retry_count: int = 0
    max_retries: int = 3
    chunk_size: int = 8192
    timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    checksum: Optional[str] = None
    checksum_type: str = "md5"
    created_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None

    @property
    def progress(self) -> float:
        """下载进度百分比"""
        if self.file_size > 0:
            return (self.downloaded_size / self.file_size) * 100
        return 0.0

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == DownloadStatus.COMPLETED

    @property
    def can_resume(self) -> bool:
        """是否可以断点续传"""
        # Ensure file_size is known for resume to make sense, or if downloaded_size > 0
        return self.downloaded_size > 0 and (
            self.file_size == 0 or self.downloaded_size < self.file_size
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "url": self.url,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "downloaded_size": self.downloaded_size,
            "status": self.status.value,
            "speed": self.speed,
            "eta": self.eta,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "chunk_size": self.chunk_size,
            "timeout": self.timeout,
            "headers": self.headers,
            "checksum": self.checksum,
            "checksum_type": self.checksum_type,
            "created_time": self.created_time,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_message": self.error_message,
        }


class DownloadWorker(QThread):
    """下载工作线程"""

    # id, downloaded, total, speed
    progress_updated = Signal(str, int, int, float)
    status_changed = Signal(str, DownloadStatus)
    download_completed = Signal(str)
    download_failed = Signal(str, str)

    def __init__(self, download_item: DownloadItem, download_manager: Any) -> None:
        super().__init__()
        self.download_item = download_item
        # Keep if needed for future, currently unused by worker
        self.download_manager = download_manager
        self.session = requests.Session()
        self.cancelled = False

    def run(self) -> None:
        """运行下载"""
        try:
            self._perform_download_steps()
        except Exception as e:
            # This is a fallback for truly unexpected errors not caught by _perform_download_steps's internal handling
            logger.critical(
                f"Critical unhandled error in DownloadWorker run for {self.download_item.id}: {e}",
                exc_info=True,
            )
            if self.download_item.status not in [
                DownloadStatus.FAILED,
                DownloadStatus.CANCELLED,
                DownloadStatus.COMPLETED,
            ]:
                self._handle_error(f"Critical worker error: {str(e)}")
            else:
                self.download_failed.emit(
                    self.download_item.id, f"Critical worker error: {str(e)}"
                )

    def _perform_download_steps(self) -> None:
        """Orchestrates the download process."""
        item = self.download_item
        item.status = DownloadStatus.DOWNLOADING
        item.start_time = time.time()  # Record start time for this download attempt
        self.status_changed.emit(item.id, item.status)

        try:
            headers = self._prepare_request_headers(item)
            response = self._execute_request(item, headers)
            self._update_file_size_from_response(item, response)

            os.makedirs(os.path.dirname(item.file_path), exist_ok=True)
            self._process_response_content(item, response)

            if self.cancelled:
                item.status = DownloadStatus.CANCELLED
                self.status_changed.emit(item.id, item.status)
                logger.info(f"Download cancelled by worker: {item.id}")
                return

            if item.checksum and not self._verify_checksum():
                # More specific exception
                raise ValueError("Checksum verification failed")

            item.status = DownloadStatus.COMPLETED
            item.end_time = time.time()
            self.status_changed.emit(item.id, item.status)
            self.download_completed.emit(item.id)
            logger.info(f"Download completed: {item.id}")

        except requests.exceptions.RequestException as e:
            self._handle_error(f"Network error: {e}")
        except ValueError as e:  # Catch checksum or other value errors
            self._handle_error(str(e))
        except Exception as e:
            self._handle_error(f"Unexpected download error: {str(e)}")

    def _prepare_request_headers(self, item: DownloadItem) -> Dict[str, str]:
        """Prepares request headers, including Range for resuming."""
        headers = item.headers.copy()
        if item.can_resume and os.path.exists(item.file_path):
            current_size = os.path.getsize(item.file_path)
            if current_size > 0:
                headers["Range"] = f"bytes={current_size}-"
                item.downloaded_size = (
                    current_size  # Ensure downloaded_size is up-to-date
                )
        return headers

    def _execute_request(
        self, item: DownloadItem, headers: Dict[str, str]
    ) -> requests.Response:
        """Executes the HTTP GET request."""
        response = self.session.get(
            item.url, headers=headers, stream=True, timeout=item.timeout
        )
        response.raise_for_status()
        return response

    def _update_file_size_from_response(
        self, item: DownloadItem, response: requests.Response
    ) -> None:
        """Updates file_size based on Content-Range or Content-Length headers."""
        # Prefer Content-Range for total size if available
        if "content-range" in response.headers:
            range_info = response.headers["content-range"]
            if "/" in range_info:
                total_size_str = range_info.split("/")[-1]
                if total_size_str != "*":
                    try:
                        item.file_size = int(total_size_str)
                        return
                    except ValueError:
                        logger.warning(
                            f"Could not parse total size from Content-Range: {range_info} for {item.id}"
                        )

        if "content-length" in response.headers:
            try:
                content_length = int(response.headers["content-length"])
                if item.can_resume and item.downloaded_size > 0:
                    item.file_size = item.downloaded_size + content_length
                else:
                    item.file_size = content_length
            except ValueError:
                logger.warning(
                    f"Could not parse Content-Length: {response.headers['content-length']} for {item.id}"
                )

        if item.file_size == 0:
            logger.warning(
                f"Could not determine total file size for {item.id} from headers. Progress may be inaccurate."
            )

    @profile_performance(threshold=0.1)  # 监控文件写入性能
    def _process_response_content(
        self, item: DownloadItem, response: requests.Response
    ) -> None:
        """Processes the response stream, writes to file, and updates progress."""
        # Determine file mode based on whether we are resuming an existing file part
        mode = (
            "ab"
            if item.can_resume
            and item.downloaded_size > 0
            and os.path.exists(item.file_path)
            else "wb"
        )

        last_progress_update_time = time.time()
        buffer = bytearray()
        buffer_size = item.chunk_size * 10  # 缓冲10个chunk以减少I/O操作

        with open(item.file_path, mode, buffering=buffer_size) as f:
            for chunk in response.iter_content(chunk_size=item.chunk_size):
                if self.cancelled:
                    logger.debug(
                        f"Cancellation detected during content processing for {item.id}"
                    )
                    return

                if chunk:
                    buffer.extend(chunk)
                    item.downloaded_size += len(chunk)

                    # 当缓冲区满时或者是最后一个chunk时写入文件
                    if len(buffer) >= buffer_size:
                        f.write(buffer)
                        f.flush()  # 确保数据写入磁盘
                        buffer.clear()

                current_time = time.time()
                if current_time - last_progress_update_time >= 0.5:
                    if item.start_time:  # Ensure start_time is set
                        elapsed_since_current_download_start = (
                            current_time - item.start_time
                        )
                        if elapsed_since_current_download_start > 1e-6:
                            item.speed = (
                                item.downloaded_size
                                / elapsed_since_current_download_start
                            )
                        else:
                            item.speed = 0.0

                        if item.speed > 0 and item.file_size > 0:
                            remaining_bytes = item.file_size - item.downloaded_size
                            item.eta = (
                                int(remaining_bytes / item.speed)
                                if remaining_bytes > 0
                                else 0
                            )
                        else:
                            item.eta = 0

                    self.progress_updated.emit(
                        item.id, item.downloaded_size, item.file_size, item.speed
                    )
                    last_progress_update_time = current_time

            # 写入剩余的缓冲区数据
            if buffer:
                f.write(buffer)
                f.flush()
                buffer.clear()

        if not self.cancelled:  # Final progress update
            self.progress_updated.emit(
                item.id, item.downloaded_size, item.file_size, item.speed
            )

    def _verify_checksum(self) -> bool:
        """验证校验和"""
        item = self.download_item
        try:
            if not item.checksum:  # If no checksum is provided, skip verification
                return True

            hash_func_name = item.checksum_type.lower()
            if hash_func_name == "md5":
                hash_func = hashlib.md5()
            elif hash_func_name == "sha1":
                hash_func = hashlib.sha1()
            elif hash_func_name == "sha256":
                hash_func = hashlib.sha256()
            else:
                logger.warning(
                    f"Unsupported checksum type: {item.checksum_type} for {item.id}"
                )
                return True  # Or False, depending on desired strictness

            with open(item.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)

            calculated_checksum = hash_func.hexdigest()
            # item.checksum is confirmed not None by the check at the beginning
            return calculated_checksum.lower() == item.checksum.lower()

        except Exception as e:
            logger.error(f"Checksum verification error for {item.id}: {e}")
            return False

    def _handle_error(self, error_msg: str) -> None:
        """处理错误"""
        item = self.download_item
        item.error_message = error_msg
        item.status = DownloadStatus.FAILED
        item.end_time = time.time()  # Record end time on failure as well

        logger.error(f"Download failed for {item.id}: {error_msg}")

        self.status_changed.emit(item.id, item.status)
        self.download_failed.emit(item.id, error_msg)

    def cancel(self) -> None:
        """取消下载"""
        self.cancelled = True
        logger.debug(f"Cancel flag set for worker of {self.download_item.id}")


class DownloadManager(QObject):
    """下载管理器"""

    # 信号
    download_added = Signal(str)
    download_started = Signal(str)
    download_completed = Signal(str)
    download_failed = Signal(str, str)
    download_progress = Signal(str, int, int, float)
    download_status_changed = Signal(str, DownloadStatus)

    def __init__(self, max_concurrent_downloads: int = 3) -> None:
        super().__init__()
        self.downloads: Dict[str, DownloadItem] = {}
        self.workers: Dict[str, DownloadWorker] = {}
        self.max_concurrent_downloads = max_concurrent_downloads

        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)

        self.state_file = (
            self.download_dir / "download_state.json"
        )  # Path object for consistency

        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self._check_retries)
        self.retry_timer.start(5000)

        self._load_state()

    def add_download(self, url: str, file_path: Optional[str] = None, **kwargs: Any) -> str:
        """添加下载任务"""
        try:
            download_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:12]

            actual_file_path: str
            if not file_path:
                parsed_url = urlparse(url)
                filename_from_url = os.path.basename(parsed_url.path)
                if not filename_from_url:  # Handle cases like domain.com/
                    filename_from_url = (
                        "download_" + hashlib.md5(url.encode()).hexdigest()[:8]
                    )
                actual_file_path = str(self.download_dir / filename_from_url)
            else:
                actual_file_path = file_path

            download_item = DownloadItem(
                id=download_id, url=url, file_path=actual_file_path, **kwargs
            )

            self.downloads[download_id] = download_item

            logger.info(f"Added download: {download_id} -> {url}")
            self.download_added.emit(download_id)

            if self._can_start_download():
                self.start_download(download_id)

            return download_id

        except Exception as e:
            logger.error(f"Failed to add download for URL {url}: {e}", exc_info=True)
            raise  # Re-raise after logging

    def start_download(self, download_id: str) -> bool:
        """开始下载"""
        try:
            if download_id not in self.downloads:
                logger.error(f"Download {download_id} not found for starting.")
                return False

            download_item = self.downloads[download_id]

            if download_item.status == DownloadStatus.DOWNLOADING:
                logger.warning(f"Download {download_id} is already running.")
                return True

            if download_item.status == DownloadStatus.COMPLETED:
                logger.warning(f"Download {download_id} is already completed.")
                return True

            if not self._can_start_download():
                download_item.status = DownloadStatus.PENDING
                self.download_status_changed.emit(download_id, download_item.status)
                logger.info(
                    f"Download {download_id} queued, max concurrent downloads reached."
                )
                return True  # Queued successfully

            # Pass self as download_manager
            worker = DownloadWorker(download_item, self)
            worker.progress_updated.connect(self._on_progress_updated)
            worker.status_changed.connect(self._on_status_changed)
            worker.download_completed.connect(self._on_download_completed)
            worker.download_failed.connect(self._on_download_failed)
            worker.finished.connect(lambda: self._cleanup_worker(download_id))

            self.workers[download_id] = worker
            worker.start()  # Starts the QThread

            # download_item.status is set to DOWNLOADING inside worker.run()
            # self.download_started.emit(download_id) # Emitted when status actually changes to DOWNLOADING
            logger.info(f"Attempting to start download: {download_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start download {download_id}: {e}", exc_info=True)
            if (
                download_id in self.downloads
            ):  # Ensure item exists before trying to set status
                self.downloads[download_id].status = DownloadStatus.FAILED
                self.downloads[download_id].error_message = str(e)
                self.download_status_changed.emit(download_id, DownloadStatus.FAILED)
                self.download_failed.emit(download_id, str(e))
            return False

    def pause_download(self, download_id: str) -> bool:
        """暂停下载"""
        try:
            if download_id not in self.downloads:
                logger.warning(f"Download {download_id} not found for pausing.")
                return False

            download_item = self.downloads[download_id]

            if download_item.status != DownloadStatus.DOWNLOADING:
                logger.warning(
                    f"Download {download_id} is not in DOWNLOADING state, cannot pause. Status: {download_item.status}"
                )
                return False

            if download_id in self.workers:
                worker = self.workers[download_id]
                worker.cancel()  # Signal the worker to stop
                # Worker will emit status_changed to CANCELLED or handle it internally
                # We set to PAUSED here to reflect user intent. Worker might finish chunk then stop.

            download_item.status = DownloadStatus.PAUSED
            self.download_status_changed.emit(download_id, download_item.status)

            logger.info(f"Paused download: {download_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to pause download {download_id}: {e}", exc_info=True)
            return False

    def resume_download(self, download_id: str) -> bool:
        """恢复下载"""
        try:
            if download_id not in self.downloads:
                logger.warning(f"Download {download_id} not found for resuming.")
                return False

            download_item = self.downloads[download_id]

            if download_item.status not in [
                DownloadStatus.PAUSED,
                DownloadStatus.FAILED,
            ]:
                logger.warning(
                    f"Download {download_id} is not in PAUSED or FAILED state, cannot resume. Status: {download_item.status}"
                )
                return False

            # Reset retry count if resuming from a failed state by user action
            if download_item.status == DownloadStatus.FAILED:
                download_item.retry_count = 0
                download_item.error_message = None

            return self.start_download(download_id)

        except Exception as e:
            logger.error(f"Failed to resume download {download_id}: {e}", exc_info=True)
            return False

    def cancel_download(self, download_id: str, delete_file: bool = True) -> bool:
        """取消下载"""
        try:
            if download_id not in self.downloads:
                logger.warning(f"Download {download_id} not found for cancelling.")
                return False

            download_item = self.downloads[download_id]

            if download_id in self.workers:
                worker = self.workers[download_id]
                worker.cancel()
                # Worker will set its own status to CANCELLED upon graceful exit

            download_item.status = DownloadStatus.CANCELLED
            self.download_status_changed.emit(download_id, download_item.status)

            if (
                delete_file
                and os.path.exists(download_item.file_path)
                and not download_item.is_completed
            ):
                try:
                    os.remove(download_item.file_path)
                    logger.info(
                        f"Deleted file for cancelled download {download_id}: {download_item.file_path}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to remove file for cancelled download {download_id}: {e}"
                    )

            logger.info(f"Cancelled download: {download_id}")
            # No need to _cleanup_worker here, 'finished' signal will do it.
            return True

        except Exception as e:
            logger.error(f"Failed to cancel download {download_id}: {e}", exc_info=True)
            return False

    def remove_download(self, download_id: str, delete_file: bool = False) -> bool:
        """移除下载任务"""
        try:
            if download_id not in self.downloads:
                logger.warning(f"Download {download_id} not found for removal.")
                return False

            # Get item before potential cancel
            download_item = self.downloads[download_id]

            if (
                download_item.status == DownloadStatus.DOWNLOADING
                or download_id in self.workers
            ):
                # Cancel first, don't delete file yet
                self.cancel_download(download_id, delete_file=False)
                # Wait for worker to finish if it was running. This might need a timeout or be async.
                # For simplicity, we assume cancel_download signals worker and it will cleanup.

            if delete_file and os.path.exists(download_item.file_path):
                try:
                    os.remove(download_item.file_path)
                    logger.info(
                        f"Deleted file upon removing download {download_id}: {download_item.file_path}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to remove file {download_item.file_path} for download {download_id}: {e}"
                    )

            del self.downloads[download_id]
            if (
                download_id in self.workers
            ):  # Should be cleaned by finished signal, but as a safeguard
                del self.workers[download_id]

            logger.info(f"Removed download: {download_id}")
            self._start_next_download()  # Try to start another if a slot opened up
            return True

        except Exception as e:
            logger.error(f"Failed to remove download {download_id}: {e}", exc_info=True)
            return False

    def get_download_info(self, download_id: str) -> Optional[DownloadItem]:
        return self.downloads.get(download_id)

    def list_downloads(self) -> Dict[str, DownloadItem]:
        return self.downloads.copy()

    def get_active_downloads(self) -> List[str]:
        return [
            download_id
            for download_id, item in self.downloads.items()
            if item.status == DownloadStatus.DOWNLOADING
        ]

    def get_download_statistics(self) -> Dict[str, Any]:
        total = len(self.downloads)
        completed = sum(1 for item in self.downloads.values() if item.is_completed)
        downloading = len(self.get_active_downloads())
        failed = sum(
            1
            for item in self.downloads.values()
            if item.status == DownloadStatus.FAILED
        )
        paused = sum(
            1
            for item in self.downloads.values()
            if item.status == DownloadStatus.PAUSED
        )
        pending = sum(
            1
            for item in self.downloads.values()
            if item.status == DownloadStatus.PENDING
        )

        total_size = sum(
            item.file_size for item in self.downloads.values() if item.file_size > 0
        )
        downloaded_size = sum(item.downloaded_size for item in self.downloads.values())

        total_speed = sum(
            item.speed
            for item in self.downloads.values()
            if item.status == DownloadStatus.DOWNLOADING
        )

        return {
            "total": total,
            "completed": completed,
            "downloading": downloading,
            "failed": failed,
            "paused": paused,
            "pending": pending,
            "total_size": total_size,
            "downloaded_size": downloaded_size,
            "total_speed": total_speed,
            "progress": (downloaded_size / total_size * 100) if total_size > 0 else 0,
        }

    def _can_start_download(self) -> bool:
        active_count = len(self.get_active_downloads())
        return active_count < self.max_concurrent_downloads

    def _on_progress_updated(
        self, download_id: str, downloaded: int, total: int, speed: float
    ) -> None:
        if download_id in self.downloads:
            item = self.downloads[download_id]
            item.downloaded_size = downloaded
            if total > 0:
                item.file_size = total  # Only update if valid total received
            item.speed = speed
            # ETA is calculated in worker

        self.download_progress.emit(download_id, downloaded, total, speed)

    def _on_status_changed(self, download_id: str, status: DownloadStatus) -> None:
        if download_id in self.downloads:
            item = self.downloads[download_id]
            item.status = status
            if status == DownloadStatus.DOWNLOADING and not item.start_time:
                item.start_time = time.time()
            elif status in [
                DownloadStatus.COMPLETED,
                DownloadStatus.FAILED,
                DownloadStatus.CANCELLED,
            ]:
                item.end_time = time.time()

            self.download_status_changed.emit(download_id, status)
            if (
                status == DownloadStatus.DOWNLOADING
            ):  # Emit download_started when status actually changes
                self.download_started.emit(download_id)

        else:
            logger.warning(f"Status changed for unknown download_id: {download_id}")

    def _on_download_completed(self, download_id: str) -> None:
        logger.info(f"Manager notified: Download completed for {download_id}")
        if download_id in self.downloads:
            # Ensure status
            self.downloads[download_id].status = DownloadStatus.COMPLETED
            self.downloads[download_id].end_time = time.time()
        self.download_completed.emit(download_id)
        self._save_state()
        self._start_next_download()

    def _on_download_failed(self, download_id: str, error_msg: str) -> None:
        logger.error(
            f"Manager notified: Download failed for {download_id} - {error_msg}"
        )
        if download_id in self.downloads:
            item = self.downloads[download_id]
            item.status = DownloadStatus.FAILED  # Ensure status
            item.error_message = error_msg
            item.end_time = time.time()
            item.retry_count += 1

        self.download_failed.emit(download_id, error_msg)
        self._save_state()
        # Retry logic is handled by _check_retries timer, but we can also start next download
        self._start_next_download()

    def _cleanup_worker(self, download_id: str) -> None:
        if download_id in self.workers:
            # self.workers[download_id].deleteLater() # If QObject ownership is an issue
            del self.workers[download_id]
            logger.debug(f"Cleaned up worker for download {download_id}")
        # After a worker finishes (completed, failed, cancelled), try to start a new one.
        self._start_next_download()

    def _start_next_download(self) -> None:
        if not self._can_start_download():
            return

        for download_id, item in self.downloads.items():
            if item.status == DownloadStatus.PENDING:
                logger.info(f"Attempting to start next pending download: {download_id}")
                self.start_download(download_id)
                return  # Start one at a time

    def _check_retries(self) -> None:
        # Iterate over a copy for safe modification
        for download_id, item in list(self.downloads.items()):
            if (
                item.status == DownloadStatus.FAILED
                and item.retry_count < item.max_retries
            ):

                logger.info(
                    f"Retrying download: {download_id} (attempt {item.retry_count + 1}/{item.max_retries})"
                )

                item.status = DownloadStatus.PENDING  # Set to PENDING to be picked up
                item.error_message = None
                # item.start_time = None # Reset start time for the new attempt
                # item.end_time = None

                self.download_status_changed.emit(download_id, item.status)
                if self._can_start_download():
                    self.start_download(download_id)

    def _save_state(self) -> None:
        try:
            state_data = {
                "downloads": {
                    dl_id: item.to_dict() for dl_id, item in self.downloads.items()
                }
            }
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            logger.debug("Download state saved.")
        except Exception as e:
            logger.error(f"Failed to save download state: {e}", exc_info=True)

    def _load_state(self) -> None:
        try:
            if not self.state_file.exists():
                return

            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)

            loaded_items = 0
            for download_id, item_data_dict in state.get("downloads", {}).items():
                # Convert status string back to Enum
                status_str = item_data_dict.get("status")
                try:
                    item_data_dict["status"] = DownloadStatus(status_str)
                except ValueError:
                    logger.warning(
                        f"Invalid status '{status_str}' for {download_id}, defaulting to FAILED."
                    )
                    item_data_dict["status"] = DownloadStatus.FAILED

                item = DownloadItem(**item_data_dict)

                if (
                    item.status == DownloadStatus.DOWNLOADING
                ):  # If app crashed during download
                    item.status = (
                        DownloadStatus.PAUSED
                    )  # Change to paused so user can resume
                    logger.info(
                        f"Download {item.id} was DOWNLOADING, set to PAUSED on load."
                    )

                # Ensure file_path is absolute or handled correctly if relative paths were saved
                # Assuming file_path was saved as intended (e.g., relative to download_dir or absolute)

                self.downloads[download_id] = item
                loaded_items += 1

            if loaded_items > 0:
                logger.info(
                    f"Loaded {loaded_items} downloads from state file: {self.state_file}"
                )

        except Exception as e:
            logger.error(
                f"Failed to load download state from {self.state_file}: {e}",
                exc_info=True,
            )

    def shutdown(self) -> None:
        try:
            logger.info("Shutting down download manager...")
            self.retry_timer.stop()

            active_workers_ids = list(self.workers.keys())
            if active_workers_ids:
                logger.info(f"Cancelling {len(active_workers_ids)} active downloads...")
                for download_id in active_workers_ids:
                    if (
                        download_id in self.workers
                    ):  # Check again as it might be removed by another thread
                        self.workers[download_id].cancel()
                        # self.workers[download_id].wait(2000) # Wait for thread to finish, with timeout

            # Wait for all workers to finish (up to a timeout)
            # This is tricky with QThreads if the main event loop is also shutting down.
            # For now, assume cancel() is enough and workers will terminate.
            # A more robust shutdown might involve QEventLoop processing or direct QThread.wait().

            self._save_state()

            # self.executor.shutdown(wait=True) # Removed as executor is not used

            logger.info("Download manager shutdown process initiated.")

        except Exception as e:
            logger.error(f"Error during download manager shutdown: {e}", exc_info=True)


# Global instance (consider if this is the best pattern for your app structure)
download_manager = DownloadManager()
