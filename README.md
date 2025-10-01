# 🧬 Mito-Forge

**线粒体基因组学多智能体自动化框架**

一个基于 LangGraph 的智能线粒体基因组组装工具，使用多智能体协作实现线粒体基因组分析的全流程自动化。支持 Windows、Linux 和 macOS 跨平台运行。

## ✨ 特性

- 🤖 **多智能体协作** - Supervisor、QC、Assembly、Annotation 智能体协同工作
- 🔄 **LangGraph 状态机** - 基于状态机的工作流编排，支持检查点恢复和失败重试
- 🚀 **一键式流水线** - 从原始 FASTQ 数据到最终注释结果的完整自动化
- 🎯 **现代化CLI界面** - 清晰的命令行界面，支持详细的状态显示和诊断
- ⚡ **跨平台支持** - 支持 Windows、Linux、macOS 多平台运行
- 📊 **智能诊断** - 内置系统健康检查和自动修复功能
- 🔧 **灵活配置** - 完整的配置管理系统，支持个性化设置

## 🔧 安装

### 系统要求
- Python 3.8+ (推荐 3.10+)
- 4GB+ RAM (推荐 8GB)
- 支持 Windows 10+、Linux (Ubuntu 18.04+)、macOS 10.15+

### 快速安装
```bash
# 克隆项目
git clone https://github.com/mito-forge/mito-forge.git
cd mito-forge

# 安装 Python 依赖
pip install -e .

# 检查系统状态
python -m mito_forge doctor

# 自动修复依赖问题（可选）
python -m mito_forge doctor --fix-issues
```

## 🚀 快速开始

### 系统检查
```bash
# 检查系统环境和依赖
python -m mito_forge doctor

# 查看智能体状态
python -m mito_forge agents

# 查看当前配置
python -m mito_forge config
```

### 完整流水线分析
```bash
# 分析 FASTQ 测序数据
python -m mito_forge pipeline --reads sample.fastq \
    --output ./results \
    --threads 8 \
    --kingdom animal \
    --verbose
```

### 智能体管理
```bash
# 查看智能体详细状态
python -m mito_forge agents --detailed

# 重启指定智能体
python -m mito_forge agents --restart supervisor
```

### 配置管理
```bash
# 查看当前配置
python -m mito_forge config

# 设置配置参数
python -m mito_forge config --set threads 16
python -m mito_forge config --set memory 16G

# 重置为默认配置
python -m mito_forge config --reset
```
+++++++ REPLACE</div>
</replace_in_file>

<replace_in_file id="mf0jdrirk6h5pux001ij263rm1o89xc1">
<path>README.md</path>
<diff>------- SEARCH
## 📋 主要命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `pipeline` | 完整分析流水线 | `mito-forge pipeline R1.fq R2.fq -o results/` |
| `qc` | 数据质量控制 | `mito-forge qc *.fastq --quality-threshold 25` |
| `assembly` | 基因组组装 | `mito-forge assembly --assembler spades` |
| `annotate` | 基因注释 | `mito-forge annotate genome.fa --tool mitos` |
| `agents` | 智能体状态 | `mito-forge agents status` |
| `config` | 配置管理 | `mito-forge config set threads 8` |
| `doctor` | 系统诊断 | `mito-forge doctor --check-system` |

## 🏗️ 架构

Mito-Forge采用模块化的多智能体架构：

- **总指挥智能体** - 任务分解和流程协调
- **质控智能体** - FastQC、Trimmomatic等工具集成
- **组装智能体** - SPAdes、Unicycler、Flye等组装器
- **注释智能体** - MITOS、GeSeq等注释工具
- **分析智能体** - 系统发育、比较基因组学分析
- **联邦知识库** - 领域专业知识和最佳实践
=======
## 📋 主要命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `pipeline` | 完整分析流水线 | `python -m mito_forge pipeline --reads data.fastq -o results/` |
| `agents` | 智能体状态管理 | `python -m mito_forge agents --detailed` |
| `config` | 配置管理 | `python -m mito_forge config --set threads 8` |
| `doctor` | 系统诊断 | `python -m mito_forge doctor --fix-issues` |
| `model` | 模型配置管理 | `python -m mito_forge model list` |
| `status` | 流水线状态查看 | `python -m mito_forge status --checkpoint path/to/checkpoint` |

## 🏗️ 架构

Mito-Forge 采用基于 LangGraph 的多智能体架构：

### 核心智能体
- **Orchestrator (总指挥)** - 协调整个分析流程，管理智能体间的通信
- **Supervisor Agent** - 智能分析数据并制定执行策略
- **QC Agent** - 自动质量控制和数据清理
- **Assembly Agent** - 多工具组装策略选择和执行
- **Annotation Agent** - 基因功能注释和结果整理

### 技术特性
- **状态机编排** - 基于 LangGraph 的工作流状态管理
- **检查点恢复** - 支持流水线中断后的断点续传
- **失败重试** - 智能错误处理和自动重试机制
- **跨平台兼容** - 统一的 CLI 界面，支持多操作系统

## 🔧 系统诊断与修复

Mito-Forge 内置了完整的诊断系统：

### 自动检查项目
- ✅ **系统环境** - Python版本、内存、磁盘空间
- ✅ **Python依赖** - click, rich, biopython, numpy, pandas
- ✅ **生物信息学工具** - FastQC, SPAdes, BLAST+, MUSCLE, IQ-TREE

### 自动修复功能
```bash
# 检查并自动修复 Python 依赖问题
python -m mito_forge doctor --fix-issues

# 检查特定组件
python -m mito_forge doctor --check-dependencies
python -m mito_forge doctor --check-tools
python -m mito_forge doctor --check-system
```

## 🚨 已修复的问题

本版本修复了以下关键问题：

### ✅ 表格显示问题
- **问题**: Rich 表格在窄终端中内容被截断显示为 "X" 字符
- **修复**: 重写显示逻辑，使用清晰的文本格式替代复杂表格
- **影响**: `config`, `doctor`, `agents` 命令显示正常

### ✅ 智能体系统错误
- **问题**: `'Orchestrator' object has no attribute 'get_agents_status'`
- **修复**: 添加完整的智能体状态管理和重启功能
- **新功能**: 支持智能体状态查看和重启操作

### ✅ 帮助文档格式
- **问题**: CLI 帮助文档格式混乱，缺少换行符
- **修复**: 优化帮助文档格式，提升用户体验

### ✅ 编码兼容性
- **问题**: Windows 环境下 emoji 字符编码错误
- **修复**: 统一使用 UTF-8 编码，支持跨平台字符显示

## 📋 主要命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `pipeline` | 完整分析流水线 | `mito-forge pipeline R1.fq R2.fq -o results/` |
| `qc` | 数据质量控制 | `mito-forge qc *.fastq --quality-threshold 25` |
| `assembly` | 基因组组装 | `mito-forge assembly --assembler spades` |
| `annotate` | 基因注释 | `mito-forge annotate genome.fa --tool mitos` |
| `agents` | 智能体状态 | `mito-forge agents status` |
| `config` | 配置管理 | `mito-forge config set threads 8` |
| `doctor` | 系统诊断 | `mito-forge doctor --check-system` |

## 🏗️ 架构

Mito-Forge采用模块化的多智能体架构：

- **总指挥智能体** - 任务分解和流程协调
- **质控智能体** - FastQC、Trimmomatic等工具集成
- **组装智能体** - SPAdes、Unicycler、Flye等组装器
- **注释智能体** - MITOS、GeSeq等注释工具
- **分析智能体** - 系统发育、比较基因组学分析
- **联邦知识库** - 领域专业知识和最佳实践

## 🧭 架构与运行模式（LangGraph + LLM Agents）

Mito-Forge 采用基于 LangGraph 的“主管Agent + 多子Agent”编排方式，且主管与各子Agent均由各自的 LLM 驱动，负责“审阅阶段结果 → 生成自然语言报告 → 给出建议 → 驱动下一步决策”。

- 角色与职责
  - Supervisor/Orchestrator（主管Agent，LLM）：负责规划流程、派发任务、收集结果、做出继续/重试/终止等决策，并输出阶段性与最终报告
  - QCAgent（LLM）：审阅质控结果与日志，生成自然语言报告与结构化评估（是否通过、改进建议）
  - AssemblyAgent（LLM）：审阅组装结果与统计，生成报告与参数/策略建议（如切换组装器、调线程、调K-mer）
  - AnnotateAgent（LLM）：审阅注释结果（基因数、覆盖度、一致性等），生成报告与交付清单建议
  - Reporter（可选，LLM）：将各阶段报告整合为最终交付说明

- 运行模式
  - 真实执行：工具实际运行产生产物与日志，各阶段Agent基于真实结果调用 LLM 做审阅与报告
  - 模拟演示（Windows 友好）：通过 MITO_SIM 产生阶段性“模拟结果”，但报告与建议仍由各阶段的 LLM 路径输出，便于无依赖环境下展示“像LLM看过结果后的自然语言汇报”
    - 示例：MITO_SIM="qc=ok,assembly=ok,annotate=ok" 走通完整流程；若设置 assembly=assembler_not_found，则由 AssemblyAgent（LLM）输出异常分析与可行修复建议，主管Agent据此决定是否终止或切换策略

- LangGraph 流程（简述）
  1) 主管Agent接收输入与参数，制定阶段计划（QC → Assembly → Annotate）
  2) 触发阶段Agent执行（真实或模拟），阶段完成后由该Agent的 LLM 审阅并产出：
     - 自然语言报告（结论、要点、风险/异常、建议）
     - 结构化评估（pass/fail、关键指标、下一步建议）
  3) 主管Agent汇总阶段结果并决策：继续下一阶段、重试或切换策略，或在关键错误时终止
  4) 流程结束后由主管/Reporter 生成交付摘要与路径清单

- 语言与可观测性
  - MITO_LANG 控制中文/英文单语输出，覆盖 CLI 文案与 LLM 报告
  - 关键节点输出（报告、产物路径、统计摘要）将统一在控制台与结果目录中可见（真实执行路径）

- 后续最小落地（规划）
  - 新增 pipeline 的 LangGraph 实现（例如：mito_forge/graph/pipeline_graph.py）
  - 新增基类 BaseLLMAgent（例如：mito_forge/core/agents/base_llm_agent.py），统一各 Agent 的 LLM 审阅接口
  - 在保持现有 CLI 不变的前提下，将 pipeline run 接线到上述图中；真实/模拟两种路径均可触发“LLM式审阅与报告”

提示：当前版本已支持 MITO_LANG 与 MITO_SIM，用于演示“无依赖环境下的完整流程”和“错误场景的非0退出行为”。后续将把 LLM 审阅与 LangGraph 调度按以上方案逐步落地。

## 📖 文档

- [架构文档](docs/architecture.md) - 系统架构和设计原理
- [LangGraph架构](docs/langgraph_architecture.md) - 状态机工作流详解
- [线粒体组装指南](docs/mitochondrial_assembly_guide.md) - 分析流程说明
- [模型配置指南](docs/model_configuration_guide.md) - LLM模型配置
- [修复日志](BUGFIX_LOG.md) - 问题修复记录

## 🌐 语言切换

Mito-Forge 的 CLI 输出语言可通过环境变量控制，推荐使用 MITO_LANG 设置语言（zh 或 en）：
- PowerShell (Windows):
  $env:MITO_LANG = "zh"
  python -m mito_forge qc --help
  $env:MITO_LANG = "en"
  python -m mito_forge qc --help

- bash (Linux/macOS):
  MITO_LANG=zh python -m mito_forge qc --help
  MITO_LANG=en python -m mito_forge qc --help

说明：CLI 仍兼容 --lang 选项，但不建议在命令中显式使用。文档示例均采用 MITO_LANG。

## 🎯 使用示例

### 基本工作流
```bash
# 1. 系统检查
python -m mito_forge doctor

# 2. 查看配置
python -m mito_forge config

# 3. 运行分析
python -m mito_forge pipeline --reads sample.fastq -o results --kingdom animal

# 4. 查看结果
ls results/work/
```

### 高级功能
```bash
# 智能体管理
python -m mito_forge agents --detailed
python -m mito_forge agents --restart qc

# 模型配置
python -m mito_forge model list
python -m mito_forge model current

# 流水线恢复
python -m mito_forge pipeline --resume checkpoint.json
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置
```bash
git clone https://github.com/mito-forge/mito-forge.git
cd mito-forge
pip install -e .
python -m mito_forge doctor --fix-issues
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [项目主页](https://github.com/mito-forge/mito-forge)
- [问题反馈](https://github.com/mito-forge/mito-forge/issues)
- [更新日志](CHANGELOG.md)

---

**Mito-Forge v1.0.0** - 基于 LangGraph 的智能线粒体基因组分析工具 🧬✨

*让线粒体基因组学分析更简单、更智能、更可靠！*