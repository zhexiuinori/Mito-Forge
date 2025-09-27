# Mito-Forge CLI 使用指南

## 概述

Mito-Forge 提供了强大的命令行界面，专为生物信息学研究人员设计。CLI界面支持完整的线粒体基因组分析流水线，包括质量控制、基因组组装、功能注释和高级分析。

## 安装

### 快速安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/your-org/mito-forge.git
cd mito-forge

# 运行安装脚本
chmod +x scripts/install.sh
./scripts/install.sh
```

### 手动安装

```bash
# 创建虚拟环境
python3 -m venv mito-forge-env
source mito-forge-env/bin/activate

# 安装依赖
pip install -r requirements-cli.txt

# 安装Mito-Forge
pip install -e .
```

## 基本用法

### 查看帮助

```bash
# 查看主帮助
mito-forge --help

# 查看特定命令帮助
mito-forge pipeline --help
mito-forge qc --help
```

### 系统检查

```bash
# 完整系统检查
mito-forge doctor

# 检查特定组件
mito-forge doctor --check-tools
mito-forge doctor --check-deps
mito-forge doctor --check-db
```

## 主要命令

### 1. 完整流水线分析

运行从质控到注释的完整分析流水线：

```bash
# 基本用法
mito-forge pipeline sample_R1.fastq sample_R2.fastq -o results/

# 自定义参数
mito-forge pipeline \
    sample_R1.fastq sample_R2.fastq \
    --output-dir ./analysis_results \
    --quality-threshold 25 \
    --assembler spades \
    --annotation-tool mitos \
    --threads 8 \
    --memory 16G
```

### 2. 质量控制

单独进行数据质量控制：

```bash
# 基本质控
mito-forge qc sample_R1.fastq sample_R2.fastq

# 自定义质控参数
mito-forge qc \
    sample_R1.fastq sample_R2.fastq \
    --output-dir ./qc_results \
    --quality-threshold 20 \
    --adapter-file adapters.fa \
    --threads 4
```

### 3. 基因组组装

进行基因组组装：

```bash
# 使用SPAdes组装
mito-forge assembly \
    clean_R1.fastq clean_R2.fastq \
    --assembler spades \
    --threads 8 \
    --memory 16G

# 使用Unicycler组装
mito-forge assembly \
    clean_R1.fastq clean_R2.fastq \
    --assembler unicycler \
    --kmer-sizes 21,33,55,77
```

### 4. 基因组注释

对组装好的基因组进行注释：

```bash
# 使用MITOS注释
mito-forge annotate \
    contigs.fasta \
    --annotation-tool mitos \
    --genetic-code 2 \
    --output-dir ./annotation_results

# 使用自定义参考数据库
mito-forge annotate \
    contigs.fasta \
    --annotation-tool mitos \
    --reference-db custom_db.fasta
```

### 5. 高级分析

进行系统发育和比较基因组学分析：

```bash
# 系统发育分析
mito-forge analyze \
    *.fasta \
    --analysis-type phylogeny \
    --output-dir ./phylogeny_results

# 比较基因组学分析
mito-forge analyze \
    genome1.fasta genome2.fasta genome3.fasta \
    --analysis-type comparative \
    --reference-file reference.fasta
```

## 智能体管理

### 查看智能体状态

```bash
# 表格格式显示
mito-forge agents

# JSON格式输出
mito-forge agents --format json

# YAML格式输出
mito-forge agents --format yaml
```

### 知识库查询

```bash
# 查询质控知识库
mito-forge knowledge --kb-name qc --query "FastQC参数优化"

# 查询组装知识库
mito-forge knowledge --kb-name assembly --query "SPAdes内存使用" --top-k 3

# 查询注释知识库
mito-forge knowledge --kb-name annotation --query "线粒体基因预测"
```

## 高级用法

### 批量处理

```bash
#!/bin/bash
# 批量处理多个样本

SAMPLES_DIR="/path/to/samples"
OUTPUT_DIR="/path/to/results"

for sample in $(ls $SAMPLES_DIR/*_R1.fastq | sed 's/_R1.fastq//'); do
    sample_name=$(basename $sample)
    echo "处理样本: $sample_name"
    
    mito-forge pipeline \
        ${sample}_R1.fastq \
        ${sample}_R2.fastq \
        --output-dir $OUTPUT_DIR/$sample_name \
        --threads 8 \
        --verbose
done
```

### 配置文件使用

创建配置文件 `config.yaml`：

```yaml
# Mito-Forge 配置文件
quality_control:
  threshold: 25
  adapter_file: "adapters.fa"
  
assembly:
  assembler: "spades"
  kmer_sizes: [21, 33, 55, 77]
  memory: "16G"
  
annotation:
  tool: "mitos"
  genetic_code: 2
  
analysis:
  threads: 8
  output_format: "fasta"
```

使用配置文件：

```bash
mito-forge pipeline \
    sample_R1.fastq sample_R2.fastq \
    --config-file config.yaml \
    --output-dir results/
```

### 流水线定制

跳过特定步骤：

```bash
# 跳过质控（使用已清理的数据）
mito-forge pipeline \
    clean_R1.fastq clean_R2.fastq \
    --skip-qc \
    --output-dir results/

# 只进行质控和组装
mito-forge pipeline \
    sample_R1.fastq sample_R2.fastq \
    --skip-annotation \
    --output-dir results/
```

## 输出文件结构

典型的输出目录结构：

```
results/
├── 01_quality_control/
│   ├── fastqc_reports/
│   ├── trimmed_reads/
│   └── qc_summary.json
├── 02_assembly/
│   ├── contigs.fasta
│   ├── scaffolds.fasta
│   └── assembly_stats.json
├── 03_annotation/
│   ├── genes.gff
│   ├── proteins.faa
│   └── annotation_summary.json
├── 04_analysis/
│   ├── phylogeny/
│   └── comparative/
└── pipeline_report.html
```

## 性能优化

### 资源配置

```bash
# 高性能服务器配置
mito-forge pipeline \
    sample_R1.fastq sample_R2.fastq \
    --threads 32 \
    --memory 64G \
    --output-dir results/

# 低资源环境配置
mito-forge pipeline \
    sample_R1.fastq sample_R2.fastq \
    --threads 2 \
    --memory 4G \
    --output-dir results/
```

### 并行处理

```bash
# 使用GNU parallel进行并行处理
parallel -j 4 "mito-forge qc {} --output-dir qc_results/{/.}" ::: *.fastq
```

## 故障排除

### 常见问题

1. **工具未找到错误**
   ```bash
   # 检查工具安装
   mito-forge doctor --check-tools
   
   # 重新安装工具
   ./scripts/install.sh
   ```

2. **内存不足错误**
   ```bash
   # 减少内存使用
   mito-forge assembly sample.fastq --memory 4G
   ```

3. **权限错误**
   ```bash
   # 检查输出目录权限
   chmod 755 output_directory
   ```

### 调试模式

```bash
# 启用详细输出
mito-forge pipeline sample.fastq --verbose

# 启用调试模式
export MITO_FORGE_DEBUG=1
mito-forge pipeline sample.fastq
```

## 集成其他工具

### 与Nextflow集成

```nextflow
process MITO_FORGE_QC {
    input:
    tuple val(sample_id), path(reads)
    
    output:
    tuple val(sample_id), path("${sample_id}_qc/*")
    
    script:
    """
    mito-forge qc ${reads[0]} ${reads[1]} \
        --output-dir ${sample_id}_qc \
        --threads ${task.cpus}
    """
}
```

### 与Snakemake集成

```python
rule mito_forge_pipeline:
    input:
        r1="samples/{sample}_R1.fastq",
        r2="samples/{sample}_R2.fastq"
    output:
        directory("results/{sample}")
    threads: 8
    shell:
        "mito-forge pipeline {input.r1} {input.r2} "
        "--output-dir {output} --threads {threads}"
```

## 最佳实践

1. **数据预处理**：始终先进行质量控制
2. **资源管理**：根据数据大小调整线程和内存
3. **结果验证**：使用多种工具验证关键结果
4. **文档记录**：保存分析参数和版本信息
5. **备份重要结果**：定期备份分析结果

## 更多资源

- [API文档](https://mito-forge.readthedocs.io/)
- [GitHub仓库](https://github.com/your-org/mito-forge)
- [问题报告](https://github.com/your-org/mito-forge/issues)
- [社区论坛](https://forum.mito-forge.org/)