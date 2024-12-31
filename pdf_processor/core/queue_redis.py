import json
import uuid
from typing import Any, Dict, Optional

import redis.asyncio as redis
from cryptography.fernet import Fernet

from pdf_processor.core.queue import BaseQueue, TaskStatus


class RedisQueue(BaseQueue):
    """Redis 기반 작업 큐 구현 (싱글톤)"""

    _instance: Optional["RedisQueue"] = None
    _redis: Optional[redis.Redis] = None
    _fernet: Optional[Fernet] = None

    def __new__(
        cls, redis_url: Optional[str] = None, encryption_key: Optional[str] = None
    ) -> "RedisQueue":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, redis_url: Optional[str] = None, encryption_key: Optional[str] = None):
        # __new__에서 이미 처리되었으므로 초기화 생략
        pass

    @classmethod
    def initialize(cls, redis_url: str, encryption_key: str) -> "RedisQueue":
        """RedisQueue 초기화 (비동기 처리 시작 시 한 번만 호출)"""
        if not cls._instance:
            cls._instance = cls(redis_url, encryption_key)
            cls._redis = redis.from_url(redis_url)
            cls._fernet = Fernet(encryption_key.encode())
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RedisQueue":
        """RedisQueue 인스턴스 반환"""
        if not cls._instance or not cls._redis or not cls._fernet:
            raise RuntimeError(
                "RedisQueue가 초기화되지 않았습니다. initialize()를 먼저 호출하세요."
            )
        return cls._instance

    def _encrypt_data(self, data: Any) -> bytes:
        """데이터 암호화"""
        json_data = json.dumps(data)
        return self._fernet.encrypt(json_data.encode())

    def _decrypt_data(self, encrypted_data: bytes) -> Any:
        """데이터 복호화"""
        json_data = self._fernet.decrypt(encrypted_data).decode()
        return json.loads(json_data)

    async def enqueue(self, task_data: Dict[str, Any]) -> None:
        """작업 추가"""
        task_id = task_data.get("task_id") or f"task_{uuid.uuid4()}"
        task_data["task_id"] = task_id
        encrypted_data = self._encrypt_data(task_data)
        await self._redis.lpush("task_queue", encrypted_data)
        await self.update_task_status(task_id, TaskStatus.PENDING)

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """작업 가져오기"""
        encrypted_data = await self._redis.rpop("task_queue")
        if encrypted_data:
            return self._decrypt_data(encrypted_data)
        return None

    async def store_result(self, task_id: str, result: Any) -> None:
        """작업 결과 저장"""
        encrypted_result = self._encrypt_data(result)
        await self._redis.set(f"result:{task_id}", encrypted_result)

    async def get_result(self, task_id: str) -> Optional[Any]:
        """작업 결과 조회"""
        encrypted_result = await self._redis.get(f"result:{task_id}")
        if encrypted_result:
            return self._decrypt_data(encrypted_result)
        return None

    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """작업 상태 업데이트"""
        await self._redis.set(f"status:{task_id}", status.value)

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """작업 상태 조회"""
        status = await self._redis.get(f"status:{task_id}")
        if status:
            return TaskStatus(status.decode())
        return None
