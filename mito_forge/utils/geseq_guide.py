"""GeSeq Web服务交互向导"""

import webbrowser
from pathlib import Path
from typing import Dict
import json
import uuid
from .logging import get_logger

logger = get_logger(__name__)


class GeSeqGuide:
    """GeSeq注释向导"""
    
    GESEQ_URL = "https://chlorobox.mpimp-golm.mpg.de/geseq.html"
    
    def __init__(self, assembly_path: Path, kingdom: str, workdir: Path):
        self.assembly_path = assembly_path
        self.kingdom = kingdom
        self.workdir = workdir
        self.task_id = self._generate_task_id()
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        return str(uuid.uuid4())[:8]
    
    def display_instructions(self):
        """显示详细的操作指南"""
        print("\n" + "=" * 70)
        print("🔬 GeSeq 注释向导")
        print("=" * 70)
        print(f"\n📋 任务ID: {self.task_id}")
        print(f"📁 待注释文件: {self.assembly_path}")
        print(f"\n步骤 1: 打开GeSeq网站")
        print(f"  URL: {self.GESEQ_URL}")
        print(f"  (浏览器将自动打开)")
        
        print(f"\n步骤 2: 上传序列文件")
        print(f"  点击 'Choose File' 并选择:")
        print(f"  {self.assembly_path.absolute()}")
        
        print(f"\n步骤 3: 配置参数 (推荐)")
        print(f"  ☑ Sequence source: MPI-MP chloroplast references")
        print(f"  ☑ BLAT search: Plant mitochondria")
        print(f"  ☑ BLAT identity: 85%")
        print(f"  ☑ Annotate plastid IR: ON")
        print(f"  ☑ Generate multi GenBank: ON")
        
        print(f"\n步骤 4: 提交任务")
        print(f"  点击 'ANNOTATE' 按钮")
        print(f"  等待任务完成 (通常5-15分钟)")
        
        print(f"\n步骤 5: 下载结果")
        print(f"  下载 'GenBank file' (.gbk格式)")
        print(f"  保存到任意位置")
        
        print(f"\n步骤 6: 恢复Pipeline")
        print(f"  运行命令:")
        print(f"  mito-forge resume {self.task_id} --annotation <结果.gbk>")
        
        print("\n" + "=" * 70)
        print("💡 提示: 保持终端开启,完成后运行resume命令")
        print("=" * 70 + "\n")
        
        # 保存checkpoint
        self._save_checkpoint()
    
    def _save_checkpoint(self):
        """保存checkpoint供resume使用"""
        checkpoint_file = self.workdir / f"checkpoint_{self.task_id}.json"
        checkpoint_data = {
            "task_id": self.task_id,
            "assembly_path": str(self.assembly_path),
            "kingdom": self.kingdom,
            "stage": "annotation_paused",
            "awaiting": "geseq_result"
        }
        checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))
        logger.info(f"Checkpoint saved: {checkpoint_file}")
    
    def open_browser(self):
        """打开浏览器"""
        try:
            webbrowser.open(self.GESEQ_URL)
            logger.info(f"Opened GeSeq in browser: {self.GESEQ_URL}")
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")
            print(f"⚠️  无法自动打开浏览器,请手动访问: {self.GESEQ_URL}")
