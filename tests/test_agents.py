"""
Agent 基础架构测试
"""
import pytest
from pathlib import Path
from mito_forge.core.agents import BaseAgent, AgentStatus, StageResult, TaskSpec, AgentCapability

class TestAgent(BaseAgent):
    """测试用的简单 Agent 实现"""
    
    def prepare(self, workdir: Path, **kwargs):
        self.workdir = workdir
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = workdir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def run(self, inputs, **config):
        # 模拟一些工作
        self.emit_event("progress", percent=50, message="Processing...")
        
        # 创建一个测试输出文件
        output_file = self.workdir / "test_output.txt"
        output_file.write_text("Test output content")
        
        return StageResult(
            status=AgentStatus.FINISHED,
            outputs={"test_file": output_file},
            metrics={"test_metric": 42}
        )
    
    def finalize(self):
        # 清理工作
        pass
    
    def get_capability(self):
        return AgentCapability(
            name="test_agent",
            supported_inputs=["test_input"],
            supported_outputs=["test_output"],
            required_tools=[]
        )

def test_agent_lifecycle():
    """测试 Agent 基本生命周期"""
    agent = TestAgent("test_agent")
    
    # 初始状态
    assert agent.get_status() == AgentStatus.IDLE
    
    # 创建任务
    task = TaskSpec(
        task_id="test_task_001",
        agent_type="test",
        inputs={"test_input": "test_data"}
    )
    
    # 执行任务
    result = agent.execute_task(task)
    
    # 验证结果
    assert result.status == AgentStatus.FINISHED
    assert "test_file" in result.outputs
    assert result.metrics["test_metric"] == 42
    assert result.agent_name == "test_agent"

def test_agent_event_callback():
    """测试事件回调机制"""
    events = []
    
    def event_handler(event):
        events.append(event)
    
    agent = TestAgent("test_agent")
    agent.set_event_callback(event_handler)
    
    task = TaskSpec(
        task_id="test_task_002",
        agent_type="test",
        inputs={"test_input": "test_data"}
    )
    
    result = agent.execute_task(task)
    
    # 验证事件
    assert len(events) >= 3  # started, progress, finished
    assert events[0].event_type == "started"
    assert events[-1].event_type == "finished"
    
    # 检查进度事件
    progress_events = [e for e in events if e.event_type == "progress"]
    assert len(progress_events) >= 1
    assert progress_events[0].payload["percent"] == 50

def test_agent_capability():
    """测试 Agent 能力描述"""
    agent = TestAgent("test_agent")
    capability = agent.get_capability()
    
    assert capability.name == "test_agent"
    assert "test_input" in capability.supported_inputs
    assert "test_output" in capability.supported_outputs

def test_agent_validation():
    """测试输入验证"""
    agent = TestAgent("test_agent")
    
    # 有效输入
    valid_inputs = {"test_input": "data"}
    errors = agent.validate_inputs(valid_inputs)
    assert len(errors) == 0
    
    # 无效输入
    invalid_inputs = {"wrong_input": "data"}
    errors = agent.validate_inputs(invalid_inputs)
    assert len(errors) > 0
    assert "Missing required input: test_input" in errors

if __name__ == "__main__":
    # 简单的手动测试
    print("Testing Agent base architecture...")
    
    test_agent_lifecycle()
    print("✓ Agent lifecycle test passed")
    
    test_agent_event_callback()
    print("✓ Event callback test passed")
    
    test_agent_capability()
    print("✓ Capability test passed")
    
    test_agent_validation()
    print("✓ Validation test passed")
    
    print("All tests passed! Agent base architecture is working.")