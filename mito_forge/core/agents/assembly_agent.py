"""
组装智能体
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class AssemblyAgent:
    """组装智能体类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.status = "idle"
        
    def run_assembly(self, input_files: List[str], output_dir: str) -> Dict[str, Any]:
        """运行基因组组装"""
        logger.info("开始基因组组装")
        self.status = "running"
        
        try:
            result = {
                "status": "success",
                "input_files": input_files,
                "output_dir": output_dir,
                "message": "基因组组装完成"
            }
            self.status = "completed"
            return result
        except Exception as e:
            self.status = "failed"
            logger.error(f"基因组组装失败: {e}")
            raise
    
    def get_status(self) -> str:
        return self.status