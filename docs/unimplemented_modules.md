# 未实现功能模块拆分清单

说明：以下为“纯CLI + 模块化架构 + LangGraph主管智能体”的未实现模块清单。每个模块包含建议路径、职责、关键函数与输入/输出约定。当前仅用于规划，无需立即实现。

## 1) 工具执行与封装层（高优先级）
- [ ] mito_forge/tools/shell_runner.py
  - 职责：统一外部命令执行（stdout/stderr/returncode），支持超时、cwd、env
  - 函数：
    - run_cmd(cmd: List[str], cwd: Path|None, env: Dict[str,str]|None, timeout: int|None) -> ShellResult
  - I/O：输入命令与运行上下文；输出标准化结果对象

- [ ] mito_forge/tools/tool_discovery.py
  - 职责：工具路径解析（配置/环境PATH），版本获取
  - 函数：
    - resolve_tool(tool_name: str, config: Dict[str,str]) -> str|None
    - get_version(tool_path: str, version_args: Tuple[str,...]=("--version",)) -> str|None

- [ ] mito_forge/tools/fastqc.py
  - 职责：封装FastQC运行与输出解析
  - 函数：
    - run_fastqc(inputs: List[Path], out_dir: Path, threads: int, config: Dict) -> Dict[str,str]
  - 输出：报告路径、QC指标JSON

- [ ] mito_forge/tools/trimmomatic.py（可选）
  - 职责：低质量/接头序列清理
  - 函数：
    - run_trimmomatic(R1: Path, R2: Path, out_dir: Path, args: Dict, config: Dict) -> Dict[str,Path]

- 组装器封装
  - [ ] mito_forge/tools/spades.py
  - [ ] mito_forge/tools/unicycler.py
  - [ ] mito_forge/tools/flye.py
  - 职责：统一组装接口，产出 contigs.fasta 与统计
  - 函数示例：
    - run_spades(inputs: List[Path], out_dir: Path, threads: int, params: Dict, config: Dict) -> Dict[str,Path]

- 注释工具封装
  - [ ] mito_forge/tools/mitos.py
  - [ ] mito_forge/tools/geseq.py
  - 职责：生成注释GFF、表格及日志
  - 函数：
    - run_mitos(fasta: Path, out_dir: Path, genetic_code: int, threads: int, config: Dict) -> Dict[str,str]

## 2) 流水线阶段（高优先级）
- [ ] mito_forge/core/pipeline/stages/qc_stage.py
  - 职责：协调QC（QCAgent + fastqc/trimmomatic）
  - 函数：
    - execute(inputs: Dict, config: Dict, workdir: Path) -> StageResult
  - 输出：clean_fastq（如有）、QC报告与指标

- [ ] mito_forge/core/pipeline/stages/assembly_stage.py
  - 职责：调用组装器并汇总统计（N50等）
  - 函数：
    - execute(inputs: Dict, config: Dict, workdir: Path) -> StageResult
  - 输出：contigs.fasta、统计JSON

- [ ] mito_forge/core/pipeline/stages/annotation_stage.py
  - 职责：调用注释工具
  - 函数：
    - execute(inputs: Dict, config: Dict, workdir: Path) -> StageResult
  - 输出：GFF、注释表

- [ ] mito_forge/core/pipeline/checkpoint.py
  - 职责：阶段检查点写入/读取（JSON）
  - 函数：
    - save(stage: str, data: Dict, path: Path) -> None
    - load(stage: str, path: Path) -> Dict

- [ ] mito_forge/core/pipeline/retry_policy.py
  - 职责：重试控制与错误分类
  - 函数：
    - should_retry(stage: str, error: str, retries_left: int) -> bool
    - backoff_delay(attempt: int) -> float

- [x] mito_forge/core/pipeline/manager.py（现为占位，需增强）
  - 职责：串联阶段、支持跳步/断点续跑/重试与清理临时目录
  - 函数：
    - run_pipeline(inputs: Dict, config: Dict, base_dir: Path) -> Dict

## 3) 智能体层（中优先级）
- [ ] mito_forge/core/agents/base_agent.py
  - 职责：统一生命周期接口（prepare/run/finalize/get_status）
  - 函数：
    - prepare(workdir: Path, **kwargs) -> None
    - run(inputs: Dict, **kwargs) -> StageResult
    - finalize(**kwargs) -> None
    - get_status() -> AgentStatus

- [ ] mito_forge/core/agents/types.py
  - 职责：数据模型（AgentStatus/StageResult）
  - 模型字段：state/progress/logs/metrics/errors/outputs 等

- 具体智能体（需重构为继承 BaseAgent）
  - [x] mito_forge/core/agents/qc_agent.py
  - [x] mito_forge/core/agents/assembly_agent.py
  - [x] mito_forge/core/agents/annotation_agent.py
  - 职责：组合工具封装，返回标准化 StageResult

- [x] 主管（Orchestrator/Supervisor）
  - mito_forge/graph/nodes.py (supervisor_node 函数)
  - 职责：智能数据分析、策略选择、资源评估、执行计划制定、监控配置
  - 已完成功能：
    - 深度数据分析（读长类型、质量、覆盖度、复杂度评分）
    - 智能策略选择（基于数据特征的动态策略矩阵）
    - 资源需求评估（内存、CPU、时间、磁盘空间估算）
    - 执行计划制定（阶段依赖、条件阶段、关键路径）
    - 监控和容错策略（质量阈值、重试策略、备用工具）
    - 分析结果持久化（JSON 格式保存到工作目录）

## 4) 配置与验证（中优先级）
- [ ] mito_forge/utils/config.py（已有，需增强）
  - 新增：
    - load_yaml(path: Path) -> Dict
    - env_override(prefix: str="MITO_") -> Dict
    - tools 路径块支持：{"fastqc_path": "...", "spades_path": "..."}

- [ ] mito_forge/utils/validation.py
  - 职责：输入文件存在性、参数范围、工具路径有效性
  - 函数：
    - validate_inputs(inputs: Dict) -> List[str]（错误列表）
    - validate_config(config: Dict) -> List[str]
    - validate_tools(config: Dict) -> List[str]

- [ ] mito_forge/utils/fs.py
  - 职责：安全文件操作、临时目录管理
  - 函数：
    - ensure_dir(path: Path) -> None
    - atomic_write(path: Path, content: str|bytes) -> None

## 5) 知识与建议层（后续增强）
- [ ] mito_forge/core/knowledge/interfaces.py
  - 职责：查询/建议接口
  - 函数：
    - query(context: Dict, question: str) -> Dict
    - advise(metrics: Dict, rules: Dict) -> List[str]

- [ ] mito_forge/core/knowledge/rules.py
  - 职责：基于规则的建议（例如低质量→建议修剪）
  - 数据结构：
    - RULES = [{condition, action, message}...]

- [ ] mito_forge/core/knowledge/advisor.py
  - 职责：在各阶段后生成建议摘要并写入报告
  - 函数：
    - summarize(stage: str, metrics: Dict) -> List[str]

## 6) 报告与产出规范（中优先级）
- 目录结构（建议）
  - results/
    - 01_qc/
    - 02_assembly/
    - 03_annotation/
    - logs/
    - report/

- [ ] mito_forge/reports/summary.py
  - 职责：汇总阶段结果为统一JSON
  - 函数：
    - build_summary(outputs: Dict, metrics: Dict, config: Dict) -> Dict

- [ ] mito_forge/reports/html_report.py
  - 职责：生成最终HTML报告（模板+数据）
  - 函数：
    - render(summary: Dict, template_dir: Path, out_path: Path) -> Path

## 7) CLI增强（中优先级）
- [ ] config 命令增强
  - 支持 list、unset、import/export（JSON/YAML）
- [ ] doctor 命令增强
  - 工具探测（路径、版本）、CPU/内存检查、常见错误诊断
- [x] pipeline 命令增强
  - 已完成：LangGraph 流水线命令、检查点恢复 (--resume)、详细输出 (-v)、配置文件支持、Rich 界面
  - 已完成：status 命令查看流水线状态

## 8) 测试（高优先级）
- [ ] tests/tools/test_shell_runner.py（mock subprocess）
- [ ] tests/tools/test_fastqc.py（输出解析）
- [ ] tests/pipeline/test_stages.py（阶段契约）
- [ ] tests/utils/test_config_validation.py
- [ ] tests/cli/test_commands.py（Click命令）
- [x] tests/test_langgraph_pipeline.py
  - 已完成：LangGraph 流水线完整测试、状态管理测试、检查点测试、策略选择测试

## 9) LangGraph主管编排（关键）
- [x] mito_forge/graph/state.py
  - 职责：PipelineState/StageMetrics/StageOutputs 类型定义（TypedDict）
  - 已完成：状态结构定义、状态操作函数、检查点机制

- [x] mito_forge/graph/nodes.py
  - 职责：节点函数（supervisor/qc/assembly/annotation/report）
  - 已完成：
    - **Supervisor Agent**: 完整的智能分析和策略选择系统
    - QC/Assembly/Annotation/Report 节点基础实现
    - 智能策略选择矩阵（支持 Nanopore/Illumina/PacBio + Animal/Plant）
    - 数据特征分析（文件信息、读长分布、质量评估、复杂度计算）
    - 资源需求评估和执行计划制定
    - 监控配置和容错策略设置

- [x] mito_forge/graph/build.py
  - 职责：构建 StateGraph、添加条件边与终止
  - 已完成：图构建逻辑、条件路由、检查点保存/恢复、同步执行器

- [ ] mito_forge/graph/policies.py
  - 职责：重试/超时策略、路由判定逻辑
  - 可集成 checkpointer（SQLite）以实现断点续跑

---

备注：
- 此文档仅作为实现规划，帮助后续逐步落地；不需要在当前阶段编写代码。
- 优先顺序建议：工具执行层 → QC阶段 → 组装阶段 → 注释阶段 → Checkpoint/Retry → 报告 → LangGraph编排与持久化。

## 已完成模块总结（当前进度）
✅ **LangGraph 核心架构** - 状态驱动的多智能体流水线框架
✅ **PipelineState 状态管理** - 完整的状态类型定义和操作函数
✅ **Supervisor Agent** - 智能数据分析和策略选择系统
✅ **CLI 流水线命令** - 完整的用户界面和检查点恢复
✅ **测试验证** - LangGraph 流水线的端到端测试
✅ **日志系统** - 统一的日志配置和输出

## 下一个建议实现的模块
🎯 **1) 工具执行层** - `mito_forge/tools/shell_runner.py` 和 `tool_discovery.py`
   - 这是所有实际工具调用的基础
   - 完成后可以让 LangGraph 节点调用真实的生物信息学工具

## 10) 运行时与可观测性（关键）
- [ ] mito_forge/utils/runtime.py（运行时可视化与事件总线）
  - 职责：实时日志流（stdout/stderr）到控制台与日志文件；事件回调（Started/Stdout/Stderr/Finished）；命令与时间信息落盘（cmd.json、timing.json）
  - 函数（规划）：run_cmd_streaming(cmd, cwd, env, timeout, logs_dir, tag, event_cb) -> ShellResult；emit(event_cb, type, payload)

- [ ] 失败处理与重试/回退策略
  - 职责：统一失败分类（TOOL_NOT_FOUND/TIMEOUT/RUNTIME_ERROR/RESOURCE_LIMIT）、失败报告（failure.json）、指数退避重试与备用工具回退
  - 函数（规划）：classify_failure(returncode, stderr_excerpt) -> str；write_failure_report(logs_dir, tag, result, stderr_excerpt, extra) -> Path；should_retry(error_code, retries_left) -> bool；backoff_delay(attempt) -> float

- [x] mito_forge/utils/logging.py
  - 已完成：统一日志配置、控制台和文件输出、日志级别控制