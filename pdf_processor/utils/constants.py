from enum import Enum

PACKAGE_BANNER = """
██████╗ ██████╗ ███████╗    ██████╗ ██████╗  ██████╗  ██████╗███████╗███████╗███████╗ ██████╗ ██████╗ 
██╔══██╗██╔══██╗██╔════╝    ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝██╔════╝██╔═══██╗██╔══██╗
██████╔╝██║  ██║█████╗      ██████╔╝██████╔╝██║   ██║██║     █████╗  ███████╗███████╗██║   ██║██████╔╝
██╔═══╝ ██║  ██║██╔══╝      ██╔═══╝ ██╔══██╗██║   ██║██║     ██╔══╝  ╚════██║╚════██║██║   ██║██╔══██╗
██║     ██████╔╝██║         ██║     ██║  ██║╚██████╔╝╚██████╗███████╗███████║███████║╚██████╔╝██║  ██║
╚═╝     ╚═════╝ ╚═╝         ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
"""


class PDFProcessType(str, Enum):
    """PDF Processing Types"""

    INVOICE = "invoice"
    RECEIPT = "receipt"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class ProcessStep(str, Enum):
    """Processing Stages"""

    ANALYSIS = "analysis"
    EXTRACTION = "extraction"


class RedisKeys:
    """Utility for Redis Key Generation"""

    @staticmethod
    def get_analysis_key(task_id: str) -> str:
        """Key for storing PDF analysis results"""
        return f"pdf:analysis:{task_id}"

    @staticmethod
    def get_extraction_key(task_id: str, process_type: str) -> str:
        """Key for storing data extraction results"""
        return f"pdf:extraction:{process_type}:{task_id}"

    @staticmethod
    def get_status_key(task_id: str) -> str:
        """Key for storing task status"""
        return f"pdf:status:{task_id}"
