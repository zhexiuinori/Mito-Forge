# Mito-Forge LangGraph 架构总览

## 概述

Mito-Forge 采用基于 LangGraph 的状态驱动多智能体架构，实现了智能化的线粒体基因组组装流水线。该架构通过状态机编排多个专业化的 Agent，实现了自动化的数据分析、工具选择、执行监控和结果生成。

## 核心设计理念

### 1. 状态驱动 (State-Driven)
- **统一状态管理**：所有执行信息都存储在 `PipelineState` 中
- **状态持久化**：支持检查点保存和恢复，实现断点续跑
- **状态可观测**：实时追踪流水线执行状态和进度

### 2. 智能体协作 (Multi-Agent Collaboration)
- **专业化分工**：每个 Agent 负责特定的生物信息学任务
- **智能决策**：Supervisor Agent 根据数据特征自动选择最佳策略
- **容错机制**：支持重试、降级和备用工具切换

### 3. 条件路由 (Conditional Routing)
- **动态流程**：根据执行结果决定下一步操作
- **智能重试**：失败时自动分析原因并选择合适的重试策略
- **优雅降级**：主要工具失败时自动切换到备用方案

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mito-Forge Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Input     │    │ PipelineState│    │   Output    │         │
│  │   Data      │───▶│   Manager    │───▶│   Results   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  LangGraph StateGraph                       │ │
│  │                                                             │ │
│  │  ┌─────────────┐                                           │ │
│  │  │ Supervisor  │◄──────────────────────────────────────────┤ │
│  │  │   Agent     │                                           │ │
│  │  └─────┬───────┘                                           │ │
│  │        │                                                   │ │
│  │        ▼                                                   │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │ │
│  │  │     QC      │───▶│  Assembly   │───▶│ Annotation  │   │ │
│  │  │   Agent     │    │   Agent     │    │   Agent     │   │ │
│  │  └─────────────┘    └─────────────┘    └─────────────┘   │ │
│  │        │                   │                   │         │ │
│  │        └───────────────────┼───────────────────┘         │ │
│  │                            ▼                             │ │
│  │                    ┌─────────────┐                       │ │
│  │                    │   Report    │                       │ │
│  │                    │   Agent     │                       │ │
│  │                    └─────────────┘                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件详解

### 1. PipelineState (状态管理器)

**位置**: `mito_forge/graph/state.py`

**职责**:
- 维护整个流水线的执行状态
- 管理各阶段的输入输出数据
- 记录执行指标和错误信息
- 支持检查点保存和恢复

**核心数据结构**:
```python
class PipelineState(TypedDict):
    # 输入与配置
    inputs: Dict[str, Any]              # 原始输入数据
    config: Dict[str, Any]              # 配置参数
    workdir: str                        # 工作目录
    
    # 执行状态
    current_stage: str                  # 当前阶段
    completed_stages: List[str]         # 已完成阶段
    failed_stages: List[str]            # 失败阶段
    
    # 数据流
    stage_outputs: Dict[str, Any]       # 各阶段输出
    metrics: Dict[str, Any]             # 统计指标
    logs: Dict[str, str]                # 日志文件路径
    
    # 控制流
    route: str                          # 路由决策
    retries: Dict[str, int]             # 重试计数
    errors: List[str]                   # 错误记录
    
    # 元数据
    pipeline_id: str                    # 流水线唯一ID
    start_time: float                   # 开始时间
    done: bool                          # 是否完成
```

### 2. Agent 节点系统

**位置**: `mito_forge/graph/nodes.py`

#### 2.1 Supervisor Agent (主管智能体)

**职责**:
- 分析输入数据类型（短读/长读/HiFi）
- 根据物种类型选择最佳工具链
- 制定执行策略和参数配置
- 监控整体执行进度

**智能决策逻辑**:
```python
策略选择矩阵:
┌─────────────┬──────────┬──────────┬─────────────┐
│ 数据类型    │ 物种类型 │ 组装工具 │ 注释工具    │
├─────────────┼──────────┼──────────┼─────────────┤
│ Nanopore    │ Animal   │ Flye     │ MITOS       │
│ Illumina    │ Animal   │ SPAdes   │ MITOS       │
│ PacBio HiFi │ Animal   │ hifiasm  │ MITOS       │
│ Illumina    │ Plant    │ SPAdes   │ GeSeq       │
└─────────────┴──────────┴──────────┴─────────────┘
```

#### 2.2 QC Agent (质量控制智能体)

**职责**:
- 执行 FastQC 质量分析
- 根据质量评分决定是否需要数据清理
- 可选的接头去除和质量修剪
- 生成质量控制报告

**输出指标**:
- QC 评分 (0-1)
- 总读长数量
- 清理后读长数量
- 质量分布统计

#### 2.3 Assembly Agent (组装智能体)

**职责**:
- 根据策略执行基因组组装
- 筛选线粒体候选序列
- 进行环化检测
- 计算组装统计指标

**线粒体筛选策略**:
- **启发式筛选**: 基于长度和覆盖度
- **BLAST 筛选**: 与参考序列比对
- **混合策略**: 结合多种方法

**关键指标**:
- N50 值
- 最大 contig 长度
- 线粒体候选数量
- 环化状态

#### 2.4 Annotation Agent (注释智能体)

**职责**:
- 对线粒体序列进行基因注释
- 识别蛋白编码基因、tRNA、rRNA
- 生成 GFF 格式注释文件
- 评估注释完整性

**输出产物**:
- GFF3 注释文件
- GenBank 格式文件
- 基因功能表格
- 注释质量报告

#### 2.5 Report Agent (报告智能体)

**职责**:
- 汇总所有阶段的执行结果
- 生成综合性 HTML 报告
- 创建数据可视化图表
- 提供结果解读和建议

### 3. 状态图构建器

**位置**: `mito_forge/graph/build.py`

**核心功能**:
- 构建 LangGraph StateGraph
- 定义节点间的连接关系
- 实现条件路由逻辑
- 管理检查点机制

**路由决策树**:
```
START
  │
  ▼
┌─────────────┐
│ Supervisor  │
└─────┬───────┘
      │
      ▼
┌─────────────┐    Success    ┌─────────────┐
│     QC      │──────────────▶│  Assembly   │
└─────┬───────┘               └─────┬───────┘
      │                             │
      │ Retry/Fail                  │ Success
      │                             ▼
      │                       ┌─────────────┐
      │                       │ Annotation  │
      │                       └─────┬───────┘
      │                             │
      │                             │ Success/Continue
      │                             ▼
      │                       ┌─────────────┐
      │                       │   Report    │
      │                       └─────┬───────┘
      │                             │
      │                             ▼
      └─────────────────────────── END
```

## 执行流程详解

### 1. 流水线启动

```python
# 1. 初始化状态
state = init_pipeline_state(inputs, config, workdir)

# 2. 构建执行图
graph = build_pipeline_graph()

# 3. 开始执行
final_state = graph.invoke(state)
```

### 2. 状态转换流程

```
IDLE → SUPERVISOR → QC → ASSEMBLY → ANNOTATION → REPORT → DONE
  ▲                   │    │         │            │
  │                   ▼    ▼         ▼            ▼
  └─────────────── RETRY/FALLBACK ──────────────────┘
```

### 3. 错误处理机制

**重试策略**:
- **指数退避**: 重试间隔逐渐增加
- **最大重试次数**: 每个阶段最多重试 2 次
- **智能重试**: 根据错误类型决定是否重试

**降级策略**:
- **工具回退**: 主要工具失败时切换到备用工具
- **参数调整**: 自动降低资源要求或精度要求
- **跳过非关键步骤**: 注释失败时仍可生成报告

## 扩展性设计

### 1. 添加新的 Agent

```python
def new_agent_node(state: PipelineState) -> PipelineState:
    """新 Agent 节点实现"""
    try:
        # 1. 获取输入数据
        inputs = state["stage_outputs"]["previous_stage"]
        
        # 2. 执行核心逻辑
        results = execute_new_task(inputs, state["config"])
        
        # 3. 更新状态
        update_stage_completion(state, "new_stage", results)
        
        return state
    except Exception as e:
        update_stage_failure(state, "new_stage", str(e))
        return state
```

### 2. 修改路由逻辑

```python
def custom_route_decider(state: PipelineState) -> str:
    """自定义路由决策"""
    if custom_condition(state):
        return "custom_path"
    return "default_path"

# 在图构建时添加条件边
graph.add_conditional_edges(
    "source_node",
    custom_route_decider,
    {
        "custom_path": "target_node_1",
        "default_path": "target_node_2"
    }
)
```

### 3. 集成新工具

```python
def integrate_new_tool(inputs, config):
    """集成新的生物信息学工具"""
    # 1. 工具路径解析
    tool_path = resolve_tool("new_tool", config)
    
    # 2. 构建命令
    cmd = [tool_path, "--input", inputs["file"], "--output", "results/"]
    
    # 3. 执行并监控
    result = run_cmd_streaming(cmd, timeout=3600)
    
    # 4. 解析输出
    return parse_tool_output(result.stdout_path)
```

## 性能优化

### 1. 并行执行
- **阶段内并行**: 同一阶段的多个任务可并行执行
- **流水线并行**: 多个样本可同时处理
- **资源调度**: 智能分配 CPU 和内存资源

### 2. 缓存机制
- **结果缓存**: 相同输入的结果可复用
- **中间文件缓存**: 避免重复计算
- **工具版本缓存**: 缓存工具路径和版本信息

### 3. 资源管理
- **内存监控**: 实时监控内存使用情况
- **磁盘清理**: 自动清理临时文件
- **超时控制**: 防止任务无限期运行

## 监控和调试

### 1. 实时监控
- **进度追踪**: 实时显示执行进度
- **资源监控**: CPU、内存、磁盘使用情况
- **日志聚合**: 统一收集和展示日志

### 2. 调试支持
- **状态检查**: 随时查看流水线状态
- **断点调试**: 在特定阶段暂停执行
- **错误诊断**: 详细的错误信息和建议

### 3. 性能分析
- **执行时间分析**: 各阶段耗时统计
- **瓶颈识别**: 找出性能瓶颈
- **优化建议**: 基于执行数据的优化建议

## 部署和运维

### 1. 环境要求
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+)
- **Python**: 3.8+
- **依赖**: LangGraph, Rich, Click 等
- **生物信息学工具**: Flye, SPAdes, FastQC, MITOS 等

### 2. 配置管理
- **工具路径配置**: 自动发现或手动配置工具路径
- **参数调优**: 根据硬件配置调整默认参数
- **环境变量**: 支持环境变量覆盖配置

### 3. 故障恢复
- **检查点机制**: 定期保存执行状态
- **自动恢复**: 系统重启后自动恢复执行
- **手动干预**: 支持手动修复和继续执行

## LLM 驱动与报告生成

- Supervisor 与各阶段 Agent（QC / Assembly / Annotation / Report）均可调用 LLM：
  - 对工具产出进行审阅与一致性检查
  - 以自然语言生成阶段报告（面向用户与后续决策）
  - 提出修复方案与是否进入下一阶段的建议
- 建议的报告结构：
  1) 结论与置信度
  2) 证据与关键指标（引用阶段产出与日志）
  3) 异常与风险点
  4) 修复建议与可执行方案
  5) 下一步决策建议（继续/重试/降级/终止）
- Supervisor 聚合各阶段报告后进行整体判断，驱动条件路由与重试/降级策略。

## 运行模式与 CLI 映射

- 一键全流程（示例）：pipeline 命令负责从 QC → Assembly → Annotation → Report 的完整执行，其内部由 LangGraph 的状态与条件路由驱动。
- 单阶段命令与图节点对应：
  - qc 命令 → QC Agent 节点
  - assembly 命令 → Assembly Agent 节点
  - annotate 命令 → Annotation Agent 节点
- 各阶段命令既可独立运行，也可在一键流程中由 Supervisor 统一编排；阶段产物通过 PipelineState 串联。

## 平台兼容性与模拟运行（Windows 支持）

- 为兼容 Windows/本地缺少工具的场景，支持通过环境变量 MITO_SIM 进行模拟运行（便于演示与 TDD）：
  - QC：ok / tool_missing / timeout / low_quality
  - Assembly：ok / assembler_not_found / memory_exceeded / timeout
  - Annotation：ok / db_missing / invalid_genetic_code / timeout
- 约定：错误场景需以非零退出码结束（raise SystemExit(1)），便于测试断言与上游编排判断。
- 模拟分支仅影响运行时行为与输出，不改变 LangGraph 的节点关系与状态管理逻辑。

## 国际化（i18n）与语言切换

- 通过环境变量 MITO_LANG 进行全局语言切换（如 zh / en），CLI 不提供 --lang 选项，示例文档与帮助信息以环境变量为准。
- 文案通过集中化 i18n 工具函数渲染；帮助信息在运行时按当前语言单语呈现，避免双语冗余。

## 总结

Mito-Forge 的 LangGraph 架构提供了一个强大、灵活、可扩展的多智能体平台，具有以下核心优势：

1. **智能化**: 自动分析数据特征并选择最佳策略
2. **可靠性**: 完善的错误处理和恢复机制
3. **可观测性**: 实时监控和详细的执行日志
4. **可扩展性**: 易于添加新的 Agent 和工具
5. **用户友好**: 简洁的 CLI 接口和丰富的报告

该架构为线粒体基因组分析提供了一个现代化、自动化的解决方案，同时为其他生物信息学流水线的开发提供了可参考的设计模式。