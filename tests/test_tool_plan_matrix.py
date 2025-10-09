from mito_forge.cli.commands.pipeline import select_tool_plan

def test_plan_for_illumina():
    plan = select_tool_plan("illumina")
    assert plan["assembler"]["name"] == "spades"
    assert "fastp" in plan["qc"]
    assert "pilon" in plan["polishers"]

def test_plan_for_ont():
    plan = select_tool_plan("ont")
    assert plan["assembler"]["name"] == "flye"
    assert "racon" in plan["polishers"]
    assert "medaka" in plan["polishers"]

def test_plan_for_pacbio_hifi():
    plan = select_tool_plan("pacbio-hifi")
    assert plan["assembler"]["name"] in ("hifiasm", "flye")
    # hifi 通常无需重抛光，若存在也应是轻量
    assert isinstance(plan["polishers"], list)

def test_plan_for_pacbio_clr():
    plan = select_tool_plan("pacbio-clr")
    assert plan["assembler"]["name"] == "flye"
    # 误差较高，一般需要多轮 racon
    assert plan["polishers"].count("racon") >= 1

def test_plan_for_hybrid():
    plan = select_tool_plan("hybrid")
    assert plan["assembler"]["name"] in ("unicycler", "spades")
    # 混合策略常见：先长读抛光，再短读精修
    assert "racon" in plan["polishers"] or "pilon" in plan["polishers"]