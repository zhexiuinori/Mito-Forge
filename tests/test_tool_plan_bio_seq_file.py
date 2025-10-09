from mito_forge.cli.commands.pipeline import select_tool_plan

def test_animal_illumina_fastq_has_mitoz_getorganelle_candidates():
    plan = select_tool_plan("illumina", kingdom="animal", input_types=["FASTQ"])
    assert "candidates" in plan and isinstance(plan["candidates"], dict)
    asm_list = plan["candidates"].get("assembler", [])
    assert any(x.lower() in {"mitoz", "getorganelle", "novoplasty", "spades"} for x in asm_list)
    # 仍保持兼容的主 assembler
    assert plan["assembler"]["name"] in {"spades"}

def test_animal_ont_fastq_has_flye_and_polish_order():
    plan = select_tool_plan("ont", kingdom="animal", input_types=["FASTQ"])
    asm_list = plan["candidates"].get("assembler", [])
    assert any(x.lower() in {"flye", "canu"} for x in asm_list)
    # 抛光顺序 racon -> medaka
    pol = [p.lower() for p in plan["polishers"]]
    assert "racon" in pol and "medaka" in pol
    assert pol.index("racon") < pol.index("medaka")

def test_animal_pacbio_hifi_prefers_mitohifi_or_hifiasm():
    plan = select_tool_plan("pacbio-hifi", kingdom="animal", input_types=["FASTQ"])
    asm_list = [x.lower() for x in plan["candidates"].get("assembler", [])]
    assert any(x in {"mitohifi", "hifiasm"} for x in asm_list)
    assert plan["assembler"]["name"] in {"hifiasm", "flye"}

def test_plant_illumina_fastq_has_getorganelle_novoplasty():
    plan = select_tool_plan("illumina", kingdom="plant", input_types=["FASTQ"])
    asm_list = [x.lower() for x in plan["candidates"].get("assembler", [])]
    assert any(x in {"getorganelle", "novoplasty", "spades"} for x in asm_list)

def test_fungi_illumina_fastq_has_norgal_or_novoplasty():
    plan = select_tool_plan("illumina", kingdom="fungi", input_types=["FASTQ"])
    asm_list = [x.lower() for x in plan["candidates"].get("assembler", [])]
    assert any(x in {"norgal", "novoplasty", "spades"} for x in asm_list)

def test_hybrid_fastq_has_unicycler_and_polish_order():
    plan = select_tool_plan("hybrid", kingdom="animal", input_types=["FASTQ"])
    asm_list = [x.lower() for x in plan["candidates"].get("assembler", [])]
    assert any(x in {"unicycler", "spades"} for x in asm_list)
    pol = [p.lower() for p in plan["polishers"]]
    assert "racon" in pol and "pilon" in pol
    assert pol.index("racon") < pol.index("pilon")

def test_bam_input_suggests_baiting_tools():
    plan = select_tool_plan("illumina", kingdom="animal", input_types=["BAM"])
    extras = plan.get("extras", {})
    bait = [x.lower() for x in extras.get("baiting_tools", [])]
    # MITObim/ARC 任意一个出现即可
    assert any(x in {"mitobim", "arc"} for x in bait)