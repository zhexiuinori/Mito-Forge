"""
配置管理模块

统一管理Mito-Forge的所有配置参数
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ConfigError

class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        # 基本设置
        "threads": 4,
        "memory": "8G",
        "temp_dir": "/tmp/mito_forge",
        "output_dir": "./mito_forge_results",
        
        # 质控设置
        "quality_threshold": 20,
        "min_length": 50,
        "adapter_removal": False,
        
        # 组装设置
        "assembler": "spades",
        "k_values": [21, 33, 55, 77],
        "careful_mode": False,
        
        # 注释设置
        "annotation_tool": "mitos",
        "genetic_code": 2,
        "reference_db": "mitochondria",
        
        # 日志设置
        "log_level": "INFO",
        "log_file": None,
        
        # 智能体设置
        "agent_timeout": 3600,
        "max_retries": 3,
        
        # 知识库设置
        "knowledge_base_path": None,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        
        # 其他设置
        "verbose": False,
        "quiet": False
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认位置
        """
        self.config_file = config_file or self._get_default_config_file()
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _get_default_config_file(self) -> str:
        """获取默认配置文件路径"""
        config_dir = Path.home() / ".mito_forge"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.json")
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                self._config.update(user_config)
            except (json.JSONDecodeError, IOError) as e:
                raise ConfigError(f"无法加载配置文件 {self.config_file}: {e}")
    
    def save(self):
        """保存配置到文件"""
        try:
            config_dir = Path(self.config_file).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise ConfigError(f"无法保存配置文件 {self.config_file}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        # 类型验证
        if key in self.DEFAULT_CONFIG:
            expected_type = type(self.DEFAULT_CONFIG[key])
            if expected_type != type(None) and not isinstance(value, expected_type):
                # 尝试类型转换
                try:
                    if expected_type == int:
                        value = int(value)
                    elif expected_type == float:
                        value = float(value)
                    elif expected_type == bool:
                        value = str(value).lower() in ('true', '1', 'yes', 'on')
                    elif expected_type == list:
                        if isinstance(value, str):
                            value = [item.strip() for item in value.split(',')]
                except (ValueError, TypeError):
                    raise ConfigError(f"配置项 {key} 的值类型错误，期望 {expected_type.__name__}")
        
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """批量更新配置"""
        for key, value in config_dict.items():
            self.set(key, value)
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._config = self.DEFAULT_CONFIG.copy()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证线程数
        if self._config['threads'] <= 0:
            errors.append("线程数必须大于0")
        
        # 验证内存设置
        memory = self._config['memory']
        if isinstance(memory, str) and not memory.endswith(('G', 'M', 'K')):
            errors.append("内存设置格式错误，应为如 '8G', '1024M' 等")
        
        # 验证质量阈值
        if not 0 <= self._config['quality_threshold'] <= 50:
            errors.append("质量阈值应在0-50之间")
        
        # 验证组装器
        valid_assemblers = ['spades', 'unicycler', 'flye']
        if self._config['assembler'] not in valid_assemblers:
            errors.append(f"组装器必须是 {valid_assemblers} 之一")
        
        # 验证注释工具
        valid_annotators = ['mitos', 'geseq', 'prokka']
        if self._config['annotation_tool'] not in valid_annotators:
            errors.append(f"注释工具必须是 {valid_annotators} 之一")
        
        if errors:
            raise ConfigError("配置验证失败:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return key in self._config
    
    def __str__(self) -> str:
        """字符串表示"""
        return json.dumps(self._config, indent=2, ensure_ascii=False)