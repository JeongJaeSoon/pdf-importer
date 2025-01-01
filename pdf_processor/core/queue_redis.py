import json
import uuid
from typing import Any, Dict, Optional

import redis.asyncio as redis
from cryptography.fernet import Fernet

from pdf_processor.core.queue import BaseQueue, TaskStatus


class RedisQueue(BaseQueue):
    """Redis-based task queue implementation (Singleton)"""

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
        # Skip initialization as it's already handled in __new__
        pass

    @classmethod
    def initialize(cls, redis_url: str, encryption_key: str) -> "RedisQueue":
        """Initialize RedisQueue (called once when starting async processing)"""
        if not cls._instance:
            cls._instance = cls(redis_url, encryption_key)
            cls._redis = redis.from_url(redis_url)
            cls._fernet = Fernet(encryption_key.encode())
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RedisQueue":
        """Return RedisQueue instance"""
        if not cls._instance or not cls._redis or not cls._fernet:
            raise RuntimeError("RedisQueue is not initialized. Call initialize() first.")
        return cls._instance

    def _encrypt_data(self, data: Any) -> bytes:
        """Encrypt data"""
        json_data = json.dumps(data)
        return self._fernet.encrypt(json_data.encode())

    def _decrypt_data(self, encrypted_data: bytes) -> Any:
        """Decrypt data"""
        json_data = self._fernet.decrypt(encrypted_data).decode()
        return json.loads(json_data)

    async def enqueue(self, task_data: Dict[str, Any]) -> None:
        """Add task"""
        task_id = task_data.get("task_id") or f"task_{uuid.uuid4()}"
        task_data["task_id"] = task_id
        encrypted_data = self._encrypt_data(task_data)
        await self._redis.lpush("task_queue", encrypted_data)
        await self.update_task_status(task_id, TaskStatus.PENDING)

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Get task"""
        encrypted_data = await self._redis.rpop("task_queue")
        if encrypted_data:
            return self._decrypt_data(encrypted_data)
        return None

    async def store_result(self, task_id: str, result: Any) -> None:
        """Save task result"""
        encrypted_result = self._encrypt_data(result)
        await self._redis.set(f"result:{task_id}", encrypted_result)

    async def get_result(self, task_id: str) -> Optional[Any]:
        """Get task result"""
        encrypted_result = await self._redis.get(f"result:{task_id}")
        if encrypted_result:
            return self._decrypt_data(encrypted_result)
        return None

    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status"""
        await self._redis.set(f"status:{task_id}", status.value)

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        status = await self._redis.get(f"status:{task_id}")
        if status:
            return TaskStatus(status.decode())
        return None
