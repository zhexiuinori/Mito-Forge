# 快速开始（用户视角）

本指南带你在最少的步骤下跑通 Mito-Forge。你可以选择干跑（不调用真实外部工具）或真实模式。

## 1. 准备运行环境

- 容器（推荐）：已安装 Docker/Apptainer，直接运行
- 或 Conda/mamba（Linux/WSL2）：创建环境后运行
- 或原生 Windows（实验性）：建议用 WSL2，原生仅作演示

## 2. 使用示例数据（仓库内已有）

- 示例 reads：
  - work/test_task_llm/reads.fastq
  - 或 work/tmp_demo/R1.fastq、R2.fastq

## 3. 干跑（推荐新手先验证）

- Windows PowerShell：
  - $env:MITO_DRY_RUN = "1"
- Linux/WSL2：
  - export MITO_DRY_RUN=1

- 执行流水线：
  - python -m mito_forge.cli.commands.pipeline --reads "work/test_task_llm/reads.fastq" -o "work/test_task_002" --threads 2 --lang zh --detail-level quick

- 预期结果：
  - 终端显示各阶段进度与摘要
  - 输出目录：work/test_task_002/work/
  - 报告文件：work/test_task_002/work/report/pipeline_report.html

## 4. 实跑（调用真实外部工具）

- 取消干跑：
  - Windows：Remove-Item Env:MITO_DRY_RUN
  - Linux/WSL2：unset MITO_DRY_RUN
- 确认外部工具已安装并在 PATH：
  - QC：fastqc 或 NanoPlot
  - 组装：spades（或 spades.py）、flye
  - 注释：mitos/mitos2 等
- 运行示例：
  - python -m mito_forge.cli.commands.pipeline --reads /path/to/reads.fastq -o /path/to/output --threads 4 --lang zh

## 5. 子命令用法（按需逐步运行）

- 查看帮助：
  - python -m mito_forge.cli.commands.pipeline --help
  - python -m mito_forge.cli.commands.qc --help
  - python -m mito_forge.cli.commands.assembly --help
  - python -m mito_forge.cli.commands.annotation --help
  - python -m mito_forge.cli.commands.config --help
  - python -m mito_forge.cli.commands.doctor --help
- 建议路径：
  - 先运行 doctor 进行体检 → 干跑验证 → 真实模式执行

## 6. 常见问题与提示

- 首次运行失败？
  - 检查外部工具是否安装；运行 doctor 获取缺失项与安装建议
- 网络受限导致 LLM 错误？
  - 系统自动降级为规则评估，不影响主流程；报告中会注明
- Windows 原生报错多？
  - 强烈建议在 WSL2 环境运行，兼容性更好
- 输出目录结构：
  - work/<task>/work/01_qc、02_assembly、03_annotation、report 等
  - 关键产物：fastqc_report.html、contigs.fasta、mitochondrial_candidates.fasta、annotation.gff、genes.tsv、pipeline_report.html

## 7. 下一步

- 在 Linux/WSL2 环境下安装工具并进行真实运行
- 使用自己的测序数据并根据 --seq-type 选择工具链（auto/illumina/ont/pacbio-hifi/pacbio-clr/hybrid）
- 将报告用于分析与复现，保存 tools.json/params.json（后续版本将补充）

祝你使用顺利！如需我进一步生成更详细的安装清单或容器镜像说明，请告知。