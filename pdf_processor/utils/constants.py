from enum import Enum


class PDFProcessType(str, Enum):
    """PDF 처리 타입"""

    INVOICE = "invoice"  # 청구서/인보이스
    RESUME = "resume"  # 이력서
    CONTRACT = "contract"  # 계약서
    RECEIPT = "receipt"  # 영수증

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class ProcessStep(str, Enum):
    """처리 단계"""

    ANALYSIS = "analysis"  # PDF 분석 단계
    EXTRACTION = "extraction"  # 데이터 추출 단계


class RedisKeys:
    """Redis 키 생성을 위한 유틸리티"""

    @staticmethod
    def get_analysis_key(task_id: str) -> str:
        """PDF 분석 결과를 저장하기 위한 키"""
        return f"pdf:analysis:{task_id}"

    @staticmethod
    def get_extraction_key(task_id: str, process_type: str) -> str:
        """데이터 추출 결과를 저장하기 위한 키"""
        return f"pdf:extraction:{process_type}:{task_id}"

    @staticmethod
    def get_status_key(task_id: str) -> str:
        """작업 상태를 저장하기 위한 키"""
        return f"pdf:status:{task_id}"
