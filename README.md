# 🧬 Mito-Forge

智能化线粒体基因组组装与分析平台，采用 LangGraph 多智能体架构，集成 LLM 驱动的智能决策系统。

## 🌟 核心特性

- **🧠 多智能体协作**: Supervisor、QC、Assembly、Annotation、Report 五大智能体协同工作
- **🔄 LangGraph 架构**: 基于状态机的智能工作流编排，支持条件路由和错误恢复  
- **🤖 LLM 驱动分析**: 集成 OpenAI、Ollama 等多模型，提供智能决策和报告生成
- **⚡ 一键式分析**: `pipeline` 命令完成从质控到注释的完整流程
- **🛠️ 跨平台支持**: Windows/Linux/macOS 全兼容，支持模拟运行模式
- **🔍 智能诊断**: 内置系统诊断工具，自动检测和修复环境问题
- **🛡️ 容错机制**: 支持检查点保存、断点续跑和智能重试策略
- **📊 实时监控**: 实时追踪流水线状态，提供详细的进度报告

## 🚀 快速开始

### 安装
```bash
# 克隆项目
git clone https://github.com/your-username/Mito-Forge.git
cd Mito-Forge
pip install -e .

# 或使用开发模式
pip install -r requirements-dev.txt
```

### 系统诊断
```bash
# 基础诊断
python -m mito_forge doctor

# 检查依赖工具
python -m mito_forge doctor --check-tools

# 自动修复问题
python -m mito_forge doctor --fix-issues
```

### 一键分析
```bash
# 基础分析
python -m mito_forge pipeline --reads your_reads.fastq --output results/

# 交互式分析（推荐）
python -m mito_forge pipeline --reads your_reads.fastq --interactive

# 指定物种类型
python -m mito_forge pipeline --reads your_reads.fastq --kingdom animal --threads 8
```

## 🔧 核心命令

### 主要分析命令
| 命令 | 功能描述 | 演示命令 |
|-----|---------|----------|
| `pipeline` | 完整分析流水线 | `python -m mito_forge pipeline --reads data.fastq` |
| `qc` | 质量控制与预处理 | `python -m mito_forge qc --reads reads.fastq` |
| `assembly` | 基因组组装优化 | `python -m mito_forge assembly --input qc/` |
| `annotate` | 基因注释分析 | `python -m mito_forge annotate --input assembly/` |

### 系统管理命令
| 命令 | 功能描述 | 演示命令 |
|-----|---------|----------|
| `agents` | 智能体状态管理 | `python -m mito_forge agents --status --detailed` |
| `doctor` | 系统诊断修复 | `python -m mito_forge doctor --check-tools --fix-issues` |
| `config` | 配置管理 | `python -m mito_forge config --show` |
| `model` | LLM 模型配置 | `python -m mito_forge model list` |
| `status` | 查看执行状态 | `python -m mito_forge status --checkpoint checkpoint.json` |

### 交互式命令
```bash
# 进入交互式菜单
python -m mito_forge menu

# 快捷运行命令
python -m mito_forge run --reads data.fastq  # pipeline的别名
```

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

### 🧠 LLM 模型配置
```bash
# 配置 OpenAI
python -m mito_forge model add openai --model gpt-4o-mini --api-key your-key

# 配置本地 Ollama
python -m mito_forge model add ollama --model qwen2.5:7b --api-base http://localhost:11434

# 测试模型连接
python -m mito_forge model test openai
```

### 🧪 模拟运行模式
```bash
# 完整流程模拟
MITO_SIM="qc=ok,assembly=ok,annotate=ok" python -m mito_forge pipeline --reads demo.fastq

# 错误场景模拟  
MITO_SIM="assembly=tool_missing" python -m mito_forge pipeline --reads demo.fastq

# 部分阶段模拟
MITO_SIM="qc=ok" python -m mito_forge pipeline --reads demo.fastq
```

### 🌍 多语言支持
```bash
# 中文界面（默认）
MITO_LANG=zh python -m mito_forge qc --reads reads.fastq

# 英文界面
MITO_LANG=en python -m mito_forge pipeline --reads reads.fastq
```

### 🔧 智能体管理
```bash
# 查看智能体状态
python -m mito_forge agents --status

# 查看详细信息
python -m mito_forge agents --detailed

# 重启特定智能体
python -m mito_forge agents --restart qc_agent
```

### 💾 检查点与恢复
```bash
# 查看流水线状态
python -m mito_forge status --checkpoint work/checkpoint.json

# 从检查点恢复
python -m mito_forge pipeline --reads data.fastq --resume work/checkpoint.json
```

### ⚙️ 高级配置
```bash
# 显示当前配置
python -m mito_forge config --show

# 设置参数
python -m mito_forge config --set threads=16 memory=32GB

# 重置配置
python -m mito_forge config --reset
```

## 📋 系统要求

### 基础要求
- **Python**: 3.9+
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

### 🛠️ 工具缺失问题
```bash
# 检查所有依赖工具
python -m mito_forge doctor --check-tools

# 自动修复常见问题
python -m mito_forge doctor --fix-issues

# 检查特定工具
python -m mito_forge doctor --check-spades
python -m mito_forge doctor --check-fastqc
```

### 🌐 LLM 连接问题
```bash
# 测试模型连接
python -m mito_forge model test openai

# 检查API配置
python -m mito_forge model current

# 重新配置模型
python -m mito_forge model add openai --model gpt-4o-mini --api-key YOUR_KEY
```

### 💾 内存和性能优化
```bash
# 减少线程数
python -m mito_forge pipeline --reads reads.fastq --threads 2

# 启用内存优化模式
export MITO_MEMORY_OPTIMIZE=1

# 限制最大内存使用
python -m mito_forge config --set max_memory=16GB

# 使用轻量级分析模式
python -m mito_forge pipeline --reads reads.fastq --detail-level quick
```

### 🔄 断点续跑和恢复
```bash
# 从检查点恢复
python -m mito_forge pipeline --reads data.fastq --resume checkpoint.json

# 查看可用检查点
ls -la work/*/checkpoint.json

# 清理旧的检查点
python -m mito_forge doctor --clean-checkpoints
```

### 🐛 常见错误和解决方案

| 错误类型 | 症状 | 解决方案 |
|---------|------|----------|
| **工具未找到** | `ToolNotFoundError` | 运行 `python -m mito_forge doctor --fix-issues` |
| **内存不足** | `MemoryError` | 减少线程数，启用内存优化 |
| **LLM API错误** | `APIConnectionError` | 检查网络连接和API密钥 |
| **数据格式错误** | `InvalidDataError` | 检查输入文件格式和质量 |
| **权限错误** | `PermissionError` | 检查输出目录权限 |

### 📞 获取帮助
```bash
# 查看帮助信息
python -m mito_forge --help
python -m mito_forge pipeline --help

# 查看版本信息
python -m mito_forge --version

# 进入交互式菜单
python -m mito_forge menu
```

## 📚 文档资源

### 📖 核心文档
- [🏗️ 系统架构](docs/architecture.md) - 系统架构详解和技术规范
- [🔄 LangGraph工作流](docs/langgraph_architecture.md) - 状态机实现和工作流设计
- [🧬 线粒体分析指南](docs/mitochondrial_assembly_guide.md) - 生物信息学分析教程
- [🤖 模型配置指南](docs/model_configuration_guide.md) - LLM配置和API设置
- [💻 CLI使用示例](examples/cli_usage.md) - 命令行完整使用指南

### 🔧 开发文档
- [📋 更新日志](CHANGELOG.md) - 版本历史和功能更新
- [🐛 修复记录](BUGFIX_LOG.md) - 已知问题修复历程
- [📁 项目结构](docs/unimplemented_modules.md) - 模块设计和开发计划

## 🤝 参与开发

### 环境搭建
```bash
# 克隆开发分支
git clone -b develop https://github.com/your-username/Mito-Forge.git
cd Mito-Forge

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试套件
pytest tests/ -v --cov=mito_forge

# 代码质量检查
black mito_forge/ --check
flake8 mito_forge/
mypy mito_forge/
```

### 贡献指南
1. **Fork** 项目并创建功能分支
2. **编写测试** 确保代码覆盖率达到80%+
3. **遵循规范** 使用Black格式化和类型注解
4. **更新文档** 同步更新相关文档和示例
5. **提交PR** 详细描述变更内容和测试情况

### 开发架构
```
mito_forge/
├── core/           # 核心智能体系统
├── cli/            # 命令行界面
├── graph/          # LangGraph工作流
├── tools/          # 生物信息学工具封装
└── utils/          # 工具函数和配置
```

## 📞 社区支持

- **💬 问题反馈**: [GitHub Issues](https://github.com/your-org/mito-forge/issues)
- **📧 邮件联系**: contact@mito-forge.org
- **🌐 项目主页**: https://github.com/your-org/mito-forge
- **📖 文档站点**: https://mito-forge.readthedocs.io

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**版本**: v1.0.0 | **更新**: 2025-01-09 | **状态**: ✅ 生产就绪

**⭐ 如果这个项目对您有帮助，请给个Star支持我们！**