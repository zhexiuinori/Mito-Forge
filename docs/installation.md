# 安装与环境准备（用户指南）

本指南帮助你在 Linux、WSL2（Windows）、以及容器环境下快速搭建并运行 Mito-Forge。建议优先使用容器或 Conda/mamba 环境，获得更好的复现与兼容性。

## 一、推荐顺序

1. 容器镜像（Docker/Apptainer）：最省心，版本可复现，科研/集群场景友好
2. Conda/mamba 环境（Linux/WSL2）：跨平台易安装，体检工具后即可运行
3. 原生 Windows：建议使用 WSL2；原生支持子集工具，适合轻量演示

---

## 二、容器方式（推荐）

### Docker（桌面/服务器）
- 准备：
  - 安装 Docker（Linux/Windows/macOS）
  - 将数据目录挂载进容器
- 运行示例：
  - docker run --rm -v "$PWD":/work ghcr.io/your-org/mito-forge:latest \
    python -m mito_forge.cli.commands.pipeline --reads /work/path/to/reads.fastq -o /work/results --threads 4 --lang zh
- 优点：
  - 免安装依赖，镜像内已包含所需工具（fastqc/spades/flye/mitos 等）
  - 可复现，一次构建，多处运行
- 集群无 Docker 时，使用 Apptainer/Singularity 运行同一镜像

### Apptainer/Singularity（集群）
- 拉取镜像并运行：
  - apptainer run --bind "$PWD":/work mito-forge.sif python -m mito_forge.cli.commands.pipeline --reads /work/reads.fastq -o /work/results

---

## 三、Conda/mamba 环境（Linux/WSL2/原生）

### 安装 mamba（推荐）
- Linux/macOS：
  - curl -Ls https://micro.mamba.pm/install.sh | bash
  - 重新打开终端使 mamba 可用
- Windows（WSL2 Ubuntu）：
  - 同上，在 WSL2 里安装

### 创建环境
- 在项目根目录：
  - mamba env create -f environment.yml
  - conda activate mito-forge

若未提供 environment.yml，可手动安装基础依赖：
- pip install -e .
- 外部工具（用户自行安装并确保在 PATH）：
  - fastqc、NanoPlot（QC）
  - spades 或 spades.py、flye（Assembly）
  - mitos/mitos2 或相关注释工具（Annotation）

---

## 四、Windows 指南

### 强烈推荐：WSL2 + mamba
- 在 Microsoft Store 安装 Ubuntu（WSL2），然后按“Conda/mamba 环境”步骤创建环境
- 从 WSL2 内运行命令，兼容性与性能更好

### 原生 Windows（实验性）
- PowerShell：
  - python -m venv .venv; .\.venv\Scripts\Activate.ps1
  - pip install -U pip
  - pip install -e .
- 外部工具安装注意：
  - 大多数生信工具对 Linux 支持更好；Windows 原生安装可能受限
  - 如需原生演示，建议先使用干跑模式验证流程

---

## 五、依赖自检与干跑模式

### 依赖体检
- 运行 doctor（若提供）：
  - python -m mito_forge.cli.commands.doctor --help
  - doctor 将检测工具是否安装与版本是否满足要求

### 干跑模式（不调用真实外部工具）
- Windows PowerShell：
  - $env:MITO_DRY_RUN = "1"
- Linux/WSL2：
  - export MITO_DRY_RUN=1
- 干跑会生成日志与报告框架，便于快速验证流程

---

## 六、外部工具准备策略

- 默认建议用户自行安装（或使用容器）：
  - 项目体积小、许可清晰、更新容易
- 容器镜像内预置工具（生产推荐）：
  - 统一版本，保证复现；用容器运行即可
- 提供 doctor 与安装提示：
  - 缺失工具时 CLI 给出安装建议与最低版本要求
- 支持在配置中指定工具路径：
  - 便于集群模块化环境或多版本共存

---

## 七、常见问题（FAQ）

- 找不到命令 mito_forge/mito-forge？
  - 通过 python -m 模式运行子命令：python -m mito_forge.cli.commands.pipeline --help
  - 或安装后由 console_scripts 提供统一入口（未来版本）

- LLM 网络不可用报错？
  - 流程会自动降级为规则评估；不影响主流程完成

- 输出目录与数据体量？
  - pipeline 可能生成较多文件，请确保磁盘空间足够；建议将输出目录放在可写入路径

---

如需我提供 environment.yml 或容器 Dockerfile 草案，可在后续版本中添加至 docs 并在 doctor 命令中联动提示。