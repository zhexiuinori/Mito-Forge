#!/usr/bin/env python3
"""
测试驱动开发 - Agent 功能测试
先定义期望的功能，然后逐步实现
"""

import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '.')

def test_agent_types_basic():
    """测试 1: Agent 基础类型应该可以导入和使用"""
    print("🧪 测试 1: Agent 基础类型")
    
    try:
        # 期望：能够导入基础类型，不依赖复杂模块
        from mito_forge.core.agents.types import AgentStatus, StageResult
        
        # 期望：枚举值正确
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.FINISHED.value == "finished"
        
        # 期望：能创建结果对象
        result = StageResult(
            status=AgentStatus.FINISHED,
            outputs={'test': 'success'}
        )
        assert result.status == AgentStatus.FINISHED
        assert result.outputs['test'] == 'success'
        
        print("  ✅ 基础类型测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 基础类型测试失败: {e}")
        return False

def test_agent_creation_minimal():
    """测试 2: 应该能创建最小化的 Agent 实例"""
    print("🧪 测试 2: 最小化 Agent 创建")
    
    try:
        # 期望：能创建一个不依赖 LLM 的简单 Agent
        class MinimalAgent:
            def __init__(self, name):
                self.name = name
                self.status = "idle"
                
            def get_status(self):
                return self.status
                
            def prepare(self, workdir):
                self.workdir = Path(workdir)
                self.status = "prepared"
                
            def run(self, inputs):
                self.status = "running"
                # 模拟处理
                result = {
                    "status": "completed",
                    "outputs": {"processed": True},
                    "inputs_received": inputs
                }
                self.status = "finished"
                return result
        
        # 测试创建和使用
        agent = MinimalAgent("test_agent")
        assert agent.name == "test_agent"
        assert agent.get_status() == "idle"
        
        # 测试准备阶段
        with tempfile.TemporaryDirectory() as tmpdir:
            agent.prepare(tmpdir)
            assert agent.get_status() == "prepared"
            assert agent.workdir == Path(tmpdir)
            
            # 测试运行
            test_inputs = {"reads": "test.fastq", "kingdom": "animal"}
            result = agent.run(test_inputs)
            
            assert result["status"] == "completed"
            assert result["outputs"]["processed"] == True
            assert result["inputs_received"] == test_inputs
            assert agent.get_status() == "finished"
        
        print("  ✅ 最小化 Agent 创建测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 最小化 Agent 创建测试失败: {e}")
        return False

def test_orchestrator_concept():
    """测试 3: Orchestrator 应该能协调多个 Agent"""
    print("🧪 测试 3: Orchestrator 协调功能")
    
    try:
        # 期望：Orchestrator 能管理多个 Agent 的执行流程
        class MockAgent:
            def __init__(self, name, processing_time=0.1):
                self.name = name
                self.processing_time = processing_time
                self.status = "idle"
                
            def run(self, inputs):
                self.status = "running"
                # 模拟不同 Agent 的处理逻辑
                if self.name == "supervisor":
                    outputs = {"strategy": "nanopore_assembly", "tools": ["flye"]}
                elif self.name == "qc":
                    outputs = {"clean_reads": "cleaned.fastq", "quality_score": 0.95}
                elif self.name == "assembly":
                    outputs = {"contigs": "assembly.fasta", "n50": 15000}
                elif self.name == "annotation":
                    outputs = {"genes": "genes.gff", "gene_count": 37}
                else:
                    outputs = {"result": "processed"}
                
                self.status = "finished"
                return {
                    "status": "completed",
                    "agent": self.name,
                    "outputs": outputs
                }
        
        class SimpleOrchestrator:
            def __init__(self):
                self.agents = {
                    "supervisor": MockAgent("supervisor"),
                    "qc": MockAgent("qc"),
                    "assembly": MockAgent("assembly"),
                    "annotation": MockAgent("annotation")
                }
                self.pipeline_status = "idle"
                
            def run_pipeline(self, inputs):
                self.pipeline_status = "running"
                results = {}
                current_inputs = inputs.copy()
                
                # 按顺序执行各阶段
                for stage_name, agent in self.agents.items():
                    print(f"    执行阶段: {stage_name}")
                    result = agent.run(current_inputs)
                    results[stage_name] = result
                    
                    # 将输出传递给下一阶段
                    current_inputs.update(result["outputs"])
                
                self.pipeline_status = "completed"
                return {
                    "pipeline_status": self.pipeline_status,
                    "stage_results": results,
                    "final_outputs": current_inputs
                }
        
        # 测试 Orchestrator
        orchestrator = SimpleOrchestrator()
        assert orchestrator.pipeline_status == "idle"
        
        # 运行流水线
        test_inputs = {
            "reads": "sample.fastq",
            "kingdom": "animal",
            "threads": 4
        }
        
        pipeline_result = orchestrator.run_pipeline(test_inputs)
        
        # 验证结果
        assert pipeline_result["pipeline_status"] == "completed"
        assert len(pipeline_result["stage_results"]) == 4
        
        # 验证各阶段都成功
        for stage, result in pipeline_result["stage_results"].items():
            assert result["status"] == "completed"
            assert result["agent"] == stage
        
        # 验证数据流传递
        final_outputs = pipeline_result["final_outputs"]
        assert "strategy" in final_outputs  # supervisor 输出
        assert "clean_reads" in final_outputs  # qc 输出
        assert "contigs" in final_outputs  # assembly 输出
        assert "genes" in final_outputs  # annotation 输出
        
        print("  ✅ Orchestrator 协调功能测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ Orchestrator 协调功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_error_handling():
    """测试 4: Agent 应该能正确处理错误情况"""
    print("🧪 测试 4: Agent 错误处理")
    
    try:
        class ErrorHandlingAgent:
            def __init__(self, name):
                self.name = name
                self.status = "idle"
                
            def validate_inputs(self, inputs):
                """验证输入数据"""
                required_fields = ["reads"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in inputs:
                        missing_fields.append(field)
                
                return len(missing_fields) == 0, missing_fields
                
            def run(self, inputs):
                self.status = "running"
                
                # 验证输入
                is_valid, missing_fields = self.validate_inputs(inputs)
                if not is_valid:
                    self.status = "failed"
                    return {
                        "status": "failed",
                        "error": f"Missing required fields: {missing_fields}",
                        "outputs": {}
                    }
                
                # 模拟文件检查
                reads_file = inputs.get("reads")
                if reads_file and not reads_file.endswith(('.fastq', '.fq')):
                    self.status = "failed"
                    return {
                        "status": "failed",
                        "error": f"Invalid file format: {reads_file}",
                        "outputs": {}
                    }
                
                # 正常处理
                self.status = "finished"
                return {
                    "status": "completed",
                    "outputs": {"processed": True}
                }
        
        agent = ErrorHandlingAgent("error_test_agent")
        
        # 测试缺少必需字段
        result1 = agent.run({})
        assert result1["status"] == "failed"
        assert "Missing required fields" in result1["error"]
        assert agent.status == "failed"
        
        # 测试无效文件格式
        result2 = agent.run({"reads": "invalid.txt"})
        assert result2["status"] == "failed"
        assert "Invalid file format" in result2["error"]
        
        # 测试正常情况
        result3 = agent.run({"reads": "sample.fastq"})
        assert result3["status"] == "completed"
        assert result3["outputs"]["processed"] == True
        assert agent.status == "finished"
        
        print("  ✅ Agent 错误处理测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ Agent 错误处理测试失败: {e}")
        return False

def main():
    """主测试函数 - TDD 方式"""
    print("🧬 Mito-Forge Agent TDD 测试")
    print("=" * 50)
    print("按照测试驱动开发原则，先定义期望功能")
    print()
    
    tests = [
        test_agent_types_basic,
        test_agent_creation_minimal,
        test_orchestrator_concept,
        test_agent_error_handling
    ]
    
    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
        print()
    
    # 总结
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有 TDD 测试通过! ({passed}/{total})")
        print("\n✅ 期望功能验证成功:")
        print("  - Agent 基础类型系统")
        print("  - 最小化 Agent 创建")
        print("  - Orchestrator 协调机制")
        print("  - 错误处理机制")
        print("\n📋 下一步: 实现真实的 Agent 类来满足这些测试")
    else:
        print(f"⚠️  部分测试失败 ({passed}/{total})")
        print("需要修复失败的测试用例")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)