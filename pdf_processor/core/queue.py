from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    """Task Status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseQueue(ABC):
    """Task Queue Interface"""

    @abstractmethod
    async def enqueue(self, task_data: Dict[str, Any]) -> None:
        """Add task"""
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Get task"""
        pass

    @abstractmethod
    async def store_result(self, task_id: str, result: Any) -> None:
        """Save task result"""
        pass

    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[Any]:
        """Get task result"""
        pass

    @abstractmethod
    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status"""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        pass
