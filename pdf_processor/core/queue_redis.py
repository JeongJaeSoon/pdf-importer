import json
from typing import Any, Dict, Optional

import redis.asyncio as redis
from cryptography.fernet import Fernet

from .queue import BaseQueue, TaskStatus, generate_task_id


class RedisQueue(BaseQueue):
    """Redis를 사용한 작업 큐 구현"""

    def __init__(
        self,
        redis_url: str,
        encryption_key: str,
        queue_name: str = "pdf_processor_queue",
        result_prefix: str = "pdf_result:",
        status_prefix: str = "pdf_status:",
    ):
        self.redis = redis.from_url(redis_url)
        self.queue_name = queue_name
        self.result_prefix = result_prefix
        self.status_prefix = status_prefix
        self.fernet = Fernet(encryption_key.encode())

    async def enqueue(self, task_data: Dict[str, Any]) -> str:
        task_id = generate_task_id()
        task_data["task_id"] = task_id

        # 작업 데이터 암호화
        encrypted_data = self.fernet.encrypt(json.dumps(task_data).encode())

        # 작업 큐에 추가
        await self.redis.lpush(self.queue_name, encrypted_data)

        # 초기 상태 설정
        await self.update_task_status(task_id, TaskStatus.PENDING)

        return task_id

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        encrypted_data = await self.redis.rpop(self.queue_name)
        if not encrypted_data:
            return None

        # 데이터 복호화
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data)

    async def get_task_status(self, task_id: str) -> TaskStatus:
        status = await self.redis.get(f"{self.status_prefix}{task_id}")
        return TaskStatus(status.decode()) if status else TaskStatus.FAILED

    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        await self.redis.set(f"{self.status_prefix}{task_id}", status.value)

    async def store_result(self, task_id: str, result: Dict[str, Any], ttl: int = 3600) -> None:
        # 결과 데이터 암호화
        encrypted_result = self.fernet.encrypt(json.dumps(result).encode())

        # 결과 저장 및 TTL 설정
        key = f"{self.result_prefix}{task_id}"
        await self.redis.set(key, encrypted_result)
        await self.redis.expire(key, ttl)

        # 상태 업데이트
        await self.update_task_status(task_id, TaskStatus.COMPLETED)

    async def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        encrypted_result = await self.redis.get(f"{self.result_prefix}{task_id}")
        if not encrypted_result:
            return None

        # 결과 복호화
        decrypted_result = self.fernet.decrypt(encrypted_result)
        return json.loads(decrypted_result)
