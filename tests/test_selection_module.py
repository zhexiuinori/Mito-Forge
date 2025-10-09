from mito_forge.utils.selection import detect_input_types, build_tool_plan, select_tool_plan as sel_select_tool_plan
from mito_forge.cli.commands.pipeline import select_tool_plan as pl_select_tool_plan, detect_seq_type as pl_detect_seq_type

def test_detect_input_types_fastq():
    assert detect_input_types("reads.fastq") == ["FASTQ"]
    assert detect_input_types(["a.fq","b.fastq"]) == ["FASTQ"]

def test_detect_input_types_fasta_bam():
    assert detect_input_types("ref.fasta") == ["FASTA"]
    assert detect_input_types("aln.bam") == ["BAM"]

def test_build_tool_plan_basic_illumina():
    plan = build_tool_plan("illumina", "animal", "reads.fastq")
    assert isinstance(plan, dict)
    assert plan["assembler"]["name"] in {"spades"}
    assert "candidates" in plan and "assembler" in plan["candidates"]
    assert any(x.lower() in {"mitoz","getorganelle","novoplasty","spades"} for x in [y.lower() for y in plan["candidates"]["assembler"]])

def test_select_tool_plan_consistency_with_pipeline():
    # 两个接口在核心选择上需一致
    p1 = sel_select_tool_plan("ont", kingdom="animal", input_types=["FASTQ"])
    p2 = pl_select_tool_plan("ont")
    assert p1["assembler"]["name"] == p2["assembler"]["name"]
    assert p1["polishers"][0].lower() == "racon"

def test_pipeline_detect_seq_type_compat():
    # 确保 pipeline 的封装仍可用
    assert pl_detect_seq_type(["R1.fastq","R2.fastq"]) == "illumina"