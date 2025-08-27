"""
Module Workflow Manager

Orchestrates the complete module lifecycle with state management, progress tracking,
and rollback capabilities. Provides a unified interface for guiding users through
the Download → Validate → Install → Configure → Enable workflow.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from src.heal.common.logging_config import get_logger
from .module_models import ModuleConfig, ModuleState

logger = get_logger(__name__)


class WorkflowStep(Enum):
    """Workflow step enumeration"""

    DOWNLOAD = "download"
    VALIDATE = "validate"
    INSTALL = "install"
    CONFIGURE = "configure"
    ENABLE = "enable"
    COMPLETE = "complete"


class WorkflowStatus(Enum):
    """Workflow status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"


@dataclass
class WorkflowStepInfo:
    """Information about a workflow step"""

    step: WorkflowStep
    status: WorkflowStatus = WorkflowStatus.PENDING
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    rollback_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleWorkflow:
    """Complete module workflow state"""

    module_name: str
    workflow_id: str
    current_step: WorkflowStep = WorkflowStep.DOWNLOAD
    steps: Dict[WorkflowStep, WorkflowStepInfo] = field(default_factory=dict)
    overall_progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize workflow steps"""
        if not self.steps:
            for step in WorkflowStep:
                if step != WorkflowStep.COMPLETE:
                    self.steps[step] = WorkflowStepInfo(step=step)


class ModuleWorkflowManager(QObject):
    """Manages module installation workflows with state persistence and rollback"""

    # Signals for workflow events
    workflow_started = Signal(str, str)  # workflow_id, module_name
    workflow_step_started = Signal(str, str)  # workflow_id, step
    workflow_step_completed = Signal(str, str)  # workflow_id, step
    workflow_step_failed = Signal(str, str, str)  # workflow_id, step, error
    workflow_progress_updated = Signal(str, float)  # workflow_id, progress
    workflow_completed = Signal(str)  # workflow_id
    workflow_cancelled = Signal(str)  # workflow_id
    workflow_rollback_started = Signal(str)  # workflow_id
    workflow_rollback_completed = Signal(str)  # workflow_id

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.logger = logger.bind(component="ModuleWorkflowManager")

        # Active workflows
        self.active_workflows: Dict[str, ModuleWorkflow] = {}

        # Workflow persistence
        self.workflows_file = Path("config/workflows.json")
        self.workflows_file.parent.mkdir(exist_ok=True)

        # Step handlers
        self.step_handlers: Dict[WorkflowStep, Callable] = {}
        self.rollback_handlers: Dict[WorkflowStep, Callable] = {}

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_workflows)
        self.auto_save_timer.start(30000)  # Save every 30 seconds

        # Load existing workflows
        self.load_workflows()

        self.logger.info("Module Workflow Manager initialized")

    def register_step_handler(
        self,
        step: WorkflowStep,
        handler: Callable[..., Any],
        rollback_handler: Optional[Callable[..., Any]] = None,
    ) -> None:
        """Register handlers for workflow steps"""
        self.step_handlers[step] = handler
        if rollback_handler:
            self.rollback_handlers[step] = rollback_handler
        self.logger.debug(f"Registered handler for step: {step.value}")

    def start_workflow(
        self,
        module_name: str,
        workflow_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new module workflow"""
        if not workflow_id:
            workflow_id = f"{module_name}_{int(time.time())}"

        # Check if workflow already exists
        if workflow_id in self.active_workflows:
            self.logger.warning(f"Workflow {workflow_id} already exists")
            return workflow_id

        # Create new workflow
        workflow = ModuleWorkflow(
            module_name=module_name, workflow_id=workflow_id, metadata=metadata or {}
        )

        self.active_workflows[workflow_id] = workflow
        self.workflow_started.emit(workflow_id, module_name)

        self.logger.info(
            f"Started workflow {workflow_id} for module {module_name}")
        return workflow_id

    def execute_next_step(self, workflow_id: str) -> bool:
        """Execute the next step in the workflow"""
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False

        workflow = self.active_workflows[workflow_id]
        current_step = workflow.current_step

        # Check if workflow is complete
        if current_step == WorkflowStep.COMPLETE:
            self.logger.info(f"Workflow {workflow_id} already complete")
            return True

        # Get step info
        step_info = workflow.steps[current_step]

        # Skip if step already completed
        if step_info.status == WorkflowStatus.COMPLETED:
            return self._advance_to_next_step(workflow_id)

        # Check if handler exists
        if current_step not in self.step_handlers:
            self.logger.error(
                f"No handler registered for step {current_step.value}")
            self._fail_workflow_step(
                workflow_id, current_step, "No handler registered")
            return False

        # Execute step
        try:
            step_info.status = WorkflowStatus.IN_PROGRESS
            step_info.start_time = time.time()
            step_info.message = f"Executing {current_step.value}..."

            self.workflow_step_started.emit(workflow_id, current_step.value)

            # Call step handler
            handler = self.step_handlers[current_step]
            success = handler(workflow_id, workflow.module_name, step_info)

            if success:
                step_info.status = WorkflowStatus.COMPLETED
                step_info.end_time = time.time()
                step_info.progress = 100.0
                step_info.message = f"{current_step.value} completed successfully"

                self.workflow_step_completed.emit(
                    workflow_id, current_step.value)

                # Advance to next step
                return self._advance_to_next_step(workflow_id)
            else:
                self._fail_workflow_step(
                    workflow_id, current_step, "Step handler returned False"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error executing step {current_step.value}: {e}")
            self._fail_workflow_step(workflow_id, current_step, str(e))
            return False

    def update_step_progress(
        self, workflow_id: str, progress: float, message: str = ""
    ) -> None:
        """Update progress for current workflow step"""
        if workflow_id not in self.active_workflows:
            return

        workflow = self.active_workflows[workflow_id]
        current_step = workflow.current_step

        if current_step in workflow.steps:
            step_info = workflow.steps[current_step]
            step_info.progress = max(0.0, min(100.0, progress))
            if message:
                step_info.message = message

            # Update overall workflow progress
            self._update_overall_progress(workflow_id)

            workflow.updated_at = time.time()

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow"""
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False

        workflow = self.active_workflows[workflow_id]
        current_step = workflow.current_step

        # Mark current step as cancelled
        if current_step in workflow.steps:
            step_info = workflow.steps[current_step]
            step_info.status = WorkflowStatus.CANCELLED
            step_info.end_time = time.time()
            step_info.message = "Cancelled by user"

        self.workflow_cancelled.emit(workflow_id)
        self.logger.info(f"Cancelled workflow {workflow_id}")
        return True

    def rollback_workflow(
        self, workflow_id: str, to_step: Optional[WorkflowStep] = None
    ) -> bool:
        """Rollback workflow to a previous step"""
        if workflow_id not in self.active_workflows:
            self.logger.error(f"Workflow {workflow_id} not found")
            return False

        workflow = self.active_workflows[workflow_id]
        self.workflow_rollback_started.emit(workflow_id)

        try:
            # Determine rollback target
            if to_step is None:
                to_step = WorkflowStep.DOWNLOAD

            # Rollback completed steps in reverse order
            steps_to_rollback = []
            for step in reversed(list(WorkflowStep)):
                if step == WorkflowStep.COMPLETE:
                    continue
                if step == to_step:
                    break
                if workflow.steps[step].status == WorkflowStatus.COMPLETED:
                    steps_to_rollback.append(step)

            # Execute rollback handlers
            for step in steps_to_rollback:
                if step in self.rollback_handlers:
                    try:
                        rollback_handler = self.rollback_handlers[step]
                        rollback_handler(
                            workflow_id, workflow.module_name, workflow.steps[step]
                        )

                        # Reset step status
                        step_info = workflow.steps[step]
                        step_info.status = WorkflowStatus.PENDING
                        step_info.progress = 0.0
                        step_info.start_time = None
                        step_info.end_time = None
                        step_info.error = None

                    except Exception as e:
                        self.logger.error(
                            f"Error rolling back step {step.value}: {e}")

            # Reset workflow to target step
            workflow.current_step = to_step
            self._update_overall_progress(workflow_id)

            self.workflow_rollback_completed.emit(workflow_id)
            self.logger.info(
                f"Rolled back workflow {workflow_id} to step {to_step.value}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Error rolling back workflow {workflow_id}: {e}")
            return False

    def get_workflow(self, workflow_id: str) -> Optional[ModuleWorkflow]:
        """Get workflow by ID"""
        return self.active_workflows.get(workflow_id)

    def get_workflows_for_module(self, module_name: str) -> List[ModuleWorkflow]:
        """Get all workflows for a specific module"""
        return [
            w for w in self.active_workflows.values() if w.module_name == module_name
        ]

    def get_active_workflows(self) -> Dict[str, ModuleWorkflow]:
        """Get all active workflows"""
        return self.active_workflows.copy()

    def remove_workflow(self, workflow_id: str) -> bool:
        """Remove a completed or cancelled workflow"""
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
            self.logger.info(f"Removed workflow {workflow_id}")
            return True
        return False

    def save_workflows(self) -> None:
        """Save workflows to disk"""
        try:
            # Convert workflows to serializable format
            workflows_data = {}
            for workflow_id, workflow in self.active_workflows.items():
                workflows_data[workflow_id] = {
                    "module_name": workflow.module_name,
                    "workflow_id": workflow.workflow_id,
                    "current_step": workflow.current_step.value,
                    "overall_progress": workflow.overall_progress,
                    "created_at": workflow.created_at,
                    "updated_at": workflow.updated_at,
                    "metadata": workflow.metadata,
                    "steps": {
                        step.value: {
                            "status": step_info.status.value,
                            "progress": step_info.progress,
                            "message": step_info.message,
                            "error": step_info.error,
                            "start_time": step_info.start_time,
                            "end_time": step_info.end_time,
                            "rollback_data": step_info.rollback_data,
                        }
                        for step, step_info in workflow.steps.items()
                    },
                }

            with open(self.workflows_file, "w", encoding="utf-8") as f:
                json.dump(workflows_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving workflows: {e}")

    def load_workflows(self) -> None:
        """Load workflows from disk"""
        if not self.workflows_file.exists():
            return

        try:
            with open(self.workflows_file, "r", encoding="utf-8") as f:
                workflows_data = json.load(f)

            for workflow_id, data in workflows_data.items():
                # Reconstruct workflow
                workflow = ModuleWorkflow(
                    module_name=data["module_name"],
                    workflow_id=data["workflow_id"],
                    current_step=WorkflowStep(data["current_step"]),
                    overall_progress=data["overall_progress"],
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    metadata=data["metadata"],
                )

                # Reconstruct steps
                for step_name, step_data in data["steps"].items():
                    step = WorkflowStep(step_name)
                    workflow.steps[step] = WorkflowStepInfo(
                        step=step,
                        status=WorkflowStatus(step_data["status"]),
                        progress=step_data["progress"],
                        message=step_data["message"],
                        error=step_data["error"],
                        start_time=step_data["start_time"],
                        end_time=step_data["end_time"],
                        rollback_data=step_data["rollback_data"],
                    )

                self.active_workflows[workflow_id] = workflow

            self.logger.info(
                f"Loaded {len(workflows_data)} workflows from disk")

        except Exception as e:
            self.logger.error(f"Error loading workflows: {e}")

    def _advance_to_next_step(self, workflow_id: str) -> bool:
        """Advance workflow to next step"""
        workflow = self.active_workflows[workflow_id]
        current_step = workflow.current_step

        # Get next step
        steps = list(WorkflowStep)
        current_index = steps.index(current_step)

        if current_index < len(steps) - 1:
            next_step = steps[current_index + 1]
            workflow.current_step = next_step
            workflow.updated_at = time.time()

            self._update_overall_progress(workflow_id)

            if next_step == WorkflowStep.COMPLETE:
                self.workflow_completed.emit(workflow_id)
                self.logger.info(
                    f"Workflow {workflow_id} completed successfully")

            return True

        return False

    def _fail_workflow_step(self, workflow_id: str, step: WorkflowStep, error: str) -> None:
        """Mark workflow step as failed"""
        workflow = self.active_workflows[workflow_id]
        step_info = workflow.steps[step]

        step_info.status = WorkflowStatus.FAILED
        step_info.end_time = time.time()
        step_info.error = error
        step_info.message = f"Failed: {error}"

        workflow.updated_at = time.time()

        self.workflow_step_failed.emit(workflow_id, step.value, error)
        self.logger.error(
            f"Workflow {workflow_id} step {step.value} failed: {error}")

    def _update_overall_progress(self, workflow_id: str) -> None:
        """Update overall workflow progress"""
        workflow = self.active_workflows[workflow_id]

        # Calculate progress based on completed steps
        total_steps = len(
            [s for s in WorkflowStep if s != WorkflowStep.COMPLETE])
        completed_steps = len(
            [s for s in workflow.steps.values() if s.status ==
             WorkflowStatus.COMPLETED]
        )

        # Add partial progress from current step
        current_step_progress = 0.0
        if workflow.current_step in workflow.steps:
            current_step_info = workflow.steps[workflow.current_step]
            if current_step_info.status == WorkflowStatus.IN_PROGRESS:
                current_step_progress = current_step_info.progress / 100.0

        overall_progress = (
            (completed_steps + current_step_progress) / total_steps * 100.0
        )
        workflow.overall_progress = min(100.0, overall_progress)

        self.workflow_progress_updated.emit(
            workflow_id, workflow.overall_progress)
