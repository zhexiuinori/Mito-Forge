# 🧬 Mito-Forge

**线粒体基因组学多智能体自动化框架**

一个专为Linux环境设计的命令行工具，基于联邦知识系统的多智能体协作，实现线粒体基因组分析的全流程自动化。

## ✨ 特性

- 🤖 **多智能体协作** - 质控、组装、注释、分析智能体协同工作
- 🧠 **联邦知识系统** - 基于RAG的专业知识库支持
- 🚀 **一键式流水线** - 从原始数据到最终结果的完整自动化
- 🎯 **专业CLI界面** - 符合生物信息学工作习惯
- ⚡ **高性能处理** - 支持多线程并行和HPC集群
- 📊 **标准化输出** - 生成发表级别的分析报告

## 🔧 安装

### 系统要求
- Linux (Ubuntu 18.04+, CentOS 7+)
- Python 3.8+
- 8GB+ RAM (推荐16GB)

### 快速安装
```bash
# 克隆项目
git clone https://github.com/mito-forge/mito-forge.git
cd mito-forge

# 安装依赖和工具
./install_linux.sh

# 安装Mito-Forge
pip install -e .
```

## 🚀 快速开始

### 完整流水线分析
```bash
# 分析双端测序数据
mito-forge pipeline sample_R1.fastq sample_R2.fastq \
    --output-dir ./results \
    --threads 8 \
    --assembler spades
```

### 单步分析
```bash
# 质量控制
mito-forge qc *.fastq --threads 4

# 基因组组装
mito-forge assembly contigs.fasta --assembler unicycler

# 基因注释
mito-forge annotate genome.fasta --tool mitos

# 系统检查
mito-forge doctor --check-all
```

### 配置管理
```bash
# 查看当前配置
mito-forge config show

# 设置默认参数
mito-forge config set threads 16
mito-forge config set memory 32G
```

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

## 📖 文档

- [架构文档](docs/architecture.md)
- [使用示例](examples/cli_usage.md)
- [API参考](https://mito-forge.readthedocs.io)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [项目主页](https://github.com/mito-forge/mito-forge)
- [文档站点](https://mito-forge.readthedocs.io)
- [问题反馈](https://github.com/mito-forge/mito-forge/issues)

---

**Mito-Forge** - 让线粒体基因组学分析更简单、更智能！ 🧬✨