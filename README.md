# 🧬 Mito-Forge

智能化线粒体基因组组装与分析平台，采用 LangGraph 多智能体架构，集成 LLM 驱动的智能决策系统。

## 🌟 核心特性

- **🧠 多智能体协作**: Supervisor、QC、Assembly、Annotation、Report 五大智能体协同工作
- **🔄 LangGraph 架构**: 基于状态机的智能工作流编排，支持条件路由和错误恢复  
- **🤖 LLM 驱动分析**: 集成 OpenAI、Ollama 等多模型，提供智能决策和报告生成
- **⚡ 一键式分析**: `pipeline` 命令完成从质控到注释的完整流程
- **🛠️ 跨平台支持**: Windows/Linux/macOS 全兼容，支持模拟运行模式

## 🚀 快速开始

### 安装
```bash
# 克隆项目
git clone https://github.com/your-username/Mito-Forge.git
cd Mito-Forge
pip install -r requirements.txt
```

### 系统诊断
```bash
python -m mito_forge doctor          # 检查环境
python -m mito_forge doctor --fix    # 自动修复
```

### 一键分析
```bash
python -m mito_forge pipeline --reads your_reads.fastq --output results/
```

## 🔧 核心命令

| 命令 | 功能描述 | 状态 | 演示命令 |
|-----|---------|------|----------|
| `pipeline` | 完整分析流水线 | ✅ | `python -m mito_forge pipeline --reads data.fastq` |
| `qc` | 质量控制与预处理 | ✅ | `python -m mito_forge qc --reads reads.fastq` |
| `assembly` | 基因组组装优化 | ✅ | `python -m mito_forge assembly --input qc/` |
| `annotate` | 基因注释分析 | ✅ | `python -m mito_forge annotate --input assembly/` |
| `agents` | 智能体状态管理 | ✅ | `python -m mito_forge agents --status` |
| `doctor` | 系统诊断修复 | ✅ | `python -m mito_forge doctor --check-tools` |
| `config` | 配置管理 | ✅ | `python -m mito_forge config --show` |
| `model` | LLM 模型配置 | ✅ | `python -m mito_forge model list` |
| `status` | 查看执行状态 | ✅ | `python -m mito_forge status` |

## 🧠 智能体架构

```
输入数据 → Supervisor → 阶段决策 → 条件路由 → 最终报告
              ↓
      QC → Assembly → Annotation → Report
              ↓
      状态保存 ← 错误恢复 ← 检查点机制
```

### 智能体职责
- **Supervisor**: 总体规划、任务派发、结果汇总
- **QC Agent**: 质量评估、预处理建议、适用性判断  
- **Assembly Agent**: 组装策略、参数优化、质量改进
- **Annotation Agent**: 基因注释、功能分析、完整性评估
- **Report Agent**: 结果可视化、发表建议、交付说明

## 🛠️ 高级功能

### LLM 模型配置
```bash
# 配置 OpenAI
python -m mito_forge model add openai --model gpt-4o-mini --api-key your-key

# 配置本地 Ollama
python -m mito_forge model add ollama --model qwen2.5:7b --api-base http://localhost:11434
```

### 模拟运行
```bash
# 完整流程模拟
MITO_SIM="qc=ok,assembly=ok,annotate=ok" python -m mito_forge pipeline --reads demo.fastq

# 错误场景模拟  
MITO_SIM="assembly=tool_missing" python -m mito_forge pipeline --reads demo.fastq
```

### 多语言支持
```bash
MITO_LANG=zh python -m mito_forge qc --reads reads.fastq    # 中文
MITO_LANG=en python -m mito_forge pipeline --reads reads.fastq  # 英文
```

## 📋 系统要求

- **Python**: 3.8+
- **内存**: 8GB+ (推荐 16GB+)
- **磁盘**: 10GB+ 可用空间
- **系统**: Windows 10+, Ubuntu 20.04+, macOS 10.15+

### 生物信息学工具
- FastQC (质量控制)
- SPAdes/Flye (基因组组装)  
- BLAST+ (序列比对)
- MUSCLE (多序列比对)
- IQ-TREE (系统发育分析)

## 🔍 故障排除

### 工具缺失
```bash
python -m mito_forge doctor --check-tools    # 检查工具
python -m mito_forge doctor --fix-issues      # 自动修复
```

### LLM 连接问题
```bash
python -m mito_forge model test your-model   # 测试连接
```

### 内存优化
```bash
python -m mito_forge pipeline --reads reads.fastq --threads 2  # 减少线程
export MITO_MEMORY_OPTIMIZE=1  # 启用内存优化
```

## 📚 文档资源

- [📖 架构设计](docs/architecture.md) - 系统架构详解
- [🔄 LangGraph工作流](docs/langgraph_architecture.md) - 状态机实现
- [🧬 分析指南](docs/mitochondrial_assembly_guide.md) - 使用教程
- [🤖 模型配置](docs/model_configuration_guide.md) - LLM配置说明
- [💻 使用示例](examples/cli_usage.md) - 命令行示例

## 🤝 参与开发

```bash
git clone -b develop https://github.com/your-username/Mito-Forge.git
pip install -r requirements-dev.txt
pytest tests/  # 运行测试
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**版本**: v1.0.0 | **更新**: 2025-01-09 | **状态**: ✅ 生产就绪