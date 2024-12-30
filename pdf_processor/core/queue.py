import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseQueue(ABC):
    """작업 큐 관리를 위한 기본 추상 클래스"""

    @abstractmethod
    async def enqueue(self, task_data: Dict[str, Any]) -> str:
        """작업을 큐에 추가하고 작업 ID를 반환"""
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """큐에서 다음 작업을 가져옴"""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """작업 상태 조회"""
        pass

    @abstractmethod
    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """작업 상태 업데이트"""
        pass

    @abstractmethod
    async def store_result(self, task_id: str, result: Dict[str, Any], ttl: int = 3600) -> None:
        """작업 결과 저장 (TTL 포함)"""
        pass

    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 결과 조회"""
        pass


def generate_task_id() -> str:
    """고유한 작업 ID 생성"""
    return str(uuid.uuid4())
