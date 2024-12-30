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
        result_prefix: str = "pdf_result",
        status_prefix: str = "pdf_status",
    ):
        self.redis = redis.from_url(redis_url)
        self.queue_name = queue_name
        self.result_prefix = result_prefix
        self.status_prefix = status_prefix
        self.fernet = Fernet(encryption_key.encode())

    def _get_result_key(self, task_id: str, pdf_type: str) -> str:
        """결과 저장을 위한 Redis 키 생성"""
        return f"{self.result_prefix}:{pdf_type}:{task_id}"

    def _get_status_key(self, task_id: str, pdf_type: str) -> str:
        """상태 저장을 위한 Redis 키 생성"""
        return f"{self.status_prefix}:{pdf_type}:{task_id}"

    def _get_queue_key(self, pdf_type: str) -> str:
        """큐 이름 생성"""
        return f"{self.queue_name}:{pdf_type}"

    async def enqueue(self, task_data: Dict[str, Any]) -> str:
        task_id = generate_task_id()
        pdf_type = task_data.get("pdf_type", "text")
        task_data["task_id"] = task_id

        # 작업 데이터 암호화
        encrypted_data = self.fernet.encrypt(json.dumps(task_data).encode())

        # PDF 유형별 큐에 작업 추가
        queue_key = self._get_queue_key(pdf_type)
        await self.redis.lpush(queue_key, encrypted_data)

        # 초기 상태 설정
        await self.update_task_status(task_id, TaskStatus.PENDING, pdf_type)

        return task_id

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        # 모든 PDF 유형의 큐를 확인
        pdf_types = ["text", "scanned", "password_protected", "copy_protected"]

        for pdf_type in pdf_types:
            queue_key = self._get_queue_key(pdf_type)
            encrypted_data = await self.redis.rpop(queue_key)

            if encrypted_data:
                # 데이터 복호화
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return json.loads(decrypted_data)

        return None

    async def get_task_status(self, task_id: str, pdf_type: str = "text") -> TaskStatus:
        status = await self.redis.get(self._get_status_key(task_id, pdf_type))
        return TaskStatus(status.decode()) if status else TaskStatus.FAILED

    async def update_task_status(
        self, task_id: str, status: TaskStatus, pdf_type: str = "text"
    ) -> None:
        await self.redis.set(self._get_status_key(task_id, pdf_type), status.value)

    async def store_result(
        self, task_id: str, result: Dict[str, Any], ttl: int = 3600, pdf_type: str = "text"
    ) -> None:
        # 결과 데이터 암호화
        encrypted_result = self.fernet.encrypt(json.dumps(result).encode())

        # 결과 저장 및 TTL 설정
        key = self._get_result_key(task_id, pdf_type)
        await self.redis.set(key, encrypted_result)
        await self.redis.expire(key, ttl)

        # 상태 업데이트
        await self.update_task_status(task_id, TaskStatus.COMPLETED, pdf_type)

    async def get_result(self, task_id: str, pdf_type: str = "text") -> Optional[Dict[str, Any]]:
        encrypted_result = await self.redis.get(self._get_result_key(task_id, pdf_type))
        if not encrypted_result:
            return None

        # 결과 복호화
        decrypted_result = self.fernet.decrypt(encrypted_result)
        return json.loads(decrypted_result)
