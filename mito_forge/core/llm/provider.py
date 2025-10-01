"""
统一的模型调用接口
支持本地模型和云端 API 的抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import re
from pathlib import Path

class ModelProvider(ABC):
    """统一的模型调用接口，支持云端和本地模型"""
    
    def __init__(self, model: str, **kwargs):
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    def generate(self, prompt: str, *, system: Optional[str] = None, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户提示词
            system: 系统提示词（可选）
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            str: 模型生成的文本
        """
        raise NotImplementedError
    
    def generate_json(
        self, 
        prompt: str, 
        *, 
        system: Optional[str] = None, 
        schema: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化 JSON 响应
        
        Args:
            prompt: 用户提示词
            system: 系统提示词（可选）
            schema: JSON Schema 约束（可选）
            max_retries: 最大重试次数
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 解析后的 JSON 对象
        """
        # 强制 JSON 输出的系统提示
        json_system = (system or "") + "\n\n请严格按照 JSON 格式输出，不要包含任何其他文本。"
        
        for attempt in range(max_retries + 1):
            try:
                # 生成响应
                response = self.generate(prompt, system=json_system, **kwargs)
                
                # 尝试解析 JSON
                parsed = self._parse_json_response(response)
                
                # 如果有 schema，进行验证
                if schema:
                    self._validate_json_schema(parsed, schema)
                
                return parsed
                
            except Exception as e:
                if attempt == max_retries:
                    # 最后一次尝试失败，返回错误信息
                    return {
                        "error": f"Failed to generate valid JSON after {max_retries + 1} attempts",
                        "last_error": str(e),
                        "raw_response": response if 'response' in locals() else None
                    }
                
                # 重试时调整提示词
                if attempt > 0:
                    prompt = f"{prompt}\n\n注意：请确保输出是有效的 JSON 格式，上次尝试失败了。"
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        从响应中提取并解析 JSON
        
        Args:
            response: 模型原始响应
            
        Returns:
            Dict[str, Any]: 解析后的 JSON
            
        Raises:
            ValueError: 无法解析 JSON 时抛出
        """
        # 首先尝试直接解析
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试提取代码块中的 JSON
        json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        for block in json_blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue
        
        # 尝试查找第一个完整的 JSON 对象
        start = response.find('{')
        if start != -1:
            brace_count = 0
            for i, char in enumerate(response[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            return json.loads(response[start:i+1])
                        except json.JSONDecodeError:
                            break
        
        # 所有方法都失败了
        raise ValueError(f"Could not extract valid JSON from response: {response[:200]}...")
    
    def _validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        简单的 JSON Schema 验证
        
        Args:
            data: 要验证的数据
            schema: JSON Schema
            
        Raises:
            ValueError: 验证失败时抛出
        """
        # 这里实现简单的验证逻辑
        # 实际项目中可以使用 jsonschema 库
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 检查必需字段
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # 检查字段类型
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get("type")
                if expected_type and not self._check_type(data[field], expected_type):
                    raise ValueError(f"Field '{field}' has wrong type. Expected: {expected_type}")
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值的类型是否符合预期"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查模型提供者是否可用
        
        Returns:
            bool: 是否可用
        """
        raise NotImplementedError
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model": self.model,
            "provider": self.__class__.__name__,
            "config": self.config
        }