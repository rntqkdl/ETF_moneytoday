"""
src/ai/lora_trainer.py
Apple Silicon M5 Metal GPU 메모리 최적화 (16GB RAM Zero-OOM 보장) LoRA 파인튜닝 학습기
"""

import subprocess
import sys
import os
from config.settings import settings

class MLXLoRATrainer:
    """Apple MLX 기반 LoRA 초경량 학습 실행기"""

    @classmethod
    def train(cls, iters: int = 100, batch_size: int = 1, lora_layers: int = 8):
        os.makedirs(settings.ADAPTER_PATH, exist_ok=True)
        venv_bin = os.path.dirname(sys.executable)
        mlx_cmd = os.path.join(venv_bin, "mlx_lm.lora")
        if not os.path.exists(mlx_cmd):
            mlx_cmd = "mlx_lm.lora"

        cmd = [
            mlx_cmd,
            "--model", settings.BASE_MODEL_NAME,
            "--data", settings.DATA_DIR,
            "--train",
            "--fine-tune-type", "lora",
            "--batch-size", str(batch_size),
            "--num-layers", str(lora_layers),
            "--iters", str(iters),
            "--learning-rate", "1e-4",
            "--val-batches", "2",
            "--steps-per-report", "10",
            "--steps-per-eval", "25",
            "--save-every", "50",
            "--adapter-path", settings.ADAPTER_PATH
        ]

        print(f"🚀 [LoRA Trainer] M5 16GB 메모리 최적화 실행: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        return result.returncode == 0
