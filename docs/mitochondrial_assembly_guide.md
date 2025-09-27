# 线粒体基因组组装指南（仅组装）

本指南聚焦“只做线粒体基因组的组装”，不包含质控与注释。内容涵盖动物/植物差异、工具选择、输入输出规范、环形检测与线粒体候选筛选策略、抛光建议与失败处理。

## 1. 目标与范围
- 目标：将原始测序数据（Illumina短读、ONT长读、PacBio HiFi）组装为线粒体基因组候选产物。
- 范围：仅组装阶段，不包含质控（QC）与注释（Annotation）。
- 输出：标准化的 contigs.fasta、mito_contig.fasta（动物通常单条；植物可能多条候选）、assembly_metrics.json、circularization.txt、logs/assembler.log。

## 2. 输入与输出规范
- 输入
  - Illumina：R1.fastq / R2.fastq（或 .fastq.gz）
  - ONT：reads.fastq(.gz)
  - PacBio HiFi：hifi.fastq(.gz)
  - 可选参考库（BLAST用）：`ref_fasta`（动物或植物线粒体参考集合）
- 输出目录结构（建议）
```
results/02_assembly/
├── contigs.fasta
├── mito_contig.fasta                # 动物多为单条；植物可能为空或转为候选列表
├── mito_candidates/                 # 植物场景可能存在多个候选
│   ├── candidate_1.fasta
│   └── candidate_2.fasta
├── assembly_metrics.json            # N50、contigs数、最大长度、是否环化、覆盖估计等
├── circularization.txt              # 环形检测证据与结论
└── logs/
    └── assembler.log
```

## 3. 动物 vs 植物的差异
- 动物（animal）
  - 典型大小：14–20 kb（多数 16–17 kb），单环结构、基因集保守
  - 期望产出：单条环形 contig（mito_contig.fasta）
  - 干扰因素：NUMTs（核插入的线粒体片段），需通过环化与BLAST排除
- 植物（plant）
  - 大小范围宽：几十 kb 到数 Mb；结构复杂（多重环/亚环、重复、重组）
  - 期望产出：多个候选 contig；不强制单环
  - 干扰因素：叶绿体序列混入、核-质体互转片段；需BLAST与长度/标志基因综合筛选

## 4. 工具选择矩阵（按测序类型）
- Illumina 短读
  - 动物：Unicycler（环形友好）或 SPAdes
  - 植物：GetOrganelle / NOVOPlasty（器官基因组专用，需种子/参考）
- ONT 长读
  - 动物：Flye（对小环支持好；可加 `--plasmids`）
  - 植物：Flye（接受多部分结构；必要时参数调整）
- PacBio HiFi
  - 动物：hifiasm（推荐）或 HiCanu（genomeSize≈16k）
  - 植物：hifiasm / HiCanu（genomeSize需谨慎，可能多条候选）

建议的最小支持集（MVP）：
- animal：Unicycler / Flye / hifiasm
- plant：GetOrganelle / Flye

## 5. 线粒体候选筛选策略
- 动物（默认：启发式 + 可选BLAST）
  - 启发式：长度 14–20 kb、覆盖度最高、工具标注 circular 优先
  - BLAST：命中动物线粒体参考（如 cox1/cox2 标志基因）得分最高者为 `mito_contig.fasta`
- 植物（默认：BLAST优先）
  - BLAST：对植物线粒体参考库命中显著者，可能返回多个候选
  - 辅助启发式：长度 > 50 kb、包含线粒体标志基因，覆盖度次要
  - 产出：`mito_candidates/` 多条，附每条得分/环化证据说明

## 6. 环形检测（circularization）
- 基于工具标注（Unicycler/Flye 常有 circular 标记）
- 末端重叠检测：对候选 contig 进行末端比对（例如 ≥200 bp 高相似重叠）判定环化
- 证据记录：写入 `circularization.txt` 包含方法、阈值、结论

## 7. 抛光（polishing）建议
- HiFi：通常不需要抛光（误差率低）
- ONT：可选 Racon / Medaka；短读：Pilon
- 默认关闭抛光，仅在指标不佳时作为“降级策略”启用

## 8. 失败处理与降级策略
- 动物
  - N50 过低或 contigs 过碎 → 切换工具（SPAdes ↔ Unicycler / Flye），或启用抛光后重试
  - BLAST 不命中且长度异常 → 标注“不确定”，输出全部 contigs 并建议人工审阅
- 植物
  - 单环不可信 → 输出多个候选，记录结构复杂性说明；避免误导为“完成单环”
  - BLAST 命中混杂（叶绿体/核片段）→ 加强参考库或参数过滤，保留候选列表

## 9. CLI 参数建议（仅组装）
- 通用：
  - `--threads`、`--memory`
  - `--assembler {unicycler, spades, flye, hifiasm, hicanu, getorganelle, novoplasty}`
  - `--kingdom {animal, plant}`（默认 animal）
  - `--select-mito {none, heuristic, blast, hybrid}`（animal 推荐 heuristic/hybrid；plant 推荐 blast）
  - `--ref-fasta PATH`（BLAST 用，推荐提供）
  - `--genome-size SIZE`（如 16k，仅在支持的工具上有用）
  - `--polish {none, pilon, racon, medaka}`（默认 none）
  - `--circular-only`（animal 建议默认 true；plant 建议默认 false）

## 10. 示例用法（概念）
- 动物短读（Illumina）
  - `mito-forge assembly R1.fastq R2.fastq -o results/02_assembly --kingdom animal --assembler unicycler --threads 8 --select-mito hybrid --ref-fasta animal_mito_refs.fasta`
- 植物短读
  - `mito-forge assembly R1.fastq R2.fastq -o results/02_assembly --kingdom plant --assembler getorganelle --threads 16 --select-mito blast --ref-fasta plant_mito_refs.fasta`
- 动物 HiFi
  - `mito-forge assembly hifi.fastq.gz -o results/02_assembly --kingdom animal --assembler hifiasm --threads 16 --select-mito heuristic`
- 植物 ONT
  - `mito-forge assembly ont.fastq.gz -o results/02_assembly --kingdom plant --assembler flye --threads 16 --select-mito blast --ref-fasta plant_mito_refs.fasta`

## 11. 实施路线（文档层规划）
- MVP：animal（Unicycler/Flye/hifiasm）+ plant（GetOrganelle/Flye），启发式/BLAST筛选与环化检测
- 增强1：加入 HiCanu / SPAdes；抛光作为降级策略
- 增强2：器官专用工具与参考库优化；多候选报告增强
- 增强3：自动判定数据类型与工具推荐；失败重试与工具切换策略完善

> 注：本指南仅为文档规划与使用建议，不涉及具体代码实现。后续实现可依此文档逐步落地。