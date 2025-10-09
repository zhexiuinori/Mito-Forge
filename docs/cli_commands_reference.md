# Mito-Forge CLI 命令参考

## 🎯 快速开始

```bash
# 查看帮助
python -m mito_forge --help

# 系统诊断
python -m mito_forge doctor

# 进入交互式菜单
python -m mito_forge menu
```

---

## 🧬 核心分析命令

### 完整流水线
**主命令 - 线粒体基因组组装完整流程**
```bash
python -m mito_forge pipeline --reads INPUT_FILE [OPTIONS]
# 或别名
python -m mito_forge run --reads INPUT_FILE [OPTIONS]
```

**参数说明：**
- `--reads PATH` - 输入测序数据文件 (必需)
- `-o, --output PATH` - 输出目录
- `-t, --threads INTEGER` - 线程数
- `--kingdom [animal|plant]` - 物种类型
- `--resume PATH` - 从检查点恢复执行
- `--checkpoint PATH` - 检查点保存路径
- `--config-file PATH` - 配置文件路径
- `-v, --verbose` - 详细输出
- `--interactive` - 交互式错误处理
- `--detail-level [quick|detailed|expert]` - 详细程度

**使用示例：**
```bash
# 基础运行
python -m mito_forge pipeline --reads sample.fastq --kingdom animal

# 完整参数
python -m mito_forge pipeline --reads sample.fastq -o results -t 8 --kingdom plant --verbose

# 从检查点恢复
python -m mito_forge pipeline --resume results/checkpoint.json
```

---

### 质量控制 (QC)
**测序数据质量控制分析**
```bash
python -m mito_forge qc INPUT_FILES... [OPTIONS]
```

**参数说明：**
- `-o, --output-dir TEXT` - 输出目录 (默认: ./qc_results)
- `-q, --quality-threshold INTEGER` - 质量阈值 (默认: 20)
- `-j, --threads INTEGER` - 线程数 (默认: 4)
- `--adapter-removal` - 执行接头序列去除
- `--trim-quality INTEGER` - 修剪质量阈值 (默认: 20)
- `--min-length INTEGER` - 最小序列长度 (默认: 50)
- `--report-only` - 仅生成质控报告，不进行数据处理
- `--detail-level [quick|detailed|expert]` - 详细程度

**使用示例：**
```bash
# 基础QC
python -m mito_forge qc sample.fastq

# 高质量QC
python -m mito_forge qc sample.fastq -q 30 --adapter-removal --threads 8

# 仅报告模式
python -m mito_forge qc sample.fastq --report-only --detail-level expert
```

---

### 基因组组装
**线粒体基因组组装**
```bash
python -m mito_forge assembly INPUT_FILES... [OPTIONS]
```

**参数说明：**
- `-o, --output-dir TEXT` - 输出目录 (默认: ./assembly_results)
- `-a, --assembler [spades|unicycler|flye]` - 组装器选择 (默认: spades)
- `-j, --threads INTEGER` - 线程数 (默认: 4)
- `-m, --memory TEXT` - 内存限制 (默认: 8G)
- `--k-values TEXT` - K-mer值 (默认: 21,33,55,77)
- `--careful-mode` - 启用careful模式（更慢但更准确）

**使用示例：**
```bash
# 基础组装
python -m mito_forge assembly cleaned_reads.fastq

# SPAdes组装
python -m mito_forge assembly cleaned_reads.fastq -a spades --threads 16 -m 32G

# Unicycler组装
python -m mito_forge assembly cleaned_reads.fastq -a unicycler --careful-mode
```

---

### 基因注释
**线粒体基因注释**
```bash
python -m mito_forge annotate INPUT_FILE [OPTIONS]
```

**参数说明：**
- `-o, --output-dir TEXT` - 输出目录 (默认: ./annotation_results)
- `-t, --annotation-tool [mitos|geseq|prokka]` - 注释工具选择 (默认: mitos)
- `-j, --threads INTEGER` - 线程数 (默认: 4)
- `--genetic-code INTEGER` - 遗传密码表 (默认: 2 - 脊椎动物线粒体)
- `--reference-db TEXT` - 参考数据库 (默认: mitochondria)

**使用示例：**
```bash
# 基础注释
python -m mito_forge annotate assembly.fasta

# MITOS注释
python -m mito_forge annotate assembly.fasta -t mitos --genetic-code 2

# GeSeq注释
python -m mito_forge annotate assembly.fasta -t geseq --threads 8
```

---

## 🎛️ 管理和配置命令

### 智能体管理
**智能体状态管理**
```bash
python -m mito_forge agents [OPTIONS]
```

**参数说明：**
- `--status` - 显示智能体状态
- `--detailed` - 显示详细信息
- `--restart TEXT` - 重启指定智能体

**使用示例：**
```bash
# 查看智能体状态
python -m mito_forge agents --status

# 详细状态
python -m mito_forge agents --detailed

# 重启智能体
python -m mito_forge agents --restart supervisor
```

---

### 配置管理
**系统配置管理**
```bash
python -m mito_forge config [OPTIONS] [ACTION]
```

**参数说明：**
- `--show` - 显示当前配置
- `--set KEY VALUE` - 设置配置项
- `--reset` - 重置为默认配置
- `--config-file PATH` - 指定配置文件路径

**使用示例：**
```bash
# 显示当前配置
python -m mito_forge config --show

# 设置线程数
python -m mito_forge config --set threads 16

# 重置配置
python -m mito_forge config --reset
```

---

### 模型配置管理
**AI模型配置管理**
```bash
python -m mito_forge model [OPTIONS] COMMAND [ARGS]...
```

**子命令：**
- `add` - 添加新的模型配置
- `create-from-preset` - 从预设创建新的配置
- `current` - 显示当前默认配置
- `doctor` - 诊断模型配置问题
- `export` - 导出配置到文件
- `import-config` - 从文件导入配置
- `list` - 列出所有可用的模型配置
- `presets` - 显示所有预设配置
- `remove` - 删除模型配置
- `show` - 显示指定配置的详细信息
- `test` - 测试指定的模型配置
- `update` - 更新现有的模型配置
- `use` - 设置默认模型配置

**使用示例：**
```bash
# 列出模型配置
python -m mito_forge model list

# 显示当前配置
python -m mito_forge model current

# 测试模型
python -m mito_forge model test gpt-4

# 切换模型
python -m mito_forge model use gpt-4-turbo
```

---

## 🔍 监控和诊断命令

### 状态查看
**流水线状态监控**
```bash
python -m mito_forge status [OPTIONS]
```

**参数说明：**
- `--checkpoint PATH` - 检查点保存路径 (必需)

**使用示例：**
```bash
# 查看运行状态
python -m mito_forge status --checkpoint results/checkpoint.json
```

---

### 系统诊断
**系统健康检查和诊断**
```bash
python -m mito_forge doctor [OPTIONS]
```

**参数说明：**
- `--check-tools` - 检查生物信息学工具
- `--check-system` - 检查系统环境
- `--check-dependencies` - 检查Python依赖
- `--fix-issues` - 尝试自动修复问题

**使用示例：**
```bash
# 完整诊断
python -m mito_forge doctor

# 检查工具
python -m mito_forge doctor --check-tools

# 自动修复
python -m mito_forge doctor --fix-issues
```

---

## 🎯 交互式工具

### 交互式菜单
**图形化交互界面**
```bash
python -m mito_forge menu    # 进入交互式菜单
```

---

## 📋 完整工作流示例

### 示例1: 完整分析流程
```bash
# 1. 系统检查
python -m mito_forge doctor --check-tools

# 2. 质量控制
python -m mito_forge qc raw_reads.fastq -o qc_results --adapter-removal

# 3. 基因组组装
python -m mito_forge assembly qc_results/cleaned_reads.fastq -o assembly_results -t 8

# 4. 基因注释
python -m mito_forge annotate assembly_results/final_assembly.fasta -o annotation_results

# 5. 或一次性完成所有步骤
python -m mito_forge pipeline --reads raw_reads.fastq --kingdom animal -o final_results -t 8
```

### 示例2: 高级配置
```bash
# 配置优化
python -m mito_forge config --set threads 16
python -m mito_forge config --set memory 32G

# 模型选择
python -m mito_forge model use gpt-4-turbo

# 运行流水线
python -m mito_forge pipeline --reads sample.fastq --kingdom plant --detail-level expert --verbose
```

### 示例3: 故障恢复
```bash
# 查看状态
python -m mito_forge status --checkpoint results/checkpoint.json

# 从检查点恢复
python -m mito_forge pipeline --resume results/checkpoint.json

# 诊断问题
python -m mito_forge doctor --check-dependencies --fix-issues
```

---

## 💡 提示和最佳实践

### 性能优化
- 使用 `-t` 或 `--threads` 参数充分利用多核CPU
- 根据可用内存调整 `-m` 或 `--memory` 参数
- 对于大型数据集，考虑使用 `--detail-level quick` 先进行快速分析

### 质量控制
- 始终先运行QC检查：`python -m mito_forge doctor --check-tools`
- 使用 `--verbose` 获取详细的运行信息
- 定期使用 `python -m mito_forge doctor` 进行系统诊断

### 结果管理
- 为每个项目创建独立的输出目录
- 使用描述性的输出目录名称
- 定期备份重要的检查点文件

### 故障排除
- 查看状态：`python -m mito_forge status --checkpoint results/checkpoint.json`
- 系统诊断：`python -m mito_forge doctor --fix-issues`
- 查看日志文件获取详细错误信息

---

## 📚 相关文档
- [架构设计](architecture.md) - 系统架构和技术细节
- [LangGraph架构](langgraph_architecture.md) - 工作流引擎设计
- [线粒体组装指南](mitochondrial_assembly_guide.md) - 生物信息学背景
- [模型配置指南](model_configuration_guide.md) - AI模型配置

---

*最后更新: 2024年* | *版本: 1.0.0*