from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    """작업 상태"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseQueue(ABC):
    """작업 큐 인터페이스"""

    @abstractmethod
    async def enqueue(self, task_data: Dict[str, Any]) -> None:
        """작업 추가"""
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """작업 가져오기"""
        pass

    @abstractmethod
    async def store_result(self, task_id: str, result: Any) -> None:
        """작업 결과 저장"""
        pass

    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[Any]:
        """작업 결과 조회"""
        pass

    @abstractmethod
    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """작업 상태 업데이트"""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """작업 상태 조회"""
        pass
