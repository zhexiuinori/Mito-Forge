from mito_forge.cli.commands.pipeline import select_tool_plan

def _assert_common_shape(plan):
    assert isinstance(plan, dict)
    assert "qc" in plan and isinstance(plan["qc"], list)
    assert "assembler" in plan and isinstance(plan["assembler"], dict)
    assert "polishers" in plan and isinstance(plan["polishers"], list)
    asm = plan["assembler"]
    assert "name" in asm and isinstance(asm["name"], str)
    assert "params" in asm and isinstance(asm["params"], dict)

def test_illumina_plan_details():
    plan = select_tool_plan("illumina")
    _assert_common_shape(plan)
    # QC 包含 fastp 与 fastqc（顺序非强制，但两者应存在）
    assert "fastp" in plan["qc"]
    assert "fastqc" in plan["qc"]
    # 组装器为 SPAdes
    assert plan["assembler"]["name"] == "spades"
    # 抛光采用 Pilon
    assert plan["polishers"] == ["pilon"]

def test_ont_plan_details():
    plan = select_tool_plan("ont")
    _assert_common_shape(plan)
    # 长读 QC
    assert plan["qc"][0] in ("nanoqc", "nanoplot", "nanoqc")
    # Flye 模式应为 ont
    assert plan["assembler"]["name"] == "flye"
    mode = plan["assembler"]["params"].get("mode")
    assert mode in ("ont", "nano-raw", "nano-corr")  # 兼容命名
    # 抛光顺序至少 racon 在前、medaka 在后
    assert "racon" in plan["polishers"]
    assert "medaka" in plan["polishers"]
    assert plan["polishers"].index("racon") < plan["polishers"].index("medaka")

def test_pacbio_hifi_plan_details():
    plan = select_tool_plan("pacbio-hifi")
    _assert_common_shape(plan)
    # Hifi 首选 hifiasm；若 flye 则模式应为 pacbio-hifi
    asm = plan["assembler"]
    assert asm["name"] in ("hifiasm", "flye")
    if asm["name"] == "flye":
        assert asm["params"].get("mode") in ("pacbio-hifi", "pb-hifi")
    # 抛光可为空或轻量
    assert isinstance(plan["polishers"], list)

def test_pacbio_clr_plan_details():
    plan = select_tool_plan("pacbio-clr")
    _assert_common_shape(plan)
    # Flye 模式应为 pacbio-raw
    assert plan["assembler"]["name"] == "flye"
    assert plan["assembler"]["params"].get("mode") in ("pacbio-raw", "pb-raw")
    # Racon 多轮
    assert plan["polishers"].count("racon") >= 2

def test_hybrid_plan_details():
    plan = select_tool_plan("hybrid")
    _assert_common_shape(plan)
    # 混合策略优先 Unicycler；若非则允许 spades + scaffold
    assert plan["assembler"]["name"] in ("unicycler", "spades")
    # QC 需同时覆盖短读与长读统计
    assert "fastp" in plan["qc"]
    assert any(x in plan["qc"] for x in ("longread_stats", "nanoqc", "nanoplot", "nanoqc"))
    # 抛光链包含 racon（长读校正）与 pilon（短读精修），顺序 racon -> pilon
    assert "racon" in plan["polishers"]
    assert "pilon" in plan["polishers"]
    assert plan["polishers"].index("racon") < plan["polishers"].index("pilon")