"""
LangGraph 多智能体流水线演示
展示如何使用新的状态驱动架构
"""
import tempfile
from pathlib import Path
from mito_forge.graph.build import run_pipeline_sync, save_checkpoint
from mito_forge.graph.state import init_pipeline_state

def demo_basic_pipeline():
    """演示基本流水线执行"""
    print("🧬 LangGraph 多智能体流水线演示")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 模拟输入数据
        inputs = {
            "reads": "demo_nanopore_reads.fastq"
        }
        
        config = {
            "threads": 4,
            "kingdom": "animal",
            "assembler_preference": ["flye", "spades"],
            "genetic_code": 2
        }
        
        print(f"📁 工作目录: {tmpdir}")
        print(f"📊 输入配置: {config}")
        print()
        
        # 运行流水线
        print("🚀 启动流水线...")
        final_state = run_pipeline_sync(
            inputs=inputs,
            config=config,
            workdir=tmpdir,
            pipeline_id="demo_001"
        )
        
        # 显示结果
        print("\n📋 执行结果:")
        print(f"  状态: {'✅ 完成' if final_state['done'] else '❌ 失败'}")
        print(f"  流水线ID: {final_state['pipeline_id']}")
        print(f"  已完成阶段: {', '.join(final_state['completed_stages'])}")
        
        if final_state['errors']:
            print(f"  错误: {final_state['errors']}")
        
        # 显示各阶段输出
        print("\n📊 各阶段结果:")
        for stage, outputs in final_state['stage_outputs'].items():
            print(f"  {stage}:")
            if 'metrics' in outputs:
                for key, value in outputs['metrics'].items():
                    print(f"    {key}: {value}")
        
        return final_state

def demo_checkpoint_resume():
    """演示检查点和恢复功能"""
    print("\n🔄 检查点和恢复演示")
    print("=" * 30)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = Path(tmpdir) / "pipeline.checkpoint"
        
        # 创建一个中间状态
        state = init_pipeline_state(
            inputs={"reads": "test.fastq"},
            config={"threads": 2},
            workdir=tmpdir
        )
        
        # 模拟部分完成
        state['completed_stages'] = ['supervisor', 'qc']
        state['current_stage'] = 'assembly'
        state['stage_outputs'] = {
            'qc': {
                'files': {'clean_reads': 'qc/clean.fastq'},
                'metrics': {'qc_score': 0.95}
            }
        }
        
        # 保存检查点
        save_checkpoint(state, str(checkpoint_path))
        print(f"💾 检查点已保存: {checkpoint_path}")
        
        # 从检查点恢复
        from mito_forge.graph.build import load_checkpoint
        restored_state = load_checkpoint(str(checkpoint_path))
        
        print(f"🔄 恢复状态:")
        print(f"  当前阶段: {restored_state['current_stage']}")
        print(f"  已完成: {restored_state['completed_stages']}")

def demo_strategy_selection():
    """演示智能策略选择"""
    print("\n🧠 智能策略选择演示")
    print("=" * 30)
    
    test_cases = [
        {"reads": "nanopore_sample.fastq", "kingdom": "animal"},
        {"reads": "illumina_sample.fastq", "kingdom": "plant"},
        {"reads": "pacbio_hifi_sample.fastq", "kingdom": "animal"}
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}:")
        print(f"  输入: {case}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            state = init_pipeline_state(
                inputs=case,
                config={"threads": 2},
                workdir=tmpdir
            )
            
            # 只运行 supervisor 来看策略选择
            from mito_forge.graph.nodes import supervisor_node
            result_state = supervisor_node(state)
            
            strategy = result_state['config']['selected_strategy']
            print(f"  选择策略: {strategy['name']}")
            print(f"  工具链: {strategy['tools']}")

if __name__ == "__main__":
    # 运行所有演示
    demo_basic_pipeline()
    demo_checkpoint_resume()
    demo_strategy_selection()
    
    print("\n🎉 演示完成！")
    print("\n💡 使用方法:")
    print("  python -m mito_forge pipeline --reads your_data.fastq --output results")
    print("  python -m mito_forge status --checkpoint results/checkpoint.json")
    print("  python -m mito_forge pipeline --resume results/checkpoint.json")