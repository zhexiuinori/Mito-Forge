"""
测试 Polishing 集成

验证 polishing 工具封装和节点集成
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mito_forge.graph.nodes import polish_node, _run_polishing, _calculate_improvement
from mito_forge.graph.state import init_pipeline_state


def test_polish_node_skip_when_no_tool():
    """测试当没有指定 polishing 工具时跳过"""
    state = init_pipeline_state(
        inputs={"reads": "test.fastq"},
        config={
            "tool_chain": {}  # 没有 polishing
        },
        workdir="/tmp/test",
        pipeline_id="test"
    )
    
    # 添加假的 assembly 输出
    state["stage_outputs"]["assembly"] = {
        "files": {"assembly": "/tmp/assembly.fasta"}
    }
    
    with patch("mito_forge.graph.nodes.Path.exists", return_value=True):
        result = polish_node(state)
    
    assert result["route"] == "continue"
    assert state["stage_status"]["polish"] == "skipped"


def test_polish_node_skip_when_no_assembly():
    """测试当没有组装文件时跳过"""
    state = init_pipeline_state(
        inputs={"reads": "test.fastq"},
        config={
            "tool_chain": {"polishing": "racon"}
        },
        workdir="/tmp/test",
        pipeline_id="test"
    )
    
    # 没有 assembly 输出
    state["stage_outputs"]["assembly"] = {
        "files": {}
    }
    
    result = polish_node(state)
    
    assert result["route"] == "continue"
    assert state["stage_status"]["polish"] == "skipped"


@patch("mito_forge.graph.nodes._run_polishing")
@patch("mito_forge.graph.nodes._calculate_improvement")
def test_polish_node_success(mock_improvement, mock_polishing):
    """测试 polishing 成功执行"""
    # Mock polishing 结果
    mock_polishing.return_value = {
        "tool": "racon",
        "polished_file": "/tmp/polished.fasta",
        "iterations": 2,
        "success": True
    }
    
    # Mock improvement 计算
    mock_improvement.return_value = {
        "status": "calculated",
        "n50_change": 1000,
        "n50_change_pct": 5.2
    }
    
    state = init_pipeline_state(
        inputs={"reads": "test.fastq"},
        config={
            "tool_chain": {"polishing": "racon"},
            "detected_read_type": "nanopore",
            "threads": 4
        },
        workdir="/tmp/test",
        pipeline_id="test"
    )
    
    # 添加假的 assembly 输出
    state["stage_outputs"]["assembly"] = {
        "files": {"assembly": "/tmp/assembly.fasta"}
    }
    state["stage_outputs"]["qc"] = {
        "files": {"clean_reads": "/tmp/clean.fastq"}
    }
    
    with patch("mito_forge.graph.nodes.Path.exists", return_value=True), \
         patch("mito_forge.graph.nodes.Path.mkdir"):
        result = polish_node(state)
    
    assert result["route"] == "continue"
    assert state["stage_status"]["polish"] == "completed"
    assert "polished_assembly" in state["stage_outputs"]["polish"]["files"]
    
    # 验证组装文件已更新为抛光版本
    assert state["stage_outputs"]["assembly"]["files"]["assembly"] == "/tmp/polished.fasta"


def test_run_polishing_racon():
    """测试 Racon 抛光调用"""
    with patch("mito_forge.graph.nodes.run_racon") as mock_racon:
        mock_racon.return_value = {
            "tool": "racon",
            "polished_file": "/tmp/polished.fasta",
            "iterations": 2
        }
        
        result = _run_polishing(
            reads_file="/tmp/reads.fastq",
            reads2_file=None,
            assembly_file="/tmp/assembly.fasta",
            output_dir=Path("/tmp/polish"),
            tool="racon",
            read_type="nanopore",
            threads=4
        )
        
        assert result["tool"] == "racon"
        assert mock_racon.called
        
        # 验证调用参数
        call_args = mock_racon.call_args
        assert call_args.kwargs["threads"] == 4
        assert call_args.kwargs["iterations"] == 2  # Nanopore 默认 2 轮
        assert call_args.kwargs["minimap_preset"] == "map-ont"


def test_run_polishing_pilon():
    """测试 Pilon 抛光调用"""
    with patch("mito_forge.graph.nodes.run_pilon") as mock_pilon:
        mock_pilon.return_value = {
            "tool": "pilon",
            "polished_file": "/tmp/polished.fasta",
            "iterations": 1
        }
        
        result = _run_polishing(
            reads_file="/tmp/reads.fastq",
            reads2_file="/tmp/reads2.fastq",
            assembly_file="/tmp/assembly.fasta",
            output_dir=Path("/tmp/polish"),
            tool="pilon",
            read_type="illumina",
            threads=4
        )
        
        assert result["tool"] == "pilon"
        assert mock_pilon.called
        
        # 验证调用参数
        call_args = mock_pilon.call_args
        assert call_args.kwargs["threads"] == 4
        assert call_args.kwargs["iterations"] == 1
        assert call_args.kwargs["memory"] == "16G"


def test_run_polishing_medaka():
    """测试 Medaka 抛光调用"""
    with patch("mito_forge.graph.nodes.run_medaka") as mock_medaka:
        mock_medaka.return_value = {
            "tool": "medaka",
            "polished_file": "/tmp/polished.fasta",
            "model": "r941_min_high_g360"
        }
        
        result = _run_polishing(
            reads_file="/tmp/reads.fastq",
            reads2_file=None,
            assembly_file="/tmp/assembly.fasta",
            output_dir=Path("/tmp/polish"),
            tool="medaka",
            read_type="nanopore",
            threads=4
        )
        
        assert result["tool"] == "medaka"
        assert mock_medaka.called


def test_calculate_improvement():
    """测试改进计算"""
    # 创建临时 FASTA 文件用于测试
    import tempfile
    from Bio import SeqIO
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f1, \
         tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f2:
        
        # 原始序列
        orig_seq = SeqRecord(Seq("A" * 10000), id="contig1")
        SeqIO.write([orig_seq], f1, "fasta")
        f1.flush()
        
        # 抛光后序列（稍长）
        polish_seq = SeqRecord(Seq("A" * 10050), id="contig1")
        SeqIO.write([polish_seq], f2, "fasta")
        f2.flush()
        
        result = _calculate_improvement(f1.name, f2.name)
        
        assert result["status"] == "calculated"
        assert result["length_change"] == 50
        assert result["length_change_pct"] == pytest.approx(0.5, 0.01)
        assert result["original"]["total_length"] == 10000
        assert result["polished"]["total_length"] == 10050
        
        # 清理
        Path(f1.name).unlink()
        Path(f2.name).unlink()


def test_polish_node_error_handling():
    """测试 polishing 错误处理"""
    state = init_pipeline_state(
        inputs={"reads": "test.fastq"},
        config={
            "tool_chain": {"polishing": "racon"},
            "detected_read_type": "nanopore"
        },
        workdir="/tmp/test",
        pipeline_id="test"
    )
    
    state["stage_outputs"]["assembly"] = {
        "files": {"assembly": "/tmp/assembly.fasta"}
    }
    
    # Mock _run_polishing 抛出异常
    with patch("mito_forge.graph.nodes.Path.exists", return_value=True), \
         patch("mito_forge.graph.nodes.Path.mkdir"), \
         patch("mito_forge.graph.nodes._run_polishing", side_effect=Exception("Tool failed")):
        
        result = polish_node(state)
    
    # 抛光失败不应该终止流程
    assert result["route"] == "continue"
    assert state["stage_status"]["polish"] == "failed"


def test_run_polishing_unknown_tool():
    """测试未知工具错误"""
    with pytest.raises(ValueError, match="Unknown polishing tool"):
        _run_polishing(
            reads_file="/tmp/reads.fastq",
            reads2_file=None,
            assembly_file="/tmp/assembly.fasta",
            output_dir=Path("/tmp/polish"),
            tool="unknown_tool",
            read_type="illumina",
            threads=4
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
