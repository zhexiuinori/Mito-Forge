"""
统一日志配置
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """设置日志配置"""
    
    if format_string is None:
        # 使用更简洁的格式，避免在窄终端中换行
        format_string = "%(asctime)s [%(levelname)s] %(message)s"
    
    # 创建根日志器
    logger = logging.getLogger("mito_forge")
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器 - 设置编码以支持emoji
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    
    # 在Windows环境下设置编码
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except Exception:
            pass  # 如果设置失败，继续使用默认编码
    
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定）- 设置UTF-8编码
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(f"mito_forge.{name}")

# 默认设置
setup_logging()