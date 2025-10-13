# Polishing（抛光）功能使用指南

## 概述

Polishing（抛光）是提高基因组组装准确性的重要步骤，通过将原始读段比对回组装结果，修正碱基错误、小片段插入缺失等问题。

Mito-Forge 集成了三种主流抛光工具，自动根据数据类型选择最佳策略。

## 支持的抛光工具

### 1. Racon - 长读数据快速抛光

**适用数据**：
- Oxford Nanopore (ONT)
- PacBio CLR (连续长读)

**特点**：
- 快速（通常 10-30 分钟）
- 支持多轮迭代
- 使用 minimap2 进行比对

**推荐配置**：
```yaml
tool_chain:
  polishing: "racon"
parameters:
  racon:
    iterations: 2  # Nanopore 推荐 2 轮
    # iterations: 3  # PacBio CLR 推荐 3 轮
```

### 2. Pilon - 短读数据精确抛光

**适用数据**：
- Illumina（双端或单端）

**特点**：
- 高精度碱基修正
- 需要比对（BWA + SAMtools）
- 可修复小片段插入缺失

**推荐配置**：
```yaml
tool_chain:
  polishing: "pilon"
parameters:
  pilon:
    memory: "16G"  # Java 堆内存
    iterations: 1  # 通常 1 轮即可
```

### 3. Medaka - Nanopore 神经网络抛光

**适用数据**：
- Oxford Nanopore (ONT)

**特点**：
- ONT 官方推荐
- 使用神经网络模型
- 精度高于 Racon
- 需要选择正确的模型

**推荐配置**：
```yaml
tool_chain:
  polishing: "medaka"
parameters:
  medaka:
    model: "r941_min_high_g360"  # R9.4.1 MinION/GridION high accuracy
    # model: "r103_min_high_g360"  # R10.3 MinION high accuracy
    # model: "r104_e81_sup_g5015"  # R10.4.1 SUP basecalling
```

**常用模型列表**：
- `r941_min_high_g360`: R9.4.1 MinION/GridION high accuracy (Guppy ≥3.6.0)
- `r941_min_fast_g303`: R9.4.1 MinION/GridION fast basecalling (Guppy 3.0.3+)
- `r941_prom_high_g360`: R9.4.1 PromethION high accuracy (Guppy ≥3.6.0)
- `r103_min_high_g360`: R10.3 MinION high accuracy (Guppy ≥3.6.0)
- `r104_e81_sup_g5015`: R10.4.1 SUP basecalling (Guppy 5.0.15+)

## 使用方法

### 自动选择（推荐）

Supervisor Agent 会根据数据类型自动选择最佳抛光工具：

```bash
# Nanopore 数据 → 自动使用 Racon 或 Medaka
python -m mito_forge pipeline --reads nanopore.fastq --kingdom animal

# Illumina 数据 → 自动使用 Pilon
python -m mito_forge pipeline --reads illumina_R1.fastq --reads2 illumina_R2.fastq

# PacBio HiFi 数据 → 不需要抛光（质量已足够高）
python -m mito_forge pipeline --reads pacbio_hifi.fastq
```

### 手动指定

通过配置文件手动指定抛光工具：

```bash
# 创建配置文件 custom_config.yaml
cat > custom_config.yaml << EOF
tool_chain:
  qc: "fastqc"
  assembly: "spades"
  polishing: "medaka"  # 手动指定使用 Medaka
  annotation: "mitos"

parameters:
  medaka:
    model: "r941_min_high_g360"
    threads: 8
EOF

# 使用配置文件运行
python -m mito_forge pipeline --reads data.fastq --config custom_config.yaml
```

### 跳过抛光

如果不需要抛光，设置 `polishing: null`：

```yaml
tool_chain:
  polishing: null  # 跳过抛光步骤
```

## 抛光策略矩阵

| 数据类型 | 推荐工具 | 迭代次数 | 预期时间 | 预期改进 |
|---------|---------|---------|---------|---------|
| Illumina | Pilon | 1 | 30-60 分钟 | N50 +2-5% |
| Nanopore (R9) | Racon + Medaka | 2 + 1 | 20-40 分钟 | N50 +5-10% |
| Nanopore (R10) | Medaka | 1 | 30-60 分钟 | N50 +3-8% |
| PacBio CLR | Racon | 3 | 30-60 分钟 | N50 +5-15% |
| PacBio HiFi | 无 | - | - | 不需要 |

## 工作流程

```
QC → Assembly → Polishing → Annotation → Report
                    ↓
                质量评估
                    ↓
              更新组装文件
```

### Polishing 阶段详细步骤

1. **检查是否需要抛光**
   - 检查 `tool_chain.polishing` 配置
   - 如果为 `null` 或未设置，跳过抛光

2. **准备输入文件**
   - 原始读段（来自 QC 阶段）
   - 组装结果（来自 Assembly 阶段）

3. **执行抛光**
   - Racon: minimap2 比对 → racon 抛光 → 多轮迭代
   - Pilon: BWA 比对 → BAM 转换 → Pilon 修正
   - Medaka: medaka_consensus 一步完成

4. **质量评估**
   - 对比抛光前后的统计信息
   - 计算 N50、总长度、contig 数量变化

5. **更新结果**
   - 将抛光后的序列作为最终组装结果
   - 传递给 Annotation 阶段

## 输出文件

抛光阶段会在 `work/<pipeline_id>/03_polish/` 目录下生成：

```
03_polish/
├── iter1.paf                    # 第一轮比对（Racon）
├── polished_iter1.fasta         # 第一轮抛光
├── iter2.paf                    # 第二轮比对（Racon）
├── polished_iter2.fasta         # 第二轮抛光
├── polished.fasta               # 最终抛光结果
├── iter1.sorted.bam             # BWA 比对结果（Pilon）
├── iter1.sorted.bam.bai         # BAM 索引
└── medaka_output/               # Medaka 输出目录
    └── consensus.fasta
```

## 质量评估指标

Polishing 完成后会生成改进报告：

```json
{
  "status": "calculated",
  "length_change": 50,
  "length_change_pct": 0.5,
  "n50_change": 1200,
  "n50_change_pct": 5.2,
  "original": {
    "total_length": 368000,
    "num_contigs": 3,
    "n50": 16800
  },
  "polished": {
    "total_length": 368050,
    "num_contigs": 3,
    "n50": 18000
  }
}
```

## 故障排除

### 工具未安装

**错误**: `RuntimeError: Racon not found in PATH`

**解决**:
```bash
# Conda 安装（推荐）
conda install -c bioconda racon
conda install -c bioconda pilon
conda install -c bioconda medaka

# 或使用 doctor 命令自动安装
python -m mito_forge doctor --fix-issues
```

### 内存不足

**错误**: `OutOfMemoryError` (Pilon)

**解决**:
```yaml
parameters:
  pilon:
    memory: "32G"  # 增加 Java 堆内存
```

### Medaka 模型选择错误

**错误**: `Model not found`

**解决**: 根据测序化学配方和 basecaller 版本选择正确的模型
```bash
# 查看可用模型
medaka tools list_models

# 在配置中使用正确的模型名称
```

### 抛光失败不影响流程

如果抛光失败，流程会继续执行后续阶段（Annotation），并记录错误：
```
[WARNING] Polishing failed: Tool execution error
[INFO] Continuing with original assembly...
```

## 性能优化

### 1. 增加线程数
```bash
python -m mito_forge pipeline --reads data.fastq --threads 16
```

### 2. 减少迭代次数（快速模式）
```yaml
parameters:
  racon:
    iterations: 1  # 从 2-3 轮减少到 1 轮
```

### 3. 跳过不必要的抛光
```yaml
# PacBio HiFi 数据通常不需要抛光
tool_chain:
  polishing: null
```

## 最佳实践

1. **Nanopore 数据**：推荐 Racon (2轮) + Medaka (1轮) 组合
2. **Illumina 数据**：Pilon (1轮) 通常足够
3. **PacBio CLR**：Racon (3轮) 可显著提高质量
4. **PacBio HiFi**：通常不需要抛光
5. **混合数据**：先用长读组装，再用短读 Pilon 抛光

## 参考文献

- Racon: Vaser et al. (2017) "Fast and accurate de novo genome assembly from long uncorrected reads"
- Pilon: Walker et al. (2014) "Pilon: An Integrated Tool for Comprehensive Microbial Variant Detection"
- Medaka: Oxford Nanopore Technologies (2021) "Medaka: Sequence correction provided by ONT Research"

## 示例命令

```bash
# 1. Nanopore 数据完整流程（带抛光）
python -m mito_forge pipeline \
  --reads nanopore.fastq \
  --kingdom animal \
  --threads 8

# 2. Illumina 双端数据（带 Pilon 抛光）
python -m mito_forge pipeline \
  --reads illumina_R1.fastq \
  --reads2 illumina_R2.fastq \
  --kingdom plant \
  --threads 16

# 3. 手动指定 Medaka 模型
python -m mito_forge pipeline \
  --reads nanopore.fastq \
  --config custom_config.yaml

# 4. 跳过抛光（快速模式）
python -m mito_forge pipeline \
  --reads hifi.fastq \
  --skip-polish

# 5. 查看抛光结果
cat work/<pipeline_id>/03_polish/polished.fasta
```

## 下一步

完成抛光后，流程会自动进入 **Annotation（注释）** 阶段，使用抛光后的高质量序列进行基因注释。
