"""
Agent 基类定义
所有具体 Agent（QC、Assembly、Annotation 等）的基础接口
"""
import abc
import uuid
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from .types import AgentStatus, StageResult, TaskSpec, AgentEvent, AgentCapability, AgentMetrics
from ...utils.logging import get_logger

# 延迟导入 LLM 相关模块，避免启动时依赖检查
def _get_model_config_manager():
    """延迟导入 ModelConfigManager"""
    try:
        from ..llm.config_manager import ModelConfigManager
        return ModelConfigManager
    except ImportError as e:
        logger.warning(f"LLM 功能不可用: {e}")
        return None

def _get_model_provider():
    """延迟导入 ModelProvider"""
    try:
        from ..llm.provider import ModelProvider
        return ModelProvider
    except ImportError as e:
        logger.warning(f"LLM 提供者不可用: {e}")
        return None

logger = get_logger(__name__)

# RAG 共享单例（延迟创建）
_SHARED_CHROMA = None

class HashEmbeddingFunction:
    """
    轻量级本地哈希嵌入器（完全离线）：
    - 字符 n-gram (2..4)，固定维度 2048
    - 采用 SHA1 对 n-gram 映射到桶，TF 计数后做 L2 归一化
    - 兼容 Chroma 1.1.x：提供 __call__/embed_documents/embed_query/name/is_legacy
    """
    def __init__(self, n_features: int = 2048, ngram_min: int = 2, ngram_max: int = 4):
        self.n_features = int(n_features)
        self.ngram_min = int(ngram_min)
        self.ngram_max = int(ngram_max)

    def name(self):
        return "local-hash"

    def is_legacy(self):
        return True

    def _vectorize_one(self, text: str):
        import math, hashlib
        vec = [0.0] * self.n_features
        if not text:
            return vec
        t = text.replace("\n", " ").replace("\r", " ")
        n = len(t)
        for ngram_len in range(self.ngram_min, self.ngram_max + 1):
            if ngram_len <= 0 or ngram_len > n:
                continue
            for i in range(0, n - ngram_len + 1):
                g = t[i:i+ngram_len]
                h = hashlib.sha1(g.encode("utf-8")).digest()
                idx = int.from_bytes(h[:8], "big") % self.n_features
                vec[idx] += 1.0
        s = math.sqrt(sum(v*v for v in vec))
        if s > 0:
            vec = [v / s for v in vec]
        return vec

    def _vectorize(self, texts):
        if not texts:
            return []
        return [self._vectorize_one(x or "") for x in texts]

    def __call__(self, input):
        return self._vectorize(input)

    def embed_documents(self, input):
        return self._vectorize(input)

    def embed_query(self, input):
        if isinstance(input, str):
            return self._vectorize([input])
        return self._vectorize(input)

class BaseAgent(abc.ABC):
    """
    Agent 基类 - 定义统一的生命周期和接口
    
    所有 Agent 必须实现：
    1. prepare() - 准备阶段（检查工具、创建目录等）
    2. run() - 核心执行逻辑
    3. finalize() - 清理和后处理
    4. get_capability() - 返回能力描述
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        # RAG/Mem0 默认开启与默认参数
        self.config.setdefault("enable_rag", True)
        self.config.setdefault("rag_top_k", 4)
        self.config.setdefault("enable_memory", True)
        # 每个 Agent 独立的 Mem0 客户端缓存
        self._mem0 = None
        self.status = AgentStatus.IDLE
        self.current_task: Optional[TaskSpec] = None
        self.metrics = AgentMetrics()
        
        # 事件回调 - 用于向 Supervisor 或 CLI 报告状态
        self.event_callback: Optional[Callable[[AgentEvent], None]] = None
        
        # 工作目录和日志
        self.workdir: Optional[Path] = None
        self.logs_dir: Optional[Path] = None
        
        # LLM 提供者 - 延迟初始化
        self._provider: Optional[ModelProvider] = None
        self._profile_name: Optional[str] = config.get("llm_profile") if config else None
    
    def set_event_callback(self, callback: Callable[[AgentEvent], None]):
        """设置事件回调函数"""
        self.event_callback = callback
    
    def emit_event(self, event_type: str, **payload):
        """发送事件到上层（Supervisor/CLI）"""
        if self.event_callback and self.current_task:
            event = AgentEvent(
                event_type=event_type,
                agent_name=self.name,
                task_id=self.current_task.task_id,
                payload=payload
            )
            self.event_callback(event)
            # Mem0 记忆集成（可选）
            try:
                if self.config.get("enable_memory"):
                    self.memory_write({
                        "event_type": event_type,
                        "agent_name": self.name,
                        "task_id": self.current_task.task_id,
                        "tags": [self.name, event_type],
                        "payload": payload,
                    })
            except Exception:
                # 记忆不可用时静默跳过
                pass
    
    def run_tool(self, exe: str, args, cwd: Path, env: Optional[dict] = None, timeout: Optional[int] = None) -> dict:
        """
        通用外部工具执行器：
        - 先用 shutil.which 检查可执行是否存在（允许 exe 为 'spades.py'/'spades' 等）
        - 使用 subprocess.run 执行（shell=False），将 stdout/stderr 写入工作目录日志文件
        - 返回一个 dict: {exit_code, stdout_path, stderr_path, elapsed_sec}
        """
        import shutil, subprocess, time
        resolved = shutil.which(exe) or shutil.which(exe.split("/")[-1]) or shutil.which(exe.split("\\")[-1])
        if resolved is None:
            # Fallback: search in project's tools/bin via ToolsManager
            try:
                from ...utils.tools_manager import ToolsManager
                tm = ToolsManager(project_root=Path.cwd())
                tool_name = Path(exe).stem
                p = tm.where(tool_name)
                if p:
                    resolved = str(p)
            except Exception:
                resolved = None
        if resolved is None:
            return {"exit_code": 127, "stdout_path": "", "stderr_path": "", "elapsed_sec": 0.0}

        dry_run = bool(self.config.get("dry_run") or os.getenv("MITO_DRY_RUN"))
        stdout_path = Path(cwd) / f"{Path(exe).name}.stdout.log"
        stderr_path = Path(cwd) / f"{Path(exe).name}.stderr.log"
        if dry_run:
            # 不实际执行，直接返回成功
            try:
                stdout_path.write_text("DRY RUN\\n")
                stderr_path.write_text("")
            except Exception:
                pass
            return {"exit_code": 0, "stdout_path": str(stdout_path), "stderr_path": str(stderr_path), "elapsed_sec": 0.0}

        cmd = [resolved] + list(args)
        env_all = os.environ.copy()
        
        # 检查工具是否需要conda环境
        tool_name = Path(exe).stem
        try:
            from ...utils.tool_env_manager import ToolEnvironmentManager
            env_mgr = ToolEnvironmentManager()
            
            # 获取工具需要的环境名称
            required_env = env_mgr.get_tool_required_env(tool_name)
            
            if required_env:
                # 检查环境是否存在
                if env_mgr.env_exists(required_env):
                    # 注入环境的bin路径到PATH
                    env_bin_path = env_mgr.get_env_bin_path(required_env)
                    if env_bin_path:
                        env_all["PATH"] = f"{env_bin_path}:{env_all.get('PATH', '')}"
                        logger.info(f"Using conda environment: mito-forge-{required_env}")
                else:
                    logger.warning(f"Tool {tool_name} requires environment '{required_env}' but it's not installed")
                    logger.warning(f"Run: mito-forge doctor  # to setup environment")
        except Exception as e:
            logger.debug(f"Failed to setup tool environment: {e}")
        
        if env:
            env_all.update(env)
        start = time.time()
        with open(stdout_path, "w", encoding="utf-8") as out, open(stderr_path, "w", encoding="utf-8") as err:
            proc = subprocess.run(cmd, cwd=str(cwd), env=env_all, stdout=out, stderr=err, timeout=timeout or self.config.get("tool_timeout"))
        elapsed = time.time() - start
        return {"exit_code": proc.returncode, "stdout_path": str(stdout_path), "stderr_path": str(stderr_path), "elapsed_sec": elapsed}

    def execute_task(self, task: TaskSpec) -> StageResult:
        """
        执行完整任务流程 - 外部调用的主入口
        包含完整的生命周期管理和异常处理
        """
        self.current_task = task
        self.status = AgentStatus.PREPARING
        self.metrics = AgentMetrics()
        
        try:
            # 发送开始事件
            self.emit_event("started", task_spec=task)
            
            # 准备阶段
            self.prepare(task.workdir or Path("work") / task.task_id, **task.inputs)
            
            # 执行阶段
            self.status = AgentStatus.RUNNING
            result = self.run(task.inputs, **task.config)
            
            # 完成阶段
            self.finalize()
            self.status = AgentStatus.FINISHED
            self.metrics.finish()
            
            # 填充结果元数据
            result.agent_name = self.name
            result.stage_name = task.agent_type
            result.agent_metrics = self.metrics
            
            # 发送完成事件
            self.emit_event("finished", result=result)
            
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.metrics.finish()
            
            # 创建失败结果
            error_result = StageResult(
                status=AgentStatus.FAILED,
                errors=[str(e)],
                agent_name=self.name,
                stage_name=task.agent_type if task else "unknown",
                agent_metrics=self.metrics
            )
            
            # 发送错误事件
            self.emit_event("error", error=str(e), result=error_result)
            
            return error_result
        
        finally:
            self.current_task = None
    
    @abc.abstractmethod
    def prepare(self, workdir: Path, **kwargs) -> None:
        """
        准备阶段 - 在执行前的初始化工作
        
        Args:
            workdir: 工作目录
            **kwargs: 任务输入参数
            
        应该包含：
        - 检查必需的工具是否可用
        - 创建工作目录结构
        - 验证输入文件
        - 设置日志路径
        """
        pass
    
    @abc.abstractmethod
    def run(self, inputs: Dict[str, Any], **config) -> StageResult:
        """
        核心执行逻辑
        
        Args:
            inputs: 输入数据字典
            **config: 配置参数
            
        Returns:
            StageResult: 标准化执行结果
            
        应该包含：
        - 调用外部工具或执行算法
        - 实时报告进度（通过 emit_event）
        - 解析工具输出
        - 生成统计指标
        """
        pass
    
    @abc.abstractmethod
    def finalize(self) -> None:
        """
        清理和后处理阶段
        
        应该包含：
        - 清理临时文件
        - 移动结果文件到最终位置
        - 生成摘要报告
        - 释放资源
        """
        pass
    
    @abc.abstractmethod
    def get_capability(self) -> AgentCapability:
        """
        返回 Agent 能力描述
        用于 Supervisor 进行任务分配决策
        """
        pass
    
    def get_status(self) -> AgentStatus:
        """获取当前状态"""
        return self.status
    
    def cancel(self) -> bool:
        """
        取消当前执行（如果支持）
        
        Returns:
            bool: 是否成功取消
        """
        if self.status in (AgentStatus.RUNNING, AgentStatus.PREPARING):
            self.status = AgentStatus.CANCELLED
            self.emit_event("cancelled")
            return True
        return False
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        验证输入参数
        
        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []
        capability = self.get_capability()
        
        # 检查必需的输入类型
        for input_type in capability.supported_inputs:
            if input_type not in inputs:
                errors.append(f"Missing required input: {input_type}")
        
        return errors
    
    def estimate_resources(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        估算资源需求
        
        Returns:
            Dict: 包含 cpu_cores, memory_gb, disk_gb, estimated_time_sec 等
        """
        capability = self.get_capability()
        return capability.resource_requirements.copy()
    
    # ========== LLM 提供者相关方法 ==========
    
    def get_llm_provider(self):
        """
        获取 LLM 提供者实例（延迟初始化）
        
        Returns:
            ModelProvider: 统一的模型提供者，如果不可用则返回 None
        """
        if self._provider is None:
            try:
                ModelConfigManager = _get_model_config_manager()
                if ModelConfigManager is None:
                    logger.warning(f"Agent {self.name}: LLM 功能不可用，ModelConfigManager 导入失败")
                    return None
                
                config_manager = ModelConfigManager()
                if self._profile_name:
                    self._provider = config_manager.create_provider(self._profile_name)
                    logger.info(f"Agent {self.name} using LLM profile: {self._profile_name}")
                else:
                    self._provider = config_manager.create_provider_with_fallback()
                    logger.info(f"Agent {self.name} using default LLM provider with fallback")
            except Exception as e:
                logger.warning(f"Agent {self.name} LLM provider 初始化失败: {e}")
                logger.info(f"Agent {self.name} 将在无 LLM 模式下运行")
                return None
        
        return self._provider
    
    def generate_llm_response(
        self, 
        prompt: str, 
        *, 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成 LLM 文本响应的便捷方法
        # RAG 集成（可选）
        try:
            if self.config.get("enable_rag"):
                prompt, _ = self.rag_augment(prompt, task=self.current_task, top_k=int(self.config.get("rag_top_k", 4)))
        except Exception:
            # RAG 不可用时静默跳过
            pass
        
        Args:
            prompt: 用户提示词
            system: 系统提示词
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            str: LLM 生成的文本，如果 LLM 不可用则返回默认响应
        """
        provider = self.get_llm_provider()
        
        if provider is None:
            # LLM 不可用时的降级处理
            logger.warning(f"Agent {self.name}: LLM 不可用，返回默认响应")
            return f"[LLM不可用] 基于规则的分析结果 - 提示词: {prompt[:100]}..."
        
        # 记录 LLM 调用
        self.emit_event("llm_call", prompt_length=len(prompt), system_length=len(system or ""))
        
        try:
            response = provider.generate(prompt, system=system, **kwargs)
            logger.debug(f"Agent {self.name} LLM response length: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Agent {self.name} LLM generation failed: {e}")
            self.emit_event("llm_error", error=str(e))
            # 降级处理而不是抛出异常
            return f"[LLM错误] 无法生成响应: {str(e)}"
    
    def generate_llm_json(
        self, 
        prompt: str, 
        *, 
        system: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化 JSON 响应的便捷方法
        # RAG 集成（可选）
        try:
            if self.config.get("enable_rag"):
                prompt, _ = self.rag_augment(prompt, task=self.current_task, top_k=int(self.config.get("rag_top_k", 4)))
        except Exception:
            pass
        
        Args:
            prompt: 用户提示词
            system: 系统提示词
            schema: JSON Schema 约束
            max_retries: 最大重试次数
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 解析后的 JSON 对象
        """
        provider = self.get_llm_provider()
        
        # 记录 LLM 调用
        self.emit_event("llm_json_call", 
                       prompt_length=len(prompt), 
                       system_length=len(system or ""),
                       has_schema=schema is not None)
        
        try:
            response = provider.generate_json(
                prompt, 
                system=system, 
                schema=schema, 
                max_retries=max_retries, 
                **kwargs
            )
            logger.debug(f"Agent {self.name} LLM JSON response keys: {list(response.keys())}")
            return response
        except Exception as e:
            logger.error(f"Agent {self.name} LLM JSON generation failed: {e}")
            self.emit_event("llm_json_error", error=str(e))
            raise
    
    def get_llm_info(self) -> Dict[str, Any]:
        """
        获取当前 LLM 提供者信息
        
        Returns:
            Dict: 提供者信息
        """
        try:
            provider = self.get_llm_provider()
            return provider.get_model_info()
        except Exception as e:
            return {"error": str(e), "available": False}
    
    # ========== RAG 与记忆钩子（默认自动探测，可用即启用） ==========
    def _get_shared_chroma(self):
        """
        获取共享的 Chroma 客户端与集合。创建失败时返回 None。
        """
        global _SHARED_CHROMA
        if _SHARED_CHROMA is not None:
            return _SHARED_CHROMA
        try:
            from pathlib import Path as _P
            import chromadb
            base = _P("work") / "chroma"
            base.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(base))
            # 仅使用本地 Hash 嵌入（默认离线、零依赖）
            emb = HashEmbeddingFunction()

            collection = client.get_or_create_collection(
                name="knowledge",
                metadata={"hnsw:space": "cosine"},
                embedding_function=emb,
            )
            _SHARED_CHROMA = {"client": client, "collection": collection}
            return _SHARED_CHROMA
        except Exception:
            return None

    def _get_mem0(self):
        """
        获取（并缓存）当前 Agent 独立的 Mem0 客户端。失败时返回 None。
        """
        if getattr(self, "_mem0", None) is not None:
            return self._mem0
        try:
            from mem0 import Mem0
            self._mem0 = Mem0()
            return self._mem0
        except Exception:
            self._mem0 = None
            return None
    def rag_augment(self, prompt: str, task: Optional[TaskSpec] = None, top_k: int = 4) -> (str, List[Dict[str, Any]]):
        """
        使用 Chroma 进行检索增强，返回增强后的提示与引用条目。
        如不可用则返回原始提示与空列表。
        """
        # 支持通过环境变量模拟 RAG 返回，便于无依赖快速联调
        try:
            flag = (os.getenv("MITO_RAG_SIMULATE") or "").strip().lower()
            if flag in {"1", "true", "yes", "on"}:
                simulated_citations: List[Dict[str, Any]] = [
                    {"title": "模拟知识库条目：Assembly Best Practices", "source": "sim://kb/assembly_best_practices", "score": 0.99},
                    {"title": "模拟知识库条目：QC Parameters", "source": "sim://kb/qc_parameters", "score": 0.97},
                ]
                augmented = (
                    f"{prompt}"
                    + "\n参考资料（模拟）："
                    + "\n- " + simulated_citations[0]["title"]
                    + "\n- " + simulated_citations[1]["title"]
                )
                return augmented, simulated_citations
        except Exception:
            # 若环境读取异常，继续正常路径
            pass
        try:
            shared = self._get_shared_chroma()
            if not shared or "collection" not in shared or shared["collection"] is None:
                return prompt, []
            collection = shared["collection"]
            query_text = prompt
            res = collection.query(query_texts=[query_text], n_results=top_k)
            citations: List[Dict[str, Any]] = []
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            for i, doc in enumerate(docs):
                meta = metas[i] if i < len(metas) else {}
                citations.append({
                    "title": meta.get("title") or meta.get("id") or f"doc_{i}",
                    "source": meta.get("source") or "",
                    "snippet": (doc or "")[:320],})
            if citations:
                lines = ["参考资料:"]
                lines += [f"- {c['title']}: {c['snippet']}" for c in citations]
                augmented = prompt + "\n" + "\n".join(lines)
                return augmented, citations
            return prompt, []
        except Exception:
            return prompt, []
    
    def memory_query(self, tags: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        查询 Mem0 记忆（短期上下文）。不可用时返回空列表。
        每个 Agent 保持独立的 Mem0 实例。
        """
        try:
            mem = self._get_mem0()
            if mem is None:
                return []
            items = mem.query({"tags": tags}, top_k=top_k)
            return items or []
        except Exception:
            return []
    
    def memory_write(self, event: Dict[str, Any]) -> None:
        """
        写入 Mem0 记忆（长期存储）。不可用时静默跳过。
        每个 Agent 保持独立的 Mem0 实例。
        """
        try:
            mem = self._get_mem0()
            if mem is None:
                return
            mem.write(event)
        except Exception:
            pass
    
    def auto_adjust_parameters(self, 
                              error_msg: str, 
                              current_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据错误信息自动调整工具参数
        
        这是一个简单的规则系统，基于常见错误模式自动修复参数。
        可以被子类覆盖以实现更复杂的调整逻辑。
        
        Args:
            error_msg: 错误消息
            current_params: 当前参数配置
        
        Returns:
            调整后的参数配置
        
        支持的错误类型：
        - Out of Memory (OOM): 减少线程数和内存使用
        - Timeout: 增加超时时间
        - Input Format: 启用严格模式
        - Disk Space: 启用压缩和清理临时文件
        """
        adjusted = current_params.copy()
        error_lower = error_msg.lower()
        
        # 内存不足错误
        if any(keyword in error_lower for keyword in ["out of memory", "oom", "memory error", "cannot allocate"]):
            logger.info("🔧 Detected OOM error, adjusting memory-related parameters")
            
            # 减少线程数
            if "threads" in adjusted:
                old_threads = adjusted["threads"]
                adjusted["threads"] = max(1, old_threads // 2)
                logger.info(f"   Reducing threads: {old_threads} → {adjusted['threads']}")
            
            # 减少内存参数
            if "memory" in adjusted:
                old_mem = adjusted["memory"]
                adjusted["memory"] = max(1, int(old_mem * 0.6))
                logger.info(f"   Reducing memory: {old_mem}GB → {adjusted['memory']}GB")
            
            # SPAdes 特定参数
            if "careful" in adjusted:
                adjusted["careful"] = False
                logger.info("   Disabling careful mode to save memory")
        
        # 超时错误
        elif any(keyword in error_lower for keyword in ["timeout", "timed out", "time limit"]):
            logger.info("🔧 Detected timeout error, adjusting time-related parameters")
            
            if "timeout" in adjusted:
                old_timeout = adjusted["timeout"]
                adjusted["timeout"] = int(old_timeout * 1.5)
                logger.info(f"   Increasing timeout: {old_timeout}s → {adjusted['timeout']}s")
            else:
                adjusted["timeout"] = 3600  # 1 hour default
                logger.info(f"   Setting timeout: {adjusted['timeout']}s")
        
        # 输入格式错误
        elif any(keyword in error_lower for keyword in ["format", "invalid input", "parse error", "malformed"]):
            logger.info("🔧 Detected format error, enabling strict input handling")
            
            adjusted["careful_mode"] = True
            adjusted["ignore_errors"] = False
            logger.info("   Enabling careful mode and strict validation")
        
        # 磁盘空间不足
        elif any(keyword in error_lower for keyword in ["disk", "no space", "storage", "write error"]):
            logger.info("🔧 Detected disk space error, enabling compression")
            
            adjusted["compress"] = True
            adjusted["keep_intermediate"] = False
            logger.info("   Enabling compression and removing intermediate files")
        
        # K-mer 相关错误（组装工具特定）
        elif any(keyword in error_lower for keyword in ["kmer", "k-mer", "coverage too low"]):
            logger.info("🔧 Detected k-mer error, adjusting k-mer size")
            
            if "kmer" in adjusted or "k" in adjusted:
                key = "kmer" if "kmer" in adjusted else "k"
                old_k = adjusted[key]
                adjusted[key] = max(21, old_k - 10)  # 减小 k-mer 大小
                logger.info(f"   Reducing k-mer size: {old_k} → {adjusted[key]}")
        
        # 返回调整后的参数
        if adjusted != current_params:
            logger.info(f"✓ Parameters adjusted based on error pattern")
            return adjusted
        else:
            logger.debug("No parameter adjustments made")
            return current_params